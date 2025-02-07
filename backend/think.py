import ollama
from typing import List, Optional, Generator
from PIL import Image
import io
import json
import sys

class Think:
    def __init__(self):
        self.available_models = self._list_available_models()

    def _list_available_models(self) -> List[str]:
        """
        Lista los modelos disponibles en la API de Ollama.

        Returns:
            List[str]: Lista con los nombres de los modelos disponibles.
        """
        try:
            models = ollama.list()
            print(f"Ollama models response: {models}")
            return [model.model for model in models['models']]
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            return []



    def generate_response(
        self,
        prompt: str,
        model_name: str,
        image: Optional[Image.Image] = None,
        history: Optional[List[dict]] = None,
        system_message: Optional[str] = None,
        depth: int = 1
    ) -> Generator[str, None, None]:
        """
        Genera una respuesta usando el modelo especificado de Ollama, iterando 'depth' veces,
        y devolviendo bloques de texto de manera iterativa.

        Args:
            prompt (str): Prompt de entrada.
            model_name (str): Nombre del modelo de Ollama a utilizar.
            image (Optional[Image.Image]): Imagen opcional que se puede incluir en el prompt.
            history (Optional[List[dict]]): Historial previo de mensajes.
            system_message (Optional[str]): Mensaje del sistema que se puede incluir en el prompt.

        Yields:
            str: Fragmentos de la respuesta generada por Ollama.
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
                # Convertir la imagen PIL a bytes
                image_bytes = io.BytesIO()
                image.save(image_bytes, format=image.format if image.format else "PNG")
                image_bytes = image_bytes.getvalue()
                
                messages.append({"role": "user", "content": prompt, "images": [image_bytes]})
            else:
                messages.append({"role": "user", "content": prompt})

            # Asegurarnos de usar solo el nombre del modelo (separado por :)
            model_name = model_name.split(":")[0]

            final_prompt = prompt  # Inicializar con el prompt original

            for i in range(depth):
                print(f"\n--- Iteración #{i + 1} de {depth} ---")

                if i > 0:
                    final_prompt = f"{prompt}\nWait, I have to think it again..."

                # Limpiar el historial de mensajes antes de cada iteración
                messages = messages[:2] if system_message else []
                messages.append({"role": "user", "content": final_prompt})

                # Hacer la llamada a Ollama
                response_stream = ollama.chat(model=model_name, messages=messages, stream=True)
                for chunk in response_stream:
                    yield chunk['message']['content']

        except Exception as e:
            yield f"Error generating response: {e}"


