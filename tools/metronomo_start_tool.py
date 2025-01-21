import socket
import sys
import os

SOCKET_PATH = '/tmp/metronomo.sock'

def get_tool_description():
    return {
        "name": "start_metronome",
        "description": "Starts the metronome with the specified tempo and time signature.",
        "parameters": [
            {
                "name": "tempo",
                "type": "integer",
                "description": "The tempo of the metronome in BPM."
            },
            {
                "name": "compas",
                "type": "integer",
                "description": "The time signature of the metronome (number of beats per measure)."
            }
        ]
    }

def execute(tempo, compas):
    """Starts the metronome server with the given tempo and time signature."""
    
    # Check if the server is already running
    server_running = False
    try:
        client_test = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_test.connect(SOCKET_PATH)
        server_running = True
        client_test.close()
    except socket.error:
        server_running = False

    if server_running:
        return "Metronome server is already running. Use the update command to change tempo or time signature."
    
    # Start the server if it's not running
    try:
        if compas not in [2, 3, 4, 5, 6, 7, 8]:
            raise ValueError("The time signature must be a number between 2 and 8.")
        
        command = f"{tempo},{compas}"
        
        # Start the server in a new process
        pid = os.fork()
        if pid == 0:
            # Child process
            os.execl(sys.executable, sys.executable, os.path.join(os.path.dirname(__file__), '..', 'metronomo_ejemplo.py'), command)
        else:
            # Parent process
            return f"Metronome started with Tempo={tempo}, Compás={compas}."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
