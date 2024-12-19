import os
import mimetypes

def get_tool_description():
    return "This tool reads a file and returns its content if it is a text file, otherwise returns file information."

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
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text/'):
            with open(file_path, 'r') as file:
                return file.read()
        else:
            file_size = os.path.getsize(file_path)
            return f"File information: \n- Path: {file_path}\n- Size: {file_size} bytes\n- Mime Type: {mime_type}"
    except Exception as e:
        return f"Error reading file: {e}"
