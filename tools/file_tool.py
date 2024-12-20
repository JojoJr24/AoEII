import os
import json

def get_tool_description():
    return """
    This tool reads a file and returns its content if it is a text file, otherwise returns file information.
    It accepts a JSON object with the following format:
    {
        "tool_name": "file_tool",
        "parameters": {
            "file_path": "path/to/your/file.txt"
        }
    }
    
    The tool will return the content of the file or file information.
    """

def execute(file_path):
    """
    Reads a file and returns its content if it is a text file, otherwise returns file information.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file if it is a text file, otherwise file information.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at path: {file_path}"
        
        file_size = os.path.getsize(file_path)
        if file_size > 60 * 1024:  # 20KB limit
            return f"File information: \n- Path: {file_path}\n- Size: {file_size} bytes\n- File is larger than 20KB."
        
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except UnicodeDecodeError:
            return f"File information: \n- Path: {file_path}\n- Size: {file_size} bytes\n- File is not a valid text file."
    except Exception as e:
        return f"Error reading file: {e}"
