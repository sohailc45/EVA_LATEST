from typing import List, Dict, Any
import threading

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.utils import ConfigurableFieldSpec
import chromadb
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from flask import jsonify
# from utils import setup_logging
from chat_bot.config import CHROMA_DB_PATH, MODEL_NAME, GROQ_API_KEY, PRODUCTS, EMBEDDING
import json
import re
import warnings

warnings.filterwarnings('ignore')

# logger = setup_logging()

### Chat session
class ChatSession: 
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.max_history = 20
        self.lock = threading.Lock()

    def add_message(self, role: str, content: str):
        with self.lock:
            self.history.append({"role": role, "content": content})
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]

    def get_history(self) -> List[Dict[str, str]]:
        with self.lock:
            return self.history.copy()

    def clear_history(self):
        with self.lock:
            self.history.clear()

# Global chat session object
chat_session = None

# Global dictionary to store user sessions
# user_sessions = {}
# sessions_lock = threading.Lock()

## User session management
# def get_or_create_session(user_id: str) -> ChatSession:
#     with sessions_lock:
#         if user_id not in user_sessions:
#             user_sessions[user_id] = ChatSession()
#         return user_sessions[user_id]

# def initialize_service(user_id: str):
#     session = get_or_create_session(user_id)
#     session.clear_history()

# def end_service(user_id: str):
#     with sessions_lock:
#         if user_id in user_sessions:
#             del user_sessions[user_id]

## define llm
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
## Dictionary for history store user id wise
store = {}


## loading database using path
def load_from_local():
    """Load the Chroma database from local storage."""
    try:
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        return db
    except Exception as e:
        # logger.error("Error while loading Database...")
        return jsonify({"status": "error", "message": "Error while loading database."}), 400

### retriever function
def retriever(query: str, product_name: str, k: int = 10) -> list[Document]:
    """Retrieve relevant documents based on the query and product name."""
    
    db = load_from_local()
    collection = db.get_collection(product_name)

    results = collection.query(query_texts=[query], n_results=k)
    
    processed_results = []
    for i in range(min(k, len(results['ids'][0]))):
        data = Document(page_content=results["documents"][0][i], metadata=results["metadatas"][0][i])
        data.metadata['score'] = results["distances"][0][i]
        processed_results.append(data)

    return processed_results

### creating history aware retriever with updated k value
def create_history_aware_retriever_with_k(llm, contextualize_q_prompt, product_name, k):
    @chain
    def retriever_with_k(query: str) -> list[Document]:
        return retriever(query, product_name, k)
    
    return create_history_aware_retriever(
        llm, retriever_with_k, contextualize_q_prompt
    )


### geting session history using user id and conversation id
def get_session_history(
    user_id: str, conversation_id: str
) -> BaseChatMessageHistory:
    if (user_id, conversation_id) not in store:
        store[(user_id, conversation_id)] = ChatMessageHistory()
    return store[(user_id, conversation_id)]

### creating dynamic qa chain
def create_dynamic_qa_chain(llm, qa_system_prompt, product_name):
    
    formatted_prompt = qa_system_prompt.format(product=product_name, context="{context}")
    
    # Create the prompt template
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", formatted_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # Create and return the QA chain
    return create_stuff_documents_chain(llm, qa_prompt)


### creating dynamic contextualize chain
def create_dynamic_contextualize_q_prompt(llm, contextualize_q_system_prompt, product_name, k):
    
    formatted_prompt = contextualize_q_system_prompt.format(product=product_name)

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", formatted_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    return create_history_aware_retriever_with_k(llm, contextualize_q_prompt,str(product_name), k)




## query the database and getting response from llm
# def unified_query(query, session: ChatSession, product, vid_src, pdf_src, k, user_id):
def unified_query(query, product, vid_src, pdf_src, k, user_id):
    """Generate an answer based on the query and return it in the required format."""

    if product not in PRODUCTS:
        return {
        "Answer": f"Product '{product}' not found in our database.",
        "Video_Source": None,
        "PDF_Sources": None,
        "QnA_Source": None
    }
    



    ### define prompts
    ### Contextualize question
    contextualize_q_system_prompt = """You are a {product} AI assistant For M{product}Platform. \
        Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is.
        Note: Don't answer any questions outside {product} platform or Non relevant to the provided context or chat history . \
        """

    ## Answer question ###
    qa_system_prompt = """You are a {product} AI assistant For {product} Platform. Answer the following question like an assistant using only the information provided \
    in the given context. If the answer cannot be fully determined from the context, say 'I don't have enough information to answer that question. \
    Kindly connect with First Insight Representative.' \
    Do not use any external knowledge or make assumptions beyond what is explicitly stated in the context. \
    Note: Don't answer any questions outside {product} platform or Non relevant to the provided context or chat history . \
    "Provide the answer directly without using any prefixes such as 'According to' or 'Based on'. Give only the relevant information from the provided context."
    {context}"""


    ### history aware retriever without k
    # history_aware_retriever = create_history_aware_retriever(
    #     llm, , contextualize_q_prompt
    # )

    ### history aware retriever with k
    # history_aware_retriever = create_history_aware_retriever_with_k(llm, contextualize_q_prompt, str(product), k)
    history_aware_retriever = create_dynamic_contextualize_q_prompt(llm, contextualize_q_system_prompt, str(product), k)

    ### qa chain
    question_answer_chain = create_dynamic_qa_chain(llm, qa_system_prompt, str(product))

    ### complete rag chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
        history_factory_config=[
        ConfigurableFieldSpec(
            id="user_id",
            annotation=str,
            name="User ID",
            description="Unique identifier for the user.",
            default="",
            is_shared=True,
        ),
        ConfigurableFieldSpec(
            id="conversation_id",
            annotation=str,
            name="Conversation ID",
            description="Unique identifier for the conversation.",
            default="",
            is_shared=True,
        ),
    ],
    )

    try:
        ### getting response form llm
        ans = conversational_rag_chain.invoke({"input": query}, config={
            "configurable": {"user_id": user_id, "conversation_id": "1"}
        },)
        
        ### saving metadata
        metadatas = [i.metadata for i in ans["context"]]

    except Exception as e:
        ans = "I don't have enough information to answer that question." 
        metadatas = "no metadata"


    # session.add_message("human", query)
    # session.add_message("assistant", ans['answer'])

    if re.search("I don't have enough information", ans["answer"]):
        return {"Answer": "I don't have enough information to answer that question. Kindly connect with First Insight Representative or Rephrase your question.", 
                "Video_Source": None, 
                "PDF_Sources": None, 
                "QnA_Source": None}
    
    return format_answer(query, ans["answer"], metadatas, vid_src, pdf_src)

### checking image relevancy
def analyze_image_relevance(question: str, answer: str, image_description: str) -> float:
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("human", """
            Question: {question}
            Answer: {answer}
            Image Description: {image_description}

            On a scale of 0 to 1, how relevant is this image to the question and answer?
            NOTE: Provide only a number as the response, with 1 being highly relevant and 0 being not relevant at all.
            """)
        ])
        chain = LLMChain(llm=llm, prompt=prompt)
        response = chain.run(question=question, answer=answer, image_description=image_description)
        response = float(response.strip())
        return response
    
    except Exception as e:
        # logger.error("Error while image analysis...")
        return jsonify({"status": "error", "message": "Error while image analysis"}), 400

### formating sources using score
def format_answer(query, answer, metadatas, vid_src: int = 1, pdf_src: int = 1):
    video_sources = []
    pdf_sources = []
    qna_source = None

    for metadata in metadatas:
        
        if metadata["source_type"] == 'qna' and metadata["score"] < 0.8 and qna_source is None:
            qna_source = metadata.get('source', 'QnA Database')

        elif metadata["source_type"] == 'video' and len(video_sources) < vid_src and metadata["score"] < 1.1:
            video_sources.append({
                "file_link": metadata.get('file_link'),
                "file_name": metadata.get('file_name'),
                "source": metadata.get('source'),
                "start_time": metadata.get('start_time'),
                "stop_time": metadata.get('stop_time'),
                "score": metadata.get('score'),
            })
        elif metadata["source_type"] == 'pdf' and len(pdf_sources) < pdf_src and metadata["score"] < 1.1:
            pdf_source = {
                "source": metadata.get('source'),
                "file_link": metadata.get('file_link'),
                "page": metadata.get('page'),
                "images": []
            }
            if 'images' in metadata:
                image_metadata = json.loads(metadata['images'])
                for img in image_metadata:
                    relevancy_score = analyze_image_relevance(query, answer, img.get('description', ''))
                    
                    if relevancy_score > 0.5:
                        pdf_source['images'].append({
                            'index': img.get('index'),
                            'base64': img.get('image_base64'),
                            'relevance_score': relevancy_score
                        })
            pdf_sources.append(pdf_source)


    return {
        "Answer": answer,
        "Video_Source": video_sources if video_sources else None,
        "PDF_Sources": pdf_sources if pdf_sources else None,
        "QnA_Source": qna_source
        }

