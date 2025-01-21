import curses
import json
import os
import time
import uuid
from typing import List, Dict, Any
import requests

# Constants
API_BASE_URL = "http://127.0.0.1:5000/api"
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-1.5-flash"
MAX_HISTORY_LENGTH = 10
MAX_MESSAGE_LENGTH = 1000
MAX_CONVERSATION_TITLE_LENGTH = 30

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
        self.tools = []
        self.selected_tools = []
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
        self.load_data()

    def load_data(self):
        self.fetch_models()
        self.fetch_conversations()
        self.fetch_system_messages()
        self.fetch_tools()

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

    def fetch_tools(self):
        try:
            response = requests.get(f"{API_BASE_URL}/tools")
            response.raise_for_status()
            self.tools = response.json()
        except requests.exceptions.RequestException as e:
            self.add_message(f"Error fetching tools: {e}", is_user=False)

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

    def display_menu(self):
        menu_y = 1
        menu_x = self.width - 20
        self.menu_items = [
            "Provider",
            "Model",
            "Conversations",
            "System Message",
            "Tools",
            "Think Mode",
            "Think Depth",
            "Reset",
            "Stop"
        ]
        self.selected_menu_item = 0
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
            self.select_tools()
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
        while True:
            key = self.stdscr.getch()
            if 49 <= key <= 49 + len(providers) - 1:
                self.selected_provider = providers[key - 49]
                self.fetch_models()
                self.stdscr.clear()
                break
            elif key == 27:
                self.stdscr.clear()
                break

    def select_model(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Model:")
        for i, model in enumerate(self.available_models):
            self.stdscr.addstr(i + 2, 3, f"{i + 1}. {model}")
        self.stdscr.refresh()
        while True:
            key = self.stdscr.getch()
            if 49 <= key <= 49 + len(self.available_models) - 1:
                self.selected_model = self.available_models[key - 49]
                self.stdscr.clear()
                break
            elif key == 27:
                self.stdscr.clear()
                break

    def select_conversation(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Conversation:")
        for i, conversation in enumerate(self.conversations):
            title = conversation.get('title', f"Conversation {conversation['id']}")
            self.stdscr.addstr(i + 2, 3, f"{i + 1}. {title}")
        self.stdscr.refresh()
        while True:
            key = self.stdscr.getch()
            if 49 <= key <= 49 + len(self.conversations) - 1:
                self.selected_conversation_id = self.conversations[key - 49]['id']
                self.load_conversation(self.selected_conversation_id)
                self.stdscr.clear()
                break
            elif key == 27:
                self.stdscr.clear()
                break

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
        while True:
            key = self.stdscr.getch()
            if 49 <= key <= 49 + len(self.system_messages) - 1:
                self.selected_system_message_id = self.system_messages[key - 49]['id']
                self.stdscr.clear()
                break
            elif key == 27:
                self.stdscr.clear()
                break

    def select_tools(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Tools (Space to toggle, Enter to confirm):")
        for i, tool in enumerate(self.tools):
            prefix = "[x] " if tool['name'] in self.selected_tools else "[ ] "
            self.stdscr.addstr(i + 2, 3, f"{prefix}{tool['name']}")
        self.stdscr.refresh()
        current_selection = 0
        while True:
            key = self.stdscr.getch()
            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(self.tools) - 1:
                current_selection += 1
            elif key == ord(' '):
                tool_name = self.tools[current_selection]['name']
                if tool_name in self.selected_tools:
                    self.selected_tools.remove(tool_name)
                else:
                    self.selected_tools.append(tool_name)
            elif key == 10:
                self.stdscr.clear()
                break
            elif key == 27:
                self.stdscr.clear()
                break
            self.stdscr.clear()
            self.stdscr.addstr(1, 1, "Select Tools (Space to toggle, Enter to confirm):")
            for i, tool in enumerate(self.tools):
                prefix = "[x] " if tool['name'] in self.selected_tools else "[ ] "
                if i == current_selection:
                    self.stdscr.addstr(i + 2, 3, f"> {prefix}{tool['name']}", curses.A_REVERSE)
                else:
                    self.stdscr.addstr(i + 2, 3, f"  {prefix}{tool['name']}")
            self.stdscr.refresh()

    def toggle_think_mode(self):
        self.think_mode = not self.think_mode
        self.stdscr.clear()

    def select_think_depth(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Select Think Depth (0 for auto):")
        for i in range(11):
            self.stdscr.addstr(i + 2, 3, f"{i}. {i}")
        self.stdscr.refresh()
        while True:
            key = self.stdscr.getch()
            if 48 <= key <= 57:
                self.think_depth = key - 48
                self.stdscr.clear()
                break
            elif key == 27:
                self.stdscr.clear()
                break

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
        
        data = {
            'prompt': message,
            'model': self.selected_model,
            'provider': self.selected_provider,
            'history': json.dumps(self.chat_history),
            'selected_tools': json.dumps(self.selected_tools),
            'think': self.think_mode,
            'think_depth': self.think_depth
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
                    'tools': self.selected_tools
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
            return False
        return True

    def run(self):
        while True:
            self.stdscr.clear()
            self.display_chat()
            self.display_input_area()
            self.display_menu()
            key = self.stdscr.getch()
            if key == curses.KEY_IC:
                self.stdscr.clear()
                self.display_menu()
                menu_selection = ""
                while True:
                    key = self.stdscr.getch()
                    if key == 10:
                        self.stdscr.clear()
                        self.handle_menu_selection(menu_selection)
                        break
                    elif key == 27:
                        self.stdscr.clear()
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
