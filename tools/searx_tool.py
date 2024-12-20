import requests
import os
import json

def get_tool_description():
    return """
    This tool searches the web using SearxNG.
    It accepts a JSON object with the following format:
    {
        "tool_name": "searx_tool",
        "parameters": {
            "query": "your search query"
        }
    }
    
    The tool will return the search results in JSON format.
    """

def execute(query):
    """
    Searches the web using SearxNG.

    Args:
        query (str): The search query.

    Returns:
        str: The search results in JSON format.
    """
    searx_domain = os.getenv("SEARXNG_DOMAIN")
    if not searx_domain:
        return "Error: SEARXNG_DOMAIN not set in environment variables."
    
    url = f"{searx_domain}/search?q={query}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return json.dumps(response.json(), indent=4)
    except requests.exceptions.RequestException as e:
        return f"Error during search: {e}"
