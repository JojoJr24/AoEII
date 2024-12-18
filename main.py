import gradio as gr

# Función ficticia que emula la generación de respuestas de un LLM.
# Aquí deberías integrar tu modelo, por ejemplo:
#  - Una llamada a una API (OpenAI, etc.)
#  - Un modelo local (transformers, llama.cpp, etc.)
def generate_response(prompt):
    # Ejemplo simplificado: el modelo repite la entrada con un prefijo
    # Reemplaza esta lógica con tu propio pipeline de inferencia.
    return f"Respuesta del modelo: {prompt}"

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
