import curses
import json
import time
from typing import List, Dict, Any
import requests
import json
import argparse
from voice_input import record_and_transcribe

# Constants
API_BASE_URL = "http://127.0.0.1:5000/api"
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-1.5-flash"
MAX_HISTORY_LENGTH = 10
MAX_MESSAGE_LENGTH = 1000
MAX_CONVERSATION_TITLE_LENGTH = 30
CONFIG_FILE = "config.json"

class ConsoleApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.clear()
        self.stdscr.refresh()
        curses.curs_set(0)
        self.height, self.width = stdscr.getmaxyx()
        self.chat_history = []
        self.current_input = ""
        self.selected_provider = DEFAULT_PROVIDER
        self.selected_model = DEFAULT_MODEL
        self.available_models = []
        self.conversations = []
        self.selected_conversation_id = None
        self.system_messages = []
        self.selected_system_message_id = None
        self.modes = []
        self.selected_modes = []
        self.think_mode = False
        self.think_depth = 0
        self.openai_base_url = None
        self.first_message = True
        self.conversation_title = None
        self.tokens_per_second = ""
        self.last_response = None
        self.previous_responses = []
        self.response_start_time = None
        self.streaming = False
        self.menu_active = False
        self.voice_input_active = False
        self.load_data()
        self.load_config()

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.selected_provider = config.get("selected_provider", DEFAULT_PROVIDER)
                self.selected_model = config.get("selected_model", DEFAULT_MODEL)
                self.selected_conversation_id = config.get("selected_conversation_id")
                self.selected_system_message_id = config.get("selected_system_message_id")
                self.selected_modes = config.get("selected_modes", [])
                self.think_mode = config.get("think_mode", False)
                self.think_depth = config.get("think_depth", 0)
                self.openai_base_url = config.get("openai_base_url")
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            self.add_message("Error loading config file", is_user=False)

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Console application with voice input option.")
        parser.add_argument("--listen", action="store_true", help="Enable voice input by default.")
        args = parser.parse_args()
        if args.listen:
            self.voice_input_active = True

    def save_config(self):
        config = {
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "selected_conversation_id": self.selected_conversation_id,
            "selected_system_message_id": self.selected_system_message_id,
            "selected_modes": self.selected_modes,
            "think_mode": self.think_mode,
            "think_depth": self.think_depth,
            "openai_base_url": self.openai_base_url
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.add_message(f"Error saving config: {e}", is_user=False)

    def load_data(self):
        self.fetch_models()
        self.fetch_conversations()
        self.fetch_system_messages()
        self.fetch_modes()

    def fetch_models(self):
        try:
            response = requests.get(f"{API_BASE_URL}/models?provider={self.selected_provider}")
            response.raise_for_status()
            self.available_models = response.json()
            if self.available_models:
                self.selected_model = self.available_models[0]
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error fetching models: {e}", is_user=False)

    def fetch_conversations(self):
        try:
            response = requests.get(f"{API_BASE_URL}/conversations")
            response.raise_for_status()
            self.conversations = response.json()
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error fetching conversations: {e}", is_user=False)

    def fetch_system_messages(self):
        try:
            response = requests.get(f"{API_BASE_URL}/system_messages")
            response.raise_for_status()
            self.system_messages = response.json()
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error fetching system messages: {e}", is_user=False)

    def fetch_modes(self):
        try:
            response = requests.get(f"{API_BASE_URL}/tool_modes")
            response.raise_for_status()
            self.modes = response.json()
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error fetching modes: {e}", is_user=False)

    def add_message(self, message, is_user=True):
        self.chat_history.append({"role": "user" if is_user else "llm", "content": message})
        if len(self.chat_history) > MAX_HISTORY_LENGTH:
            self.chat_history.pop(0)

    def display_chat(self):
        chat_height = self.height - 5
        start_y = max(0, len(self.chat_history) - chat_height)
        for i, message in enumerate(self.chat_history[start_y:]):
            y = i + 1
            prefix = "User: " if message["role"] == "user" else "LLM:  "
            content = message["content"]
            lines = self.wrap_text(prefix + content, self.width - 2)
            for line in lines:
                self.stdscr.addstr(y, 1, line)
                y += 1
        self.stdscr.addstr(chat_height + 1, 1, f"Tokens/sec: {self.tokens_per_second}")
        self.stdscr.refresh()

    def wrap_text(self, text, width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) + 1 <= width:
                current_line += (word + " ")
            else:
                lines.append(current_line.rstrip())
                current_line = word + " "
        lines.append(current_line.rstrip())
        return lines

    def display_input_area(self):
        input_y = self.height - 3
        self.stdscr.addstr(input_y, 1, "Input: " + self.current_input)
        self.stdscr.addstr(self.height - 2, 1, " " * (self.width - 2))
        self.stdscr.addstr(self.height - 2, 1, f"Provider: {self.selected_provider}, Model: {self.selected_model}")
        self.stdscr.refresh()

    def display_menu(self, menu_selection=""):
        menu_y = 1
        menu_x = self.width - 20
        self.menu_items = [
            "Provider",
            "Model",
            "Conversations",
            "System Message",
            "Modes",
            "Think Mode",
            "Think Depth",
            "Reset",
            "Stop"
        ]
        self.selected_menu_item = 0
        if self.menu_active:
            self.stdscr.addstr(menu_y, menu_x, "Menu:")
            menu_y += 1
            for i, item in enumerate(self.menu_items):
                self.stdscr.addstr(menu_y + i, menu_x, f"  {i + 1}. {item}")
            if menu_selection:
                self.stdscr.addstr(menu_y + len(self.menu_items) + 1, menu_x, f"Selected: {menu_selection}")
        self.stdscr.refresh()

    def handle_menu_selection(self, menu_selection):
        try:
            key = int(menu_selection)
        except ValueError:
            return
        if key == 1:
            self.select_provider()
        elif key == 2:
            self.select_model()
        elif key == 3:
            self.select_conversation()
        elif key == 4:
            self.select_system_message()
        elif key == 5:
            self.select_modes()
        elif key == 6:
            self.toggle_think_mode()
        elif key == 7:
            self.select_think_depth()
        elif key == 8:
            self.reset_chat()
        elif key == 9:
            self.stop_stream()

    def select_provider(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Provider:")
        providers = ["gemini", "ollama", "openai", "claude", "groq"]
        for i, provider in enumerate(providers):
            self.stdscr.addstr(i + 2, 3, f"{i + 1}. {provider}")
        self.stdscr.refresh()
        selection = ""
        while True:
            key = self.stdscr.getch()
            if key == 10:
                try:
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(providers):
                        self.selected_provider = providers[selected_index]
                        self.fetch_models()
                        self.stdscr.clear()
                        self.save_config()
                        break
                except ValueError:
                    pass
                selection = ""
            elif key == 27:
                self.stdscr.clear()
                break
            elif 48 <= key <= 57:
                selection += chr(key)
                self.stdscr.addstr(len(providers) + 3, 3, f"Selected: {selection}")
                self.stdscr.refresh()

    def select_model(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Model:")
        for i, model in enumerate(self.available_models):
            self.stdscr.addstr(i + 2, 3, f"{i + 1}. {model}")
        self.stdscr.refresh()
        selection = ""
        while True:
            key = self.stdscr.getch()
            if key == 10:
                try:
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(self.available_models):
                        self.selected_model = self.available_models[selected_index]
                        self.stdscr.clear()
                        self.save_config()
                        break
                except ValueError:
                    pass
                selection = ""
            elif key == 27:
                self.stdscr.clear()
                break
            elif 48 <= key <= 57:
                selection += chr(key)
                self.stdscr.addstr(len(self.available_models) + 3, 3, f"Selected: {selection}")
                self.stdscr.refresh()

    def select_conversation(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Conversation:")
        for i, conversation in enumerate(self.conversations):
            title = conversation.get('title', f"Conversation {conversation['id']}")
            self.stdscr.addstr(i + 2, 3, f"{i + 1}. {title}")
        self.stdscr.refresh()
        selection = ""
        while True:
            key = self.stdscr.getch()
            if key == 10:
                try:
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(self.conversations):
                        self.selected_conversation_id = self.conversations[selected_index]['id']
                        self.load_conversation(self.selected_conversation_id)
                        self.stdscr.clear()
                        self.save_config()
                        break
                except ValueError:
                    pass
                selection = ""
            elif key == 27:
                self.stdscr.clear()
                break
            elif 48 <= key <= 57:
                selection += chr(key)
                self.stdscr.addstr(len(self.conversations) + 3, 3, f"Selected: {selection}")
                self.stdscr.refresh()

    def load_conversation(self, conversation_id):
        try:
            response = requests.get(f"{API_BASE_URL}/conversations/{conversation_id}")
            response.raise_for_status()
            data = response.json()
            self.chat_history = []
            if data and data.get('messages'):
                for message in data['messages']:
                    self.add_message(message['content'], message['role'] == 'user')
            if data and data.get('conversation') and data['conversation'].get('title'):
                self.conversation_title = data['conversation']['title']
            else:
                self.conversation_title = f"Conversation {conversation_id}"
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error loading conversation: {e}", is_user=False)

    def select_system_message(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select System Message:")
        for i, message in enumerate(self.system_messages):
            self.stdscr.addstr(i + 2, 3, f"{i + 1}. {message['name']}")
        self.stdscr.refresh()
        selection = ""
        while True:
            key = self.stdscr.getch()
            if key == 10:
                try:
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(self.system_messages):
                        self.selected_system_message_id = self.system_messages[selected_index]['id']
                        self.stdscr.clear()
                        self.save_config()
                        break
                except ValueError:
                    pass
                selection = ""
            elif key == 27:
                self.stdscr.clear()
                break
            elif 48 <= key <= 57:
                selection += chr(key)
                self.stdscr.addstr(len(self.system_messages) + 3, 3, f"Selected: {selection}")
                self.stdscr.refresh()

    def select_modes(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Modes (Space to toggle, Enter to confirm):")
        for i, mode in enumerate(self.modes):
            prefix = "[x] " if mode in self.selected_modes else "[ ] "
            self.stdscr.addstr(i + 2, 3, f"{prefix}{mode}")
        self.stdscr.refresh()
        current_selection = 0
        while True:
            key = self.stdscr.getch()
            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(self.modes) - 1:
                current_selection += 1
            elif key == ord(' '):
                mode_name = self.modes[current_selection]
                if mode_name in self.selected_modes:
                    self.selected_modes.remove(mode_name)
                else:
                    self.selected_modes.append(mode_name)
            elif key == 10:
                self.stdscr.clear()
                self.save_config()
                break
            elif key == 27:
                self.stdscr.clear()
                break
            self.stdscr.clear()
            self.stdscr.addstr(1, 1, "Select Modes (Space to toggle, Enter to confirm):")
            for i, mode in enumerate(self.modes):
                prefix = "[x] " if mode in self.selected_modes else "[ ] "
                if i == current_selection:
                    self.stdscr.addstr(i + 2, 3, f"> {prefix}{mode}", curses.A_REVERSE)
                else:
                    self.stdscr.addstr(i + 2, 3, f"  {prefix}{mode}")
            self.stdscr.refresh()

    def toggle_think_mode(self):
        self.think_mode = not self.think_mode
        self.stdscr.clear()
        self.save_config()

    def select_think_depth(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Think Depth (0 for auto):")
        for i in range(11):
            self.stdscr.addstr(i + 2, 3, f"{i}. {i}")
        self.stdscr.refresh()
        selection = ""
        while True:
            key = self.stdscr.getch()
            if key == 10:
                try:
                    self.think_depth = int(selection)
                    self.stdscr.clear()
                    self.save_config()
                    break
                except ValueError:
                    pass
                selection = ""
            elif key == 27:
                self.stdscr.clear()
                break
            elif 48 <= key <= 57:
                selection += chr(key)
                self.stdscr.addstr(13, 3, f"Selected: {selection}")
                self.stdscr.refresh()

    def reset_chat(self):
        self.chat_history = []
        self.selected_conversation_id = None
        self.first_message = True
        self.previous_responses = []
        self.stdscr.clear()

    def stop_stream(self):
        try:
            requests.post(f"{API_BASE_URL}/stop")
            self.streaming = False
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error stopping stream: {e}", is_user=False)

    def send_message(self):
        if not self.current_input.strip():
            return
        message = self.current_input
        self.add_message(message)
        self.current_input = ""
        
        transformed_history = []
        for item in self.chat_history:
            if item['role'] == 'user':
                transformed_history.append({'role': 'user', 'content': item['content']})
            elif item['role'] == 'llm':
                transformed_history.append({'role': 'model', 'content': item['content']})
        
        data = {
            'prompt': message,
            'model': self.selected_model,
            'provider': self.selected_provider,
            'history': json.dumps(transformed_history),
            'selected_modes': json.dumps(self.selected_modes),
            'think': self.think_mode,
            'think_depth': self.think_depth,
        }
        if self.selected_system_message_id:
            system_message = next((msg['content'] for msg in self.system_messages if msg['id'] == self.selected_system_message_id), None)
            if system_message:
                data['system_message'] = system_message
        if self.selected_conversation_id:
            data['conversation_id'] = self.selected_conversation_id
        if self.openai_base_url:
            data['base_url'] = self.openai_base_url
            data['model'] = ''
        if self.first_message:
            self.conversation_title = message
            data['conversation_title'] = self.conversation_title
        
        api_url = f"{API_BASE_URL}/generate"
        if self.think_mode:
            api_url = f"{API_BASE_URL}/think"
        
        self.streaming = True
        try:
            self.response_start_time = time.time()
            with requests.post(api_url, data=data, stream=True) as response:
                response.raise_for_status()
                partial_response = ""
                for line in response.iter_lines():
                    if not self.streaming:
                        break
                    if line:
                        try:
                            json_line = json.loads(line.decode('utf-8').strip())
                            partial_response += json_line.get('response', '')
                        except json.JSONDecodeError:
                            self.add_message(f"Error decoding response: {line}", is_user=False)
                self.last_response = partial_response
                self.add_message(partial_response, is_user=False)
                elapsed_time = time.time() - self.response_start_time
                tokens = len(partial_response.split())
                self.tokens_per_second = f"{tokens / elapsed_time:.2f}" if elapsed_time > 0 else "0.00"
                self.previous_responses.append({
                    'prompt': message,
                    'response': partial_response,
                    'conversationId': self.selected_conversation_id,
                    'model': self.selected_model,
                    'provider': self.selected_provider,
                    'systemMessage': data.get('system_message'),
                    'modes': self.select_modes
                })
                if self.first_message:
                    self.first_message = False
                    self.fetch_conversations()
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error sending message: {e}", is_user=False)
        self.streaming = False

    def handle_input(self, key):
        if key == 10:  # Enter key
            self.send_message()
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
            self.current_input = self.current_input[:-1]
        elif 32 <= key <= 126:  # Printable characters
            if len(self.current_input) < MAX_MESSAGE_LENGTH:
                self.current_input += chr(key)
        elif key == 27:
            self.stdscr.clear()
            self.menu_active = False
            return False
        elif key == curses.KEY_F2 or self.voice_input_active:  # F2 for voice input
            transcription = record_and_transcribe(self.stdscr)
            if transcription and transcription != "Error during recording":
                self.current_input = transcription
            self.voice_input_active = False
        return True

    def run(self):
        self.parse_arguments()
        while True:
            self.stdscr.clear()
            self.display_chat()
            self.display_input_area()
            self.display_menu()
            self.stdscr.addstr(self.height - 4, 1, "F2: Voice Input")
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == curses.KEY_IC:
                self.menu_active = True
                self.stdscr.clear()
                self.display_menu()
                menu_selection = ""
                while True:
                    key = self.stdscr.getch()
                    if key == 10:
                        self.stdscr.clear()
                        self.handle_menu_selection(menu_selection)
                        self.menu_active = False
                        break
                    elif key == 27:
                        self.stdscr.clear()
                        self.menu_active = False
                        break
                    elif 48 <= key <= 57:
                        menu_selection += chr(key)
                        self.display_menu(menu_selection)
            elif not self.handle_input(key):
                break

def main(stdscr):
    app = ConsoleApp(stdscr)
    app.run()

if __name__ == '__main__':
    curses.wrapper(main)
