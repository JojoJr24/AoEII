import gradio as gr
from gemini_api import GeminiAPI

# Initialize the Gemini API
gemini_api = GeminiAPI()

# Dictionary to hold available LLMs
llm_models = {
    "gemini-pro": gemini_api,
    # Add other LLMs here as needed
}

# Default LLM
selected_llm = "gemini-pro"

# Function to generate responses using the selected LLM
def generate_response(prompt):
    global selected_llm
    llm = llm_models.get(selected_llm)
    if llm:
        return llm.generate_response(prompt)
    else:
        return "Error: LLM not found"

# Function to update the selected LLM
def update_selected_llm(llm_name):
    global selected_llm
    selected_llm = llm_name
    return f"LLM seleccionado: {llm_name}"

# Interfaz de Gradio
def chatbot_interface(user_input, history):
    # history es una lista de pares (usuario, asistente).
    # Append el nuevo input del usuario
    history = history or []
    history.append((user_input, None))
    
    # Genera la respuesta del LLM
    response = generate_response(user_input)
    history[-1] = (user_input, response)
    return history, history

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## Configuración")
            llm_selector = gr.Dropdown(
                choices=list(llm_models.keys()),
                value=selected_llm,
                label="Selecciona un LLM"
            )
            llm_status = gr.Textbox(label="Estado del LLM", value=f"LLM seleccionado: {selected_llm}")
            llm_selector.change(fn=update_selected_llm, inputs=llm_selector, outputs=llm_status)
        with gr.Column(scale=4):
            gr.Markdown("# Mi Playground de LLM con Gradio")
            gr.Markdown("Escribe un mensaje y recibe una respuesta del modelo.")
            
            chatbot = gr.Chatbot()
            msg = gr.Textbox(label="Escribe tu mensaje aquí...")
            state = gr.State([])

            submit_btn = gr.Button("Enviar")
            submit_btn.click(fn=chatbot_interface, 
                            inputs=[msg, state], 
                            outputs=[chatbot, state])
            
            # O también podrías permitir enviar con Enter:
            msg.submit(fn=chatbot_interface, 
                    inputs=[msg, state], 
                    outputs=[chatbot, state])

# Ejecuta la interfaz localmente en http://localhost:7860/
if __name__ == "__main__":
    demo.launch()
