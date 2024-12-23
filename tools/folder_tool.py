import os
import json

def get_tool_description():
    return """
    This tool reads a folder and returns the content of all text files in it, or file information for non-text files or large files.
    It accepts a JSON object with the following format:
    {
        "tool_name": "folder_tool",
        "parameters": {
            "folder_path": "path/to/your/folder"
        }
    }
    
    The tool will return the content of the text files or file information for other files.
    """

def execute(folder_path):
    """
    Reads a folder and returns the content of all text files in it, or file information for non-text files or large files.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        str: The content of the text files or file information for other files.
    """
    try:
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return f"Error: Folder not found at path: {folder_path}"
        
        contents = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 60 * 1024:  # 60KB limit
                    contents.append(f"File information: \n- Path: {file_path}\n- Size: {file_size} bytes\n- File is larger than 60KB.")
                else:
                    try:
                        with open(file_path, 'r') as file:
                            contents.append(f"File: {filename}\nContent:\n{file.read()}")
                    except UnicodeDecodeError:
                        contents.append(f"File information: \n- Path: {file_path}\n- Size: {file_size} bytes\n- File is not a valid text file.")
            
        if not contents:
             return f"No files found in folder: {folder_path}"
        return "\n\n".join(contents)
    except Exception as e:
        return f"Error reading folder: {e}"
