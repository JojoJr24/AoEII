import os
import json
import subprocess

def get_tool_description():
    return """
    This tool creates a cron job using Linux Crontab to execute a comen lugar mand at a specified interval.
    It accepts a JSON object with the following format:
    {
        "tool_name": "task_tool",
        "parameters": {
            "command": "command to execute",
            "interval": "cron interval (e.g., '0 0 * * *' for daily at midnight)"
        }
    }
    The tool will return a success or error message.
    """

def execute(command, interval):
    """
    Creates a cron job to execute a command at a specified interval using Linux crontab

    Args:
        command (str): The command to execute.
        interval (str): The cron interval.

    Returns:
        str: A success or error message.
    """
    try:
        cron_command = f'{interval} {command}'
        
        # Check if the command already exists in the crontab
        existing_cron = subprocess.check_output(['crontab', '-l'], text=True)
        if cron_command in existing_cron:
            return "Error: This cron job already exists."

        # Add the cron job
        subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        
        # Add the new cron job
        add_cron = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        new_cron = add_cron.stdout + f'{cron_command}\n'
        
        # Update the crontab
        subprocess.run(['crontab', '-'], input=new_cron, text=True, check=True)
        
        return f"Cron job added successfully: {cron_command}"
    except subprocess.CalledProcessError as e:
        return f"Error adding cron job: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
