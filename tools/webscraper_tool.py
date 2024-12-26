import requests
from bs4 import BeautifulSoup

def execute(url):
    """
    Fetches the content of a given URL and extracts the text from the HTML.

    Args:
        url (str): The URL to scrape.

    Returns:
        str: The extracted text content, or an error message if the request fails.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text
    except requests.exceptions.RequestException as e:
        return f"Error al acceder a la URL: {e}"

def get_tool_description():
    return {
        "name": "web_scraper",
        "description": "Extrae el texto de una página web dada una URL."
    }
