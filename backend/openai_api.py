import openai
import os
from dotenv import load_dotenv
from typing import List, Optional, Generator
from PIL import Image
import io
import json

load_dotenv()

class OpenAIAPI:
    def __init__(self):
        # Configure the API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OPENAI_API_KEY found in environment variables.")
        openai.api_key = api_key
        self.available_models = self._list_available_models()

    def _list_available_models(self) -> List[str]:
        """
        Lists available models from OpenAI API.

        Returns:
            List[str]: A list of available model names.
        """
        try:
            models = openai.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            print(f"Error listing OpenAI models: {e}")
            return []

    def list_models(self) -> List[str]:
        """
        Lists available models for OpenAI API.

        Returns:
            List[str]: A list of available model names.
        """
        return self.available_models

    def generate_response(self, prompt: str, model_name: str, image: Optional[Image.Image] = None, history: Optional[List[dict]] = None, system_message: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generates a response using the specified OpenAI model, yielding chunks of the response.

        Args:
            prompt (str): The input prompt.
            model_name (str): The name of the model to use.
            image (Optional[Image.Image]): An optional image to include in the prompt.
            history (Optional[List[dict]]): An optional list of previous chat messages.
            system_message (Optional[str]): An optional system message to include in the prompt.

        Yields:
            str: The generated response chunks from OpenAI.
        """
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            if history:
                for message in history:
                    if message["role"] == "model":
                        messages.append({"role": "assistant", "content": message["content"]})
                    else:
                        messages.append({"role": message["role"], "content": message["content"]})
            
            if image:
                # Convert PIL Image to bytes
                image_bytes = io.BytesIO()
                image.save(image_bytes, format=image.format if image.format else "PNG")
                image_bytes = image_bytes.getvalue()
                
                messages.append({"role": "user", "content": prompt, "images": [image_bytes]})
            else:
                messages.append({"role": "user", "content": prompt})
            
            response_stream = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
            )
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error generating response: {e}"
```

backend/main.py
```python
<<<<<<< SEARCH
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
