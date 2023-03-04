#!/usr/bin/env python3

import sys
import os
import requests
import json
import sounddevice as sd
import subprocess
import openai
from elevenlabslib import *

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
openai.api_key = os.getenv("OPENAI_API_KEY")
OS = os.environ.get('OS')

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
import sympy

# Define variable x
x = sympy.symbols('x')

# Define equation
equation = 5x + 20 - 40

# Solve equation
solution = sympy.solve(equation, x)

print("x =", solution)
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

model_name = "text-davinci-003"
temperature = 0.7
max_tokens = 256
top_p = 1
frequency_penalty = 0
presence_penalty = 0

url = "https://api.openai.com/v1/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
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
            subprocess.run(["python.exe" if OS == 'Windows_NT' else "python3", "-c", gpt_response], check=True)
        else:
            print("Sorry. It looks like the GPT3 api failed to give a valid response!")
    # Normal question
    else:
        prompt = sys.argv[1]

        completion = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
            {"role": "system", "content": "Please answer user questions concisely - you should answer in just a few sentences."},
            {"role": "user", "content": "Tell me about healthy blood pressure ranges"},
            {"role": "assistant", "content": "A healthy blood pressure range is typically considered to be less than 120/80 mmHg. However, it's important to note that blood pressure can vary based on age, gender, and overall health, so it's best to consult with a doctor to determine what's right for you. High blood pressure (hypertension) can increase your risk for heart disease and stroke, so it's important to monitor and manage your blood pressure."},
            {"role": "user", "content": "which was more popular - windows vista or xp?"},
            {"role": "assistant", "content": "Windows XP was more popular than Windows Vista. XP was released in 2001 and was widely used by consumers and businesses for many years. Vista, which was released in 2006, was not as well-received due to its higher system requirements and compatibility issues with some software and hardware. Windows 7, which was released in 2009, became the preferred choice for many users after XP."},
            {"role": "user", "content": prompt}
          ]
        )

        response = completion.choices[0].message.content
        if (len(response) > 0):
            print(response)
            user = ElevenLabsUser(os.environ.get('ELEVEN_LABS_API_KEY'))
            voice = user.get_voices_by_name("Rachel")[0]  # This is a list because multiple voices can have the same name
            voice.generate_and_play_audio(response, playInBackground=False)
        else:
            print("Sorry. It looks like the GPT3 api failed to give a valid response!")
else:
    print("Sorry. It looks like the GPT3 api failed to give a valid response!")
