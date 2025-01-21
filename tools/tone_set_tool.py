import sys
import os
import subprocess
import json

def get_tool_description():
    return """
    This tool sets a tone with the specified frequency.
    It accepts a JSON object with the following format:
    {
        "tool_name": "tone_set_tool",
        "parameters": {
            "frequency": "frequency in Hz"
        }
    }
    """

def execute(frequency):
    """Starts the tone server with the given frequency."""
    
    # Start the server if it's not running
    try:
        command = f"{frequency}"
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), './microapps', 'tone_micro_app.py'), command])
        return f"Tone started with Frequency={frequency}."
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
