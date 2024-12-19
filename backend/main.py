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

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'

DEBUG = True

def debug_print(color, message):
    if DEBUG:
        print(f"{color}{message}{RESET}")

# Initialize the Gemini API
debug_print(CYAN, "Initializing Gemini API...")
gemini_api = GeminiAPI()
debug_print(CYAN, "Gemini API initialized.")

# Initialize the Ollama API
debug_print(CYAN, "Initializing Ollama API...")
try:
    ollama_api = OllamaAPI()
    debug_print(CYAN, "Ollama API initialized.")
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
    debug_print(YELLOW, "Ollama API not available, setting empty model list.")

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
    debug_print(BLUE, f"Getting available models for provider: {provider_name}")
    provider = llm_providers.get(provider_name)
    if provider:
        models = provider.list_models()
        debug_print(GREEN, f"Available models for {provider_name}: {models}")
        return models
    debug_print(RED, f"Provider {provider_name} not found.")
    return []

# Function to generate responses using the selected LLM
def generate_response(prompt, model_name, image=None, history=None, provider_name=None, system_message=None):
    if not provider_name:
        provider_name = selected_provider
    debug_print(BLUE, f"Generating response with provider: {provider_name}, model: {model_name}")
    provider = llm_providers.get(provider_name)
    if provider:
        if model_name:
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
    
    debug_print(BLUE, f"Request  prompt='{prompt}', model='{model_name}', provider='{provider_name}', image={'present' if image_file else 'not present'}, history='{history_str}', system_message='{system_message}', conversation_id='{conversation_id}'")
    
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
        if messages:
            history = []
            for message in messages:
                history.append({"role": message['role'], "content": message['content']})
            debug_print(GREEN, f"Retrieved conversation {conversation_id} from database.")
        else:
            debug_print(YELLOW, f"Conversation {conversation_id} not found.")
            history = []
    else:
        conversation_id = save_conversation(provider_name, model_name, system_message)
        debug_print(GREEN, f"Created new conversation with id {conversation_id}")
        history = []
    
    add_message_to_conversation(conversation_id, "user", prompt)

    def stream_response():
        debug_print(CYAN, "Starting response stream...")
        full_response = ""
        for chunk in generate_response(prompt, model_name, image, history, provider_name, system_message):
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"
        add_message_to_conversation(conversation_id, "model", full_response)
        debug_print(CYAN, "Response stream finished.")
    
    return Response(stream_response(), mimetype='text/event-stream')

@app.route('/api/conversations', methods=['GET'])
def list_conversations_route():
    debug_print(MAGENTA, "Received request for /api/conversations")
    conversations = list_conversations()
    return jsonify(conversations)

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation_route(conversation_id):
    debug_print(MAGENTA, f"Received request for /api/conversations/{conversation_id}")
    conversation, messages = get_conversation(conversation_id)
    if conversation:
        return jsonify({"conversation": conversation, "messages": messages})
    return jsonify({"message": "Conversation not found"}), 404

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation_route(conversation_id):
    debug_print(MAGENTA, f"Received request to DELETE /api/conversations/{conversation_id}")
    return jsonify({"message": f"Conversation {conversation_id} deleted"})

@app.route('/api/conversations', methods=['DELETE'])
def delete_all_conversations_route():
    debug_print(MAGENTA, "Received request to DELETE all conversations")
    delete_all_conversations()
    return jsonify({"message": "All conversations deleted"})

if __name__ == '__main__':
    # Initialize the database
    if not os.path.exists(DATABASE):
        debug_print(CYAN, "Initializing database...")
        init_db()
        debug_print(CYAN, "Database initialized.")
    app.run(debug=True, port=5000)
