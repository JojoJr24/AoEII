import ollama
from typing import List, Optional, Generator
from PIL import Image
import io
import json
import sys

class OllamaAPI:
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
        system_message: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Genera una respuesta usando el modelo especificado de Ollama, devolviendo
        bloques de texto de manera iterativa.

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
            
            # Hacer la llamada a Ollama
            response_stream = ollama.chat(model=model_name, messages=messages, stream=True)
            for chunk in response_stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"Error generating response: {e}"


def main(prompt: str, model_name: str = "llama2"):
    """
    Programa principal que:
    1) Recibe un prompt como parámetro.
    2) Envía el prompt a Ollama para que devuelva un JSON con la complejidad (dificultad).
    3) Parsea la dificultad del JSON.
    4) Entra en un bucle (loop) de iteraciones proporcional a la dificultad.
       - En cada iteración:
         a) Invoca a Ollama para obtener un "pensamiento" (sin solución).
         b) Invoca a Ollama para resumir los puntos claves del pensamiento.
         c) Suma ese resumen al pensamiento y continúa con la siguiente iteración.
    5) Al finalizar el loop, con el problema original más el resumen final, se obtiene
       la respuesta definitiva de Ollama.
    """

    ollama_api = OllamaAPI()

    # ------------------------------------------------------------------------
    # Paso 2 y 3: Solicitar a Ollama que devuelva SOLO un JSON con la complejidad.
    # ------------------------------------------------------------------------
    system_msg_for_complexity = (
        "Por favor, analiza el siguiente problema y devuelve ÚNICAMENTE un JSON "
        "con el campo 'complejidad' que indique (en un número entero) "
        "cuán difícil es el problema. No incluyas nada más que el JSON."
    )
    
    # Generamos la respuesta del modelo pidiendo solo el JSON con la complejidad
    complexity_response = ""
    for chunk in ollama_api.generate_response(
        prompt=prompt,
        model_name=model_name,
        system_message=system_msg_for_complexity
    ):
        complexity_response += chunk

    # ------------------------------------------------------------------------
    # Paso 4: Parsear la dificultad del JSON.
    # ------------------------------------------------------------------------
    dificultad = 1  # Valor por defecto si no se puede parsear
    try:
        # Se espera algo como: {"complejidad": 5}
        parsed_json = json.loads(complexity_response)
        dificultad = parsed_json.get("complejidad", 1)
    except json.JSONDecodeError as e:
        print("Error al decodificar el JSON de complejidad. Se usará dificultad = 1.")
    
    print(f"Dificultad detectada: {dificultad}")

    # ------------------------------------------------------------------------
    # Paso 5: Entrar en un loop que itera en función de la dificultad.
    # ------------------------------------------------------------------------
    pensamiento_actual = ""
    resumen_acumulado = ""

    for i in range(dificultad):
        print(f"\n--- Iteración de razonamiento #{i+1} ---")

        # ----------------------------------------------------------
        # Paso 6: Invocar a Ollama para que piense sobre el problema,
        #         sin dar la solución, solo el pensamiento.
        # ----------------------------------------------------------
        system_msg_for_thinking = (
            "Eres un experto resolviendo problemas. A continuación se te mostrará "
            "el problema y un resumen acumulado de tus reflexiones previas. "
            "Piensa en voz alta (solo devuélveme el pensamiento), no proporciones la solución. "
            "NO incluyas nada que no sea el contenido de tu pensamiento."
        )
        prompt_for_thinking = (
            f"Problema: {prompt}\n\n"
            f"Resumen previo: {resumen_acumulado}\n\n"
            "Describe tu pensamiento aquí (sin dar solución):"
        )

        pensamiento_response = ""
        for chunk in ollama_api.generate_response(
            prompt=prompt_for_thinking,
            model_name=model_name,
            system_message=system_msg_for_thinking
        ):
            pensamiento_response += chunk

        # ----------------------------------------------------------
        # Paso 7: Invocar a Ollama para que resuma los puntos clave
        #         del pensamiento anterior.
        # ----------------------------------------------------------
        system_msg_for_summary = (
            "Eres un experto en análisis. Se te proporciona un pensamiento anterior. "
            "Devuelve solamente un resumen breve y conciso de los puntos más importantes "
            "de ese pensamiento. No incluyas nada más."
        )
        prompt_for_summary = (
            f"Pensamiento anterior: {pensamiento_response}\n\n"
            "Redacta un resumen breve de los puntos clave:"
        )

        resumen_response = ""
        for chunk in ollama_api.generate_response(
            prompt=prompt_for_summary,
            model_name=model_name,
            system_message=system_msg_for_summary
        ):
            resumen_response += chunk

        # ----------------------------------------------------------
        # Paso 8: Sumar el resumen al pensamiento acumulado y
        #         continuar con la siguiente iteración.
        # ----------------------------------------------------------
        resumen_acumulado += f"\n- {resumen_response.strip()}"

    # ------------------------------------------------------------------------
    # Paso 9: Con el problema más el resumen final de los pensamientos,
    #         invocar a Ollama para que dé la respuesta final.
    # ------------------------------------------------------------------------
    system_msg_for_final = (
        "Ahora eres un experto resolviendo este tipo de problemas. "
        "Con base en el problema original y el resumen final de tu razonamiento, "
        "proporciona la solución final y justifícala brevemente."
    )
    prompt_for_final = (
        f"Problema: {prompt}\n\n"
        f"Resumen final de razonamientos: {resumen_acumulado}\n\n"
        "Dame la respuesta final al problema:"
    )

    respuesta_final = ""
    for chunk in ollama_api.generate_response(
        prompt=prompt_for_final,
        model_name=model_name,
        system_message=system_msg_for_final
    ):
        respuesta_final += chunk

    print("\n=== RESPUESTA FINAL DEL MODELO ===")
    print(respuesta_final)


if __name__ == "__main__":
    """
    Ejecución del script:
        python programa.py "Mi problema" [nombre_modelo_opcional]

    Ejemplo:
        python programa.py "Explica la teoría de la relatividad" "llama2"
    """
    if len(sys.argv) < 2:
        print("Uso: python programa.py \"<prompt>\" [nombre_modelo_opcional]")
        sys.exit(1)

    input_prompt = sys.argv[1]
    
    if len(sys.argv) >= 3:
        model = sys.argv[2]
    else:
        model = "vanilj/Phi-4:latest"

    main(input_prompt, model)
