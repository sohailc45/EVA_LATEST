from django.shortcuts import render
import json
import re
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta,date
import openai
from langchain.agents import Agent, AgentExecutor, Tool, tool
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, Agent, AgentExecutor,initialize_agent
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain import PromptTemplate
# from langchain.llms import ChatOpenAI
from langchain.chat_models import ChatOpenAI
# from langchain.retrievers import VectorStoreRetriever
# from .model_loader import *
# Create your views here.
# from langchain.rag import RAG
# retriever = VectorStoreRetriever(embedding_model="sentence-transformers/all-MiniLM-L6-v2")

# llm=base_model
# Create RAG model
# rag_model = RAG(
#     retriever=retriever,
#     generator=llm
# )
def home(request):
    return render(request, "home.html")


import requests
import json

# auth_payload = { "vendor_id": "e59ec838-2fc5-4639-b761-78e3ec55176c", "vendor_password": "password@123", "AccountId": "chatbot1", "AccountPassword": "sJ0Y0oniZb6eoBMETuxUNy0aHf6tD6z3wynipZEAxcg=" }

def get_auth_token(vendor_id, vendor_password, account_id, account_password) -> str:
    """
    Get authentication token using vendor and account credentials.
    
    """
    auth_url = "https://iochatbot.maximeyes.com/api/v2/account/authenticate"
    auth_payload = { "VendorId": "e59ec838-2fc5-4639-b761-78e3ec55176c", "VendorPassword": "password@123", "AccountId": "chatbot1", "AccountPassword": "sJ0Y0oniZb6eoBMETuxUNy0aHf6tD6z3wynipZEAxcg=" }
    headers = {'Content-Type': 'application/json'}
    try:
        auth_response = requests.post(auth_url, json=auth_payload, headers=headers)
        auth_response.raise_for_status()
        response_json = auth_response.json()
        print(response_json)
        if response_json.get('IsToken'):
          response=response_json.get('Token')
          return response
        else:
            return f"Error message: {response_json.get('ErrorMessage')}"
    except requests.RequestException as e:
        return f"Authentication failed: {str(e)}"
    except json.JSONDecodeError:
        return "Failed to decode JSON response"



vendor_id="e59ec838-2fc5-4639-b761-78e3ec55176c"
vendor_password="password@123"
account_id="chatbot1"
account_password="sJ0Y0oniZb6eoBMETuxUNy0aHf6tD6z3wynipZEAxcg="
auth_token = get_auth_token(vendor_id,vendor_password,account_id,account_password)


import os
import openai
from pydantic import BaseModel, Field
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chat_models import ChatOpenAI
from openai import OpenAI
import time
import random
import json
import requests
from datetime import datetime, timedelta,date
import re
from langchain.agents import Tool, initialize_agent, AgentExecutor, AgentType

from langchain import PromptTemplate
from langchain.agents import create_react_agent, Tool
from langchain.tools import BaseTool
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
from langchain_community.llms import HuggingFaceEndpoint
from langchain.llms import HuggingFaceHub
# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# HUGGINGFACEHUB_API_TOKEN="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"
HUGGINGFACEHUB_API_TOKEN=os.getenv('hugging_face_api_token')  
# Define the PromptTemplate with the required variables
prompt_template = PromptTemplate(
    template=(
        "You are a healthcare chatbot. {context}\n"
        "Tools available: {tool_names}\n"
        "Use the following tools to assist the user:\n{tools}\n\n"
        "you are a assistant you dont know about the location reffer to the tool if any of these topic arises like 'Get location' "
        "{agent_scratchpad}\n"
        "User: {user_input}\n"
        "Bot (provide action and necessary details):"

    ),
    input_variables=["context", "user_input", "agent_scratchpad", "tools", "tool_names"]
)
OPENAI_API_KEY=""
# Initialize the LLM
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    temperature=0,
    model_name='gpt-3.5-turbo'
)

os.environ["HUGGINGFACE_API_KEY"] = HUGGINGFACEHUB_API_TOKEN


# llm = HuggingFaceHub(
#     repo_id="NousResearch/Llama-2-7b-chat-hf",  # Replace with your desired model
#     model_kwargs={"temperature": 0.7},
#     huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN
# )
# print(HUGGINGFACEHUB_API_TOKEN,"HUGGINGFACEHUB_API_TOKEN")
# llm = HuggingFaceEndpoint(
#     repo_id="NousResearch/Llama-2-7b-chat-hf", max_length=2000, temperature=0.5, token=HUGGINGFACEHUB_API_TOKEN
# )

import requests
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent

# Define the HuggingFaceLLM class
# class HuggingFaceLLM:
#     def __init__(self, api_endpoint, api_token):
#         self.api_endpoint = api_endpoint
#         self.api_token = api_token

#     def __call__(self, prompt):
#         headers = {
#             "Authorization": f"Bearer {self.api_token}",
#             "Content-Type": "application/json"
#         }
#         if hasattr(prompt, "text"):
#             prompt = prompt.text
#         payload = {
#             "inputs": prompt,
#             "parameters": {
#                 "max_length": 200,
#                 "temperature": 0.7
#             }
#         }
#         try:
#             response = requests.post(self.api_endpoint, headers=headers, json=payload)
#             response.raise_for_status()
#             output = response.json()
#             print(output,'output')
#             return output  # Ensure this is a string
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to call Hugging Face API: {e}")
#             return "Error processing request."
#     def bind(self, **kwargs):
#         # Example of handling additional parameters
#         return self

class HuggingFaceLLM:
    def __init__(self, api_endpoint, api_token):
        self.api_endpoint = api_endpoint
        self.api_token = api_token

    def run(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        if hasattr(prompt, "text"):
            prompt = prompt.text
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7
            }
        }
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            output = response.json()
            print(output, 'output')
            # Assuming output contains generated text in a field named 'generated_text'
            return output[0]["generated_text"]  # Adjust according to the actual response structure
        except requests.exceptions.RequestException as e:
            print(f"Failed to call Hugging Face API: {e}")
            return "Error processing request."

    def bind(self, **kwargs):
        # Example of handling additional parameters
        return self

# Define the Hugging Face API endpoint and token
HUGGINGFACE_API_URL = "https://zzjxmo3ypzlaxmsp.us-east-1.aws.endpoints.huggingface.cloud"

# HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3.1-8B-Instruct"
HUGGINGFACE_API_TOKEN = "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"

# Initialize the LLM
# llm = HuggingFaceLLM(HUGGINGFACE_API_URL, HUGGINGFACE_API_TOKEN)

print(llm,'----')

def print_model_structure(model):
    for name, module in model.named_modules():
        print(name)
print("Base model structure : ")

# Define the function to call the Hugging Face endpoint
def call_huggingface_endpoint(prompt, api_url, api_token, retries=3, backoff_factor=0.3):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": prompt,
        "parameters": {
            "max_length": 512,
            "num_return_sequences": 1,
        }
    }
    for attempt in range(retries):
        try:
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()[0]["generated_text"]
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                raise e


# Load API credentials
vendor_id="e59ec838-2fc5-4639-b761-78e3ec55176c"
vendor_password="password@123"
account_id="chatbot1"
account_password="sJ0Y0oniZb6eoBMETuxUNy0aHf6tD6z3wynipZEAxcg="

# Define the API interaction functions
def get_auth_token() -> str:
    """
    Get authentication token using vendor and account credentials.
    """
    auth_url = "https://iochatbot.maximeyes.com/api/v2/account/authenticate"
    auth_payload = { "VendorId": "e59ec838-2fc5-4639-b761-78e3ec55176c", "VendorPassword": "password@123", "AccountId": "chatbot1", "AccountPassword": "sJ0Y0oniZb6eoBMETuxUNy0aHf6tD6z3wynipZEAxcg=" }
    headers = {'Content-Type': 'application/json'}
    try:
        auth_response = requests.post(auth_url, json=auth_payload, headers=headers)
        auth_response.raise_for_status()
        response_json = auth_response.json()

        if response_json.get('IsToken'):
            return response_json.get('Token')
        else:
            return f"Error message: {response_json.get('ErrorMessage')}"
    except requests.RequestException as e:
        return f"Authentication failed: {str(e)}"
    except json.JSONDecodeError:
        return "Failed to decode JSON response"

def get_locations(token):
    # token=get_auth_token()
    print('token++++++++++++++++++++++++++++++=================================',token)
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
    print("Available locations:")
    for idx, location in enumerate(locations):
        print(f"{idx + 1}: {location['Name']} (ID: {location['LocationId']})")
    # location_id = input("Choose a location by entering the ID: ")
    # if location_id:
      # print('Thanks for providing location')
    return [{'Name': 'Hillsboro', 'LocationId': 1}, {'Name': 'Beaverton', 'LocationId': 3}]
    # return locations



def get_providers(location_id,token):
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {token}'}
    print('location_id-',location_id)
    get_providers_url = f"https://iochatbot.maximeyes.com/api/scheduledresource/GetScheduledResourcesChatBot?LocationId={location_id}"
    try:
        providers_response = requests.get(get_providers_url, headers=headers)
        providers_response.raise_for_status()
        providers = providers_response.json()
        print(providers,'providers---')
        provider_list = [{"Name": provider['Name'], "ProviderId": provider['ScheduleResourceId']} for provider in providers]
        print("Available providers:", provider_list)
        return provider_list
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching providers: {e}")
        # return
    if providers_response.status_code != 200:
        return f"Failed to get providers. Status code: {providers_response.status_code}"
    try:
        providers = providers_response.json()
    except ValueError:
        return "Failed to parse providers response as JSON."

    # print("Available providers:")
    # for idx, provider in enumerate(providers):
    #     print(f"{idx + 1}: {provider['Name']} (ID: {provider['ScheduleResourceId']})")

    # provider_id = input("Choose a provider by entering the ID: ")
    # return [{'Name': 'Provider1', 'ProviderId': 101}, {'Name': 'Provider2', 'ProviderId': 102}]



def get_appointment_reasons(token, location_id, provider_id):
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {auth_token}'}
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

    print("Available reasons:")
    for idx, reason in enumerate(reasons):
        print(f"{idx + 1}: {reason['ReasonName']} (ID: {reason['ReasonId']})")

    reason_id = input("Choose a reason by entering the ID: ")
    if reason_id:
      print('Thanks for providing reason')
    return [{'Reason': 'Consultation', 'ReasonId': 201}, {'Reason': 'Follow-up', 'ReasonId': 202}]




def prefred_date_time_fun(response):
    print("response12",response)
    def get_next_weekday(day_name, use_next=False):
    # Dictionary to convert day names to weekday numbers
        days_of_week = {
            'monday': 0, 'mon': 0, 'Monday': 0, 'Mon': 0,
            'tuesday': 1, 'tues': 1,'Tuesday': 1, 'Tues': 1,
            'wednesday': 2, 'wed': 2,'Wednesday': 2, 'Wed': 2,
            'thursday': 3, 'thurs': 3,'Thursday': 3, 'Thurs': 3,
            'friday': 4, 'fri': 4,'Friday':4, 'Fri':4,
            'saturday': 5, 'sat': 5,'Saturday': 5, 'Sat': 5,
            'sunday': 6, 'sun': 6,'Sunday': 6, 'Sun': 6
        }

        # Get today's date and the current weekday
        today = datetime.now()
        current_weekday = today.weekday()

        # Convert the day name to a weekday number
        target_weekday = days_of_week[day_name.lower()]

        # Calculate the number of days until the next target weekday
        days_until_target = (target_weekday - current_weekday + 7) % 7

        if days_until_target == 0 or use_next:
            days_until_target += 7

        # Calculate the date for the next target weekday
        next_weekday = today + timedelta(days=days_until_target)
        return next_weekday

    def get_upcoming_weekday(day_name):
        # Dictionary to convert day names to weekday numbers
        days_of_week = {
            'monday': 0, 'mon': 0, 'Monday': 0, 'Mon': 0,
            'tuesday': 1, 'tues': 1,'Tuesday': 1, 'Tues': 1,
            'wednesday': 2, 'wed': 2,'Wednesday': 2, 'Wed': 2,
            'thursday': 3, 'thurs': 3,'Thursday': 3, 'Thurs': 3,
            'friday': 4, 'fri': 4,'Friday':4, 'Fri':4,
            'saturday': 5, 'sat': 5,'Saturday': 5, 'Sat': 5,
            'sunday': 6, 'sun': 6,'Sunday': 6, 'Sun': 6
        }
        # Get today's date and the current weekday
        today = datetime.now()
        current_weekday = today.weekday()

        # Convert the day name to a weekday number
        target_weekday = days_of_week[day_name.lower()]

        # Calculate the number of days until the upcoming target weekday
        days_until_target = (target_weekday - current_weekday + 7) % 7

        # If the day is today and has not passed, use today's date
        if days_until_target == 0:
            next_weekday = today
        else:
            next_weekday = today + timedelta(days=days_until_target)

        return next_weekday

    def get_relative_day(keyword):
        today = datetime.now()
        if keyword == "tomorrow":
            return today + timedelta(days=1)
        elif keyword == "day after tomorrow":
            return today + timedelta(days=2)
        return None

    def extract_date_from_response(response):
        keywords = ["next", "coming", "upcoming", "tomorrow", "day after tomorrow"]
        use_next = any(keyword in response.lower() for keyword in ["next", "coming"])
        use_upcoming = "upcoming" in response.lower()

        # Check for "tomorrow" and "day after tomorrow"
        relative_day = None
        for keyword in ["tomorrow", "day after tomorrow"]:
            if keyword in response.lower():
                relative_day = get_relative_day(keyword)
                response = re.sub(keyword, "", response, flags=re.IGNORECASE).strip()
                break

        # Extract the day name from the response
        day_name_match = re.search(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tues|Wed|Thurs|Fri|Sat|Sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tues|wed|thurs|fri|sat|sun)\b', response, re.IGNORECASE)
        if day_name_match:
            day_name = day_name_match.group(0)
        else:
            day_name = None

        if relative_day:
            if day_name:
                # If there's a specific day mentioned, calculate from the relative day
                next_day = get_next_weekday(day_name)
                if next_day <= relative_day:
                    next_day += timedelta(days=7)
                if next_day < datetime.now():
                    return "Date is in the past"
                return next_day.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                return relative_day.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            # Remove the keyword from the input if it exists
            for keyword in ["next", "coming", "upcoming"]:
                response = re.sub(keyword, "", response, flags=re.IGNORECASE).strip()

            if day_name:
                if use_upcoming:
                    next_day = get_upcoming_weekday(day_name)
                else:
                    next_day = get_next_weekday(day_name, use_next)
                if next_day < datetime.now():
                    return "Date is in the past"
                return next_day.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                return "No valid day found in the response"
    if "next" in response.lower() or "coming" in response.lower() or "upcoming" in response.lower() or "tomorrow" in response.lower() or "next day" in response.lower():

        return extract_date_from_response(response)

    else:
        response=response.replace(',','')
        patterns = [
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{1,2}) (\d{4})  (Morning|Afternoon|Evening|Night)\b', '%B %d %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{1,2}) (\d{4})   (Morning|Afternoon|Evening|Night)\b', '%B %d %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{1,2}) (\d{4}) (Morning|Afternoon|Evening|Night)\b', '%B %d %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{1,2}) (\d{4})  (Morning|Afternoon|Evening|Night)\b', '%B %d %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{1,2}) (\d{4})\b', '%B %d %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{1,2}) (\d{4})\b', '%B %d %Y'),
            (r'(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{4}) (Morning|Afternoon|Evening|Night)\b', '%d %B %Y'),
            (r'(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December|january|february|march|april|May|june|july|august|september|october|november|december) (\d{4})\b', '%d %B %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}) (\d{4})\b','%B %d %Y'), # Added this line
            (r'\b(\d{1,2}) (AM|PM)\b', None),
            (r'\b(Morning|Afternoon|Evening|Night)\b', None),
            (r'\b(0[1-9]|1[0-2])(\/|-)(0[1-9]|[12][0-9]|3[01])(\/|-)(19|20)\d{2}\b', '%m/%d/%Y'),
            (r'\b(0[1-9]|1[0-2])(\/|-)(0[1-9]|[12][0-9]|3[01])(\/|-)(19|20)\d{2}\b', '%m-%d-%Y'),
            (r'\b(0[1-9]|[12][0-9]|3[01])(\/|-)(0[1-9]|1[0-2])(\/|-)(19|20)\d{2}\b', '%d/%m/%Y'),
            (r'\b(0[1-9]|[12][0-9]|3[01])(\/|-)(0[1-9]|1[0-2])(\/|-)(19|20)\d{2}\b', '%d-%m-%Y'),
            (r'\b(\d{4})-(\d{2})-(\d{1,2})\b', '%Y-%m-%d'),
            (r'\b(\d{2})/(\d{1,2})/(\d{4})\b', '%m/%d/%Y'),
            (r'\b(\d{4})/(\d{2})/(\d{1,2})\b', '%Y/%m/%d'),
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\d{1,2}), (\d{4}) (Morning|Afternoon|Evening|Night)\b', '%b %d, %Y'),
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\d{1,2}) (\d{4}) (Morning|Afternoon|Evening|Night)\b', '%b %d %Y'),
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\d{1,2}), (\d{4})\b', '%b %d, %Y'),
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\d{1,2}) (\d{4})\b', '%b %d %Y'),
            (r'(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\d{4}) (Morning|Afternoon|Evening|Night)\b', '%d %b %Y'),
            (r'(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (\d{4})\b', '%d %b %Y'),
    ]

        # Time mappings for periods of the day
        time_mappings = {
            "Morning": 9,
            "Afternoon": 15,
            "Evening": 18,
            "Night": 21
        }

        datetime_obj = None
        for pattern, date_format in patterns:
            match = re.search(pattern, response)

            if match:
                groups = match.groups()
                if date_format:

                    date_str = ' '.join(groups[:3])

                    datetime_obj = datetime.strptime(date_str, date_format)
                    if len(groups) == 4:  # If there's a time of day
                        period = groups[3]
                        hour = time_mappings.get(period, 12)
                        datetime_obj = datetime_obj.replace(hour=hour)
                        if datetime_obj < datetime.now():
                            return "Date is in the past"
                    break
                else:
                    if len(groups) == 2 and groups[1] in ["AM", "PM"]:
                        hour, am_pm = groups
                        hour = int(hour)
                        if am_pm == 'PM' and hour != 12:
                            hour += 12
                        elif am_pm == 'AM' and hour == 12:
                            hour = 0
                        if datetime_obj:
                            datetime_obj = datetime_obj.replace(hour=hour)
                        else:
                            datetime_obj = datetime.combine(datetime.now().date(), datetime.min.time()).replace(hour=hour)

                    elif len(groups) == 1 and groups[0] in time_mappings:
                        period = groups[0]
                        hour = time_mappings[period]
                        if datetime_obj:
                            datetime_obj = datetime_obj.replace(hour=hour)
                        else:
                            datetime_obj = datetime.combine(datetime.now().date(), datetime.min.time()).replace(hour=hour)
                break

        if not datetime_obj:
            raise ValueError("No valid date format found in the response")

        return datetime_obj.isoformat()


def get_open_slots(token, prefred_date_time,location_id, reason_id, provider_id):
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {auth_token}'}
    preferred = prefred_date_time_fun(prefred_date_time)
    print("prefred date time",preferred)

    # from_date = "2024-07-20T15:30:00"
    from_date = preferred
    print("from_date",from_date)
    get_open_slots_url = f"https://iochatbot.maximeyes.com/api/appointment/openslotforchatbot?fromDate={from_date}&isOpenSlotsOnly=true"
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

    print("Available open slots:")
    for idx, slot in enumerate(open_slots):
        print(f"{idx + 1}: {slot['ApptStartDateTime']} - {slot['ApptEndDateTime']} (ID: {slot['OpenSlotId']})")

    open_slot_id = input("Choose an open slot by entering the ID: ")
    pass
def sndotp(token, slot_id, appointment_date, reason_id, FirstName, LastName, PhoneNumber, DOB, Email):
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {auth_token}'}
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

    otp = input("Enter the OTP received: ")
    pass

def book_appointment(token, open_slot_id, appointment_date,from_date, reason_id, FirstName, LastName, DOB, PhoneNumber, Email):
    headers = {
        'Content-Type': 'application/json',
        'apiKey': f'bearer {auth_token}'}
    book_appointment_url = "https://iochatbot.maximeyes.com/api/appointment/onlinescheduling"
    # Convert ApptDate to 'MM/DD/YYYY' format
     #  print()
    #appointment_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S").strftime("%m/%d/%Y")
    parsed_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S")

    # Convert the datetime object to the desired format
    appointment_date = parsed_date.strftime("%m/%d/%Y")
    print(appointment_date)
    book_appointment_payload = {
        "OpenSlotId": open_slot_id,
        "ApptDate": appointment_date,
        "ReasonId": reason_id,
        "FirstName": FirstName,
        "LastName": LastName,
        "PatientDob": DOB,
        "MobileNumber": PhoneNumber,
        "EmailId": Email}

    try:
        book_appointment_response = requests.post(book_appointment_url, json=book_appointment_payload, headers=headers)
        book_appointment_response.raise_for_status()
        return book_appointment_response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while booking the appointment: {e}")
        # return
    if book_appointment_response.status_code != 200:
        return f"Failed to book appointment. Status code: {book_appointment_response.status_code}"

    return {'Status': 'Success', 'AppointmentId': 301}

# tools = [
    
#     Tool(name="Get Providers", func=lambda location_id: get_providers(location_id, get_auth_token()), description="Get the list of providers for a specific location"),
#     Tool(name="Get Appointment Reasons", func=lambda provider_id, location_id: get_appointment_reasons(provider_id, location_id, get_auth_token()), description="Get the list of appointment reasons for a specific provider and location"),
#     Tool(name="Book Appointment", func=lambda location_id, provider_id, appointment_reason_id: book_appointment(location_id, provider_id, appointment_reason_id, get_auth_token()), description="Book an appointment with the specified details")
# ]


# tools_description = "\n".join(f"{tool.name}: {tool.description}" for tool in tools)

# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=["context", "user_input", "agent_scratchpad", "tools", "tool_names"],
    template="""
    You are a healthcare chatbot. {context}\n"
        "Tools available: {tool_names}\n"
        "Use the following tools to assist the user:\n{tools}\n\n"
        "{agent_scratchpad}\n"
        "User: {user_input}\n"
        "Bot (provide action and necessary details):"
    """
)
# memory = ConversationBufferWindowMemory(
#     memory_key='chat_history',
#     k=3,
#     return_messages=True
# )

# agent = create_react_agent(
#         llm=llm,  
#         tools=tools,
#         prompt=prompt_template)





# Define the parsing function for agent's output
def parse_output(output):
    try:
        lines = output.strip().split("\n")
        action_line = next(line for line in lines if line.startswith("Action:"))
        tool_input_line = next(line for line in lines if line.startswith("Tool Input:"))
        action = action_line.split("Action:")[1].strip()
        tool_input = tool_input_line.split("Tool Input:")[1].strip()
        return action, tool_input
    except (StopIteration, IndexError) as e:
        raise ValueError("Could not parse output correctly.") from e

# Define state and memory
state = {
    "step": "start",
    "location_selected": None,
    "provider_selected": None,
    "appointment_reason_selected": None,
    "intermediate_steps": [],
    "locations": [],
    "providers": []
}

memory = ConversationBufferMemory(memory_key="chat_history")

fixed_prompt = '''Assistant is a health care chat bot for booking appointments

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant doesn't know anything about get location or book appointment and should use a tool for questions about these topics.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful system that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.'''



# Define the user input handling function


def handle_user_input(user_input):
   

    def call_get_locations(*args, **kwargs):
        token = get_auth_token()  # Call get_auth_token to get the token
        return get_locations(token) 
    location_tool=Tool(
            name="Get Locations", 
            func= call_get_locations ,
            description="Get the list of locations for booking appointments when we want to book appointment"
            )

    privider_tool=Tool(
                name="Get Providers", 
                func=lambda location_id: get_providers(location_id, get_auth_token()), 
                description="Get the list of providers for a specific location")
                


    reasons_tool=Tool(name="Get Appointment Reasons", 
            func=lambda provider_id, location_id: get_appointment_reasons(provider_id, location_id, get_auth_token()), 
            description="Get the list of appointment reasons for a specific provider and location"
            )



    book_appointment_tool=Tool(name="Book Appointment", 
            func=lambda location_id, provider_id, appointment_reason_id: book_appointment(location_id, provider_id, appointment_reason_id, get_auth_token()),
                description="Book an appointment with the specified details")




    tools=[location_tool,privider_tool,reasons_tool,book_appointment_tool]
    tool_names = ", ".join(tool.name for tool in tools)

    global state
    
    conversational_agent = initialize_agent(
        agent='chat-conversational-react-description',
        tools=tools,
        llm=llm,
        verbose=True,
        max_iterations=1,
        early_stopping_method='generate',
        
    )
    conversational_agent.agent.llm_chain.prompt = prompt_template
    print(user_input,'user_input')
    print(tools,'tools')
    # print(tool_names,'tool_names') 
    print(state,'state') 
    # 
    if state["step"] == "start":
        if "book appointment" in user_input.lower():
            # result = agent.invoke({
            #     "context": "",
            #     "user_input": user_input,
            #     "agent_scratchpad": "",
            #     "tools": tools,
            #     "tool_names": tool_names,
            #     "intermediate_steps": state["intermediate_steps"]
            # })
            # output = result['output']
            chat_history = [
                                {"role": "user", "content": "What are the available locations?"},
                                {"role": "assistant", "content": "Here are the locations..."}
                            ]
            result=conversational_agent.run({'input': user_input,'chat_history': chat_history,'tool_names':tool_names, tools:tools, 'context':'',})
            print(result,'result-------')
            try:
                action, tool_input = parse_output(output)
                if action == "Get Locations":
                    locations = tools[0].func()
                    state["locations"] = locations
                    location_names = "\n".join([f"{loc['LocationId']}: {loc['Name']}" for loc in locations])
                    state["step"] = "location_selection"
                    return "Sure, let's book an appointment. Please provide the location ID from the following list:\n" + location_names
                else:
                    return "Unexpected action. Please try again."
            except ValueError:
                return "I'm sorry, I couldn't parse the response. Please try again."

        else:
            return "I can help you book an appointment. Please type 'book appointment' to get started."

    elif state["step"] == "location_selection":
        try:
            location_id = int(user_input)
            if any(loc['LocationId'] == location_id for loc in state["locations"]):
                state["location_selected"] = location_id
                result = agent.invoke({
                    "context": "",
                    "user_input": f"Get Providers {location_id}",
                    "agent_scratchpad": "",
                    "tools": tools,
                    "tool_names": tool_names,
                    "intermediate_steps": state["intermediate_steps"]
                })
                output = result['output']
                try:
                    action, tool_input = parse_output(output)
                    if action == "Get Providers":
                        providers = tools[1].func(location_id)
                        if providers:
                            provider_list = "\n".join([f"{prov['ProviderId']}: {prov['Name']}" for prov in providers])
                            state["step"] = "provider_selection"
                            return "Please choose a provider by entering the ID from the following list:\n" + provider_list
                        else:
                            return "No providers found for this location. Please try another location."
                    else:
                        return "Unexpected action. Please try again."
                except ValueError:
                    return "I'm sorry, I couldn't parse the response. Please try again."

            else:
                return "Invalid location ID. Please enter a valid ID from the list provided."
        except ValueError:
            return "Invalid input. Please enter a numerical ID from the list provided."

    elif state["step"] == "provider_selection":
        try:
            provider_id = int(user_input)
            state["provider_selected"] = provider_id
            location_id = state["location_selected"]
            result = agent.invoke({
                "context": "",
                "user_input": f"Get Appointment Reasons {provider_id} {location_id}",
                "agent_scratchpad": "",
                "tools": tools,
                "tool_names": tool_names,
                "intermediate_steps": state["intermediate_steps"]
            })
            output = result['output']
            try:
                action, tool_input = parse_output(output)
                if action == "Get Appointment Reasons":
                    appointment_reasons = tools[2].func(provider_id, location_id)
                    if appointment_reasons:
                        reason_list = "\n".join([f"{reason['ReasonId']}: {reason['Reason']}" for reason in appointment_reasons])
                        state["step"] = "appointment_reason_selection"
                        return "Please choose an appointment reason by entering the ID from the following list:\n" + reason_list
                    else:
                        return "No appointment reasons found for this provider. Please try another provider."
                else:
                    return "Unexpected action. Please try again."
            except ValueError:
                return "I'm sorry, I couldn't parse the response. Please try again."

        except ValueError:
            return "Invalid provider ID. Please enter a valid ID."

    elif state["step"] == "appointment_reason_selection":
        try:
            appointment_reason_id = int(user_input)
            state["appointment_reason_selected"] = appointment_reason_id
            location_id = state["location_selected"]
            provider_id = state["provider_selected"]
            result = agent.invoke({
                "context": "",
                "user_input": f"Book Appointment {location_id} {provider_id} {appointment_reason_id}",
                "agent_scratchpad": "",
                "tools": tools,
                "tool_names": tool_names,
                "intermediate_steps": state["intermediate_steps"]
            })
            output = result['output']
            try:
                action, tool_input = parse_output(output)
                if action == "Book Appointment":
                    booking_result = tools[3].func(location_id, provider_id, appointment_reason_id)
                    state["step"] = "start"
                    state["location_selected"] = None
                    state["provider_selected"] = None
                    state["appointment_reason_selected"] = None
                    if booking_result.get("Status") == "Success":
                        return f"Your appointment has been booked successfully. Appointment ID: {booking_result['AppointmentId']}"
                    else:
                        return "Failed to book the appointment. Please try again."
                else:
                    return "Unexpected action. Please try again."
            except ValueError:
                return "I'm sorry, I couldn't parse the response. Please try again."

        except ValueError:
            return "Invalid appointment reason ID. Please enter a valid ID."

    return "Unexpected state. Please start over."

# Define the Django view
@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        user_input = data.get('input', '')
        response = handle_user_input(user_input)
        if response:
            bot_response = response
            memory.save_context({"input": user_input}, {"output": bot_response})
        else:
            bot_response = "I'm sorry, I couldn't process your request. Can you please try again?"
        return JsonResponse({"response": bot_response})
    return JsonResponse({"response": "Invalid request"}, status=400)