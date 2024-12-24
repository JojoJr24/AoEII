# AoEII - Minimalist Chat with Tools

This project, named AoEII, is a minimalist chat application designed for users who want a simple, subscription-free, and customizable solution. It allows you to interact with various Large Language Models (LLMs) and augment their capabilities with custom tools.

## Key Features

-   **Simplicity:** A clean and intuitive user interface, free from unnecessary distractions.
-   **Integrated Tools:** Ability to use custom tools to enhance interactions with LLMs.
-   **No Subscriptions:** Completely free and open-source, with no need to pay for usage.
-   **Privacy:** Data is stored locally, giving you more control over your information.
-   **Customizable:** Easily add new tools and features to suit your specific needs.
-   **Multiple LLM Providers:** Supports Gemini, Ollama, OpenAI, Claude and Groq.
-   **Chat History:** Saves chat history for each conversation.
-   **System Messages:** Allows saving and using system messages.
-   **Dark Mode:** Supports dark mode for comfortable usage in low-light environments.
-   **Image Upload:** Allows uploading images to include in the prompt.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    ```
2.  Navigate to the project directory:
    ```bash
    cd <project_name>
    ```
3.  Install the backend dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  Set up the environment variables:
    - Create a `.env` file in the `backend` directory.
    - Add your API keys for the LLM providers you want to use:
        ```
        GEMINI_API_KEY=<your_gemini_api_key>
        OLLAMA_API_KEY=<your_ollama_api_key>
        OPENAI_API_KEY=<your_openai_api_key>
        ANTHROPIC_API_KEY=<your_anthropic_api_key>
        GROQ_API_KEY=<your_groq_api_key>
        ```
5.  Run the backend application:
    ```bash
    python backend/main.py
    ```
6.  Open the `frontend/index.html` file in your web browser.

## Usage

1.  Select the desired LLM provider (Gemini, Ollama, OpenAI, Claude or Groq) from the sidebar.
2.  Enter the model name you want to use.
3.  Type your message in the input field and press "Send".
4.  Use the available tools by dragging them to the active tools area.
5.  Upload images using the upload button.
6.  Use the dark mode toggle for a better experience in low-light environments.
7.  Save and load system messages for different use cases.
8.  Manage your conversations using the conversation list.

## Contributing

Contributions are welcome! If you want to improve the project, please create a pull request with your changes.

## License

This project is licensed under the MIT License.
