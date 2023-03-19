import os
import json
import datetime

class ChatGPTMemory(list):
    folder_path = 'memory'
    file_prefix = 'chatgpt-memory_'
    file_extension = '.json'
    token_limit = 3500

    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
    
    def _set(self, value):
        self.clear()
        self.extend(value)

    def get_file_prefix_with_model_name(self):
        return self.file_prefix + self.model_name + '_'

    def is_valid_memory_file(self, file_name):
        is_file = os.path.isfile(
            os.path.join(self.folder_path, file_name)
        )
        return (
            is_file
            and file_name.startswith(self.get_file_prefix_with_model_name()) 
            and file_name.endswith(self.file_extension)
        )

    def is_over_token_limit(self, tokens_in_last_completion):
        return tokens_in_last_completion >= self.token_limit

    def get_latest_memory_file(self):
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        memory_files = [f for f in os.listdir(self.folder_path) if self.is_valid_memory_file(f)]

        if not memory_files:
            return None

        return max(memory_files)

    def load_memory(self):
        latest_file = self.get_latest_memory_file()

        if latest_file is not None:
            with open(os.path.join(self.folder_path, latest_file), 'r') as f:
                memory_objects = json.load(f)
                self.extend(memory_objects)

    def save_memory(self, tokens_in_last_completion):
        latest_file = self.get_latest_memory_file()

        if latest_file is None or tokens_in_last_completion >= self.token_limit:
            last_user_assistant_message_pair = self[-2:]
            self._set(last_user_assistant_message_pair)
            now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            latest_file = self.get_file_prefix_with_model_name() + now + self.file_extension

        with open(os.path.join(self.folder_path, latest_file), 'w') as f:
            json.dump(self, f)