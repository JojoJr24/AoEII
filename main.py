from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
from PIL import Image
import io
import os
import json

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

debug_print(CYAN, "Initializing Ollama API...")
ollama_api = OllamaAPI()
debug_print(CYAN, "Ollama API initialized.")

# Dictionary to hold available LLM providers
llm_providers = {
    "gemini": gemini_api,
    "ollama": ollama_api,
    # Add other LLM providers here as needed
}

# Default LLM provider and model
selected_provider = "gemini"
selected_model = "gemini-1.5-flash"

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
def generate_response(prompt, model_name, image=None, history=None, provider_name=None):
    if not provider_name:
        provider_name = selected_provider
    debug_print(BLUE, f"Generating response with provider: {provider_name}, model: {model_name}")
    provider = llm_providers.get(provider_name)
    if provider:
        if model_name:
            response = provider.generate_response(prompt, model_name, image, history)
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
    
    debug_print(BLUE, f"Request  prompt='{prompt}', model='{model_name}', provider='{provider_name}', image={'present' if image_file else 'not present'}, history='{history_str}'")
    
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

    def stream_response():
        debug_print(CYAN, "Starting response stream...")
        for chunk in generate_response(prompt, model_name, image, history, provider_name):
            yield f" {json.dumps({'response': chunk})}\n\n"
        debug_print(CYAN, "Response stream finished.")
    
    return Response(stream_response(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
