import os
from utils import BLUE, MAGENTA, debug_print
from claude_api import ClaudeAPI
from gemini_api import GeminiAPI
from ollama_api import OllamaAPI
from openai_api import OpenAIAPI
from groq_api import GroqAPI

# Initialize the Gemini API
gemini_api = GeminiAPI()
debug_print(BLUE, "Gemini API initialized.")

# Initialize the Ollama API
try:
    ollama_api = OllamaAPI()
    debug_print(BLUE, "Ollama API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing Ollama API: {e}")
    ollama_api = None

# Initialize the OpenAI API
try:
    openai_api = OpenAIAPI()
    debug_print(BLUE, "OpenAI API initialized.")
except Exception as e:
    try:
        openai_compatible_api = OpenAIAPI(base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL"))
        debug_print(BLUE, "OpenAI Compatible API initialized.")
    except Exception as e:
        debug_print(MAGENTA, f"Error initializing OpenAI API: {e}")
        openai_api = None
        openai_compatible_api = None
    else:
        openai_api = openai_compatible_api

# Initialize the Claude API
try:
    claude_api = ClaudeAPI()
    debug_print(BLUE, "Claude API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing Claude API: {e}")
    claude_api = None

# Initialize the Groq API
groq_api = None
try:
    groq_api = GroqAPI()
    debug_print(BLUE, "Groq API initialized.")
except Exception as e:
    debug_print(MAGENTA, f"Error initializing Groq API: {e}")
    groq_api = None

# Dictionary to hold available LLM providers
llm_providers = {
    "gemini": gemini_api,
}

if ollama_api:
    llm_providers["ollama"] = ollama_api
else:
    debug_print(True, "Ollama API not available, setting empty model list.")

if openai_api:
    llm_providers["openai"] = openai_api
    llm_providers["openai_compatible"] = openai_api
else:
    debug_print(True, "OpenAI API not available, setting empty model list.")

if claude_api:
    llm_providers["claude"] = claude_api
else:
    debug_print(True, "Claude API not available, setting empty model list.")

if groq_api:
    llm_providers["groq"] = groq_api
else:
    debug_print(True, "Groq API not available, setting empty model list.")

# Default LLM provider and model
selected_provider = "gemini"
selected_model = "gemini-1.5-flash"