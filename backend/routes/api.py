from flask import Blueprint, request, jsonify, Response
from llm import generate_response, generate_think_response, generate_simple_response, llm_providers, selected_model, selected_provider
from db import get_conversation, save_conversation, add_message_to_conversation, list_conversations, list_system_messages, get_system_message, save_system_message, delete_system_message, delete_all_system_messages, delete_conversation, delete_all_conversations, list_simple_responses, delete_simple_response, delete_all_simple_responses
from utils import debug_print, streaming, stop_stream_global
from tools import list_tools, list_all_modes
import json
from PIL import Image
import io

api_bp = Blueprint('api', __name__)

@api_bp.route('/models', methods=['GET'])
def list_models():
   debug_print(True, "Received request for /api/models")
   provider_name = request.args.get('provider', selected_provider)
   models = llm_providers.get(provider_name).list_models() if llm_providers.get(provider_name) else []
   return jsonify(models)

@api_bp.route('/generate', methods=['POST'])
def generate():
    debug_print(True, "Received request for /api/generate")
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
    selected_modes_str = data.get('selected_modes')
    base_url = data.get('base_url')

    if selected_modes_str:
        try:
            selected_modes = json.loads(selected_modes_str)
            debug_print(True, f"Selected modes: {selected_modes}")
        except json.JSONDecodeError:
            debug_print(True, "Error decoding selected modes")
            selected_modes = []
    else:
        selected_modes = []

    debug_print(True, f"Request: prompt='{prompt}', model='{model_name}', provider='{provider_name}', image={'present' if image_file else 'not present'}, history='{history_str}', system_message='{system_message}', conversation_id='{conversation_id}', selected_modes='{selected_modes}'")

    image = None
    if image_file:
        try:
            image = Image.open(io.BytesIO(image_file.read()))
            debug_print(True, "Image loaded successfully.")
        except Exception as e:
            debug_print(True, f"Error loading image: {e}")
            return jsonify({"response": f"Error al cargar la imagen: {e}"}), 400

    history = None
    if history_str:
        try:
            history = json.loads(history_str)
            debug_print(True, "Chat history loaded successfully.")
        except json.JSONDecodeError:
            debug_print(True, "Error decoding chat history")
            return jsonify({"response": "Error decoding chat history"}), 400

    if not prompt:
        debug_print(True, "Error: Prompt is required")
        return jsonify({"response": "Prompt is required"}), 400

    if conversation_id:
        conversation_id = int(conversation_id)
        conversation, messages = get_conversation(conversation_id)
        if conversation:
            system_message = conversation['system_message']
            history = []
            for message in messages:
                history.append({"role": message['role'], "content": message['content']})
            debug_print(True, f"Retrieved conversation {conversation_id} from database.")
        else:
            debug_print(True, f"Conversation {conversation_id} not found.")
            history = []
    else:
        conversation_title = data.get('conversation_title', '')
        if len(conversation_title) > 30:
            conversation_title = conversation_title[:30]
        conversation_id = save_conversation(provider_name, model_name, system_message, conversation_title)
        debug_print(True, f"Created new conversation with id {conversation_id}")

    add_message_to_conversation(conversation_id, "user", prompt)

    def stream_response():
        global streaming
        full_response = ""
        for chunk in generate_response(prompt, model_name, image, history, provider_name, system_message, selected_modes, base_url):
            if not streaming:
                debug_print(True, "Streaming stopped.")
                break
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"
        add_message_to_conversation(conversation_id, "model", full_response)

    return Response(stream_response(), mimetype='text/event-stream')

@api_bp.route('/generate_simple', methods=['POST'])
def generate_simple():
    debug_print(True, "Received request for /api/generate_simple")
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        debug_print(True, "Error: Prompt is required")
        return jsonify({"response": "Prompt is required"}), 400

    response = generate_simple_response(prompt)
    return jsonify({"response": response})

@api_bp.route('/simple_responses', methods=['GET'])
def list_simple_responses_route():
    debug_print(True, "Received request for /api/simple_responses")
    simple_responses = list_simple_responses()
    return jsonify(simple_responses)

@api_bp.route('/simple_responses/<int:simple_response_id>', methods=['DELETE'])
def delete_simple_response_route(simple_response_id):
    debug_print(True, f"Received request to DELETE /api/simple_responses/{simple_response_id}")
    delete_simple_response(simple_response_id)
    debug_print(True, f"Response: Simple response {simple_response_id} deleted")
    return jsonify({"message": f"Simple response {simple_response_id} deleted"})

@api_bp.route('/simple_responses', methods=['DELETE'])
def delete_all_simple_responses_route():
    debug_print(True, "Received request to DELETE all simple responses")
    delete_all_simple_responses()
    debug_print(True, "Response: All simple responses deleted")
    return jsonify({"message": "All simple responses deleted"})


@api_bp.route('/think', methods=['POST'])
def think_route():
    debug_print(True, "Received request for /api/think")
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

    debug_print(True, f"Request: prompt='{prompt}', model='{model_name}', provider='{provider_name}', depth='{depth}'")

    if not prompt:
        debug_print(True, "Error: Prompt is required")
        return jsonify({"response": "Prompt is required"}), 400

    def stream_response():
        global streaming
        full_response = ""
        for chunk in generate_think_response(prompt,  depth, model_name, provider_name):
            if not streaming:
                debug_print(True, "Streaming stopped.")
                break
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"

    return Response(stream_response(), mimetype='text/event-stream')

@api_bp.route('/conversations', methods=['GET'])
def list_conversations_route():
    debug_print(True, "Received request for /api/conversations")
    conversations = list_conversations()
    return jsonify(conversations)

@api_bp.route('/system_messages', methods=['GET'])
def list_system_messages_route():
    debug_print(True, "Received request for /api/system_messages")
    system_messages = list_system_messages()
    return jsonify(system_messages)

@api_bp.route('/system_messages/<int:system_message_id>', methods=['GET'])
def get_system_message_route(system_message_id):
    debug_print(True, f"Received request for /api/system_messages/{system_message_id}")
    system_message = get_system_message(system_message_id)
    if system_message:
        return jsonify(system_message)
    debug_print(True, f"Response: System message {system_message_id} not found")
    return jsonify({"message": "System message not found"}), 404

@api_bp.route('/system_messages/<int:system_message_id>', methods=['DELETE'])
def delete_system_message_route(system_message_id):
    debug_print(True, f"Received request to DELETE /api/system_messages/{system_message_id}")
    delete_system_message(system_message_id)
    debug_print(True, f"Response: System message {system_message_id} deleted")
    return jsonify({"message": f"System message {system_message_id} deleted"})

@api_bp.route('/system_messages', methods=['DELETE'])
def delete_all_system_messages_route():
    debug_print(True, "Received request to DELETE all system messages")
    delete_all_system_messages()
    debug_print(True, "Response: All system messages deleted")
    return jsonify({"message": "All system messages deleted"})

@api_bp.route('/tools', methods=['GET'])
def list_tools_route():
    debug_print(True, "Received request for /api/tools")
    tools = list_tools()
    return jsonify(tools)

@api_bp.route('/tool_modes', methods=['GET'])
def list_tool_modes_route():
    debug_print(True, "Received request for /api/tool_modes")
    modes = list_all_modes()
    return jsonify(modes)

@api_bp.route('/system_messages', methods=['POST'])
def save_system_message_route():
    debug_print(True, "Received request to POST /api/system_messages")
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    if not name or not content:
        debug_print(True, "Error: Name and content are required")
        return jsonify({"message": "Name and content are required"}), 400
    system_message_id = save_system_message(name, content)
    debug_print(True, f"Response: System message {system_message_id} saved")
    return jsonify({"message": f"System message {system_message_id} saved", "id": system_message_id})

@api_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation_route(conversation_id):
    debug_print(True, f"Received request for /api/conversations/{conversation_id}")
    conversation, messages = get_conversation(conversation_id)
    if conversation:
        return jsonify({"conversation": conversation, "messages": messages})
    debug_print(True, f"Response: Conversation {conversation_id} not found")
    return jsonify({"message": "Conversation not found"}), 404

@api_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation_route(conversation_id):
    debug_print(True, f"Received request to DELETE /api/conversations/{conversation_id}")
    delete_conversation(conversation_id)
    debug_print(True, f"Response: Conversation {conversation_id} deleted")
    return jsonify({"message": f"Conversation {conversation_id} deleted"})

@api_bp.route('/conversations', methods=['DELETE'])
def delete_all_conversations_route():
    debug_print(True, "Received request to DELETE all conversations")
    delete_all_conversations()
    debug_print(True, "Response: All conversations deleted")
    return jsonify({"message": "All conversations deleted"})

@api_bp.route('/stop', methods=['POST'])
def stop_stream_route():
    global streaming
    stop_stream_global()
    debug_print(True, "Received request to /api/stop")
    return jsonify({"message": "Streaming stopped"})

@api_bp.route('/edit_message', methods=['POST'])
def edit_message_route():
    debug_print(True, "Received request to POST /api/edit_message")
    data = request.get_json()
    message_id = data.get('message_id')
    edited_content = data.get('edited_content')

    if not message_id or not edited_content:
        debug_print(True, "Error: Message ID and edited content are required")
        return jsonify({"message": "Message ID and edited content are required"}), 400

    # Update the message in the database
    success = update_message(message_id, edited_content)

    if not success:
        debug_print(True, f"Error: Message {message_id} not found")
        return jsonify({"message": f"Message {message_id} not found"}), 404

    # Get the conversation ID
    conversation_id = get_conversation_id_from_message(message_id)

    # Get the conversation history
    conversation, messages = get_conversation(conversation_id)
    history = []
    for message in messages:
        history.append({"role": message['role'], "content": message['content']})

    # Generate the response
    def stream_response():
        global streaming
        full_response = ""
        for chunk in generate_response(edited_content, conversation['model'], None, history, conversation['provider'], conversation['system_message'], []):
            if not streaming:
                debug_print(True, "Streaming stopped.")
                break
            full_response += chunk
            yield f" {json.dumps({'response': chunk})}\n\n"

    return Response(stream_response(), mimetype='text/event-stream')
