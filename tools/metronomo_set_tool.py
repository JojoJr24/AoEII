import sys
import os
import subprocess

def get_tool_description():
    return """
    This tool set the metronome with the specified tempo and time signature.
    It accepts a JSON object with the following format:
    {
        "tool_name": "metronomo_set_tool",
        "parameters": {
            "tempo": "tempo in BPM",
            "compas": a number from 2 to 8 
        }
    }
    """
modes = ["music"]

def execute(tempo, compas):
    """Starts the metronome server with the given tempo and time signature."""
    
    # Start the server if it's not running
    try:
        if compas not in [2, 3, 4, 5, 6, 7, 8]:
            raise ValueError("The time signature must be a number between 2 and 8.")
        command = f"{tempo},{compas}"
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), './microapps', 'metronomo_micro_app.py'), command])
        return f"Metronome started with Tempo={tempo}, Compás={compas}."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
