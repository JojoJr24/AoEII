import socket

SOCKET_PATH = '/tmp/metronomo.sock'

import json

def get_tool_description():
    return """
    This tool stops the running metronome server.
    It accepts a JSON object with the following format:
    {
        "tool_name": "metronomo_stop_tool"
    }
    """

def execute(params):
    """Sends a command to stop the metronome server."""
    try:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(SOCKET_PATH)
        client_sock.sendall("CERRAR".encode('utf-8'))
        response = client_sock.recv(1024).decode('utf-8')
        client_sock.close()
        return "Metronome server stopped."
    except socket.error:
        return "Metronome server is not running."
    except Exception as e:
        return f"An unexpected error occurred: {e}"
