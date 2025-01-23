import os
import importlib.util
from utils import debug_print

def list_tools():
    tools_dir = '../tools'
    tools = []
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            file_path = os.path.join(tools_dir, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'get_tool_description'):
                    tools.append({
                        'name': module_name,
                        'description': module.get_tool_description(),
                        'modes': module.modes if hasattr(module, 'modes') else []
                    })
            except Exception as e:
                debug_print(True, f"Error loading tool {module_name}: {e}")
    return tools

def list_tools_by_mode(mode):
    """
    Lists tools that belong to a specific mode.

    Args:
        mode (str): The mode to filter by.

    Returns:
        list: A list of tool names that belong to the specified mode.
    """
    tools = list_tools()
    return [tool['name'] for tool in tools if mode in tool.get('modes', [])]

def list_all_modes():
    """
    Lists all unique modes available in the tools.

    Returns:
        list: A list of unique modes.
    """
    tools = list_tools()
    modes = set()
    for tool in tools:
        modes.update(tool.get('modes', []))
    return list(modes)
