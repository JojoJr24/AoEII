from abc import ABC, abstractmethod
from typing import List, Dict

class LLMInterface(ABC):
    @abstractmethod
    def list_models(self) -> List[str]:
        """
        Abstract method to list available models for the provider.

        Returns:
            List[str]: A list of available model names.
        """
        pass

    @abstractmethod
    def generate_response(self, prompt: str, model_name: str) -> str:
        """
        Abstract method to generate a response from a language model.

        Args:
            prompt (str): The input prompt.
            model_name (str): The name of the model to use.

        Returns:
            str: The generated response.
        """
        pass
