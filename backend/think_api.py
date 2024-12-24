import sys
import json
from typing import Generator
from PIL import Image
import io
import importlib.util
import os

def think(prompt: str, model_name: str = "llama2") -> Generator[str, None, None]:
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
    
    # Importar el módulo think.py
    think_dir = '../think'
    think_file = 'think.py'
    think_path = os.path.join(think_dir, think_file)
    spec = importlib.util.spec_from_file_location("think", think_path)
    think_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(think_module)
    
    ollama_api = think_module.OllamaAPI()

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

    yield respuesta_final
