from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from gemini_api import GeminiAPI
from PIL import Image
import io
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the Gemini API
gemini_api = GeminiAPI()

# Dictionary to hold available LLM providers
llm_providers = {
    "gemini": gemini_api,
    # Add other LLM providers here as needed
}

# Default LLM provider and model
selected_provider = "gemini"
selected_model = "gemini-1.5-flash"

# Function to get available models for the selected provider
def get_available_models(provider_name):
    provider = llm_providers.get(provider_name)
    if provider:
        return provider.list_models()
    return []

# Function to generate responses using the selected LLM
def generate_response(prompt, model_name, image=None):
    provider = llm_providers.get(selected_provider)
    if provider:
        if model_name:
            return provider.generate_response(prompt, model_name, image)
        else:
            return "Error: No model selected for the provider."
    else:
        return "Error: LLM provider not found"

@app.route('/api/models', methods=['GET'])
def list_models():
    provider_name = request.args.get('provider', selected_provider)
    models = get_available_models(provider_name)
    return jsonify(models)

@app.route('/api/generate', methods=['POST'])
def generate():
    global selected_provider, selected_model
    data = request.form
    prompt = data.get('prompt')
    model_name = data.get('model', selected_model)
    image_file = request.files.get('image')
    
    image = None
    if image_file:
        try:
            image = Image.open(io.BytesIO(image_file.read()))
        except Exception as e:
            return jsonify({"response": f"Error al cargar la imagen: {e}"}), 400

    if not prompt:
        return jsonify({"response": "Prompt is required"}), 400

    def stream_response():
        for chunk in generate_response(prompt, model_name, image):
            yield f" {json.dumps({'response': chunk})}\n\n"
    
    return Response(stream_response(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
