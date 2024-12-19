from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
from PIL import Image
import io
import os
import json
import sqlite3
from datetime import datetime
import importlib.util

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

DEBUG = True

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

# Dictionary to hold available LLM providers
llm_providers = {
    "gemini": gemini_api,
}

if ollama_api:
    llm_providers["ollama"] = ollama_api
else:
    debug_print(BLUE, "Ollama API not available, setting empty model list.")

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

def save_conversation(provider, model, system_message):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO conversations (provider, model, system_message, created_at) VALUES (?, ?, ?, ?)",
                   (provider, model, system_message, timestamp))
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
    print("Hist",history)
    if not provider_name:
        provider_name = selected_provider
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
                    You have access to the following tools, use them if needed:
                    {tool_descriptions}
                    
                    Use the tools by calling them with the following format:
                    ```tool_code
                    {{
                        "tool_name": "tool_name",
                        "parameters": {{
                            "param1": "value1",
                            "param2": "value2"
                        }}
                    }}
                    ```
                    
                    After using the tool, continue with the conversation.
                    
                    Now, respond to the following prompt:
                    {prompt}
                """
                
                tool_response_generator = provider.generate_response(tool_prompt, model_name, image, None, system_message)
                tool_response = ""
                for chunk in tool_response_generator:
                    tool_response += chunk
                debug_print(BLUE, f"Tool response: {tool_response}")
                
                try:
                    start_index = tool_response.find('{')
                    end_index = tool_response.rfind('}')
                    if start_index != -1 and end_index != -1:
                        json_string = tool_response[start_index:end_index+1]
                        tool_call = json.loads(json_string)
                        tool_name = tool_call.get('tool_name')
                        tool_params = tool_call.get('parameters', {})
                        
                        if tool_name:
                            tool = next((tool for tool in tool_instances if tool['name'] == tool_name), None)
                            if tool:
                                debug_print(BLUE, f"Executing tool: {tool_name} with params: {tool_params}")
                                tool_result = tool['execute'](**tool_params)
                                debug_print(BLUE, f"Tool result: {tool_result}")
                                prompt = f"""
                                The tool {tool_name} was called with the following parameters:
                                ```tool_params
                                {tool_params}
                                ```
                                The tool response is:
                                ```tool_response
                                {tool_result}
                                ```
                                
                                Now, respond to the following prompt:
                                {prompt}
                            """
                        else:
                            debug_print(RED, f"Error: Tool {tool_name} not found.")
                            prompt = f"""
                                Error: Tool {tool_name} not found.
                                
                                Now, respond to the following prompt:
                                {prompt}
                            """
                    else:
                        debug_print(RED, "Error: No tool name found in tool response.")
                        prompt = f"""
                            Error: No tool name found in tool response.
                            
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
    model_name = data.get('model', selected_model)
    provider_name = data.get('provider', selected_provider)
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
        conversation_id = save_conversation(provider_name, model_name, system_message)
        debug_print(GREEN, f"Created new conversation with id {conversation_id}")
    
    add_message_to_conversation(conversation_id, "user", prompt)

    def stream_response():
        full_response = ""
        for chunk in generate_response(prompt, model_name, image, history, provider_name, system_message, selected_tools):
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"
        add_message_to_conversation(conversation_id, "model", full_response)
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

if __name__ == '__main__':
    # Initialize the database
    debug_print(BLUE, "Initializing database...")
    init_db()
    debug_print(BLUE, "Database initialized.")
    app.run(debug=True, port=5000)
