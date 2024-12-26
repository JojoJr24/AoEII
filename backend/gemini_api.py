import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import List, Optional, Generator
from PIL import Image
import io
import json
import base64
from utils import retry_with_exponential_backoff, STREAM_START_DELAY, STREAM_YIELD_DELAY

load_dotenv()

class GeminiAPI:
    def __init__(self):
        # Configure the API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No GEMINI_API_KEY found in environment variables.")
        genai.configure(api_key=api_key)
        self.available_models = self._list_available_models()

    @retry_with_exponential_backoff()
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

    @retry_with_exponential_backoff()
    def generate_response(self, prompt: str, model_name: str, image: Optional[Image.Image] = None, history: Optional[List[dict]] = None, system_message: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generates a response using the specified Gemini model, yielding chunks of the response.

        Args:
            prompt (str): The input prompt.
            model_name (str): The name of the model to use.
            image (Optional[Image.Image]): An optional image to include in the prompt.
            history (Optional[List[dict]]): An optional list of previous chat messages.
            system_message (Optional[str]): An optional system message to include in the prompt.

        Yields:
            str: The generated response chunks from Gemini.
        """
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_message)
           
            contents = []
            if history:
                for message in history:
                    if message["role"] == "model":
                        contents.append({"role": "user", "parts": [message["content"]]})
                    elif message["role"] == "user":
                        contents.append({"role": "user", "parts": [message["content"]]})
                    else:
                        contents.append({"role": message["role"], "parts": [message["content"]]})

            
            parts = []
            if prompt:
                parts.append(prompt)
            if image:
                image_part = {
                    "mime_type": f'image/{image.format.lower() if image.format else "png"}',
                    "data": base64.b64encode(image.tobytes()).decode('utf-8')
                }
                parts.append(image_part)
            
            if parts:
                contents.append({"role": "user", "parts": parts})
            
            if not contents:
                contents.append({"role": "user", "parts": [""]})
                                        
            response_stream = model.generate_content(
                contents=contents,
                stream=True,
            )
            time.sleep(STREAM_START_DELAY)
            for chunk in response_stream:
                yield chunk.text
                time.sleep(STREAM_YIELD_DELAY)
        except Exception as e:
            yield f"Error generating response: {e}"
