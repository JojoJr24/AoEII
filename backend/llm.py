import time
from claude_api import ClaudeAPI
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
from utils import GREEN, RED, BLUE, MAGENTA, RESET
from openai_api import OpenAIAPI
from groq_api import GroqAPI
from typing import Generator
import importlib.util
import os
import json

from utils import GREEN, debug_print

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
    debug_print(True, f"Error initializing G, model_name=None, provider_name=Noneroq API: {e}")
    groq_api = None


def think(prompt: str, depth: int, selected_model=None, selected_provider=None) -> Generator[str, None, None]:
    """
    Programa que:
    1) Recibe un prompt describiendo un problema.
    2) Si la profundidad (depth) es distinta de 0, se usa como dificultad.
    3) Si la profundidad es 0, solicita al modelo LLM (Ollama o similar) que clasifique el problema y devuelva un JSON con:
       - "dificultad": Nivel de complejidad (entero de 1 a 10).
       - "tipo_problema": Categoría del problema (entero de 1 a 4).
       - "estrategias_comunes": Lista de estrategias relevantes para resolverlo.
    """
    import json
    import os
    import importlib.util

    provider = llm_providers.get(selected_provider)

    if depth != 0:
        print(f"{GREEN}Profundidad establecida por el usuario: {depth}{RESET}")

    # Mensaje al sistema para clasificación del problema
    system_msg_for_classification = (
        "Eres un experto en resolución de problemas. A continuación, se te proporcionará una descripción del problema. "
        "Por favor, analiza el problema y responde ÚNICAMENTE con un JSON con los campos: \"dificultad\", \"tipo_problema\" y \"estrategias_comunes\". "
        "- \"dificultad\": Un número entero entre 1 (muy sencillo) y 10 (extremadamente complejo).\n"
        "- \"tipo_problema\": Número entero que clasifica el problema:\n"
        "  1: Problema secuencial (requiere pensar paso a paso).\n"
        "  2: Problema con información oculta (necesita hacer explícita información implícita).\n"
        "  3: Problema con información faltante (requiere agregar datos faltantes para solucionarlo).\n"
        "  4: Problema con información distractora (incluye datos irrelevantes que confunden).\n"
        "Clasificación completa de problemas:\n"
        "  1. Problemas bien definidos:\n"
        "     - Características: Los objetivos, las restricciones y los métodos de resolución están claramente especificados.\n"
        "     - Ejemplo: Resolver un rompecabezas matemático.\n"
        "     - Estrategias comunes: Algoritmos, heurísticas específicas para el dominio.\n"
        "  2. Problemas mal definidos:\n"
        "     - Características: Los objetivos son vagos, las restricciones son ambiguas y no hay una solución única o clara.\n"
        "     - Ejemplo: ¿Cómo reducir la pobreza en una ciudad?\n"
        "     - Estrategias comunes: Definición del problema, lluvia de ideas, enfoques creativos.\n"
        "  3. Problemas convergentes:\n"
        "     - Características: Tienen una solución específica o limitada.\n"
        "     - Ejemplo: Un problema de física con una respuesta exacta.\n"
        "     - Estrategias comunes: Pensamiento lógico, uso de principios bien establecidos.\n"
        "  4. Problemas divergentes:\n"
        "     - Características: Admiten múltiples soluciones posibles.\n"
        "     - Ejemplo: Diseñar un logotipo para una empresa.\n"
        "     - Estrategias comunes: Pensamiento creativo, métodos de diseño iterativos.\n"
        "  5. Problemas de razonamiento inductivo:\n"
        "     - Características: Requieren identificar patrones o generalizaciones a partir de datos específicos.\n"
        "     - Ejemplo: Predecir tendencias a partir de datos de ventas.\n"
        "     - Estrategias comunes: Análisis de datos, inferencias basadas en ejemplos.\n"
        "  6. Problemas de razonamiento deductivo:\n"
        "     - Características: Implican aplicar principios generales a casos específicos.\n"
        "     - Ejemplo: Resolver un silogismo lógico.\n"
        "     - Estrategias comunes: Aplicación de reglas lógicas, diagramas para visualizar relaciones.\n"
        "- \"estrategias_comunes\": Lista de estrategias comunes para abordar este tipo de problemas.\n"
        "Ejemplo de respuesta: {\"dificultad\": 5, \"tipo_problema\": 2, \"estrategias_comunes\": [\"pensamiento lateral\", \"dividir en subproblemas\"]}"
    )

    classification_response = ""
    if not provider:
        yield "Error: Provider not found"
        return
    
    for chunk in provider.generate_response(
        prompt=prompt,
        model_name=selected_model,
        system_message=system_msg_for_classification
    ):
        classification_response += chunk

    # Parsear la respuesta del modelo
    dificultad = depth  # Valor por defecto si no se puede parsear
    tipo_problema = 1  # Valor por defecto
    estrategias_comunes = []

    try:
        # Buscar JSON en la respuesta
        start_index = classification_response.find('{')
        end_index = classification_response.rfind('}')
        if start_index != -1 and end_index != -1:
            json_string = classification_response[start_index:end_index+1]
            parsed_json = json.loads(json_string)
            dificultad = dificultad if dificultad !=0 else parsed_json.get("dificultad", dificultad)
            tipo_problema = parsed_json.get("tipo_problema", tipo_problema)
            estrategias_comunes = parsed_json.get("estrategias_comunes", [])
    except json.JSONDecodeError:
        print(f"{RED}Error al interpretar el JSON de clasificación.{RESET}", classification_response)

    print(f"{BLUE}Dificultad detectada: {dificultad}, Tipo de problema detectado: {tipo_problema}{RESET}")
    print(f"{BLUE}Estrategias comunes sugeridas: {estrategias_comunes}{RESET}")

    # Loop doble: iterar por cada estrategia y dentro de cada estrategia iterar en función de la dificultad
    resultados_por_estrategia = {}

    for estrategia in estrategias_comunes:
        print(f"{MAGENTA}Iniciando iteraciones para la estrategia: {estrategia}{RESET}")
        resumen_acumulado = ""
        for i in range(dificultad):
            print(f"{MAGENTA}Iteración {i + 1} de {dificultad} usando la estrategia: {estrategia}{RESET}")

            # Generar reflexión basada en estrategia y dificultad
            system_msg_for_iteration = (
                f"Eres un experto resolviendo problemas. La estrategia actual es: {estrategia}. "
                "A continuación, analiza el problema paso a paso usando esta estrategia. "
                "Proporciona una reflexión sobre cómo abordarlo, y una posible solución."
            )

            prompt_for_iteration = (
                f"Problema: {prompt}\n\n"
                f"Reflexión usando la estrategia {estrategia}:"
            )

            iteration_response = ""
            print("Enviando prompt al modelo para reflexión iterativa...")
            for chunk in provider.generate_response(
                prompt=prompt_for_iteration,
                model_name=selected_model,
                system_message=system_msg_for_iteration
            ):
                iteration_response += chunk

            print(f"{GREEN}Respuesta obtenida para la iteración {i + 1}: {iteration_response.strip()}{RESET}")
            resumen_acumulado += f"\n- Iteración {i + 1}: {iteration_response.strip()}"

        print(f"{MAGENTA}Finalizadas las iteraciones para la estrategia: {estrategia}. Generando evaluación...{RESET}")
        # Una vez terminadas las iteraciones para una estrategia, evaluar el resumen acumulado
        system_msg_for_evaluation = (
            "Eres un experto en análisis estratégico. A continuación, se te proporciona un resumen acumulado "
            "de reflexiones generadas por una estrategia. Evalúa la efectividad de estas reflexiones y "
            "proporciona una respuesta sobre si esta estrategia es la mejor o si necesitas proponer una nueva estrategia."
        )

        prompt_for_evaluation = (
            f"Problema: {prompt}\n\n"
            f"Resumen acumulado para la estrategia {estrategia}: {resumen_acumulado}\n\n"
            "Evalúa la efectividad de esta estrategia y justifica tu conclusión:"
        )

        evaluation_response = ""
        print("Enviando resumen acumulado al modelo para evaluación...")
        for chunk in provider.generate_response(
            prompt=prompt_for_evaluation,
            model_name=selected_model,
            system_message=system_msg_for_evaluation
        ):
            evaluation_response += chunk

        print(f"{GREEN}Evaluación obtenida para la estrategia {estrategia}: {evaluation_response.strip()}{RESET}")
        resultados_por_estrategia[estrategia] = {
            "resumen": resumen_acumulado,
            "evaluacion": evaluation_response.strip()
        }

    print(f"{BLUE}Todas las estrategias procesadas. Preparando solución final...{RESET}")

    # Concatenar problema original y resultados de todas las estrategias
    final_summary = (
        f"Problema original: {prompt}\n\n"
        f"Resultados por estrategia:\n"
    )

    for estrategia, datos in resultados_por_estrategia.items():
        final_summary += (
            f"\nEstrategia: {estrategia}\n"
            f"Resumen acumulado: {datos['resumen']}\n"
            f"Evaluación: {datos['evaluacion']}\n"
        )

    # Solicitar al modelo que genere la solución final
    system_msg_for_final_solution = (
        "Eres un experto resolviendo problemas complejos. Se te proporciona un problema original junto con "
        "los resultados de diferentes estrategias utilizadas para abordarlo. Con base en esta información, "
        "proporciona la mejor solución posible al problema y justifícala brevemente."
    )

    prompt_for_final_solution = (
        f"{final_summary}\n\n"
        "Proporciona la solución final al problema con justificación:"
    )

    print(f"{MAGENTA}Enviando datos al modelo para generar la solución final...{RESET}")
    for chunk in provider.generate_response(
        prompt=prompt_for_final_solution,
        model_name=selected_model,
        system_message=system_msg_for_final_solution
    ):
        yield chunk




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
    
    response = think(prompt, depth, selected_model=model_name, selected_provider=provider_name)
    debug_print(True, f"Think response generated successfully.")
    return response
