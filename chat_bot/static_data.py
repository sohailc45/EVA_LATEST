 
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

persist_directory =  'chroma_db_files/'
# Create or get the collection
collection_name = "practice_info2"
 
emb_model = "sentence-transformers/paraphrase-MiniLM-L3-v2"
embeddings = HuggingFaceEmbeddings(model_name=emb_model)
# Practice information as key-value pairs
practice_info = {
    "Practice Name": "Rose City Eye Care",
    "Practice Hours": "8 AM to 8 PM PST",
    "Practice Email": "RoseCity@gmail.com",
    "US Office Address": "6723 NE Bennett Street, Suite 200, Hillsboro, Oregon 97124",
    "India Office Address": "2nd Floor, Server Space, AG Technology Park, Aundh, Pune – 411 007",
    "Insurance Coverage": "https://www.first-insight.com/",
    "Providers": (
        "Dr Anderson (Pediatrics): 12 Years of extensive experience in Pediatric eye surgeries; "
        "Dr John (Surgeon): xxxx"
    ),
    "Services": "OPD, Cataract Surgery, Glaucoma",
    "Products": "Complete Eye check up: 200$, Comprehensive Eye checkup: 100$",
    "Parking Instructions": "Please park your vehicle in parking at L1 level in parking reserved for our clinic",
    "What to Bring": "Last medical report, Insurance card copy",
    "Cancellation Policy": "Refer google.com for cancellation policy",
    "Payment Types": "VISA, Credit card, Gpay, Cash, CareCredit",
    "Financing Options": "Yes, With several credit cards we do provide EMI option",
    "Languages Spoken": "Spanish, English",
    "Accessibility": "Yes",
    "Discounts": "Yes, we do offer 10% discount on Military employees",
    "Online Paperwork": "Yes, please visit https://intake.maximeyes.com to fill intake forms",
    "Online Payments": "Yes, We do support VISA Credit card, Gpay, Cash",
    "Online Booking": "Yes, https://booking.max.com",
    "Early Arrival": "No",
    "Wait List": "Yes, but there is no guarantee if you get an appointment or not."
}
 
practice_info2={
  "Practice Name": "First Insight Vision",
  "Practice Hours": "9 AM to 4 PM PST",
  "Practice Email": "eyecare@gmail.com",
  "Office Address": {
    "U.S Corporate Office": {
      "Name": "Rose City Eye Care",
      "Street": "5423 NE Central Street",
      "Suite": "Suite 40",
      "City": "New York",
      "Zip": "12322"
    }
  },
  "Insurance Coverage": "https://www.maximeyes.com/",
  "Providers": [
    {
      "Name": "Dr Willamson",
      "Specialty": "Pediatrics",
      "Experience": "18 Years of extensive experience in Pediatric eye surgeries"
    },
    {
      "Name": "Dr John",
      "Specialty": "Surgeon",
      "Experience": "xxxxx"
    }
  ],
  "Services": [
    "OPD",
    "Glaucoma",
    "Lasik Surgery"
  ],
  "Products": [
    {
      "Description": "Complete Eye check up",
      "Price": "600$"
    },
    {
      "Description": "Comprehensive Eye checkup",
      "Price": "400$"
    }
  ],
  "Parking Instructions": "Please park your vehicle in parking at L2 level in parking reserved for our clinic",
  "What to Bring": [
    "Last medical report",
    "Insurance card copy"
  ],
  "Cancellation Policy": "Refer maximeyes.com for cancellation policy",
  "Payment Types Accepted": [
    "Cash",
    "GPay"
  ],
  "Financing Options Available": "Yes, With several credit cards we do provide EMI option",
  "Languages Spoken": "English",
  "Accessibility": "Yes",
  "Discounts": "No",
  "Online Paperwork": {
    "Available": "Yes",
    "Instructions": "It is there and we recommend to fill before coming to clinic, it will save too much time, please visit https://intake.maximeyes.com to fill intake forms"
  },
  "Online Booking": {
    "Available": "Yes",
    "Link": "https://booking.maximeyes.com"
  },
  "Early Arrival": "No",
  "Wait List": "No"
}
 
def vectorDB(subject, practice_info2):
    db = Chroma.from_texts(
        collection_name=f"{subject}",
        texts=[f"{key}: {value}" for key, value in practice_info2.items()],
        embedding=embeddings,
        persist_directory=persist_directory
    )
    db.persist()
    print(f"VectorDB '{subject}' created and persisted.")
    return db
# Check if the collection is empty before adding
def connect_to_vectorDB(subject):
    try:
        vector_db = Chroma(collection_name=f"{subject}", persist_directory=persist_directory, embedding_function=embeddings)
        print('Connected to vector DB')
        return vector_db
    except Exception as e:
        print(f"Error occurred: {e}")
def save_practise_to_vectorDB(subject="practice_info2"):
    vector_db = vectorDB(subject, practice_info2)
    if vector_db:
        print("Practice information added successfully.")
 
 
def query_chroma_and_generate_response(query, subject="practice_info2"):
    vector_db = connect_to_vectorDB(subject)
    if vector_db:
        results = vector_db.similarity_search(query, k=1)
        if results:
            return results[0]
        else:
            return "Sorry, I couldn't find an answer to your question."
       
 
# save_practise_to_vectorDB()
 
# # Example question
# user_question = "What are the practice hours?"
 
# # Query ChromaDB and get the response
# response = query_chroma_and_generate_response(user_question)
 
# print("ResponsexsnjfhniEABHWnJ:", response)
 
 
 