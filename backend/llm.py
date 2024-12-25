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
debug_print(BLUE, "Gemini API initialized.")

# Initialize the Ollama API
try:
    ollama_api = OllamaAPI()
    debug_print(BLUE, "Ollama API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing Ollama API: {e}")
    ollama_api = None

# Initialize the OpenAI API
try:
    openai_api = OpenAIAPI()
    debug_print(BLUE, "OpenAI API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing OpenAI API: {e}")
    openai_api = None

# Initialize the Claude API
try:
    claude_api = ClaudeAPI()
    debug_print(BLUE, "Claude API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing Claude API: {e}")
    claude_api = None

# Initialize the Groq API
try:
    groq_api = GroqAPI()
    debug_print(BLUE, "Groq API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing G, model_name=None, provider_name=Noneroq API: {e}")
    groq_api = None


def think(prompt: str, depth: int, selected_model=None, selected_provider=None) -> Generator[str, None, None]:
    provider = llm_providers.get(selected_provider)

    if depth != 0:
        print(f"{GREEN}Profundidad establecida por el usuario: {depth}{RESET}")

    # Mensaje al sistema para clasificación del problema
    system_msg_for_classification = (
        "Eres un experto en resolución de problemas. A continuación, se te proporcionará una descripción del problema. "
        "Por favor, analiza el problema y responde ÚNICAMENTE con un JSON con los campos: \"dificultad\", \"tipo_problema\" y \"estrategias_comunes\". "
        "- \"dificultad\": Un número entero entre 1 (muy sencillo) y 5 (extremadamente complejo).\n"
        "- \"tipo_problema\": Número entero que clasifica el problema:\n"
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

    retries = 3
    for _ in range(retries):
        debug_print(BLUE, f"Intentando obtener clasificación del problema, intento {_ + 1} de {retries}.")
        try:
            for chunk in provider.generate_response(
                prompt=prompt,
                model_name=selected_model,
                system_message=system_msg_for_classification
            ):
                classification_response += chunk

            start_index = classification_response.find('{')
            end_index = classification_response.rfind('}')
            if start_index != -1 and end_index != -1:
                json_string = classification_response[start_index:end_index+1]
                parsed_json = json.loads(json_string)
                debug_print(GREEN, f"Clasificación obtenida exitosamente: {parsed_json}")
                break
        except json.JSONDecodeError:
            debug_print(MAGENTA, f"Error al parsear JSON en el intento {_ + 1}.")
            if _ == retries - 1:
                yield "Error: Failed to parse JSON after multiple retries"
                return

    dificultad = depth if depth != 0 else parsed_json.get("dificultad", 1)
    tipo_problema = parsed_json.get("tipo_problema", 1)
    estrategias_comunes = parsed_json.get("estrategias_comunes", [])
    debug_print(BLUE, f"Dificultad: {dificultad}, Tipo de problema: {tipo_problema}, Estrategias: {estrategias_comunes}")

    resultados_por_estrategia = {}

    for estrategia in estrategias_comunes:
        debug_print(BLUE, f"Procesando estrategia: {estrategia}")
        steps_response = ""
        for _ in range(retries):
            debug_print(BLUE, f"Intentando obtener pasos para la estrategia '{estrategia}', intento {_ + 1} de {retries}.")
            try:
                system_msg_for_steps = (
                    f"Eres un experto resolviendo problemas. La estrategia actual es: {estrategia}. "
                    "Por favor, proporciona una lista de titulos CONCISOS de pasos claros para abordar el problema usando esta estrategia. "
                    "Escribe cada paso en una nueva línea con la menor cantidad de palabras posibles y NADA MÁS.\n"
                    f"En una escala del 1 al 10 tenés que dividir este problema con un detalle de {dificultad}"
                    "El nivel de detalle define la granularidad de los pasos que vas a tener que pensar. Por lo tanto la cantidad de pasos es proporcional al detalle"
                    "Ejemplo:\n"
                    "Paso 1: Sumar los dos primeros números\n"
                    "Paso 2: Restar el tercer número\n"
                    "Paso 3: Dividir el resultado del paso 1 al del paso 2\n"
                )
                prompt_for_steps = (
                    f"Problema: {prompt}\n\n"
                    f"Genera una lista de pasos para resolverlo usando la estrategia {estrategia}:"
                )

                for chunk in provider.generate_response(
                    prompt=prompt_for_steps,
                    model_name=selected_model,
                    system_message=system_msg_for_steps
                ):
                    steps_response += chunk

                pasos_para_estrategia = [line.strip() for line in steps_response.strip().split("\n") if line.strip()]
                debug_print(GREEN, f"Pasos obtenidos: {pasos_para_estrategia}")
                break
            except Exception as e:
                debug_print(MAGENTA, f"Error al procesar pasos en el intento {_ + 1}: {e}")
                if _ == retries - 1:
                    pasos_para_estrategia = []

        resumen_acumulado = ""
        for paso in pasos_para_estrategia:
            debug_print(BLUE, f"Procesando paso: {paso}")
            step_solution_response = ""
            for chunk in provider.generate_response(
                prompt=f"Problema: {prompt}\n\nPaso actual: {paso}\n\nSolución para este paso:",
                model_name=selected_model,
                system_message=(
                    f"Eres un experto resolviendo problemas.\nLos pasos anteriores resueltos son: {resumen_acumulado} .\n "
                    "Proporciona una solución detallada para este paso."
                )
            ):
                step_solution_response += chunk
            debug_print(GREEN, f"Solución para el paso '{paso}': {step_solution_response.strip()}")
            resumen_acumulado += f"\n- Paso: {paso}: {step_solution_response.strip()}"

        evaluation_response = ""
        debug_print(BLUE,f"Generando evaluación para la estrategia: {estrategia}")
        for chunk in provider.generate_response(
            prompt=(
                f"Problema: {prompt}\n\nDetalle de razonamiento para la estrategia {estrategia}: {resumen_acumulado}\n\n"
                "Escribe la mejor solución posible que surge al usar la estrategia:"
            ),
            model_name=selected_model,
            system_message=(
                "Eres un experto en análisis estratégico. A continuación, se te proporciona un resumen acumulado "
                "de soluciones generadas para una estrategia. Evalúa la calidad de las posibles soluciones al problema original y "
                "combínalas para obtener la mejor solución posible."
            )
        ):
            evaluation_response += chunk
        debug_print(GREEN,f"Evaluación para la estrategia '{estrategia}': {evaluation_response.strip()}")

        resultados_por_estrategia[estrategia] = {
            "resumen": resumen_acumulado,
            "evaluacion": evaluation_response.strip()
        }

    final_summary = ""
    debug_print(BLUE,"Generando resumen final...")
    for estrategia, datos in resultados_por_estrategia.items():
        final_summary += (
            f"\nEstrategia: {estrategia}\n"
            f"Resumen acumulado: {datos['resumen']}\n"
            f"Evaluación: {datos['evaluacion']}\n"
        )

    debug_print(BLUE,"Generando solución final...")
    for chunk in provider.generate_response(
        prompt=(
            f"Problema : {prompt}\n\n"
            f"Esto es lo que pensaste al analizar el problema : {final_summary} .\n\n"
            "Esta es la solución al problema:"
        ),
        model_name=selected_model,
        system_message=(
            "Eres un experto resolviendo problemas complejos. Se te proporciona un problema junto con "
            "todo lo que pensaste para resolverlo. Con base en esta información, "
            "Analiza cuál de todas las propuestas soluciona el problema y escríbela como la solución final."
        )
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

    debug_print(BLUE, f"Generating response with provider: {provider_name}, model: {model_name}, tools: {selected_tools}")

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
                            debug_print(MAGENTA, f"Error: Tool {tool_name} does not have 'execute' or 'get_tool_description' functions.")
                    except Exception as e:
                        debug_print(MAGENTA, f"Error loading tool {tool_name}: {e}")
                
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
                                    debug_print(BLUE, f"Executing tool: {tool_name} with params: {tool_params}")
                                    tool_result = tool['execute'](**tool_params)
                                    debug_print(GREEN, f"Tool result: {tool_result}")
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "tool_params": tool_params,
                                        "tool_result": tool_result
                                    })
                                else:
                                    debug_print(MAGENTA, f"Error: Tool {tool_name} not found.")
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "error": "Tool not found"
                                    })
                            else:
                                debug_print(MAGENTA, "Error: No tool name found in tool call.")
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
                        debug_print(MAGENTA, "Error: No tool calls found in tool response.")
                        prompt = f"""
                            Error: No tool calls found in tool response.
                            
                            Now, respond to the following prompt:
                            {prompt}
                        """
                except json.JSONDecodeError:
                    debug_print(MAGENTA, "Error decoding tool response.")
                    prompt = f"""
                        Error decoding tool response.
                        
                        Now, respond to the following prompt:
                        {prompt}
                    """
            
            response = provider.generate_response(prompt, model_name, image, history, system_message)
            debug_print(GREEN, f"Response generated successfully.")
            return response
        else:
            debug_print(MAGENTA, "Error: No model selected for the provider.")
            return "Error: No model selected for the provider."
    else:
        debug_print(MAGENTA, "Error: LLM provider not found")
        return "Error: LLM provider not found"

def generate_think_response(prompt, depth, model_name=None, provider_name=None):
    if not model_name:
        model_name = selected_model
    if not provider_name:
        provider_name = selected_provider
    debug_print(BLUE, f"Generating think response with model: {model_name}, provider: {provider_name}, depth: {depth}")
    
    response = think(prompt, depth, selected_model=model_name, selected_provider=provider_name)
    debug_print(GREEN, f"Think response generated successfully.")
    return response
