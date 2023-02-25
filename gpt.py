#!/usr/bin/env python3

import sys
import os
import requests
import json
import sounddevice as sd
import subprocess

normal_prompt = '''
CHATBOT INSTRUCTIONS:
You are a helpful chatbot named "Robot" - your purpose is to answer questions factually and accuratly. Your answers should be short and concise--limited to 1 paragraph at most. You should never speak in a threatening tone towards the user.

USER INFORMATION:
Name: Cody
Location: Texas

QUERY:
What are the health pros and cons of split pea soup?
RESPONSE:
Pros: Split peas are high in protein, fiber, and various vitamins and minerals.
Cons: Split peas are relatively high in calories and carbohydrates.
QUERY:
What is the capital of Oklahoma?
RESPONSE:
Oklahoma City.
QUERY:
Hey robot - I'm trying to think of the name of that toy where you use bricks to build stuff. Can you help me?
RESPONSE:
It sounds like you're referring to LEGO.
QUERY:

'''

is_math_prompt = '''
INSTRUCTIONS:
Your task is to answer "true" or "false" for if a query is a math question. A math question is any question that requires the use of mathematics to be solved (no matter how easy the math is).

QUERY:
Can you give me a break down of each model of vehicle Tesla makes?
RESPONSE:
false
QUERY:
If I drive 60MPH, with a 15 minute break every two hours, how far can I drive in an 8 hour span?
RESPONSE:
true
QUERY:
Can you solve this for me? 5x + 20 = 40
RESPONSE:
true
QUERY:
Ugh hey chatbot - so my friend samantha said that she'd meet me at this restaurant 30 minutes past 6. It is 6:20 and I don't see her. Am I missing something? I thought she would have been here by now...
REPONSE:
true
QUERY:
How should I approach my employer about this: my paycheck was short 40 dollars and I need to figure out how much the check should be for.
REPONSE:
true
QUERY:

'''

math_prompt = '''
INSTRUCTIONS:
For each math query please provide python code that when executed will give the correct answer. Do not attempt to show the answer or solve the problem yourself.

QUERY:
If I drive 60MPH, with a 15 minute break every two hours, how far can I drive in an 8 hour span?
RESPONSE:
speed = 60 # miles per hour
break_time = 15 # minutes
break_interval = 120 # minutes
total_time = 8 * 60 # minutes (8 hours converted to minutes)

drive_time = total_time
num_breaks = total_time // break_interval

# Subtract time for breaks
drive_time -= num_breaks * break_time

distance = speed * (drive_time / 60) # Convert drive time from minutes to hours

print(distance)
QUERY:
Can you solve this for me? 5x + 20 = 40
RESPONSE:
# Define variable x
x = 0

left_side = 5 * x + 20
right_side = 40

# Subtract 20 from both sides
left_side -= 20
right_side -= 20

# Divide both sides by 5
x = right_side / 5

print("x =", x)
QUERY:
Hey chatbot - can you tell me what 2 to the power of 8 is?
REPONSE:
# Define variable power
power = 8

# Calculate 2 to the power of 8
result = 2**power

print("2 to the power of 8 is", result)
QUERY:

'''

is_math_prompt += sys.argv[1]
is_math_prompt += '\nRESPONSE:\n'

openai_api_key = os.environ.get('OPENAI_API_KEY')
model_name = "text-davinci-003"
temperature = 0.7
max_tokens = 256
top_p = 1
frequency_penalty = 0
presence_penalty = 0

url = "https://api.openai.com/v1/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
}

data = {
    "model": model_name,
    "prompt": is_math_prompt,
    "temperature": temperature,
    "max_tokens": max_tokens,
    "top_p": top_p,
    "frequency_penalty": frequency_penalty,
    "presence_penalty": presence_penalty
}

api_response = requests.post(url, headers=headers, data=json.dumps(data))
api_response_data = json.loads(api_response.text)
gpt_response = api_response_data['choices'][0]['text']

if (len(gpt_response) > 0):
    # Math question
    if (gpt_response == 'true'):
        math_prompt += sys.argv[1]
        math_prompt += '\nRESPONSE:\n'
        data['prompt'] = math_prompt
        api_response = requests.post(url, headers=headers, data=json.dumps(data))
        api_response_data = json.loads(api_response.text)
        gpt_response = api_response_data['choices'][0]['text']
        if (len(gpt_response) > 0):
            print(gpt_response)
            print('\n\nOUTPUT:')
            subprocess.run(["python3", "-c", gpt_response], check=True)
        else:
            print("Sorry. It looks like the GPT3 api failed to give a valid response!")
    # Normal question
    else:
        normal_prompt += sys.argv[1]
        normal_prompt += '\nRESPONSE:\n'
        data['prompt'] = normal_prompt
        api_response = requests.post(url, headers=headers, data=json.dumps(data))
        api_response_data = json.loads(api_response.text)
        gpt_response = api_response_data['choices'][0]['text']
        if (len(gpt_response) > 0):
            print(gpt_response)
        else:
            print("Sorry. It looks like the GPT3 api failed to give a valid response!")
else:
    print("Sorry. It looks like the GPT3 api failed to give a valid response!")
