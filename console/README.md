# Console Application Usage

This document provides instructions on how to use the console application.

## Running the Application

To run the console application, execute the `console.py` script. Make sure you have the required dependencies installed (listed in `requirements.txt`).

```bash
python console/console.py
```

## Basic Interaction

-   **Input:** Type your message in the input area at the bottom of the screen and press `Enter` to send.
-   **Chat History:** The chat history is displayed above the input area. User messages are prefixed with "User:", and LLM responses are prefixed with "LLM:".
-   **Navigation:** Use the `Up` and `Down` arrow keys to navigate through the menu options.
-   **Menu:** Press `Insert` to open the menu. Use numbers to select an option, and `Enter` to confirm.
-   **Exit:** Press `Esc` to exit the application.

## Menu Options

The menu provides the following options:

1.  **Provider:** Select the LLM provider (e.g., Gemini, Ollama, OpenAI, Claude, Groq).
2.  **Model:** Select the model to use for the selected provider.
3.  **Conversations:** Select a previous conversation to load.
4.  **System Message:** Select a system message to use.
5.  **Tools:** Select tools to use with the LLM.
6.  **Think Mode:** Toggle think mode on or off.
7.  **Think Depth:** Set the depth of the think mode.
8.  **Reset:** Clear the current chat history.
9.  **Stop:** Stop the current streaming response.

## Configuration

The application loads and saves its configuration in `config.json`. This file stores the selected provider, model, conversation, system message, tools, think mode, think depth, and OpenAI base URL.

## Notes

-   The application uses the `requests` library to communicate with the backend API.
-   The application uses the `curses` library for terminal UI.
-   The application supports streaming responses from the backend.
-   The application supports saving and loading conversations.
-   The application supports system messages and tools.
-   The application supports think mode for more complex reasoning.
-   The application supports setting the think depth for think mode.
-   The application supports OpenAI base URL for custom OpenAI endpoints.
-   The application saves the conversation title as the first message sent.
-   The application displays tokens per second for the last response.
-   The application supports stopping the current streaming response.