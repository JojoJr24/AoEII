import requests
import os
import json
from datetime import date

def get_tool_description():
    today = date.today().strftime("%Y-%m-%d")
    return f"""
    This tool searches the web using SearxNG.
    It accepts a JSON object with the following format:
    {{
        "tool_name": "searx_tool",
        "parameters": {{
            "query": "your search query"
        }}
    }}

    The tool will return the search results in a simplified JSON format.
    Each result will contain 'title', 'url', and a short 'content' snippet (up to 150 characters).

    Note: 
    1)If the system does not know something due to it being after its last update, this tool will be used automatically to search for updated information. 
    2)For queries about news use the current date that is {today}
    """

def execute(query):
    """
    Searches the web using SearxNG and returns a simplified JSON.

    Args:
        query (str): The search query.

    Returns:
        str: A JSON string of simplified search results.
    """
    searx_domain = os.getenv("SEARXNG_DOMAIN")
    if not searx_domain:
        return "Error: SEARXNG_DOMAIN not set in environment variables."

    url = f"{searx_domain}/search?q={query}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        simplified_results = []
        for r in data.get("results", []):
            content = r.get("content", "")
            simplified_results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": content
            })
        return json.dumps(simplified_results, indent=4)

    except requests.exceptions.RequestException as e:
        return f"Error during search: {e}"

# Example usage (Ensure SEARXNG_DOMAIN is set in environment variables):
# os.environ["SEARXNG_DOMAIN"] = "https://your-searxng-domain.com"
# print(execute("your search query"))
