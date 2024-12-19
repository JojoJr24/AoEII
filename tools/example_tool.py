s def execute(*args):
    """
    This is an example tool that takes a variable number of arguments and returns a string.
    """
    return f"Tool executed with arguments: {args}"

def get_tool_description():
    return """
    This is an example tool that takes a variable number of arguments and returns a string.
    """
