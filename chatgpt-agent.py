#!/usr/bin/env python3

import os
import openai
import sys
import subprocess
import re
import json
import datetime
import requests

response = requests.get("https://ipinfo.io/json")

if response.status_code == 200:
    ipinfo = response.json()
    city = ipinfo['city']
    region = ipinfo['region']

TERM_SUPPORTS_COLOR = os.getenv('TERM') is not None and '256' in os.getenv('TERM')

SYSTEM_PROMPT = f"""
You are an assistant on a Linux (Ubuntu) terminal.
      
User Details:
{f"* location: {city}, {region}" if city and region else ''}
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
You can use echo to write text line-by-line into a file.
Do not use programs that require user input, such as top, nano, or apt.
"""

task = sys.argv[1]

openai.api_key = os.getenv("OPENAI_API_KEY")

MEMORY_SETTINGS = {
    "folder_path": "memory",
    "file_prefix": "chatgpt-memory_",
    "file_extension": ".json",
    "token_limit": 3500
}

LOG_SETTINGS = {
    "dir": "log",
    "is_logging": True
}

ALERT_ANSI_COLOR = "91"
CHATGPT_RESPONSE_ANSI_COLOR = "38;5;24"

def get_latest_chatgpt_memory_file():
    if not os.path.exists(MEMORY_SETTINGS['folder_path']):
        os.makedirs(MEMORY_SETTINGS['folder_path'])
    memory_files = [f for f in os.listdir(MEMORY_SETTINGS['folder_path']) if os.path.isfile(os.path.join(MEMORY_SETTINGS['folder_path'], f)) 
                   and f.startswith(MEMORY_SETTINGS['file_prefix']) and f.endswith(MEMORY_SETTINGS['file_extension'])]
    if not memory_files:
        return None
    return max(memory_files)

def load_chatgpt_memory():
    latest_file = get_latest_chatgpt_memory_file()
    if latest_file is not None:
        with open(os.path.join(MEMORY_SETTINGS['folder_path'], latest_file), 'r') as f:
            memory_objects = json.load(f)
    else:
        memory_objects = []
    return memory_objects

def save_chatgpt_memory(memory_objects, tokens_in_last_completion):
    latest_file = get_latest_chatgpt_memory_file()
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    if latest_file is not None and tokens_in_last_completion < MEMORY_SETTINGS['token_limit']:
        with open(os.path.join(MEMORY_SETTINGS['folder_path'], latest_file), 'w') as f:
            json.dump(memory_objects, f)
    else:
        new_file_name = MEMORY_SETTINGS['file_prefix'] + now + MEMORY_SETTINGS['file_extension']
        with open(os.path.join(MEMORY_SETTINGS['folder_path'], new_file_name), 'w') as f:
            json.dump(memory_objects, f)

def notify_if_chatgpt_memory_exceeds_token_limit(tokens_in_last_completion):
    if tokens_in_last_completion >= MEMORY_SETTINGS['token_limit']:
        alert_message = f"ALERT: Chat memory exceeds token limit (tokens: {tokens_in_last_completion} >= {MEMORY_SETTINGS['token_limit']})\n"
        alert_message += "       Creating new chat memory file."
        colored_alert_message = format_colored_text(alert_message, ALERT_ANSI_COLOR)
        print(colored_alert_message)

def append_completion_to_log_file(completion):
    log_file_path = os.path.join(LOG_SETTINGS['dir'], 'completions.json')

    if not os.path.exists(LOG_SETTINGS['dir']):
        os.makedirs(LOG_SETTINGS['dir'])

    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w') as log_file:
            log_file.write('[\n')

    # remove last character (']')
    with open(log_file_path, 'rb+') as log_file:
        log_file.seek(-1, os.SEEK_END)
        log_file.truncate()

        # If not an empty array, add a comma
        if os.stat(log_file_path).st_size > 2:
            log_file.write(b',\n')

        # Append completion, then add a closing bracket
        log_file.write(json.dumps(completion).encode() + b'\n]')

def get_openai_chatgpt_completion(messages):
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )

    if LOG_SETTINGS['is_logging']:
        append_completion_to_log_file(completion)

    return completion

def format_colored_text(text, color_code):
    ANSI_COLOR_RESET = "\033[0m"
    if TERM_SUPPORTS_COLOR:
        return f'\033[{color_code}m{text}{ANSI_COLOR_RESET}'
    else:
        return text

def loop(task):
    memory_objects = load_chatgpt_memory()
    memory_objects.append({"role": "user", "content": task})

    messages=[
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    messages.extend(memory_objects)

    completion = get_openai_chatgpt_completion(messages)
    response = completion.choices[0].message.content
    tokens_in_last_completion = completion.usage['total_tokens']

    memory_objects.append({"role": "assistant", "content": response})

    notify_if_chatgpt_memory_exceeds_token_limit(tokens_in_last_completion)

    save_chatgpt_memory(memory_objects, tokens_in_last_completion)

    print(format_colored_text(response, CHATGPT_RESPONSE_ANSI_COLOR) + '\n')

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

if __name__ == '__main__':
    loop(task)