# Voice Interface Usage

This document provides instructions on how to use the voice interface.

## Running the Application

To run the voice interface, execute the `voice.py` script. Make sure you have the required dependencies installed (listed in `requirements.txt`).

```bash
python voice/voice.py
```

## Basic Interaction

-   **Activation:** Say "activar <prompt>" to set the prompt. A beep sound will indicate the prompt has been loaded.
-   **Execution:** Say "ejecutar" to send the loaded prompt to the backend.
-   **Continuous Mode:** Use the `--continuous` flag to enable continuous listening.

## Configuration

The application loads its configuration from `config.json`. This file stores the selected provider, model, tools, think mode, think depth, and OpenAI base URL.

## Notes

-   The application uses the `requests` library to communicate with the backend API.
-   The application uses the `voice_input.py` for voice recording and transcription.
-   The application supports streaming responses from the backend.
-   The application supports think mode for more complex reasoning.
-   The application supports setting the think depth for think mode.
-   The application supports OpenAI base URL for custom OpenAI endpoints.
-   The application clears the prompt after sending it.
-   The application prints the full response to the console.
-   The application prints errors to the console.
-   The application uses a beep sound to indicate the prompt has been loaded.
-   The application uses the same config.json as the console app.
-   The application supports continuous listening mode.
-   The application uses the same voice_input.py as the console app.
