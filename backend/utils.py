import logging
import sys
import time
from functools import wraps

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

DEBUG = True
streaming = True
STREAM_START_DELAY = 0.1
STREAM_YIELD_DELAY = 0.01

def setup_logging(app):
   """Configures the logging for the Flask app."""
   log_level = logging.DEBUG if app.debug else logging.INFO
   
   # Create a logger for the application
   logger = logging.getLogger(__name__)
   logger.setLevel(log_level)

   # Create a handler to print log messages to the console
   stream_handler = logging.StreamHandler(sys.stdout)
   stream_handler.setLevel(log_level)

   # Define a format for log messages
   formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
   stream_handler.setFormatter(formatter)

   # Add the handler to the logger
   logger.addHandler(stream_handler)

   app.logger = logger

import inspect

def debug_print(debug, message):
    if DEBUG and debug:
        caller_frame = inspect.currentframe().f_back
        caller_function = caller_frame.f_code.co_name
        print(f"{BLUE}[{caller_function}] {message}{RESET}")

def stop_stream_global():
    global streaming
    streaming = False

def retry_with_exponential_backoff(max_retries=3, base_delay=1):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries (int): Maximum number of retries.
        base_delay (int): Base delay in seconds.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e):
                        delay = base_delay * (2 ** retries)
                        debug_print(True, f"Rate limit hit. Retrying in {delay} seconds... (Attempt {retries + 1}/{max_retries + 1})")
                        time.sleep(delay)
                        retries += 1
                    else:
                        raise
            debug_print(True, f"Max retries exceeded for function {func.__name__}")
            raise Exception(f"Max retries exceeded after {max_retries} attempts.")
        return wrapper
    return decorator
