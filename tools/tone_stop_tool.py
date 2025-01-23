import socket

SOCKET_PATH = '/tmp/tone.sock'

import json

def get_tool_description():
    return """
    This tool stops the running tone server.
    It accepts a JSON object with the following format:
    {
        "tool_name": "tone_stop_tool"
    }
    """
modes = ["music"]

def execute():
    """Sends a command to stop the tone server."""
    try:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(SOCKET_PATH)
        client_sock.sendall("CERRAR".encode('utf-8'))
        response = client_sock.recv(1024).decode('utf-8')
        client_sock.close()
        return "Tone server stopped."
    except socket.error:
        return "Tone server is not running."
    except Exception as e:
        return f"An unexpected error occurred: {e}"
