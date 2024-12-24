import logging
import sys

# ANSI escape codes for colors
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

DEBUG = True
streaming = True

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

def debug_print(debug, message):
    if DEBUG and debug:
        print(f"{BLUE}{message}{RESET}")

def stop_stream_global():
    global streaming
    streaming = False
