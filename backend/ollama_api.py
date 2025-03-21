import time
import ollama
from typing import List, Optional, Generator
from PIL import Image
import io
import json
from utils import retry_with_exponential_backoff, STREAM_START_DELAY, STREAM_YIELD_DELAY

class OllamaAPI:
    def __init__(self):
        self.available_models = self._list_available_models()
        self._current_stream = None

    @retry_with_exponential_backoff()
    def _list_available_models(self) -> List[str]:
        """
        Lists available models from Ollama API.

        Returns:
            List[str]: A list of available model names.
        """
        try:
            models = ollama.list()
            print(f"Ollama models response: {models}")
            return [model.model for model in models['models']]
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            return []


    def list_models(self) -> List[str]:
        """
        Lists available models for Ollama API.

        Returns:
            List[str]: A list of available model names.
        """
        return self.available_models

    def stop_stream(self):
        """Stops the current stream."""
        self._current_stream = None

    @retry_with_exponential_backoff()
    def generate_response(self, prompt: str, model_name: str, image: Optional[Image.Image] = None, history: Optional[List[dict]] = None, system_message: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generates a response using the specified Ollama model, yielding chunks of the response.

        Args:
            prompt (str): The input prompt.
            model_name (str): The name of the model to use.
            image (Optional[Image.Image]): An optional image to include in the prompt.
            history (Optional[List[dict]]): An optional list of previous chat messages.
            system_message (Optional[str]): An optional system message to include in the prompt.

        Yields:
            str: The generated response chunks from Ollama.
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
            
            # Extract just the model name
            self._current_stream = ollama.chat(model=model_name, messages=messages, stream=True, options={"num_ctx": 16834})
            for chunk in self._current_stream:
                if self._current_stream is None:
                    break
                yield chunk['message']['content']
            self._current_stream = None
        except Exception as e:
            yield f"Error generating response: {e}"
