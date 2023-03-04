#!/usr/bin/env python3

import os
import openai
import sys
import subprocess
import argparse
import re
import json
import datetime

TERM_SUPPORTS_COLOR = os.getenv('TERM') is not None and '256' in os.getenv('TERM')

SYSTEM_PROMPT = f"""
You are an assistant on a Linux (Ubuntu) terminal.
      
User Details:
* location: Flower Mound, TX
* date: {datetime.datetime.now().strftime("%m-%d-%Y")}
* time: {datetime.datetime.now().strftime("%H:%M %p")}
* PWD: {os.getcwd()}

You can execute commands for the user by wrapping them like this: EXECUTE(command).
      
For example, EXECUTE(cd ~) would take the user to their home directory.

More examples:
User:
Please create a new directory called test and fill it with file1.txt thru file99.txt
Assistant:
EXECUTE(mkdir test)
EXECUTE(for i in {{1..99}}; do touch test/file$i.txt; done)
User:
Can you get me the weather?
Assistant:
EXECUTE(curl "https://wttr.in/Flower+Mound")
      
When asked to create a file or program, be sure to use the EXECUTE(command) syntax to create the file or program.
Do not use programs like nano or vim. Instead, you can echo line-by-line into a file.
"""

task = sys.argv[1]

openai.api_key = os.getenv("OPENAI_API_KEY")

def load_chatgpt_memory():
    with open('chatgpt-memory.json', 'r') as f:
        memory_objects = json.load(f)
    return memory_objects

def save_chatgpt_memory(memory_objects):
    with open('chatgpt-memory.json', 'w') as f:
        json.dump(memory_objects, f)

def notify_if_chatgpt_memory_exceeds_limit(memory_objects, limit=100):
    if len(memory_objects) > limit:
        print(f"\033[91mWARNING: chat memory is getting large (>{limit})\033[0m" if TERM_SUPPORTS_COLOR else f"WARNING: chat memory is getting large (>{limit})")


def loop(task):
    memory_objects = load_chatgpt_memory()

    messages=[
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    for memory_object in memory_objects:
        messages.append({"role": memory_object["role"], "content": memory_object["content"]})

    messages.append({"role": "user", "content": task})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    response = completion.choices[0].message.content

    memory_objects.append({"role": "user", "content": task})
    memory_objects.append({"role": "assistant", "content": response})

    notify_if_chatgpt_memory_exceeds_limit(memory_objects)

    save_chatgpt_memory(memory_objects)

    print(f'\n\033[38;5;24m{response}\033[0m\n' if TERM_SUPPORTS_COLOR else f'{response}\n')

    match = re.findall(r'EXECUTE\((.*)\)', response)
    for command in match:
        handle_command(command)


def handle_command(command):
    print(command)
    canExecute = input("Execute command? (y/n): ") == 'y'

    if canExecute and command.startswith('cd'):
        # whenever we have other commands separated by &&
        # We need to isolate the path we're cd-ing into
        raw_commands = command.split("&&")
        directory = raw_commands[0][3:].strip()
        
        # convert ~ to an abolute path
        if directory.startswith('~'):
            directory = os.path.expanduser(directory)

        os.chdir(directory)
        print(f'\nOUTPUT:\nPWD: {directory}')
  
        # handle remaining commands separated by &&
        if len(raw_commands) > 1:
            for cmd in raw_commands[1:]:
                handle_command(cmd.strip())

    elif canExecute:
        try:
            output = subprocess.check_output(command, shell=True).decode()
            print(f'\nOUTPUT:\n{output}')
        except subprocess.CalledProcessError as e:
            output = e

    else:
        instructions = input("If you'd like to instruct chatgpt-agent, type now: ")
        if instructions != "":
            task += f'\n\n{instructions}'
            loop(task)


loop(task)