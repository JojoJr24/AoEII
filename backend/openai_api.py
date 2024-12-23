import os
from dotenv import load_dotenv
from typing import List, Optional, Generator
from PIL import Image
from openai import OpenAI

load_dotenv()

class OpenAIAPI:
    def __init__(self):
        # Configure the API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OPENAI_API_KEY found in environment variables.")
        self.client = OpenAI(api_key=api_key)
        self.available_models = self._list_available_models()

    def _list_available_models(self) -> List[str]:
        """
        Lists available models from OpenAI API.

        Returns:
            List[str]: A list of available model names.
        """
        try:
            models = self.client.models.list()
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
                # Resize the image to 512x512
                image = image.resize((512, 512))

                # Save the image to a temporary file
                temp_image_path = "temp_image.jpg"
                image.save(temp_image_path, format="JPEG")

                # Upload the image file to OpenAI
                with open(temp_image_path, "rb") as image_file:
                    uploaded_file = self.client.files.create(file=image_file, purpose='vision')

                # Reference the uploaded image in the message
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_file", "image_file": {"file_id": uploaded_file.id}}
                    ]
                })

                # Clean up the temporary file
                os.remove(temp_image_path)
            else:
                messages.append({"role": "user", "content": prompt})

            response_stream = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
            )
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta:
                    content = getattr(chunk.choices[0].delta, 'content', None)
                    if content:
                        yield content

        except Exception as e:
            yield f"Error generating response: {e}"


