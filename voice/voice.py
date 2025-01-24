import os
import json
import time
import requests
import threading
from ..console.voice_input import record_and_transcribe, record_and_transcribe_continuous, play_beep
import argparse

# Constants
API_BASE_URL = "http://127.0.0.1:5000/api"
CONFIG_FILE = "config.json"
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-1.5-flash"

class VoiceApp:
    def __init__(self):
        self.selected_provider = DEFAULT_PROVIDER
        self.selected_model = DEFAULT_MODEL
        self.selected_modes = []
        self.think_mode = False
        self.think_depth = 0
        self.openai_base_url = None
        self.prompt = ""
        self.load_config()
        self.parse_arguments()

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Voice application.")
        parser.add_argument("--continuous", action="store_true", help="Enable continuous listening.")
        args = parser.parse_args()
        self.continuous_mode = args.continuous

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.selected_provider = config.get("selected_provider", DEFAULT_PROVIDER)
                self.selected_model = config.get("selected_model", DEFAULT_MODEL)
                self.selected_modes = config.get("selected_modes", [])
                self.think_mode = config.get("think_mode", False)
                self.think_depth = config.get("think_depth", 0)
                self.openai_base_url = config.get("openai_base_url")
        except FileNotFoundError:
            print("Config file not found, using defaults.")
        except json.JSONDecodeError:
            print("Error loading config file, using defaults.")

    def process_command(self, transcription):
        if "activar" in transcription.lower():
            play_beep(frequency=880, duration=0.1)
            self.prompt = transcription.lower().split("activar", 1)[1].strip()
            print(f"Prompt loaded: {self.prompt}")
        elif "ejecutar" in transcription.lower():
            self.send_message()
        else:
            print(f"Command not recognized: {transcription}")

    def send_message(self):
        if not self.prompt.strip():
            print("No prompt to send.")
            return

        data = {
            'prompt': self.prompt,
            'model': self.selected_model,
            'provider': self.selected_provider,
            'selected_modes': json.dumps(self.selected_modes),
            'think': self.think_mode,
            'think_depth': self.think_depth,
        }
        if self.openai_base_url:
            data['base_url'] = self.openai_base_url
            data['model'] = ''

        api_url = f"{API_BASE_URL}/generate"
        if self.think_mode:
            api_url = f"{API_BASE_URL}/think"

        try:
            response = requests.post(api_url, data=data, stream=True)
            response.raise_for_status()
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        json_line = json.loads(line.decode('utf-8').strip())
                        full_response += json_line.get('response', '')
                    except json.JSONDecodeError:
                        print(f"Error decoding response: {line}")
            print(f"Response: {full_response}")
            self.prompt = ""
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")

    def run(self):
        print("Voice interface started. Say 'activar <prompt>' to set a prompt, and 'ejecutar' to send it.")
        if self.continuous_mode:
            for transcription in record_and_transcribe_continuous():
                if transcription != "Error during recording":
                    self.process_command(transcription)
        else:
            while True:
                transcription = record_and_transcribe()
                if transcription != "Error during recording":
                    self.process_command(transcription)

if __name__ == "__main__":
    app = VoiceApp()
    app.run()
