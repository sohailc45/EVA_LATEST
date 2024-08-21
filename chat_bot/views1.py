
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import re
import requests
import os
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (format_to_openai_tool_messages,)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.tools import Tool
from langchain.agents.output_parsers import (ReActJsonSingleInputOutputParser,)


HUGGINGFACE_API_TOKEN=os.getenv('hugging_face_api_token')  
HUGGINGFACE_API_URL = "https://zzjxmo3ypzlaxmsp.us-east-1.aws.endpoints.huggingface.cloud"

class HuggingFaceLLM:
    def __init__(self, api_endpoint, api_token):
        self.api_endpoint = api_endpoint
        self.api_token = api_token
        self.tools = []

    def __call__(self, prompt, tool_name=None, tool_args=None):
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        if tool_name:
            print('Handle tool invocation')
            tool = next((t for t in self.tools if t.__name__ == tool_name), None)
            if tool:
                try:
                    # Ensure tool_args are JSON serializable
                    return tool(*tool_args)
                except TypeError as e:
                    return f"Error invoking tool: {e}"
            else:
                return f"Tool {tool_name} not found."

        print('Handle standard prompt')
        if hasattr(prompt, "text"):
            prompt = prompt.text

        # Ensure prompt is a string or convert it to a string
        if not isinstance(prompt, str):
            prompt = str(prompt)

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7
            }
        }

        try:
            print('calling Hugging face')
            response = requests.post(self.api_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            output = response.json()
            print(output,'output----')
            return output[0]["generated_text"]
        except requests.exceptions.RequestException as e:
            return f"Failed to call Hugging Face API: {e}"

    def bind_tools(self, tools):
        self.tools = tools
        return self

    def add_tool(self, tool):
        self.tools.append(tool)
        return self
llm = HuggingFaceLLM(HUGGINGFACE_API_URL, HUGGINGFACE_API_TOKEN)

def parse_huggingface_output(output):
    # Extract the generated_text from the response
    if 'generated_text' in output:
        generated_text = output['generated_text']
    else:
        return "Error: 'generated_text' not found in output."

    # Parse the generated_text content
    try:
        # Handle the specific structure of your response
        # For this example, we'll assume it follows a structured message format
        if "Could not parse LLM output" in generated_text:
            # Extract useful information from the failure message
            failure_message = generated_text.split("Could not parse LLM output:")[-1].strip()
            return f"Parsing Error: {failure_message}"
        
        # Otherwise, return the generated text as is
        return generated_text
    except Exception as e:
        return f"Error parsing output: {e}"

class CustomOutputParser:
    def parse_result(self, output):
        # Assuming output is a string from Hugging Face
        if isinstance(output, str):
            return output
        raise ValueError("Unexpected output format from Hugging Face model")

def get_locations(*args, **kwargs):
    print('')
    return 'location is Hillsboro'
def get_providers(*args, **kwargs):
    print('')
    return 'provider is dr. varun'

tools = [
    Tool(
        name="Get Locations",
        func=get_locations,
        description="Get the list of locations for booking appointments"
    ),
    Tool(
        name="Get Provider",
        func=get_providers,
        description="Get the list of providers for a specific location"
    )
]
# get_word_length.invoke("abc")

# tools = [get_location,get_provider]



llm_with_tools = llm.bind_tools(tools)
print(llm_with_tools,'sde3',llm)

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


MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a highly capable assistant with knowledge in various topics. However, you do not have specific information about location details or appointment booking. For questions regarding locations or appointments, you should utilize the provided tools to retrieve the necessary information. Use the tools effectively to address such queries.",
        ),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
chat_history = []

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | llm_with_tools
    | CustomOutputParser
    
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True,handle_parsing_errors=True,max_iterations=3)
















def home(request):
    return render(request, "home.html")

@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        user_input = data.get('input', '')
        response = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
        print(response,'-----response')
        try:
            # Parse the output using parse_output
            action, tool_input = parse_output(response)
        except:
            pass
        if response:
            bot_response = response
            bot_response = bot_response['output']
        else:
            bot_response = "I'm sorry, I couldn't process your request. Can you please try again?"
        return JsonResponse({"response": bot_response})
    return JsonResponse({"response": "Invalid request"}, status=400)

def handle_user_input(user_input):
    global state
    
    if state["step"] == "start":
        if "book appointment" in user_input.lower():
            
            chat_history = [
                                {"role": "user", "content": "What are the available locations?"},
                                {"role": "assistant", "content": "Here are the locations..."}
                            ]
            result=''
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

                # action, tool_input = parse_output(output)
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