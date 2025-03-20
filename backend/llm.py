from typing import Generator
from think import Think
from utils import BLUE, GREEN, debug_print
from providers import llm_providers, selected_model, selected_provider
from response_generator import generate_response, generate_simple_response

# Initialize Think class
think_instance = Think()

def think(prompt: str, depth: int, selected_model=None, selected_provider=None) -> Generator[str, None, None]:
    """
    Invokes the generate_response method from the Think class and returns the response.
    """
    print(f"Thinking with prompt: {prompt}, depth: {depth}, model: {selected_model}, provider: {selected_provider}")
    
    for chunk in think_instance.generate_response(
        prompt=prompt,
        model_name=selected_model,
        provider=selected_provider,
        depth=depth
    ):
        yield chunk

def generate_think_response(prompt, depth, model_name=None, provider_name=None):
    if not model_name:
        model_name = selected_model
    if not provider_name:
        provider_name = selected_provider
    debug_print(BLUE, f"Generating think response with model: {model_name}, provider: {provider_name}, depth: {depth}")
    
    response = think(prompt, depth, selected_model=model_name, selected_provider=provider_name)
    debug_print(GREEN, f"Think response generated successfully.")
    return response

# Export all necessary functions and variables
__all__ = [
    'llm_providers',
    'selected_model',
    'selected_provider',
    'generate_response',
    'generate_simple_response',
    'generate_think_response',
    'think'
]
