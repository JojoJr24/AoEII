import ollama
from typing import List, Optional, Generator
from PIL import Image
import io
import json

class OllamaAPI:
    def __init__(self):
        self.available_models = self._list_available_models()

    def _list_available_models(self) -> List[str]:
        """
        Lists available models from Ollama API.

        Returns:
            List[str]: A list of available model names.
        """
        models = ollama.list()
        print(f"Ollama models response: {models}")
        return [model.model for model in models['models']]


    def list_models(self) -> List[str]:
        """
        Lists available models for Ollama API.

        Returns:
            List[str]: A list of available model names.
        """
        return self.available_models

    def generate_response(self, prompt: str, model_name: str, image: Optional[Image.Image] = None, history: Optional[List[dict]] = None) -> Generator[str, None, None]:
        """
        Generates a response using the specified Ollama model, yielding chunks of the response.

        Args:
            prompt (str): The input prompt.
            model_name (str): The name of the model to use.
            image (Optional[Image.Image]): An optional image to include in the prompt.
            history (Optional[List[dict]]): An optional list of previous chat messages.

        Yields:
            str: The generated response chunks from Ollama.
        """
        try:
            messages = []
            if history:
                messages.extend(history)
            
            if image:
                # Convert PIL Image to bytes
                image_bytes = io.BytesIO()
                image.save(image_bytes, format=image.format if image.format else "PNG")
                image_bytes = image_bytes.getvalue()
                
                messages.append({"role": "user", "content": prompt, "images": [image_bytes]})
            else:
                messages.append({"role": "user", "content": prompt})
            
            # Extract just the model name
            print(f"Model name before extraction: {model_name}")
            model_name = model_name.split(":")[-1] if ":" in model_name else model_name
            print(f"Model name after extraction: {model_name}")
            response_stream = ollama.chat(model=model_name, messages=messages, stream=True)
            for chunk in response_stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"Error generating response: {e}"
