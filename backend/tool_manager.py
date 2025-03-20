import os
import json
import importlib.util
from utils import BLUE, MAGENTA, GREEN, debug_print

def load_tools(selected_modes):
    """
    Load tool modules and validate their structure.

    Args:
        selected_modes (list): List of tool modes to load.

    Returns:
        list: List of tool instances with execute and description methods.
    """
    tools_dir = '../tools'
    tool_instances = []
    from tools import list_tools_by_mode
    for mode in selected_modes:
        tool_names = list_tools_by_mode(mode)
        for tool_name in tool_names:
            try:
                file_path = os.path.join(tools_dir, f'{tool_name}.py')
                spec = importlib.util.spec_from_file_location(tool_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'execute') and hasattr(module, 'get_tool_description'):
                    tool_instances.append({
                            'name': tool_name,
                            'description': module.get_tool_description(),
                            'execute': module.execute
                        })
                else:
                    debug_print(MAGENTA, f"Error: Tool {tool_name} lacks required methods.")
            except Exception as e:
                debug_print(MAGENTA, f"Error loading tool {tool_name}: {e}")

    return tool_instances

def generate_tool_descriptions(tool_instances):
    """
    Generate a formatted string of tool descriptions for use in prompts.

    Args:
        tool_instances (list): List of tool instances.

    Returns:
        str: Formatted tool descriptions.
    """
    return "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tool_instances])

def parse_tool_calls(tool_response):
    """
    Parse tool calls from the LLM's response.

    Args:
        tool_response (str): The raw response from the LLM containing tool calls.

    Returns:
        list: List of parsed tool calls.
    """
    start_index = tool_response.find('[')
    end_index = tool_response.rfind(']')

    if start_index == -1 or end_index == -1:
        raise json.JSONDecodeError("No tool calls found", tool_response, 0)

    json_string = tool_response[start_index:end_index + 1]
    return json.loads(json_string)

def execute_tools(tool_calls, tool_instances):
    """
    Execute the specified tools and collect results.

    Args:
        tool_calls (list): List of tool calls to execute.
        tool_instances (list): List of available tool instances.

    Returns:
        list: Results of executed tools.
    """
    results = []

    for call in tool_calls:
        tool_name = call.get('tool_name')
        params = call.get('parameters', {})
        tool = next((t for t in tool_instances if t['name'] == tool_name), None)

        if tool:
            try:
                debug_print(BLUE, f"Executing tool: {tool_name} with params: {params}")
                result = tool['execute'](**params)
                debug_print(GREEN, f"Tool result: {result}")
                results.append({"tool_name": tool_name, "tool_params": params, "tool_result": result})
            except Exception as e:
                debug_print(MAGENTA, f"Error executing tool {tool_name}: {e}")
                results.append({"tool_name": tool_name, "error": str(e)})
        else:
            debug_print(MAGENTA, f"Error: Tool {tool_name} not found.")
            results.append({"tool_name": tool_name, "error": "Tool not found"})

    return results