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

def notify_if_chatgpt_memory_exceeds_character_limit(memory_objects, limit=10000):
    total_content_length = sum(len(memory_object["content"]) for memory_object in memory_objects)
    if total_content_length > limit:
        warning_message = f"WARNING: chat memory is getting large (>{limit})"
        print(f"\033[91m{warning_message}\033[0m" if TERM_SUPPORTS_COLOR else warning_message)

def get_openai_chatgpt_completion(messages):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return completion

def loop(task):
    memory_objects = load_chatgpt_memory()
    memory_objects.append({"role": "user", "content": task})

    messages=[
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    messages.extend(memory_objects)

    response = get_openai_chatgpt_completion(messages).choices[0].message.content
    memory_objects.append({"role": "assistant", "content": response})

    notify_if_chatgpt_memory_exceeds_character_limit(memory_objects)

    save_chatgpt_memory(memory_objects)

    print(f'\n\033[38;5;24m{response}\033[0m\n' if TERM_SUPPORTS_COLOR else f'{response}\n')

    match = re.findall(r'EXECUTE\((.*)\)', response)
    for command in match:
        handle_command(command)
    
    continuing = input("Continue using chatgpt-agent? (y/n): ") == 'y'
    if continuing:
        task = input("User: ")
        loop(task)


def change_directory(path):
    # convert ~ to an abolute path
    if path.startswith('~'):
        path = os.path.expanduser(path)

    os.chdir(path)
    print(f'\nOUTPUT:\nPWD: {path}')

def handle_command(command):
    print(command)
    canExecute = input("Execute command? (y/n): ") == 'y'

    if canExecute and command.startswith('cd'):
        # whenever we have other commands separated by &&
        # We need to isolate the path we're cd-ing into
        raw_commands = command.split("&&")
        path = raw_commands[0][3:].strip()

        change_directory(path)
  
        # handle remaining commands separated by &&
        if len(raw_commands) > 1:
            for cmd in raw_commands[1:]:
                handle_command(cmd.strip())

    elif canExecute:
        try:
            output = subprocess.check_output(command, shell=True).decode()
        except subprocess.CalledProcessError as e:
            output = e
        print(f'\nOUTPUT:\n{output}')

    else:
        instructions = input("If you'd like to instruct chatgpt-agent, type now: ")
        if instructions != "":
            task = f'{instructions}'
            loop(task)
        exit()


loop(task)