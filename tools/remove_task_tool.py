import subprocess
import json

def get_tool_description():
    return """
    This tool removes a cron job created by the task_tool.
    It accepts a JSON object with the following format:
    {
        "tool_name": "remove_task_tool",
        "parameters": {
            "prompt": "prompt used to create the task",
            "interval": "cron interval used to create the task (e.g., '0 0 * * *')"
        }
    }
    The tool will return a success or error message.
    """

def execute(prompt, interval):
    """
    Removes a cron job created by the task_tool.

    Args:
        prompt (str): The prompt used to create the task.
        interval (str): The cron interval used to create the task.

    Returns:
        str: A success or error message.
    """
    try:
        curl_command = f'curl -X POST http://127.0.0.1:5000/api/generate_simple -H "Content-Type: application/json" -d \'{{ "prompt": "{prompt}" }}\''
        cron_command = f'{interval} {curl_command}'

        # Get current crontab
        existing_cron = subprocess.check_output(['crontab', '-l'], text=True)
        
        # Check if the cron job exists
        if cron_command not in existing_cron:
            return "Error: Cron job not found."
        
        # Remove the cron job
        new_cron = existing_cron.replace(f'{cron_command}\n', '')
        subprocess.run(['crontab', '-'], input=new_cron, text=True, check=True)
        
        return f"Cron job removed successfully: {cron_command}"
    except subprocess.CalledProcessError as e:
        return f"Error removing cron job: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
