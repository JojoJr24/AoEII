# Tools Directory

This directory contains various tools that can be used to enhance the capabilities of the chat application. Each tool is a Python file that defines a `get_tool_description()` function and an `execute()` function.

## Tool Descriptions

### calculator.py
This tool performs basic arithmetic operations. It accepts a JSON object with the following format:
```json
{
    "operation": "add|subtract|multiply|divide",
    "a": number,
    "b": number
}
```
The tool will return the result of the operation.

### file_tool.py
This tool reads a file and returns its content if it is a text file, otherwise returns file information. It accepts a JSON object with the following format:
```json
{
    "tool_name": "file_tool",
    "parameters": {
        "file_path": "path/to/your/file.txt"
    }
}
```
The tool will return the content of the file or file information.

### folder_tool.py
This tool reads a folder and returns the content of all text files in it, or file information for non-text files or large files. It accepts a JSON object with the following format:
```json
{
    "tool_name": "folder_tool",
    "parameters": {
        "folder_path": "path/to/your/folder"
    }
}
```
The tool will return the content of the text files or file information for other files.

### remove_task_tool.py
This tool removes a cron job. It accepts a JSON object with the following format:
```json
{
    "tool_name": "remove_task_tool",
    "parameters": {
        "cron_line": "The full line of the cron job to remove"
    }
}
```
The tool will return a success or error message.

### searx_tool.py
This tool searches the web using SearxNG. It accepts a JSON object with the following format:
```json
{
    "tool_name": "searx_tool",
    "parameters": {
        "query": "your search query"
    }
}
```
The tool will return the search results in a simplified JSON format. Each result will contain 'title', 'url', and a short 'content' snippet (up to 150 characters).

### task_tool.py
This tool creates a cron job using Linux Crontab to execute a curl command to call the /api/generate_simple endpoint at a specified interval. It accepts a JSON object with the following format:
```json
{
    "tool_name": "task_tool",
    "parameters": {
        "prompt": "prompt to send to the /api/generate_simple endpoint",
        "interval": "cron interval (e.g., '0 0 * * *' for daily at midnight)"
    }
}
```
The tool will return a success or error message.

### webscraper_tool.py
This tool fetches the content of a given URL and extracts the text from the HTML. It accepts a JSON object with the following format:
```json
{
    "tool_name": "webscraper_tool",
    "parameters": {
        "url": "https://example.com"
    }
}
```
The tool will return the extracted text content, or an error message if the request fails.

## Adding New Tools

To add a new tool, create a new Python file in this directory. The file must contain:

-   A `get_tool_description()` function that returns a string describing the tool and its usage.
-   An `execute()` function that takes the tool's parameters as arguments and returns the result of the tool's execution.

Make sure to update this README.md file with the description of your new tool.
