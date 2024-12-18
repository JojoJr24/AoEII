import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiAPI:
    def __init__(self):
        # Configure the API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("No GOOGLE_API_KEY found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_response(self, prompt: str) -> str:
        """
        Generates a response using the Gemini Pro model.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: The generated response from Gemini.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {e}"
