import os
import openai

from constants import INTENT_DICT
from dotenv import load_dotenv
load_dotenv()

#OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")


#Initial training

def get_completion(prompt, model='gpt-3.5-turbo', temperature=0):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # make sure that randomness of model output is null
    )
    return response.choices[0].message["content"]


#initial training

training_str = ""
for intent, messages in INTENT_DICT.items():
    training_str += "Intent: " + intent + ", messages : "
    message_str = ",".join(messages) 
    training_str += message_str + ". End of Intent."

final_str = """You are designed to be a prompt chatbot. I will give you a list of intents and messages that lead to those intent. 
If a user writes any prompts afterwards, only return the intents that I specify in the training intents and messages and if you do not know the intent, 
please return 'I do not know what you are speaking about, please try something along the lines of I want to transfer money or I want to check my account balance'. Training is included below"""

final_str += training_str

print(final_str)

training_res = get_completion(final_str)
print(training_res)

# To include history as prompts are isolated 
test_prompt = "I want to transfer money"

print(get_completion(test_prompt))

## Gradio test