import gradio as gr
from gemini_api import GeminiAPI
from PIL import Image
import io

# Initialize the Gemini API
gemini_api = GeminiAPI()

# Dictionary to hold available LLM providers
llm_providers = {
    "gemini": gemini_api,
    # Add other LLM providers here as needed
}

# Default LLM provider and model
selected_provider = "gemini"
selected_model = "gemini-pro"

# Function to get available models for the selected provider
def get_available_models(provider_name):
    provider = llm_providers.get(provider_name)
    if provider:
        return provider.list_models()
    return []

# Function to generate responses using the selected LLM
def generate_response(prompt, image=None):
    global selected_provider, selected_model
    provider = llm_providers.get(selected_provider)
    if provider:
        if selected_model:
            return provider.generate_response(prompt, selected_model, image)
        else:
            return "Error: No model selected for the provider."
    else:
        return "Error: LLM provider not found"

# Function to update the selected LLM provider
def update_selected_provider(provider_name):
    global selected_provider, selected_model
    selected_provider = provider_name
    available_models = get_available_models(provider_name)
    if available_models:
        selected_model = available_models[0]  # Select the first model by default
    else:
        selected_model = None
    return gr.Dropdown.update(choices=available_models, value=selected_model), f"Proveedor seleccionado: {provider_name}, Modelo seleccionado: {selected_model}"

# Function to update the selected LLM model
def update_selected_model(model_name):
    global selected_model
    selected_model = model_name
    return f"Proveedor seleccionado: {selected_provider}, Modelo seleccionado: {model_name}"

# Interfaz de Gradio
def chatbot_interface(user_input, history, image_file):
    # history es una lista de pares (usuario, asistente).
    # Append el nuevo input del usuario
    history = history or []
    
    image = None
    if image_file:
        try:
            image = Image.open(io.BytesIO(image_file.read()))
            history.append(((user_input, image), None))
        except Exception as e:
            history.append(((user_input, "Error al cargar la imagen"), None))
            print(f"Error al cargar la imagen: {e}")
    else:
        history.append((user_input, None))
    
    # Genera la respuesta del LLM
    response = generate_response(user_input, image)
    
    # Update the history with the response
    if image:
        history[-1] = ((user_input, image), response)
    else:
        history[-1] = (user_input, response)
    
    return history, history

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## Configuración")
            llm_provider_selector = gr.Dropdown(
                choices=list(llm_providers.keys()),
                value=selected_provider,
                label="Selecciona un Proveedor de LLM"
            )
            llm_model_selector = gr.Dropdown(
                choices=get_available_models(selected_provider),
                value=selected_model,
                label="Selecciona un Modelo de LLM"
            )
            llm_status = gr.Textbox(label="Estado del LLM", value=f"Proveedor seleccionado: {selected_provider}, Modelo seleccionado: {selected_model}")
            llm_provider_selector.change(
                fn=update_selected_provider, 
                inputs=llm_provider_selector, 
                outputs=[llm_model_selector, llm_status]
            )
            llm_model_selector.change(
                fn=update_selected_model,
                inputs=llm_model_selector,
                outputs=llm_status
            )
        with gr.Column(scale=4):
            gr.Markdown("# Mi Playground de LLM con Gradio")
            gr.Markdown("Escribe un mensaje y recibe una respuesta del modelo.")
            
            chatbot = gr.Chatbot()
            with gr.Row():
                image_upload_button = gr.UploadButton("📁", file_types=["image"], label="Subir imagen")
                msg = gr.Textbox(label="Escribe tu mensaje aquí...")
            state = gr.State([])

            submit_btn = gr.Button("Enviar")
            submit_btn.click(fn=chatbot_interface, 
                            inputs=[msg, state, image_upload_button], 
                            outputs=[chatbot, state])
            
            # O también podrías permitir enviar con Enter:
            msg.submit(fn=chatbot_interface, 
                    inputs=[msg, state, image_upload_button], 
                    outputs=[chatbot, state])

# Ejecuta la interfaz localmente en http://localhost:7860/
if __name__ == "__main__":
    demo.launch()
