import requests
from bs4 import BeautifulSoup
import json

def get_tool_description():
    return """
    This tool fetches the content of a given URL and extracts the text from the HTML.
    It accepts a JSON object with the following format:
    {
        "tool_name": "webscraper_tool",
        "parameters": {
            "url": "https://example.com"
        }
    }
    
    The tool will return the extracted text content, or an error message if the request fails.
    """

def execute(url):
    """
    Fetches the content of a given URL and extracts the text from the HTML.

    Args:
        url (str): The URL to scrape.

    Returns:
        str: The extracted text content, or an error message if the request fails.
    """
    try:
        if isinstance(url, str):
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            return text
        elif isinstance(url, dict) and "url" in url:
            response = requests.get(url["url"], timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            return text
        else:
            return "Error: Invalid URL format."
    except requests.exceptions.RequestException as e:
        return f"Error al acceder a la URL: {e}"
    except Exception as e:
        return f"Error: {e}"
