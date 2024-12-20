import anthropic
import os
from dotenv import load_dotenv
from typing import List, Optional, Generator
from PIL import Image
import io

load_dotenv()

class ClaudeAPI:
    def __init__(self):
        """Initialize the Claude API client with API key from environment variables."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No ANTHROPIC_API_KEY found in environment variables.")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.available_models = self._list_available_models()
    
    def _list_available_models(self) -> List[str]:
        """
        Private method to fetch available models from Anthropic API.
        
        Returns:
            List[str]: List of available model names
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            print(f"Error listing Anthropic models: {e}")
            return []
    
    def list_models(self) -> List[str]:
        """
        Public method to get available models.
        
        Returns:
            List[str]: List of available model names
        """
        return self.available_models
    
    def generate_response(
        self,
        prompt: str,
        model_name: str,
        image: Optional[Image.Image] = None,
        history: Optional[List[dict]] = None,
        system_message: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response using the specified Anthropic model.
        
        Args:
            prompt (str): The input prompt
            model_name (str): Name of the model to use
            image (Optional[Image.Image]): Optional image to include
            history (Optional[List[dict]]): Optional chat history
            system_message (Optional[str]): Optional system message
        
        Yields:
            str: Generated response chunks
        """
        try:
            messages = []
            
            # Add chat history if provided
            if history:
                for message in history:
                    role = "assistant" if message["role"] == "model" else message["role"]
                    messages.append({
                        "role": role,
                        "content": message["content"]
                    })
            
            # Prepare the user message with optional image
            user_message = {"role": "user", "content": prompt}
            
            if image:
                # Convert PIL Image to bytes
                image_bytes = io.BytesIO()
                image.save(image_bytes, format=image.format or "PNG")
                user_message["images"] = [{"type": "image", "data": image_bytes.getvalue()}]
            
            messages.append(user_message)
            
            # Create streaming response with system message as a separate parameter
            kwargs = {
                "model": model_name,
                "messages": messages,
                "max_tokens": 4096,
                "stream": True
            }
            
            # Add system message if provided
            if system_message:
                kwargs["system"] = system_message
            
            response_stream = self.client.messages.create(**kwargs)
            
            # Yield response chunks
            for chunk in response_stream:
                if chunk.content:
                    yield chunk.content[0].text
                    
        except Exception as e:
            yield f"Error generating response: {e}"