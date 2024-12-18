import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class GeminiAPI:
    def __init__(self):
        # Configure the API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No GEMINI_API_KEY found in environment variables.")
        genai.configure(api_key=api_key)
        self.available_models = self._list_available_models()

    def _list_available_models(self) -> List[str]:
        """
        Lists available models from Gemini API.

        Returns:
            List[str]: A list of available model names.
        """
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]


    def list_models(self) -> List[str]:
        """
        Lists available models for Gemini API.

        Returns:
            List[str]: A list of available model names.
        """
        return self.available_models

    def generate_response(self, prompt: str, model_name: str) -> str:
        """
        Generates a response using the specified Gemini model.

        Args:
            prompt (str): The input prompt.
            model_name (str): The name of the model to use.

        Returns:
            str: The generated response from Gemini.
        """
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {e}"
