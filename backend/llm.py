from claude_api import ClaudeAPI
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
from openai_api import OpenAIAPI
from groq_api import GroqAPI
from typing import Generator
import importlib.util
import os
import json

from utils import debug_print

# Initialize the Gemini API
gemini_api = GeminiAPI()
debug_print(True, "Gemini API initialized.")

# Initialize the Ollama API
try:
    ollama_api = OllamaAPI()
    debug_print(True, "Ollama API initialized.")
except Exception as e:
    debug_print(True, f"Error initializing Ollama API: {e}")
    ollama_api = None

# Initialize the OpenAI API
try:
    openai_api = OpenAIAPI()
    debug_print(True, "OpenAI API initialized.")
except Exception as e:
    debug_print(True, f"Error initializing OpenAI API: {e}")
    openai_api = None

# Initialize the Claude API
try:
    claude_api = ClaudeAPI()
    debug_print(True, "Claude API initialized.")
except Exception as e:
    debug_print(True, f"Error initializing Claude API: {e}")
    claude_api = None

# Initialize the Groq API
try:
    groq_api = GroqAPI()
    debug_print(True, "Groq API initialized.")
except Exception as e:
    debug_print(True, f"Error initializing Groq API: {e}")
    groq_api = None


def think(prompt: str, depth: int) -> Generator[str, None, None]:
     """
    Programa principal que:
    1) Recibe un prompt como parámetro.
    2) Si la profundidad (depth) es distinta de 0, se usa como dificultad.
    3) Si la profundidad es 0, se envía el prompt a Ollama para que devuelva un JSON con la complejidad (dificultad).
    4) Parsea la dificultad del JSON.
    5) Entra en un bucle (loop) de iteraciones proporcional a la dificultad.
       - En cada iteración:
         a) Invoca a Ollama para obtener un "pensamiento" (sin solución).
         b) Invoca a Ollama para resumir los puntos claves del pensamiento.
         c) Suma ese resumen al pensamiento y continúa con la siguiente iteración.
    6) Al finalizar el loop, con el problema original más el resumen final, se obtiene
       la respuesta definitiva de Ollama.
    """
     global selected_provider, selected_model
     # Importar el módulo think.py
     think_dir = '../think'
     think_file = 'think.py'
     think_path = os.path.join(think_dir, think_file)
     spec = importlib.util.spec_from_file_location("think", think_path)
     think_module = importlib.util.module_from_spec(spec)
     spec.loader.exec_module(think_module)
     
     ollama_api = think_module.OllamaAPI()

     # ------------------------------------------------------------------------
     # Paso 2: Si la profundidad (depth) es distinta de 0, se usa como dificultad.
     # ------------------------------------------------------------------------
     if depth != 0:
         print(f"Profundidad establecida por el usuario: {depth}")
         
     # ------------------------------------------------------------------------
     # Paso 3 y 4: Solicitar a Ollama que devuelva SOLO un JSON con la complejidad.
     # ------------------------------------------------------------------------
     system_msg_for_complexity = (
         "Por favor, analiza el siguiente problema y devuelve ÚNICAMENTE un JSON "
         "con los campos 'complejidad' y 'tipo_problema'. "
         "'complejidad' debe ser un número entero donde 1 es demasiado sencillo y 10 es muy complejo. "
         "'tipo_problema' debe ser un número entero: 1 para problemas que requieren pensarlo en secuencia, "
         "2 para problemas que parece que les falta información por lo que hay que pensar fuera de la caja para hacer explicita información escondida, "
         "y 3 para problemas a los que le falta información por lo que hay que pensar que se le puede agregar para poder encontrar una solución. "
         "No incluyas nada más que el JSON. Ejemplo del JSON: {\"complejidad\": 3, \"tipo_problema\": 1}"
     )
     
     # Generamos la respuesta del modelo pidiendo solo el JSON con la complejidad
     complexity_response = ""
     provider = llm_providers.get(selected_provider)
     if not provider:
         yield "Error: Provider not found"
         return
     for chunk in provider.generate_response(
         prompt=prompt,
         model_name=selected_model,
         system_message=system_msg_for_complexity
     ):
         complexity_response += chunk

     # ------------------------------------------------------------------------
     # Paso 5: Parsear la dificultad y el tipo de problema del JSON.
     # ------------------------------------------------------------------------
     dificultad = depth  # Valor por defecto si no se puede parsear
     tipo_problema = 1 # Valor por defecto si no se puede parsear
     try:
         # Se espera algo como: {"complejidad": 5, "tipo_problema": 1}
         start_index = complexity_response.find('{')
         end_index = complexity_response.rfind('}')
         if start_index != -1 and end_index != -1:
            json_string = complexity_response[start_index:end_index+1]
            parsed_json = json.loads(json_string)
            dificultad = dificultad if dificultad != 0 else parsed_json.get("complejidad", 1)
            tipo_problema = parsed_json.get("tipo_problema", 1)
     except json.JSONDecodeError as e:
         print("Error al decodificar el JSON de complejidad y tipo de problema. Se usará dificultad = 1 y tipo_problema = 1.",complexity_response)
     
     print(f"Dificultad detectada: {dificultad}, Tipo de problema detectado: {tipo_problema}")

     # ------------------------------------------------------------------------
     # Paso 6: Entrar en un loop que itera en función de la dificultad.
     # ------------------------------------------------------------------------
     pensamiento_actual = ""
     resumen_acumulado = ""

     for i in range(dificultad):
         print(f"\n--- Iteración de razonamiento #{i+1} ---")

         # ----------------------------------------------------------
         # Paso 7: Invocar a Ollama para que piense sobre el problema,
         #         sin dar la solución, solo el pensamiento.
         # ----------------------------------------------------------
         if tipo_problema == 1:
            system_msg_for_thinking = (
                "Eres un experto resolviendo problemas. A continuación se te mostrará "
                "el problema y un resumen acumulado de tus reflexiones previas. "
                "Piensa en voz alta (solo devuélveme el pensamiento), continuando la idea anterior, no proporciones la solución. "
                "NO incluyas nada que no sea el contenido de tu pensamiento."
            )
            prompt_for_thinking = (
                f"Problema: {prompt}\n\n"
                f"Resumen previo: {resumen_acumulado}\n\n"
                "Describe tu pensamiento aquí (sin dar solución), continuando la idea anterior:"
            )
         elif tipo_problema == 2 or tipo_problema == 3:
            system_msg_for_thinking = (
                "Eres un experto resolviendo problemas. A continuación se te mostrará "
                "el problema y un resumen acumulado de tus reflexiones previas. "
                "Piensa en voz alta (solo devuélveme el pensamiento), buscando una idea alternativa a las ideas anteriores, no proporciones la solución. "
                "NO incluyas nada que no sea el contenido de tu pensamiento."
            )
            prompt_for_thinking = (
                f"Problema: {prompt}\n\n"
                f"Resumen previo: {resumen_acumulado}\n\n"
                "Describe tu pensamiento aquí (sin dar solución), buscando una idea alternativa a las ideas anteriores:"
            )
         else:
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
         provider = llm_providers.get(selected_provider)
         if not provider:
             yield "Error: Provider not found"
             return
         for chunk in provider.generate_response(
             prompt=prompt_for_thinking,
             model_name=selected_model,
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
         provider = llm_providers.get(selected_provider)
         if not provider:
             yield "Error: Provider not found"
             return
         for chunk in provider.generate_response(
             prompt=prompt_for_summary,
             model_name=selected_model,
             system_message=system_msg_for_summary
         ):
             resumen_response += chunk

         # ----------------------------------------------------------
         # Paso 8: Sumar el resumen al pensamiento acumulado y
         #         continuar con la siguiente iteración.
         # ----------------------------------------------------------
         resumen_acumulado += f"\n- {resumen_response.strip()}"

     # ------------------------------------------------------------------------
     # Paso 10: Con el problema más el resumen final de los pensamientos,
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
     provider = llm_providers.get(selected_provider)
     if not provider:
         yield "Error: Provider not found"
         return
     for chunk in provider.generate_response(
         prompt=prompt_for_final,
         model_name=selected_model,
         system_message=system_msg_for_final
     ):
         respuesta_final += chunk

     yield respuesta_final

# Dictionary to hold available LLM providers
llm_providers = {
    "gemini": gemini_api,
}

if ollama_api:
    llm_providers["ollama"] = ollama_api
else:
    debug_print(True, "Ollama API not available, setting empty model list.")

if openai_api:
    llm_providers["openai"] = openai_api
else:
    debug_print(True, "OpenAI API not available, setting empty model list.")

if claude_api:
    llm_providers["claude"] = claude_api
else:
    debug_print(True, "Claude API not available, setting empty model list.")

if groq_api:
    llm_providers["groq"] = groq_api
else:
    debug_print(True, "Groq API not available, setting empty model list.")

# Default LLM provider and model
selected_provider = "gemini"
selected_model = "gemini-1.5-flash"



# Function to generate responses using the selected LLM
def generate_response(prompt, model_name, image=None, history=None, provider_name=None, system_message=None, selected_tools=None):

    debug_print(True, f"Generating response with provider: {provider_name}, model: {model_name}, tools: {selected_tools}")

    provider = llm_providers.get(provider_name)
    if provider:
        if model_name:
            if selected_tools and len(selected_tools) > 0:
                tools_dir = '../tools'
                tool_instances = []
                for tool_name in selected_tools:
                    try:
                        filename = f'{tool_name}.py'
                        file_path = os.path.join(tools_dir, filename)
                        spec = importlib.util.spec_from_file_location(tool_name, file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'execute') and hasattr(module, 'get_tool_description'):
                            tool_instances.append({
                                'name': tool_name,
                                'description': module.get_tool_description(),
                                'execute': module.execute
                            })
                        else:
                            debug_print(True, f"Error: Tool {tool_name} does not have 'execute' or 'get_tool_description' functions.")
                    except Exception as e:
                        debug_print(True, f"Error loading tool {tool_name}: {e}")
                
                tool_descriptions = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tool_instances])
                tool_prompt = f"""
                    You have access to the following tools. You can use one or more of them, and you can use the same tool multiple times if needed:
                    {tool_descriptions}
                    
                    Use the tools by calling them with the following format. You can call one or more tools in a single response:
                    

tool_code
                    [
                        {{
                            "tool_name": "tool_name_1",
                            "parameters": {{
                                "param1": "value1",
                                "param2": "value2"
                            }}
                        }},
                        {{
                            "tool_name": "tool_name_2",
                            "parameters": {{
                                "param3": "value3",
                                "param4": "value4"
                            }}
                        }}
                    ]


                    Now, respond to the following prompt:
                    {prompt}
                """
                
                tool_response_generator = provider.generate_response(tool_prompt, model_name, image, None, system_message)
                tool_response = ""
                for chunk in tool_response_generator:
                    tool_response += chunk
                debug_print(True, f"Tool response: {tool_response}")
                
                try:
                    start_index = tool_response.find('[')
                    end_index = tool_response.rfind(']')
                    if start_index != -1 and end_index != -1:
                        json_string = tool_response[start_index:end_index+1]
                        tool_calls = json.loads(json_string)
                        
                        tool_results = []
                        for tool_call in tool_calls:
                            tool_name = tool_call.get('tool_name')
                            tool_params = tool_call.get('parameters', {})
                            
                            if tool_name:
                                tool = next((tool for tool in tool_instances if tool['name'] == tool_name), None)
                                if tool:
                                    debug_print(True, f"Executing tool: {tool_name} with params: {tool_params}")
                                    tool_result = tool['execute'](**tool_params)
                                    debug_print(True, f"Tool result: {tool_result}")
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "tool_params": tool_params,
                                        "tool_result": tool_result
                                    })
                                else:
                                    debug_print(True, f"Error: Tool {tool_name} not found.")
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "error": "Tool not found"
                                    })
                            else:
                                debug_print(True, "Error: No tool name found in tool call.")
                                tool_results.append({
                                    "error": "No tool name found in tool call."
                                })
                        
                        tool_results_str = json.dumps(tool_results, indent=4)
                        prompt = f"""
                            The following tools were called:
                            

tool_calls
                            {tool_results_str}


                            
                            Now, respond to the following prompt:
                            {prompt}
                        """
                    else:
                        debug_print(True, "Error: No tool calls found in tool response.")
                        prompt = f"""
                            Error: No tool calls found in tool response.
                            
                            Now, respond to the following prompt:
                            {prompt}
                        """
                except json.JSONDecodeError:
                    debug_print(True, "Error decoding tool response.")
                    prompt = f"""
                        Error decoding tool response.
                        
                        Now, respond to the following prompt:
                        {prompt}
                    """
            
            response = provider.generate_response(prompt, model_name, image, history, system_message)
            debug_print(True, f"Response generated successfully.")
            return response
        else:
            debug_print(True, "Error: No model selected for the provider.")
            return "Error: No model selected for the provider."
    else:
        debug_print(True, "Error: LLM provider not found")
        return "Error: LLM provider not found"

def generate_think_response(prompt, depth, model_name=None, provider_name=None):
    if not model_name:
        model_name = selected_model
    if not provider_name:
        provider_name = selected_provider
    debug_print(True, f"Generating think response with model: {model_name}, provider: {provider_name}, depth: {depth}")
    
    response = think(prompt, depth)
    debug_print(True, f"Think response generated successfully.")
    return response
