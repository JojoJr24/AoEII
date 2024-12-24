from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from claude_api import ClaudeAPI
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
from openai_api import OpenAIAPI
from groq_api import GroqAPI
from typing import Generator
from PIL import Image
import io
import importlib.util
import os
import sys
import json

from PIL import Image
import io
import os
import json
import sqlite3
from datetime import datetime
import importlib.util
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

DEBUG = True
streaming = True

def debug_print(color, message):
    if DEBUG:
        print(f"{color}{message}{RESET}")

# Initialize the Gemini API
gemini_api = GeminiAPI()
debug_print(BLUE, "Gemini API initialized.")

# Initialize the Ollama API
try:
    ollama_api = OllamaAPI()
    debug_print(BLUE, "Ollama API initialized.")
except Exception as e:
    debug_print(RED, f"Error initializing Ollama API: {e}")
    ollama_api = None

# Initialize the OpenAI API
try:
    openai_api = OpenAIAPI()
    debug_print(BLUE, "OpenAI API initialized.")
except Exception as e:
    debug_print(RED, f"Error initializing OpenAI API: {e}")
    openai_api = None

# Initialize the Claude API
try:
    claude_api = ClaudeAPI()
    debug_print(BLUE, "Claude API initialized.")
except Exception as e:
    debug_print(RED, f"Error initializing Claude API: {e}")
    claude_api = None

# Initialize the Groq API
try:
    groq_api = GroqAPI()
    debug_print(BLUE, "Groq API initialized.")
except Exception as e:
    debug_print(RED, f"Error initializing Groq API: {e}")
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
        dificultad = depth
        print(f"Profundidad establecida por el usuario: {dificultad}")
    else:
        # ------------------------------------------------------------------------
        # Paso 3 y 4: Solicitar a Ollama que devuelva SOLO un JSON con la complejidad.
        # ------------------------------------------------------------------------
        system_msg_for_complexity = (
            "Por favor, analiza el siguiente problema y devuelve ÚNICAMENTE un JSON "
            "con el campo 'complejidad' que indique (en un número entero) "
            "cuán difícil es el problema. No incluyas nada más que el JSON."
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
        # Paso 5: Parsear la dificultad del JSON.
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
    debug_print(BLUE, "Ollama API not available, setting empty model list.")

if openai_api:
    llm_providers["openai"] = openai_api
else:
    debug_print(BLUE, "OpenAI API not available, setting empty model list.")

if claude_api:
    llm_providers["claude"] = claude_api
else:
    debug_print(BLUE, "Claude API not available, setting empty model list.")

if groq_api:
    llm_providers["groq"] = groq_api
else:
    debug_print(BLUE, "Groq API not available, setting empty model list.")

# Default LLM provider and model
selected_provider = "gemini"
selected_model = "gemini-1.5-flash"

# Database setup
DATABASE = 'conversations.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()

def save_conversation(provider, model, system_message, title):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO conversations (provider, model, system_message, created_at, title) VALUES (?, ?, ?, ?, ?)",
                   (provider, model, system_message, timestamp, title))
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conversation_id

def add_message_to_conversation(conversation_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                   (conversation_id, role, content, timestamp))
    conn.commit()
    conn.close()

def get_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conversation = cursor.fetchone()
    if conversation:
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at", (conversation_id,))
        messages = cursor.fetchall()
        conn.close()
        return dict(conversation), [dict(message) for message in messages]
    conn.close()
    return None, None

def list_conversations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, provider, model, created_at FROM conversations ORDER BY created_at DESC")
    conversations = cursor.fetchall()
    conn.close()
    return [dict(conversation) for conversation in conversations]

def save_system_message(name, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO system_messages (name, content, created_at) VALUES (?, ?, ?)", (name, content, timestamp))
    system_message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return system_message_id

def get_system_message(system_message_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM system_messages WHERE id = ?", (system_message_id,))
    system_message = cursor.fetchone()
    conn.close()
    if system_message:
        return dict(system_message)
    return None

def list_system_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, provider, model, created_at FROM conversations ORDER BY created_at DESC")
    conversations = cursor.fetchall()
    cursor.execute("SELECT id, name, content, created_at FROM system_messages ORDER BY created_at DESC")
    system_messages = cursor.fetchall()
    conn.close()
    return [dict(system_message) for system_message in system_messages]

def list_tools():
    tools_dir = '../tools'
    tools = []
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            file_path = os.path.join(tools_dir, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'get_tool_description'):
                    tools.append({
                        'name': module_name,
                        'description': module.get_tool_description()
                    })
            except Exception as e:
                debug_print(RED, f"Error loading tool {module_name}: {e}")
    return tools

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def delete_system_message(system_message_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM system_messages WHERE id = ?", (system_message_id,))
    conn.commit()
    conn.close()

def delete_all_system_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM system_messages")
    conn.commit()
    conn.close()

def delete_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.commit()
def delete_all_conversations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations")
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

# Function to get available models for the selected provider
def get_available_models(provider_name):
    provider = llm_providers.get(provider_name)
    if provider:
        models = provider.list_models()
        debug_print(GREEN, f"Available models for {provider_name}: {models}")
        return models
    debug_print(RED, f"Provider {provider_name} not found.")
    return []

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
                            debug_print(RED, f"Error: Tool {tool_name} does not have 'execute' or 'get_tool_description' functions.")
                    except Exception as e:
                        debug_print(RED, f"Error loading tool {tool_name}: {e}")
                
                tool_descriptions = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tool_instances])
                tool_prompt = f"""
                    You have access to the following tools. You can use one or more of them, and you can use the same tool multiple times if needed:
                    {tool_descriptions}
                    
                    Use the tools by calling them with the following format. You can call one or more tools in a single response:
                    ```tool_code
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
                    ```
                    Now, respond to the following prompt:
                    {prompt}
                """
                
                tool_response_generator = provider.generate_response(tool_prompt, model_name, image, None, system_message)
                tool_response = ""
                for chunk in tool_response_generator:
                    tool_response += chunk
                debug_print(BLUE, f"Tool response: {tool_response}")
                
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
                                    debug_print(BLUE, f"Tool result: {tool_result}")
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "tool_params": tool_params,
                                        "tool_result": tool_result
                                    })
                                else:
                                    debug_print(RED, f"Error: Tool {tool_name} not found.")
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "error": "Tool not found"
                                    })
                            else:
                                debug_print(RED, "Error: No tool name found in tool call.")
                                tool_results.append({
                                    "error": "No tool name found in tool call."
                                })
                        
                        tool_results_str = json.dumps(tool_results, indent=4)
                        prompt = f"""
                            The following tools were called:
                            ```tool_calls
                            {tool_results_str}
                            ```
                            
                            Now, respond to the following prompt:
                            {prompt}
                        """
                    else:
                        debug_print(RED, "Error: No tool calls found in tool response.")
                        prompt = f"""
                            Error: No tool calls found in tool response.
                            
                            Now, respond to the following prompt:
                            {prompt}
                        """
                except json.JSONDecodeError:
                    debug_print(RED, "Error decoding tool response.")
                    prompt = f"""
                        Error decoding tool response.
                        
                        Now, respond to the following prompt:
                        {prompt}
                    """
            
            response = provider.generate_response(prompt, model_name, image, history, system_message)
            debug_print(GREEN, f"Response generated successfully.")
            return response
        else:
            debug_print(RED, "Error: No model selected for the provider.")
            return "Error: No model selected for the provider."
    else:
        debug_print(RED, "Error: LLM provider not found")
        return "Error: LLM provider not found"

def generate_think_response(prompt, depth, model_name=None, provider_name=None):
    if not model_name:
        model_name = selected_model
    if not provider_name:
        provider_name = selected_provider
    debug_print(BLUE, f"Generating think response with model: {model_name}, provider: {provider_name}, depth: {depth}")
    
    response = think(prompt, depth)
    debug_print(GREEN, f"Think response generated successfully.")
    return response

@app.route('/api/models', methods=['GET'])
def list_models():
    debug_print(MAGENTA, "Received request for /api/models")
    provider_name = request.args.get('provider', selected_provider)
    models = get_available_models(provider_name)
    return jsonify(models)

@app.route('/api/generate', methods=['POST'])
def generate():
    debug_print(MAGENTA, "Received request for /api/generate")
    global selected_provider, selected_model
    data = request.form
    prompt = data.get('prompt')
    model_name = data.get('model')
    provider_name = data.get('provider')
    if not model_name:
        model_name = selected_model
    if not provider_name:
        provider_name = selected_provider
    image_file = request.files.get('image')
    history_str = data.get('history')
    system_message = data.get('system_message')
    conversation_id = data.get('conversation_id')
    selected_tools_str = data.get('selected_tools')
    
    if selected_tools_str:
        try:
            selected_tools = json.loads(selected_tools_str)
            debug_print(GREEN, f"Selected tools: {selected_tools}")
        except json.JSONDecodeError:
            debug_print(RED, "Error decoding selected tools")
            selected_tools = []
    else:
        selected_tools = []
        
    debug_print(BLUE, f"Request: prompt='{prompt}', model='{model_name}', provider='{provider_name}', image={'present' if image_file else 'not present'}, history='{history_str}', system_message='{system_message}', conversation_id='{conversation_id}', selected_tools='{selected_tools}'")
    
    image = None
    if image_file:
        try:
            image = Image.open(io.BytesIO(image_file.read()))
            debug_print(GREEN, "Image loaded successfully.")
        except Exception as e:
            debug_print(RED, f"Error loading image: {e}")
            return jsonify({"response": f"Error al cargar la imagen: {e}"}), 400
    
    history = None
    if history_str:
        try:
            history = json.loads(history_str)
            debug_print(GREEN, "Chat history loaded successfully.")
        except json.JSONDecodeError:
            debug_print(RED, "Error decoding chat history")
            return jsonify({"response": "Error decoding chat history"}), 400

    if not prompt:
        debug_print(RED, "Error: Prompt is required")
        return jsonify({"response": "Prompt is required"}), 400
    
    if conversation_id:
        conversation_id = int(conversation_id)
        conversation, messages = get_conversation(conversation_id)
        if conversation:
            system_message = conversation['system_message']
            history = []
            for message in messages:
                history.append({"role": message['role'], "content": message['content']})
            debug_print(GREEN, f"Retrieved conversation {conversation_id} from database.")
        else:
            debug_print(RED, f"Conversation {conversation_id} not found.")
            history = []
    else:
        conversation_title = data.get('conversation_title', '')
        if len(conversation_title) > 30:
            conversation_title = conversation_title[:30]
        conversation_id = save_conversation(provider_name, model_name, system_message, conversation_title)
        debug_print(GREEN, f"Created new conversation with id {conversation_id}")
    
    add_message_to_conversation(conversation_id, "user", prompt)
    
    def stream_response():
        global streaming
        full_response = ""
        for chunk in generate_response(prompt, model_name, image, history, provider_name, system_message, selected_tools):
            if not streaming:
                debug_print(BLUE, "Streaming stopped.")
                break
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"
        add_message_to_conversation(conversation_id, "model", full_response)
        debug_print(GREEN, f"Response: {full_response}")
    
    return Response(stream_response(), mimetype='text/event-stream')


@app.route('/api/think', methods=['POST'])
def think_route():
    debug_print(MAGENTA, "Received request for /api/think")
    global selected_provider, selected_model
    data = request.form
    prompt = data.get('prompt')
    model_name = data.get('model')
    provider_name = data.get('provider')
    if not model_name:
        model_name = selected_model
    if not provider_name:
        provider_name = selected_provider
    depth = int(data.get('think_depth', 0))
    
    debug_print(BLUE, f"Request: prompt='{prompt}', model='{model_name}', provider='{provider_name}', depth='{depth}'")

    if not prompt:
        debug_print(RED, "Error: Prompt is required")
        return jsonify({"response": "Prompt is required"}), 400
    
    def stream_response():
        global streaming
        full_response = ""
        for chunk in generate_think_response(prompt,  depth, model_name, provider_name):
            if not streaming:
                debug_print(BLUE, "Streaming stopped.")
                break
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"
        debug_print(GREEN, f"Response: {full_response}")
    
    return Response(stream_response(), mimetype='text/event-stream')

@app.route('/api/conversations', methods=['GET'])
def list_conversations_route():
    debug_print(MAGENTA, "Received request for /api/conversations")
    conversations = list_conversations()
    debug_print(GREEN, f"Response: {conversations}")
    return jsonify(conversations)

@app.route('/api/system_messages', methods=['GET'])
def list_system_messages_route():
    debug_print(MAGENTA, "Received request for /api/system_messages")
    system_messages = list_system_messages()
    debug_print(GREEN, f"Response: {system_messages}")
    return jsonify(system_messages)

@app.route('/api/system_messages/<int:system_message_id>', methods=['GET'])
def get_system_message_route(system_message_id):
    debug_print(MAGENTA, f"Received request for /api/system_messages/{system_message_id}")
    system_message = get_system_message(system_message_id)
    if system_message:
        debug_print(GREEN, f"Response: {system_message}")
        return jsonify(system_message)
    debug_print(RED, f"Response: System message {system_message_id} not found")
    return jsonify({"message": "System message not found"}), 404

@app.route('/api/system_messages/<int:system_message_id>', methods=['DELETE'])
def delete_system_message_route(system_message_id):
    debug_print(MAGENTA, f"Received request to DELETE /api/system_messages/{system_message_id}")
    delete_system_message(system_message_id)
    debug_print(GREEN, f"Response: System message {system_message_id} deleted")
    return jsonify({"message": f"System message {system_message_id} deleted"})

@app.route('/api/system_messages', methods=['DELETE'])
def delete_all_system_messages_route():
    debug_print(MAGENTA, "Received request to DELETE all system messages")
    delete_all_system_messages()
    debug_print(GREEN, "Response: All system messages deleted")
    return jsonify({"message": "All system messages deleted"})

@app.route('/api/tools', methods=['GET'])
def list_tools_route():
    debug_print(MAGENTA, "Received request for /api/tools")
    tools = list_tools()
    debug_print(GREEN, f"Response: {tools}")
    return jsonify(tools)

@app.route('/api/system_messages', methods=['POST'])
def save_system_message_route():
    debug_print(MAGENTA, "Received request to POST /api/system_messages")
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    if not name or not content:
        debug_print(RED, "Error: Name and content are required")
        return jsonify({"message": "Name and content are required"}), 400
    system_message_id = save_system_message(name, content)
    debug_print(GREEN, f"Response: System message {system_message_id} saved")
    return jsonify({"message": f"System message {system_message_id} saved", "id": system_message_id})

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation_route(conversation_id):
    debug_print(MAGENTA, f"Received request for /api/conversations/{conversation_id}")
    conversation, messages = get_conversation(conversation_id)
    if conversation:
        debug_print(GREEN, f"Response: {conversation}, {messages}")
        return jsonify({"conversation": conversation, "messages": messages})
    debug_print(RED, f"Response: Conversation {conversation_id} not found")
    return jsonify({"message": "Conversation not found"}), 404

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation_route(conversation_id):
    debug_print(MAGENTA, f"Received request to DELETE /api/conversations/{conversation_id}")
    delete_conversation(conversation_id)
    debug_print(GREEN, f"Response: Conversation {conversation_id} deleted")
    return jsonify({"message": f"Conversation {conversation_id} deleted"})

@app.route('/api/conversations', methods=['DELETE'])
def delete_all_conversations_route():
    debug_print(MAGENTA, "Received request to DELETE all conversations")
    delete_all_conversations()
    debug_print(GREEN, "Response: All conversations deleted")
    return jsonify({"message": "All conversations deleted"})

@app.route('/api/stop', methods=['POST'])
def stop_stream():
    global streaming
    streaming = False
    debug_print(MAGENTA, "Received request to /api/stop")
    return jsonify({"message": "Streaming stopped"})

if __name__ == '__main__':
    # Initialize the database
    debug_print(BLUE, "Initializing database...")
    init_db()
    debug_print(BLUE, "Database initialized.")
    app.run(debug=True, port=5000)
