from abc import ABC, abstractmethod

class LLMInterface(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Abstract method to generate a response from a language model.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: The generated response.
        """
        pass
