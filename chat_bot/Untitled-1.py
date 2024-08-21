
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from transformers import pipeline
from huggingface_hub import InferenceClient
from pydantic import BaseModel
from typing import Dict, Any

# Define the tools
def get_auth_token():
    # Dummy function to get auth token
    return "dummy_token"

def get_locations(auth_token):
    # Dummy function to get locations
    return [{"LocationId": 1, "Name": "Location 1"}, {"LocationId": 2, "Name": "Location 2"}]

def get_providers(location_id, auth_token):
    # Dummy function to get providers
    return [{"ProviderId": 1, "Name": "Provider 1"}, {"ProviderId": 2, "Name": "Provider 2"}]

def get_appointment_reasons(provider_id, location_id, auth_token):
    # Dummy function to get appointment reasons
    return [{"ReasonId": 1, "Reason": "Reason 1"}, {"ReasonId": 2, "Reason": "Reason 2"}]

def book_appointment(location_id, provider_id, appointment_reason_id, auth_token):
    # Dummy function to book appointment
    return {"Status": "Success", "AppointmentId": 12345}

tools = [
    {"name": "Get Locations", "func": lambda: get_locations(get_auth_token()), "description": "Get the list of locations for booking appointments"},
    {"name": "Get Providers", "func": lambda location_id: get_providers(location_id, get_auth_token()), "description": "Get the list of providers for a specific location"},
    {"name": "Get Appointment Reasons", "func": lambda provider_id, location_id: get_appointment_reasons(provider_id, location_id, get_auth_token()), "description": "Get the list of appointment reasons for a specific provider and location"},
    {"name": "Book Appointment", "func": lambda location_id, provider_id, appointment_reason_id: book_appointment(location_id, provider_id, appointment_reason_id, get_auth_token()), "description": "Book an appointment with the specified details"}
]

tool_names = ", ".join(tool["name"] for tool in tools)
tools_description = "\n".join(f"{tool['name']}: {tool['description']}" for tool in tools)

# Set up Hugging Face LLM endpoint
endpoint_url = "https://actual_endpoint.endpoints.huggingface.cloud"
hf_token = "hf_actual_token"
client = InferenceClient(endpoint_url, token=hf_token)

# Define the prompt template
prompt_template = '''
    You are a healthcare chatbot. {context}\n
    Tools available: {tool_names}\n
    Use the following tools to assist the user:\n{tools}\n\n
    {agent_scratchpad}\n
    User: {user_input}\n
    Bot (provide action and necessary details):
'''

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

# Define the user input handling function
def handle_user_input(user_input):
    global state

    if state["step"] == "start":
        if "book appointment" in user_input.lower():
            prompt = prompt_template.format(
                context="",
                user_input=user_input,
                agent_scratchpad="",
                tools=tools_description,
                tool_names=tool_names
            )
            response = client.text_generation(prompt, max_new_tokens=50)[0]['generated_text']
            try:
                action, tool_input = parse_output(response)
                if action == "Get Locations":
                    locations = tools[0]["func"]()
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
                prompt = prompt_template.format(
                    context="",
                    user_input=f"Get Providers {location_id}",
                    agent_scratchpad="",
                    tools=tools_description,
                    tool_names=tool_names
                )
                response = client.text_generation(prompt, max_new_tokens=50)[0]['generated_text']
                try:
                    action, tool_input = parse_output(response)
                    if action == "Get Providers":
                        providers = tools[1]["func"](location_id)
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
            prompt = prompt_template.format(
                context="",
                user_input=f"Get Appointment Reasons {provider_id} {location_id}",
                agent_scratchpad="",
                tools=tools_description,
                tool_names=tool_names
            )
            response = client.text_generation(prompt, max_new_tokens=50)[0]['generated_text']
            try:
                action, tool_input = parse_output(response)
                if action == "Get Appointment Reasons":
                    appointment_reasons = tools[2]["func"](provider_id, location_id)
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
            prompt = prompt_template.format(
                context="",
                user_input=f"Book Appointment {location_id} {provider_id} {appointment_reason_id}",
                agent_scratchpad="",
                tools=tools_description,
                tool_names=tool_names
            )
            response = client.text_generation(prompt, max_new_tokens=50)[0]['generated_text']
            try:
                action, tool_input = parse_output(response)
                if action == "Book Appointment":
                    booking_result = tools[3]["func"](location_id, provider_id, appointment_reason_id)
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
        else:
            bot_response = "I'm sorry, I couldn't process your request. Can you please try again?"
        return JsonResponse({"response": bot_response})
    return JsonResponse({"response": "Invalid request"}, status=400)

