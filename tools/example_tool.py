def execute(operation, a, b):
    """
    This tool performs a calculation based on the provided operation and numbers.
    """
    try:
        a = float(a)
        b = float(b)
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                return "Cannot divide by zero"
            return a / b
        else:
            return "Invalid operation"
    except ValueError:
        return "Invalid input: 'a' and 'b' must be numbers"


def get_tool_description():
    return """
    This is a calculator tool that performs basic arithmetic operations.
    It accepts a JSON object with the following format:
    {
        "operation": "add|subtract|multiply|divide",
        "a": number,
        "b": number
    }
    
    The tool will return the result of the operation.
    """
