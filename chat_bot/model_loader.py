import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# Detect the available device
device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
print(f"Using device: {device}")


# Load the base model and tokenizer
# base_model_name = "NousResearch/Llama-2-7b-chat-hf"
# tokenizer = AutoTokenizer.from_pretrained(base_model_name)
# base_model = AutoModelForCausalLM.from_pretrained(base_model_name, device_map='auto', torch_dtype=torch.float16)

# # Load the fine-tuned adapter weights
# parent = os.path.dirname(os.path.abspath(__file__))
# adapter_path = f'{parent}/checkpoint-1070'
# print(f"adapter_path: {adapter_path}")
# print(f"Parent directory: {parent}")
# try:
#     base_model = PeftModel.from_pretrained(base_model, adapter_path)  # No .to(device)
# except KeyError as e:
#     print(f"KeyError encountered: {e}")

# base_model.to(device)
# llm=base_model

# Load the model and tokenizer
# model_name = "NousResearch/Llama-2-7b-chat-hf"  # Replace with the model you need
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name)

# # Ensure you're using a device that supports CUDA if available
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model.to(device)
# llm=model

# from langchain_community.llms import HuggingFaceHub

# llm = HuggingFaceHub(
#     repo_id="NousResearch/Llama-2-7b-chat-hf",
#     task="text-generation",
#     huggingfacehub_api_token="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",
#     model_kwargs={
#         "max_new_tokens": 512,
#         "top_k": 30,
#         "temperature": 0.1,
#         "repetition_penalty": 1.03,
#     },
# )


# from transformers import AutoTokenizer
# import transformers

# access_token = "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"
# model = "meta-llama/Meta-Llama-3.1-8B-Instruct"

# tokenizer = AutoTokenizer.from_pretrained(model, token=access_token)

# model = AutoModelForCausalLM.from_pretrained(
#     model, 
#     token=access_token
# )

# pipeline = transformers.pipeline(
#     "text-generation",
#     model=model,
#     torch_dtype=torch.float16,
#     device_map="auto",
# )

# sequences = pipeline(
#     'Hi! Tell me about yourself!',
#     do_sample=True,
# )
# print(sequences[0].get("generated_text"))