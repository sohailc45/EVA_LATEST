
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import re
import requests
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
from langchain.agents.format_scratchpad import format_log_to_str
from langchain import hub
from langchain.agents import AgentExecutor, load_tools, create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import (  ReActJsonSingleInputOutputParser,)
from langchain.tools.render import render_text_description
from langchain.agents.output_parsers import ReActSingleInputOutputParser
# from langchain.core.messages import HumanMessage, AIMessage
from . model_loader import *

import os
from langchain_community.llms import HuggingFaceTextGenInference
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder





def home(request):
    return render(request, "home.html")

@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        user_input = data.get('input', '')
        response= '' #handle_user_input(user_input)
        # response = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
        print(response,'-----response-')
        # response=''
        try:
            # Parse the output using parse_output
            action, tool_input = parse_output(response)
        except:
            pass
        if response:
            bot_response = response
           
        else:
            bot_response = "I'm sorry, I couldn't process your request. Can you please try again?"
        return JsonResponse({"response": bot_response})
    return JsonResponse({"response": "Invalid request"}, status=400)




def parse_output(output):
    try:
        lines = str(output).strip().split("\n")
        action_line = next(line for line in lines if line.startswith("Action:"))
        tool_input_line = next(line for line in lines if line.startswith("Tool Input:"))
        action = action_line.split("Action:")[1].strip()
        tool_input = tool_input_line.split("Tool Input:")[1].strip()
        return action, tool_input
    except (StopIteration, IndexError) as e:
        raise ValueError("Could not parse output correctly.") from e






