from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
from datetime import datetime
import re
import requests
from langchain.agents import tool
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langchain import hub
from langchain.agents import AgentExecutor,  create_react_agent
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
# from langchain.core.messages import HumanMessage, AIMessage
# from . model_loader import *
from langchain_community.llms import HuggingFaceTextGenInference
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
from langchain_community.llms import HuggingFaceEndpoint
# Define your custom prompt template
from chat_bot.models import UserProfile,ChatHistory
import uuid
from chat_bot.static_data import *
logfile = "output.log"
from langchain_core.callbacks import FileCallbackHandler, StdOutCallbackHandler
from loguru import logger
 
logger.add(logfile, colorize=True, enqueue=True)
handler_1 = FileCallbackHandler(logfile)
handler_2 = StdOutCallbackHandler()
prompt = PromptTemplate(
    template=("""
     <|begin_of_text|><|start_header_id|>system<|end_header_id|>
      
      You are the health care assistent Agent read the user queries and return the response using the tools
      you do not know any thing  you will use tools for everything. 
      do not put information like users details and other things if user has not shared it yet.
      Answer the following questions as best you can. You have access to the following tools:
      return the answers as soon as you get the answer to the question
      also keep the chat history in mind 
      if user ask query related to appointment with greeting like hi..then donot go to greeting response.you have to go fetch info tool for book appointment
      IF user ask any static informationn like office addres ,timing or related to  organisation then donot use fetch info
      read the instruction carefully and follow the steps.
      understand the chat history and see what user wants to do and make the action input accordingly.
      try 1 iteration only and if result is not found return this text ```Please clarify your query so I can assist you better.```
    
      Chat_history: {agent_scratchpad}
      
         
              
      Tools: {tools}
      Tools_names: {tool_names}
      Tools_description : {tool_description}
      Tools_args : {tool_args}
  
      Use the following format:
  
      Question: the input question you must answer.
  
      Thought: you should always think about what to do.
  
      Action: the action to take, should be one of [{tool_names}]
  
      Action Input: input to the action as a dictionary.
  
      Observation: Observe the result of the action.
      output : Observation.
  
      ... (this Thought/Action/Action Input/Observation can repeat only 1 time.)
  
      Thought: I now know the final answer

      Final Answer: the final answer to the original input question based on observation
      terminate the chain
      Begin!

      Question: {input}

      Thought:{agent_scratchpad}
    
      stop the chain after the obsevation
      <|start_header_id|>user<|end_header_id|>
         question: {input}.
       <|eot_id|><|start_header_id|>assistant<|end_header_id|>
       
      <|eot_id|>
      <|end_of_text|>
          """
      )
     
    ,input_variables=["input","tools","tool_names","tool_description",'tool_args','agent_scratchpad'],
  )




llm = HuggingFaceEndpoint(
    repo_id="https://j1t7my9b1s4ixuzt.us-east-1.aws.endpoints.huggingface.cloud",  huggingfacehub_api_token="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"
)

api_url = "https://j1t7my9b1s4ixuzt.us-east-1.aws.endpoints.huggingface.cloud"
headers = {
    "Authorization": "Bearer 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",  
    "Content-Type": "application/json"
}

def call_huggingface_endpoint(prompt, api_url,  max_new_tokens,  do_sample, temperature, top_p ,max_length=512,retries=1, backoff_factor=0.3):
    headers = {
        "Authorization": f"Bearer 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",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": prompt,
        "parameters": {
            "max_length":max_length,
            "max_new_tokens":max_new_tokens,
            "do_sample":do_sample,
            "temperature":temperature,
            "top_p":top_p,
            
        }
    }
    for attempt in range(retries):
        try:
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            try:
                response=(response.json()[0]["generated_text"]).split('Response:')[1]
            except:
                response=(response.json()[0]["generated_text"])
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise e

def format_appointment_date(date):
    current_date=datetime.now().strftime("%B %d, %Y")

    day=datetime.now().strftime('%A')
    model_prompt_for_appointment = f"""
            <|begin_of_text|><|start_header_id|>system<|end_header_id|>
            Instructions:
                -current date is : {current_date} 
                -day today is : {day}
            calculate the date according to users querry: {date}
            change the date in this format:"%m/%d/%Y" or  "month/day/year" 
            and return date in mm/dd/yyyy format only
            example: mm/dd/yyyy
            please provide only response
            <|eot_id|>
            <|start_header_id|>user<|end_header_id|>
            {date}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
            """
    response = call_huggingface_endpoint(model_prompt_for_appointment, api_url, 256 ,False  ,0.9 ,0.9)
    response_content = response[len(model_prompt_for_appointment):].strip()
    return response_content
def transform_input(input_text):
    # Define a list of prompts to transform the input text
    modelPromptTotransform = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        how would you ask this {input_text} as a question in a friendly and conversational tone related to appointment?
        give only one option.
        user
        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
     
    # Call the API using the latest method
    response = call_huggingface_endpoint(modelPromptTotransform, api_url,256 ,False  ,0.09 ,0.9)
    # response = query_llama3(modelPromptTotransform)
    # print(response,'transformed response-----')
    response = response[len(modelPromptTotransform):].strip()
    print(response,'transformed response-----')
    return response


def identify_intent_practice_question(user_query,data):
 
    print('identify_intent_practice_question')
    print("--",data,"-static data-")
    model_prompt_for_static_queries = (
    f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
        Data available for reference: {data}
        Instructions:
        1. Analyze the user's query to determine its intent.
        2. If the query requests information that is available in the provided data, respond with the relevant information from the data.
        3. If the query does not match any information available, respond with "Please provide valid information."
        4. If the query does not fit into the above categories, respond with "I'm sorry, I can't provide that information. Can you ask about something else related to our services or appointments?"
        5. If you don't understand the query, ask for clarification rather than returning the same text.
        6. if it is related to any glasses ques respond with "I'm sorry, I can't provide that information. Can you ask about something else related to our services or appointments?"
        please follow the above instructions carefully.
        Avoid formal language; aim for a friendly and human-like tone.
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        {user_query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    )
       
    response = call_huggingface_endpoint(model_prompt_for_static_queries, api_url,150 ,True  ,0.6 ,0.9)
    response=response[len(model_prompt_for_static_queries):].strip()
    return response
 

@tool
def short_queries(query):
    """ use this tool when users query is verry short and does not explain what does it means,
        mostly for short user queries like if user types a date only or user query is very short.
        Do not use this if query has some meaning like prefred date is this or something like that. 
        This will return text saying Please clarify your query so I can assist you better.
     """
    results= f'Please clarify your query so I can assist you better. i could not understand what this means : {query}'
    results=transform_input(results)
    
    return 'Please clarify your query so I can assist you better.'
short_queries.return_direct=True


@tool
def query_chroma_and_generate_response(query):
    """give answer to organisation related query like address or any other relevant information related to organisation 
       Do not use this if user is sharing some details about them or details related to appointment like dates name phone no or email etc.
    """
    print(query,"vvzsjjjjjjjjjzkj")
 
    subject="practice_info"
    print("regsnj",query)
    vector_db = connect_to_vectorDB(subject)
    if vector_db:
        # Perform a similarity search on the vector database
        results = vector_db.similarity_search(query, k=100)  # Fetch multiple relevant documents
       
        if results:
            # Combine content from all retrieved documents
            combined_content = "\n".join([result.page_content for result in results])
            print("rgsnkvmk",combined_content)
            # Use LLM to generate a response based on the combined content
            response = identify_intent_practice_question(query, combined_content)
            return response
        else:
            return "Sorry, I couldn't find an answer to your question."
    else:
        return "Failed to connect to the vector database."
query_chroma_and_generate_response.return_direct=True


@tool
def query_chroma_and_generate_response_2nd(query):
    """give answer to organisation related query like address or any other relevant information related to organisation 
       Do not use this if user is sharing some details about them or details related to appointment like dates name phone no or email etc.
    """
    print(query,"vvzsjjjjjjjjjzkj")
 
    subject="practice_info2"
    print("regsnj",query)
    vector_db = connect_to_vectorDB(subject)
    if vector_db:
        # Perform a similarity search on the vector database
        results = vector_db.similarity_search(query, k=100)  # Fetch multiple relevant documents
       
        if results:
            # Combine content from all retrieved documents
            combined_content = "\n".join([result.page_content for result in results])
            print("rgsnkvmk",combined_content)
            # Use LLM to generate a response based on the combined content
            response = identify_intent_practice_question(query, combined_content)
            return response
        else:
            return "Sorry, I couldn't find an answer to your question."
    else:
        return "Failed to connect to the vector database."
query_chroma_and_generate_response_2nd.return_direct=True


@tool
def get_greeting_response(user_input):
    """Respond to the user's greeting.
       if the user is greating you. 
       use this tool only if the primary intenet of the user is greeting only
       not to use when primary intent is something else.
       or do not use this if user want to book appointment"""
    modelPromptForAppointment = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>

            You are a helpful Eyecare assistant for MaximCaye Care. Start with a simple greeting and assist the user related to appointment and Do not anything from your end.<|eot_id|><|start_header_id|>user<|end_header_id|>

            {user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    response=call_huggingface_endpoint(modelPromptForAppointment,api_url,256 ,False,0.9 ,0.9)
    # response = query_llama3(modelPromptForAppointment)
    response = response[len(modelPromptForAppointment):].strip()
    print("TDgx",response)
    return response
get_greeting_response.return_direct=True



def get_auth_token() -> str:
    """
    Get authentication token using vendor and account credentials.
    """
    print("Get authentication token")
    auth_url = "https://iochatbot.maximeyes.com/api/v2/account/authenticate"
    auth_payload = { "VendorId": "e59ec838-2fc5-4639-b761-78e3ec55176c", "VendorPassword": "password@123", "AccountId": "chatbot1", "AccountPassword": "sJ0Y0oniZb6eoBMETuxUNy0aHf6tD6z3wynipZEAxcg=" }
    headers = {'Content-Type': 'application/json'}
    try:
        auth_response = requests.post(auth_url, json=auth_payload, headers=headers)
        auth_response.raise_for_status()
        response_json = auth_response.json()

        if response_json.get('IsToken'):
            print(response_json)
            return response_json.get('Token')
        else:
            return f"Error message: {response_json.get('ErrorMessage')}"
    except requests.RequestException as e:
        return f"Authentication failed: {str(e)}"
    except json.JSONDecodeError:
        return "Failed to decode JSON response"    


@tool
def fetch_info(response):
    
    """this tool will extract the users information like FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime from the given users input it can extract all at once or one at a time to book the appointment """
    print(response,'action_input is ')

    
    
    modelPromptForAppointment = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        text: {response}
        
        Extract the following information from given text : FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime  if available ,determine what could be the information
        and if any fields in the information is not there return it as ```empty``` .
        instruction:
        -here PreferredDateOrTime field is the date the user wants to book the appoinmnet on. 
        -Do not add any things if not present in the given text, leave it empty.
        -Read the full information carefully.
        -Always Provide proper indexing for each extracted field at the begining.
        -Understand the user input carefully and extract anything you can for these fields (FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime) from the user querry.
        -Do not change email and Phone no if they are incorrect Keep them as it is.
        -please extract that name whose appointment to be booked as parents can book the appointment of child so extract child name not parents names if condition arises
        -understand user query carefully and 
 
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>

        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
    try:
        result = call_huggingface_endpoint(modelPromptForAppointment, api_url,256 ,False  ,0.1 ,0.9)
        result=result[len(modelPromptForAppointment):].strip().replace('*','').replace('Not available','').replace('not available','').replace('(Not available)','').replace('(empty field)','').replace('not Available','').replace('(not available)','').replace('Not mentioned','').replace('Not Mentioned','').replace('()','').replace('empty','').replace('None','')
        print('fetched info srting',result)
        data_dict = {}
        for line in result.split('\n'):
            if ':' in line:
                pattern = r"(\d*\.)?\s*([a-zA-Z\s]+):\s*(.+)"
                matches = re.findall(pattern, line)
                if matches:
                    
                    key, value = matches[0][1].strip(), matches[0][2].strip()
                    # if key.lower()=='preferreddateortime' or key.lower()=='dateofbirth':
                    #     value=format_appointment_date(value)

                    data_dict[key] = (value).replace('(empty field)','').replace('not Available','').replace('(not available)','').replace('Not mentioned','').replace('Not Mentioned','').replace('()','').replace('empty','').replace('None','')
 
        print('data string',data_dict)
        extracted_info= data_dict
        
        return data_dict
    except Exception as e:
        print(f"Error extracting information: {e}")
        return {}
fetch_info.return_direct=True


@tool
def fetch_info_to_change(response):
    
    """this tool will analyse what user want to change and  extract the users information like FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime from the given users input it can extract all at once or one at a time  """
    print(response,'action_input is ')

    
    
    modelPromptForAppointment = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        text: {response}
        Analyse what user want to change and Extract any or all of the following information from given text : FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime  if available ,determine what could be the information
        and if any fields in the information is not there return it as ```empty``` .
        instruction:
        -Do not add any things if not present in the given text, leave it empty.
        -Read the text carefully and extract filds that can be extracted from the given text.
        -Always Provide proper indexing for each extracted field at the begining.
        -Understand the user input carefully and extract anything you can for these fields (FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime) from the user querry.
        -Do not change email and Phone no if they are incorrect Keep them as it is.
        
 
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
            { {response}}
        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
    try:
        result = call_huggingface_endpoint(modelPromptForAppointment, api_url,256 ,False  ,0.1 ,0.9)
        result=result[len(modelPromptForAppointment):].strip().replace('*','').replace('Not available','').replace('not available','').replace('(Not available)','').replace('(empty field)','').replace('not Available','').replace('(not available)','').replace('Not mentioned','').replace('Not Mentioned','').replace('()','').replace('empty','').replace('None','')
        print('fetched info srting',result)
        data_dict = {}
        for line in result.split('\n'):
            if ':' in line:
                pattern = r"(\d*\.)?\s*([a-zA-Z\s]+):\s*(.+)"
                matches = re.findall(pattern, line)
                if matches:
                    
                    key, value = matches[0][1].strip(), matches[0][2].strip()
                    # if key.lower()=='preferreddateortime' or key.lower()=='dateofbirth':
                    #     value=format_appointment_date(value)

                    data_dict[key] = (value).replace('(empty field)','').replace('not Available','').replace('(not available)','').replace('Not mentioned','').replace('Not Mentioned','').replace('()','').replace('empty','').replace('None','')
 
        print('data string',data_dict)
        extracted_info= data_dict
        
        return data_dict
    except Exception as e:
        print(f"Error extracting information: {e}")
        return {}
fetch_info_to_change.return_direct=True


@tool
def generate_response(user_query):
    """ if user ask anything other then the appointment or max eyr care and  if the users input is not related to booking appointment or eyecare. 
        Do not use this if user is sharing some details about them or details related to appointment like dates name phone no or email etc.  
    """
    prompt = (
    f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    instruction: You are a creative assistant for eye care services. You must ONLY provide information directly related to eye health, vision, and eye care services. If the user's query is not related to eye care, respond with EXACTLY this message: 'I apologize, but I can only answer questions related to eye care. If you have any eye-related questions, I'd be happy to help'
    <|eot_id|>
    <|start_header_id|>user<|end_header_id|>
    {user_query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    )
    response=call_huggingface_endpoint(prompt, api_url,256 ,False  ,0.9 ,0.9)
    response_content = response[len(prompt):].strip()
    return response_content
generate_response.return_direct=True


@tool
def get_locations(token):
    """Get the list of locations for booking appointments and require FirstName, LastName, DateOfBirth, Email, PhoneNumber and PreferredDateOrTime to go further"""
    token=get_auth_token()
    print('token++++++++++++++++++++++++++++++=================================')
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {token}'}

    # Step 1: Get the list of locations
    get_locations_url = "https://iochatbot.maximeyes.com/api/location/GetLocationsChatBot"
    try:
        locations_response = requests.get(get_locations_url, headers=headers)
        locations_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching locations: {e}")
        return
    if locations_response.status_code != 200:
        return f"Failed to get locations. Status code: {locations_response.status_code}"
    try:
        locations = locations_response.json()
    except ValueError:
        return "Failed to parse locations response as JSON."
    location_='Select any available location id:'
    print("Select any available location id:")
    for idx, location in enumerate(locations):
        location_+=f"<br> {idx + 1}: {location['Name']} (ID: {location['LocationId']})"
    # location_id = input("Choose a location by entering the ID: ")
    # if location_id:
      # print('Thanks for providing location')
    # return 'list of available location = ["Hillsboro", "Beaverton"]'
    # return [{'Name': 'Hillsboro', 'LocationId': 1}, {'Name': 'Beaverton', 'LocationId': 3}]
    return location_
get_locations.return_direct=True
@tool
def get_providers(location_id):
    """Get the list of providers for a specific location"""
    token=get_auth_token()
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {token}'}
    print('location_id-',location_id)
    match = re.search(r'\{.*\}', location_id)
    
    json_string = match.group(0)
    location_data = json.loads(json_string)
    location_id = location_data.get("location_id")
    print("erfssssssss",location_id)
    get_providers_url = f"https://iochatbot.maximeyes.com/api/scheduledresource/GetScheduledResourcesChatBot?LocationId={location_id}"
    try:
        providers_response = requests.get(get_providers_url, headers=headers)
        providers_response.raise_for_status()
        providers = providers_response.json()
        print(providers,'providers---')
        provider_list = [{"Name": provider['Name'], "ProviderId": provider['ScheduleResourceId']} for provider in providers]
        print("Available providers:", provider_list)
        # return provider_list
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching providers: {e}")
        # return
    if providers_response.status_code != 200:
        return f"Failed to get providers. Status code: {providers_response.status_code}"
    try:
        providers = providers_response.json()
    except ValueError:
        return "Failed to parse providers response as JSON."
    provider_id='Select any available provider id:'
    print("Available providers:")
    for idx, provider in enumerate(providers):
        provider_id+=f"<br> {idx + 1}: {provider['Name']} (ID: {provider['ScheduleResourceId']})"

    
    return provider_id
get_providers.return_direct=True

@tool
def get_appointment_reasons(location_id_provider_id):
    """Get the list of appointment reasons for a specific provider and location"""
    print("efjawkjk")

    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {get_auth_token()}'}

    data = json.loads(location_id_provider_id)
    print("ssdfff",data)

    provider_id = data.get("provider_id")
    location_id = data.get("location_id")

    get_reasons_url = f"https://iochatbot.maximeyes.com/api/appointment/appointmentreasonsForChatBot?LocationId={location_id}&SCHEDULE_RESOURCE_ID={provider_id}"
    try:
        reasons_response = requests.get(get_reasons_url, headers=headers)
        reasons_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching appointment reasons: {e}")
        return
    if reasons_response.status_code != 200:
        return f"Failed to get appointment reasons. Status code: {reasons_response.status_code}"
    try:
        reasons = reasons_response.json()
    except ValueError:
        return "Failed to parse appointment reasons response as JSON."

    reason_="Select any available reasons id:"
    for idx, reason in enumerate(reasons):
        reason_+=f"<br> {idx + 1}: {reason['ReasonName']} (ID: {reason['ReasonId']})"

    # reason_id = input("Choose a reason by entering the ID: ")
    # if reason_id:
    #   print('Thanks for providing reason')
    # return [{'Reason': 'Consultation', 'ReasonId': 201}, {'Reason': 'Follow-up', 'ReasonId': 202}]
    return reason_
get_appointment_reasons.return_direct=True




@tool
def get_open_slots(id):
    """Get the list of open slots based on the given reason ID and other parameters."""
    token=get_auth_token()
    print("rfesf",id)
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {token}'}
    # preferred = prefred_date_time_fun(prefred_date_time)
    # print("prefred date time",preferred)
    data = json.loads(id)  # Assuming user_input is a JSON string
    preferred_date_time = data.get("preferred_date_time")
    location_id = data.get("location_id")
    reason_id = data.get("reason_id")
    provider_id = data.get("provider_id")
    # from_date = "2024-07-20T15:30:00"
    # from_date = preferred
    # print("from_date",from_date)

    get_open_slots_url = f"https://iochatbot.maximeyes.com/api/appointment/openslotforchatbot?fromDate={preferred_date_time}&isOpenSlotsOnly=true"
    try:
        open_slots_response = requests.get(get_open_slots_url, headers=headers)
        open_slots_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching open slots: {e}")
        return
    if open_slots_response.status_code != 200:
        return f"Failed to get open slots. Status code: {open_slots_response.status_code}"
    try:
        open_slots = open_slots_response.json()
    except ValueError:
        return "Failed to parse open slots response as JSON."

    slot_="Select any available open slots id:"
    
    for idx, slot in enumerate(open_slots):
        ApptStartDateTime = datetime.fromisoformat(slot['ApptStartDateTime'])
        ApptEndDateTime = datetime.fromisoformat(slot['ApptEndDateTime'])
        
        slot_+=f'<br> {idx + 1}: {ApptStartDateTime.date()} ({ApptStartDateTime.time().strftime("%H:%M")}-{ApptEndDateTime.time().strftime("%H:%M")}) (ID: {slot["OpenSlotId"]})'

    return slot_
get_open_slots.return_direct=True


@tool
def sndotp(data):
    """to send the otp for confirmation"""
    token=get_auth_token()
    print(data)
    # data=data.replace("\'", "\"")
    # data = json.loads(data)
    # if isinstance(data, str):
        # if True:
            # Attempt to parse as JSON
    data = json.loads(data)
        # else json.JSONDecodeError:
            # If JSON parsing fails, assume it is in key-value pair format
            # try:
            #     # Split the string into key-value pairs
            #     data = data.split(', ')
            #     data_dict = {}
            #     for item in data:
            #         key, value = item.split('=')
            #         data_dict[key.strip()] = value.strip()
 
            #     # Use the converted dictionary
            #     data = data_dict
            # except ValueError:
            #     return "Invalid data format. Could not convert to dictionary."
 
    # Ensure data is a dictionary
    if not isinstance(data, dict):
        return "Invalid data format. Data must be a dictionary or correctly formatted string."
    FirstName = data.get("FirstName")
    LastName = data.get("LastName")
    PhoneNumber = data.get("PhoneNumber")
    DOB = data.get("DOB")
    Email = data.get("Email")
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {token}'}
    send_otp_url = "https://iochatbot.maximeyes.com/api/common/sendotp"
    otp_payload = {
        "FirstName": FirstName,
        "LastName": LastName,
        "DOB": DOB,
        "PhoneNumber": PhoneNumber,
        "Email": Email}
    try:
        otp_response = requests.post(send_otp_url, json=otp_payload, headers=headers)
        otp_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending OTP: {e}")
        return
    if otp_response.status_code != 200:
        return f"Failed to send OTP. Status code: {otp_response.status_code}"
sndotp.return_direct=True
 

@tool
def book_appointment(data):
    """this tool is the final step to book the appointment when all the details are available like 
    (open_slot_id,preferred_date_time,reason_id,FirstName,LastName,DOB,PhoneNumber,Email) 
    and  first we need to get these (open_slot_id,preferred_date_time,reason_id,FirstName,LastName,DOB,PhoneNumber,Email) values from other tools.
      """
    token=get_auth_token()
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {token}'}
    print("ddfnzn",data)
    data = json.loads(data)
    
    open_slot_id = data.get("open_slot_id")
    from_date = data.get("preferred_date_time")
    reason_id = data.get("reason_id")
    FirstName = data.get("FirstName")
    LastName = data.get("LastName")
    DOB = data.get("DOB")
    PhoneNumber = data.get("PhoneNumber")
    Email = data.get("Email")
    book_appointment_url = "https://iochatbot.maximeyes.com/api/appointment/onlinescheduling"
    from_date=format_appointment_date(from_date)
    DOB=format_appointment_date(DOB)
    
    # Convert ApptDate to 'MM/DD/YYYY' format
     
    # appointment_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S").strftime("%m/%d/%Y")
    # parsed_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S")

    # # Convert the datetime object to the desired format
    # appointment_date = parsed_date.strftime("%m/%d/%Y")
    # print(appointment_date)
    book_appointment_payload = {
        "OpenSlotId": open_slot_id,
        "ApptDate": from_date,
        "ReasonId": reason_id,
        "FirstName": FirstName,
        "LastName": LastName,
        "PatientDob": DOB,
        "MobileNumber": PhoneNumber,
        "EmailId": Email}
    print("dnakjik",book_appointment_payload)

    try:
        book_appointment_response = requests.post(book_appointment_url, json=book_appointment_payload, headers=headers)
        book_appointment_response.raise_for_status()
        print("dwwsfqf",book_appointment_response.json())
        return book_appointment_response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while booking the appointment: {e}")
        # return
    if book_appointment_response.status_code != 200:
        return f"Failed to book appointment. Status code: {book_appointment_response.status_code}"

    return book_appointment_response.json()

book_appointment.return_direct=True
def confirmation_intent(context):
    
    response_content_prompt = f"""
                <|begin_of_text|><|start_header_id|>system<|end_header_id|>
                identify what user wants fro user query querry 
                Instructuion:
                - If the user wants to change some thing return change
                - If the user is verifying the information are correct return correcrt  
                - If user intents to say the informatin is wrong  return incorrect.
               
                please follow the above instructions carefully.
                <|eot_id|>
                <|start_header_id|>user<|end_header_id|>
                "{context}\n"
                <|eot_id|><|start_header_id|>assistant<|end_header_id|>
                """
    response_content = call_huggingface_endpoint(response_content_prompt, api_url,256 ,False  ,0.1 ,0.9)
    response_content = response_content[len(response_content_prompt):].strip()
    print("edAWFKmkw",response_content)
    return response_content
    

 
tools=[fetch_info_to_change,query_chroma_and_generate_response,query_chroma_and_generate_response_2nd,fetch_info,get_locations,get_providers,get_appointment_reasons,get_open_slots,sndotp,book_appointment,get_greeting_response,generate_response]
memory = ConversationBufferMemory(memory_key="chat_history")

# define the agent
agent = create_react_agent(llm, tools, prompt,stop_sequence=["Final Answer","Observation","short_queries is not a valid tool"])
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools,verbose=True, handle_parsing_errors=True,max_iterations=6)

state = {
    "step": "start",
    "location_selected": None,
    "provider_selected": None,
    "appointment_reason_selected": None,
    "intermediate_steps": [],
    "locations": [],
    "providers": []
}



# funtion to validate email
def validate_email(email):
          # Regular expression pattern for a valid email address
          pattern = r'^[\w\.-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
          return re.match(pattern, email) is not None

# funtion to validate email         
def validate_phone(phone):
    # Regular expression pattern for a valid US phone number
    pattern = r'^\d{10}$|^\(\d{3}\) \d{3}-\d{4}$|^\(\d{3}\)-\d{3}-\d{4}$'
    return re.match(pattern, phone) is not None


def validate_date(session_id,preferred_date_time,DOB):
    print(preferred_date_time,DOB,'preferred_date_time,DOB')

    preferred_date_time=format_appointment_date(preferred_date_time)

    DOB=format_appointment_date(DOB)
    print(preferred_date_time,DOB,'preferred_date_time,DOB,1111111')
    UserProfile.objects.filter(session_id=session_id).update(PreferredDateOrTime=preferred_date_time ,DateOfBirth=DOB )
    current_date = datetime.now()
    preferred_date_time = datetime.strptime(preferred_date_time.strip(), '%m/%d/%Y')
    DOB = datetime.strptime(DOB.strip(), '%m/%d/%Y')
    print(current_date,preferred_date_time,DOB,type(preferred_date_time),(DOB))
    
    # Initialize validity flags
    preferred_valid = 'valid'
    dob_valid = 'valid'
    
    # Validate preferred_date_time
    if preferred_date_time < current_date:
        preferred_valid = 'not valid'
    
    # Validate DOB
    if DOB > current_date:
        dob_valid = 'not valid'
    
    # Return results based on the validity of both dates
    if preferred_valid == 'not valid' and dob_valid == 'not valid':
        text = "remove the date of birth and preferred date and time fro appointment from the context"
        UserProfile.objects.filter(session_id=session_id).update(PreferredDateOrTime='na' ,DateOfBirth='na' )
        
        return 'Please provide valid Appointment date and time and Date of birth '
    elif preferred_valid == 'not valid':
        text = " remove preferred date and time for appointment from the context"
        UserProfile.objects.filter(session_id=session_id).update(PreferredDateOrTime='na'  )
        return 'Please provide valid Appointment date and time'
    elif dob_valid == 'not valid':
        text = "remove date of birth from the context"
        UserProfile.objects.filter(session_id=session_id).update( DateOfBirth='na' )
        return 'Please provide valid Date of birth'
    else:
        return True
 

def verify_tools(request,practice):
    

    tools=[query_chroma_and_generate_response,fetch_info,get_greeting_response,generate_response]
    if practice=='practice2':
        tools=[query_chroma_and_generate_response_2nd,fetch_info,get_greeting_response,generate_response]
    data = json.loads(request.body.decode('utf-8'))
    session_id = data.get('session_id', '')
    data=UserProfile.objects.filter(session_id=session_id).first()
    try:
        if data.FirstName=='na' or data.LastName=='na' or data.DateOfBirth=='na' or data.Email=='na' or data.PhoneNumber=='na'  or data.PreferredDateOrTime=='na':
            pass      
        else:
            tools=[query_chroma_and_generate_response,get_greeting_response,generate_response]   
            if practice=='practice2':
                tools=[query_chroma_and_generate_response_2nd,get_greeting_response,generate_response]
    except:
        pass
    return tools

    


def handle_user_input(request,user_input,history,practice):
    global state
    data = json.loads(request.body.decode('utf-8'))
    user_input = data.get('input', '')
    session_id = data.get('session_id', '')
    if request.session[f"step{session_id}"] == "start":
        if user_input:
            tools=verify_tools(request,practice)
            chat_history = ChatHistory.objects.filter(session_id=session_id).order_by('timestamp')
            # Format chat history for response
            formatted_input = "User:"
            for chat in chat_history:
                formatted_input+= f"  {chat.user_input}\n "
            user_data = UserProfile.objects.filter(session_id=session_id)
            # if user_data.exists():
            #     user_input=formatted_input+user_input
            # tools=[fetch_info,get_locations,get_providers,get_appointment_reasons,get_open_slots,sndotp,book_appointment,get_greeting_response,generate_response]
            Tools_names=", ".join([t.name for t in tools])
            tool_description=", ".join([t.description for t in tools])
            tool_args=", ".join([str(t.args) for t in tools])
            try:
                result=agent_executor.invoke({"input": user_input,'tools':tools,"tool_names":Tools_names,"tool_description":tool_description,'tool_args':tool_args,'agent_scratchpad':history}, {"callbacks": [handler_1, handler_2]})
            except:
                result=agent_executor.invoke({"input": user_input,'tools':tools,"tool_names":Tools_names,"tool_description":tool_description,'tool_args':tool_args,'agent_scratchpad':history}, {"callbacks": [handler_1, handler_2]})
 
            print(result)
            logger.info(result)

            print(result)
            try:
                data = json.loads(request.body.decode('utf-8'))
                user_input = data.get('input', '')
                session_id = data.get('session_id', '')
                result_=result['output']
                print(result_,'result++++++++++++++++++')
                fields = ['FirstName', 'LastName', 'DateOfBirth', 'PhoneNumber', 'Email', 'PreferredDateOrTime']
                      
                for key, value in result_.items():
                    try:
                        user_data = UserProfile.objects.filter(session_id=session_id)
                        if value == '':
                            continue
                        if user_data.exists():
                            UserProfile.objects.filter(session_id=session_id).update(**{key:value})
                        else:
                            user_data=UserProfile.objects.create(session_id=session_id)
                            UserProfile.objects.filter(session_id=session_id).update(**{key:value})
                    except:
                        pass
                missing_fields = [field for field in fields if not result_.get(field) or result_.get(field).lower() == "none"]
                print(missing_fields,'missing_fields')
                missing_fields_=missing_fields
                missing_fields_=[]
                for field in missing_fields:
                    print(field)
                    # Query the database to get the field value for the given session_id
                    try:
                        record = UserProfile.objects.filter(session_id=session_id).values(field).first()
                    except:
                        record = None
                    
                    
                    if record: 
                        if record[field].lower() == 'na':
                            missing_fields_.append(field)

                        else:
                            pass
                    else:
                        missing_fields_.append(field)
                missing_fields=missing_fields_
                if missing_fields:
                    result = f" Please provide these missing fields {', '.join(missing_fields)}: "
                    print('missing_fields+++')
                    result=transform_input(result)
                    return result
                else:
                    user_data = UserProfile.objects.filter(session_id=session_id).first()
                    print("rfjksej", user_data)

                    validation=validate_date(session_id,user_data.PreferredDateOrTime,user_data.DateOfBirth)
                    if validation != True:
                        return validation
                    user_data = UserProfile.objects.filter(session_id=session_id).first()
                    if not validate_phone(user_data.PhoneNumber):
                        UserProfile.objects.filter(session_id=session_id).update(PhoneNumber='na' )
                        prompt = f"Please provide a valid Phone Number. The number you provided is not valid."
                        result=transform_input(prompt)
                        return result
                    if not validate_email(user_data.Email):
                        UserProfile.objects.filter(session_id=session_id).update(Email='na' )
                        prompt = f"Please provide a valid Email. The email you provided is not valid."
                        result=transform_input(prompt)
                        return result
                    confirmation_message = (
                        f"Here are the details of your appointment:\n"
                        f"Date and Time: {user_data.PreferredDateOrTime}\n"
                        f"Name: {user_data.FirstName} {user_data.LastName}\n"
                        f"DOB: {user_data.DateOfBirth}\n"
                        f"Phone: {user_data.PhoneNumber}\n"
                        f"Email: {user_data.Email}\n"
                        f"Is this information correct? (yes/no)"
                    )
                    request.session[f"step{session_id}"] = "confirmation"
                    return confirmation_message
            except:
                
                return result["output"]
 
        else:
            # Handle greeting response
            result = agent_executor.invoke({
                "input": user_input,
                "tools": [get_greeting_response],
                "tool_names": "get_greeting_response",
                "tool_description": get_greeting_response.description,
                "tool_args": json.dumps({"greeting": user_input}),
                "agent_scratchpad": history
            })
            greeting_response = result.get('output', "I'm not sure how to respond to that greeting.")
            return greeting_response
 
    elif request.session[f"step{session_id}"] == "confirmation":
        print("gtdkmrkbm",user_input)
        
        
        if user_input.lower() == "yes":
            user_data = UserProfile.objects.filter(session_id=session_id).first()
            print("fdvbkxnarmzdf",user_data)
            try:
                result = agent_executor.invoke({
                    "input": f" Send OTP to  FirstName is {user_data.FirstName} LastName is {user_data.LastName} PhoneNumber is  {user_data.PhoneNumber} DOB is  {user_data.DateOfBirth} Email is {user_data.Email}",
                    "tools": [sndotp],
                    "tool_names": "sndotp",
                    "tool_description": sndotp.description,
                    "tool_args": json.dumps({"FirstName": user_data.FirstName,"LastName": user_data.LastName,"PhoneNumber": user_data.PhoneNumber,"DOB": user_data.DateOfBirth,"Email": user_data.Email}),                
                    "agent_scratchpad": " "
                    })
            except:
                result = agent_executor.invoke({
                    "input": f" Send OTP to  FirstName is {user_data.FirstName} LastName is {user_data.LastName} PhoneNumber is  {user_data.PhoneNumber} DOB is  {user_data.DateOfBirth} Email is {user_data.Email}",
                    "tools": [sndotp],
                    "tool_names": "sndotp",
                    "tool_description": sndotp.description,
                    "tool_args": json.dumps({"FirstName": user_data.FirstName,"LastName": user_data.LastName,"PhoneNumber": user_data.PhoneNumber,"DOB": user_data.DateOfBirth,"Email": user_data.Email}),                
                    "agent_scratchpad": " "
                    })

            request.session[f"step{session_id}"] = "otp_verification"
            result="An OTP has been sent to your registered Mobile No. or Email. <br> Please enter the OTP to proceed."
            result=transform_input(result)
            return result
 
        
        elif user_input.lower() == "no":
            result="What would you like to edit?(FirstName, LastName, DateOfBirth, PhoneNumber, Email, or PreferredDateOrTime)."
            result=transform_input(result)
            return result
        else:
            intent=confirmation_intent(user_input)
            if intent.lower().strip()=='correct':
                user_data = UserProfile.objects.filter(session_id=session_id).first()
                print("fdvbkxnarmzdf",user_data)
                result = agent_executor.invoke({
                    "input":  f"Send OTP to FirstName is {user_data.FirstName} LastName is {user_data.LastName} PhoneNumber is  {user_data.PhoneNumber} DOB is  {user_data.DateOfBirth} Email is {user_data.Email}",
                    "tools": [sndotp],
                    "tool_names": "sndotp",
                    "tool_description": sndotp.description,
                    "tool_args": json.dumps({"FirstName": user_data.FirstName,"LastName": user_data.LastName,"PhoneNumber": user_data.PhoneNumber,"DOB": user_data.DateOfBirth,"Email": user_data.Email}),                
                    "agent_scratchpad": " "
                    })
                print(result)
                request.session[f"step{session_id}"] = "otp_verification"
                return f"An OTP has been sent to your registered Mobile No. or Email. <br> Please enter the OTP to proceed."
            elif intent.lower().strip()=='incorrect':  
                result="What would you like to edit?(FirstName, LastName, DateOfBirth, PhoneNumber, Email, or PreferredDateOrTime)."
                result=transform_input(result) 
                return result
            else:    
                result = agent_executor.invoke({
                    "input": user_input,
                    "tools": [fetch_info_to_change],
                    "tool_names": "fetch_info_to_change",
                    "tool_description": fetch_info_to_change.description,
                    "tool_args": json.dumps(user_input),
                    "agent_scratchpad": ""
                })
                data = json.loads(request.body.decode('utf-8'))
                session_id = data.get('session_id', '')
                result_=result['output']

                print(result_,'result------------',type(result_))
                fields = ['FirstName', 'LastName', 'DateOfBirth', 'PhoneNumber', 'Email', 'PreferredDateOrTime']
                    
                for key, value in result_.items():
                    try:
                        print(key,type(key),value,type(value),'Key value')
                        user_data = UserProfile.objects.filter(session_id=session_id)
                        if value == '':
                            continue
                        if user_data.exists():
                            UserProfile.objects.filter(session_id=session_id).update(**{key:value})
                        else:
                            user_data=UserProfile.objects.create(session_id=session_id)
                            UserProfile.objects.filter(session_id=session_id).update(**{key:value})
                    except:
                        pass
                request.session[f"step{session_id}"] = "input_new_value"
                return handle_user_input(request,user_input,history,practice)
            
  
 
    elif request.session.get(f"step{session_id}") == "input_new_value":
        try:
            field_to_edit = request.session.get(f"field_to_edit{session_id}")
            UserProfile.objects.filter(session_id=session_id).update(**{field_to_edit: user_input})
        except:
            pass
        user_data = UserProfile.objects.filter(session_id=session_id).first()
        confirmation_message = (
            f"Here are the updated details:\n"
            f"Date and Time: {user_data.PreferredDateOrTime}\n"
            f"Name: {user_data.FirstName} {user_data.LastName}\n"
            f"DOB: {user_data.DateOfBirth}\n"
            f"Phone: {user_data.PhoneNumber}\n"
            f"Email: {user_data.Email}\n"
            f"Is this information correct? (yes/no)"
        )
        request.session[f"step{session_id}"] = "confirmation"
        return confirmation_message
 
    elif request.session[f"step{session_id}"] == "otp_verification":
        # User is expected to enter the OTP now
        otp = user_input.strip()
       
        # Retrieve the user data
        user_data = UserProfile.objects.filter(session_id=session_id).first()
 
        if not user_data:
            return "User data not found."
 
        # Validate the OTP
        validate_otp_url = "https://iochatbot.maximeyes.com/api/common/checkotp"
       
        validate_otp_payload = {
            "FirstName": user_data.FirstName,
            "LastName": user_data.LastName,
            "DOB": user_data.DateOfBirth,
            "PhoneNumber": user_data.PhoneNumber,
            "Email": user_data.Email,
            "OTP": otp
        }
 
        headers = {
            'Content-Type': 'application/json',
            'apiKey': f'bearer {get_auth_token()}'
        }
 
        try:
            validate_otp_response = requests.post(validate_otp_url, json=validate_otp_payload, headers=headers)
            validate_otp_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while validating OTP: {e}")
            return "Failed to validate OTP. Please try again later."
 
        if validate_otp_response.status_code == 200:
            validation_result = validate_otp_response.json()
            if validation_result.get("Isvalidated"):
                request.session[f"step{session_id}"] = "confirmed_otp"
                # Fetch locations after OTP confirmation
                print("reeeeeesgkndksznk")
                result = agent_executor.invoke({
                    "input": "Get Locations",
                    "tools": [get_locations],
                    "tool_names": "get_locations",
                    "tool_description": get_locations.description,
                    "tool_args": {},
                    "agent_scratchpad": history
                })
                print(result['output'])
                locations = result['output']
                request.session[f"locations{session_id}"] = locations
                request.session[f"step{session_id}"] = "location_selection"
                return locations
               
            else:
                return "Invalid OTP. Please try again."
        else:
            return f"Failed to validate OTP. Status code: {validate_otp_response.status_code}"
    
    elif request.session[f"step{session_id}"] == "location_selection":
        try:
            print("location_selection")
            location_data = json.loads(user_input)  
            location_id = int(location_data)
            lovation_available=request.session[f"locations{session_id}"]
            text = lovation_available

            # Use regex to find all occurrences of "ID: <number>"
            ids = re.findall(r'ID:\s*(\d+)', text)
            ids=[x.strip() for x in ids]
            # Convert the extracted IDs to integers
            ids = list(map(int, ids))
        
            if location_id in ids:
                request.session[f"location_selected{session_id}"] = location_id
                result = agent_executor.invoke({
                    "input": f"Get Providers for location_id is {location_id}",
                    "tools": [get_providers],
                    "tool_names": "get_providers",
                    "tool_description": get_providers.description,
                    "tool_args": json.dumps({"location_id": location_id}),
                    "agent_scratchpad": history
                })
                providers = result['output']
                print("fhdb",providers)
                
                # Printing the extracted locations
                # for provider in providers:
                #     print(f"provider Name: {provider['Name']}, provider ID: {provider['ProviderId']}")
                   
                json_output = json.dumps({"output": providers}, indent=4)
                print("RSG",json_output)
                request.session[f"step{session_id}"] = "provider_selection"  # Move to the next step
       
                request.session[f"providers{session_id}"] = providers
                print(json_output,"fewjwij")
                return providers
            else:
                return "Invalid Location ID. Please enter a Location ID from the list provided."
       
        except ValueError:
            return "Invalid input. Please enter a numerical ID from the list provided."
 
 
    elif request.session[f"step{session_id}"] == "provider_selection":
        try:
            provider_id = int(user_input)
            print("dfgxg",provider_id)
            text = request.session[f"providers{session_id}"]

            # Use regex to find all occurrences of "ID: <number>"
            ids = re.findall(r'ID:\s*(\d+)', text)
            
            ids=[x.strip() for x in ids]
            # Convert the extracted IDs to integers
            ids = list(map(int, ids))
 
            if provider_id in ids:
                request.session[f"provider_selected{session_id}"] = provider_id
                location_id = request.session[f"location_selected{session_id}"]
                print("dtrgdt",location_id)
                result = agent_executor.invoke({
                    "input": f"Get Appointment Reasons when selected location_id is {location_id} and  selected provider_id is {provider_id} ",
                    "tools": [get_appointment_reasons],
                    "tool_names": "get_appointment_reasons ",
                    "tool_description": get_appointment_reasons.description,
                    "tool_args": json.dumps({"provider_id": provider_id, "location_id": location_id}),
                    #  "tool_args":get_appointment_reasons.args,
                    "agent_scratchpad": history
                })
                appointment_reasons = result['output']
                print("fhdb", appointment_reasons)
 
                # Print the extracted appointment reasons
                # reason_list = "\n".join(f"Reason ID: {reason['ReasonId']}, Reason: {reason['Reason']}" for reason in appointment_reasons)
                request.session[f"step{session_id}"] = "appointment_reason_selection"
                request.session[f"appointment_reasons{session_id}"] = appointment_reasons
                return appointment_reasons
 
            else:
                return "Invalid provider ID. Please enter a valid ID from the list provided."
 
        except ValueError:
            return "Invalid input. Please enter a numerical ID from the list provided."
 
    elif request.session[f"step{session_id}"] == "appointment_reason_selection":
        try:
            appointment_reason_id = int(user_input)
            request.session[f"appointment_reason_selected{session_id}"] = appointment_reason_id
            location_id = request.session[f"location_selected{session_id}"]
            provider_id = request.session[f"provider_selected{session_id}"]
            user_data = UserProfile.objects.filter(session_id=session_id).first()
            preferred_date_time=user_data.PreferredDateOrTime
            result = agent_executor.invoke({
                "input": f"Get open slots for  preferred_date_time is {preferred_date_time} ,location_id is {location_id}, provider_id  is {provider_id}, reason_id  is {appointment_reason_id}",
                "tools": [get_open_slots],
                "tool_names": "get_open_slots",
                "tool_description": get_open_slots.description,
                "tool_args": json.dumps({"preferred_date_time": preferred_date_time, "location_id": location_id, "reason_id": appointment_reason_id, "provider_id": provider_id}),
                "agent_scratchpad": history
            })
            open_slots = result['output']
            if open_slots:
                request.session[f"step{session_id}"] = "slot_selection"
                request.session[f"open_slots{session_id}"] = open_slots
                return open_slots
            else:
                return "No open slots available. Please try again later."
   
        except ValueError:
            return "Invalid appointment reason ID. Please enter a valid ID."
 
    elif request.session[f"step{session_id}"] == "slot_selection":
        # try:
                open_slot_id = user_input
            # if any(slot['OpenSlotId'] == open_slot_id for slot in request.session[f"open_slots"]):
                request.session[f"open_slot_selected{session_id}"] = open_slot_id
                location_id = request.session[f"location_selected{session_id}"]
                provider_id = request.session[f"provider_selected{session_id}"]
                user_data = UserProfile.objects.filter(session_id=session_id).first()
                first_name=user_data.FirstName
                last_name=user_data.LastName
                DOB=user_data.DateOfBirth
                PhoneNumber=user_data.PhoneNumber
                Email=user_data.Email
                preferred_date_time=user_data.PreferredDateOrTime
                print("ETZfgsz")
                appointment_reason_id = request.session[f"appointment_reason_selected{session_id}"]
                booking_response=''
                # Use the tool to book the appointment
                booking_result = agent_executor.invoke({
                    "input": f"Book Appointment with location_id is {location_id}, provider_id is {provider_id}, reason_id is{appointment_reason_id}, and open_slot_id is {open_slot_id} ,FirstName is {first_name},LastName is {last_name},DOB  is {DOB},preferred_date_time is {preferred_date_time},PhoneNumber is {PhoneNumber},Email is {Email}",
                    "tools": [book_appointment],
                    "tool_names": "book_appointment",
                    "tool_description": book_appointment.description,
                    "tool_args": json.dumps({"location_id": location_id, "provider_id": provider_id, "reason_id": appointment_reason_id, "open_slot_id": open_slot_id,'FirstName' :first_name,'LastName' :last_name,'DOB' :DOB,'preferred_date_time': preferred_date_time,'PhoneNumber' :PhoneNumber,'Email':Email}),
                    "agent_scratchpad": history
                })
                
                booking_response = booking_result['output']
                del request.session[f"step{session_id}"]
                data=ChatHistory.objects.filter(session_id=session_id)
                data.delete()
                data=UserProfile.objects.filter(session_id=session_id)
                data.delete()
                # request.session[f"step{session_id}"] = "start"
                # request.session[f"location_selected{session_id}"] = None
                # request.session[f"provider_selected{session_id}"] = None
                # request.session[f"appointment_reason_selected{session_id}"] = None
                # request.session[f"open_slot_selected{session_id}"] = None
               
                # if booking_response.get("Status") == "Success":
                    # return f"Your appointment has been booked successfully. Appointment ID: {booking_response['AppointmentId']}"
        #         else:
        #             return "Failed to book the appointment. Please try again."
        #     else:
        #         return "Invalid slot ID. Please enter a valid ID from the list provided."
        # except ValueError:
        #     return "Invalid input. Please enter a numerical ID from the list provided."
                return booking_response


def get_chat_history( session_id):
    chat_history = ChatHistory.objects.filter(session_id=session_id).order_by('timestamp')
    # Format chat history for response
    formatted_history = ""
    for chat in chat_history:
        formatted_history += f"User: {chat.user_input}\nBot: {chat.bot_response}\n"
    return formatted_history

def home(request):
    request.session[f'session_id1'] = str(uuid.uuid4())
    session_id=request.session[f'session_id1'] 
    return render(request, "home.html",{'session_id':session_id})
def home_dynamic(request):
    request.session[f'session_id1'] = str(uuid.uuid4())
    session_id=request.session[f'session_id1'] 
    return render(request, "home_dynamic.html",{'session_id':session_id})
def home2(request):
    request.session[f'session_id1'] = str(uuid.uuid4())
    session_id=request.session[f'session_id1'] 
    return render(request, "home2.html",{'session_id':session_id})

@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        user_input = data.get('input', '')
        session_id = data.get('session_id', '')
        practice = data.get('practice', '')
        try:
            print('trying')
            request.session[f"step{session_id}"]
        except:
            print('excepting')
            request.session[f"step{session_id}"]='start'
        history=get_chat_history( session_id)
        print(history)
        
        print(user_input,'history')

        try:
            response=handle_user_input(request,user_input,history,practice)
        except:
            try:
                response=handle_user_input(request,user_input,history,practice)
            except:
                response=handle_user_input(request,user_input,history,practice)
            
        if response=='Agent stopped due to iteration limit or time limit.':
            
            response="I'm sorry, I didn't understand that. <br> Please clarify your query so I can assist you better."

        ChatHistory.objects.create(
            session_id=session_id,
            user_input=user_input,
            bot_response=str(response)
        )
       
        response=str(response)
        return JsonResponse({"response": response})
