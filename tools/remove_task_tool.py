import subprocess
import json

def get_tool_description():
    try:
        existing_cron = subprocess.check_output(['crontab', '-l'], text=True)
        cron_list = existing_cron.strip().split('\n')
    except subprocess.CalledProcessError:
        cron_list = []
    
    cron_jobs = "\n".join([f"- {job}" for job in cron_list]) if cron_list else "No cron jobs found."

    return f"""
    This tool removes a cron job.
    It accepts a JSON object with the following format:
    {{
        "tool_name": "remove_task_tool",
        "parameters": {{
            "cron_line": "The full line of the cron job to remove"
        }}
    }}
    
    Current cron jobs:
    {cron_jobs}
    
    The tool will return a success or error message.
    """
modes = ["developer"]

def execute(cron_line):
    """
    Removes a cron job.

    Args:
        cron_line (str): The full line of the cron job to remove.

    Returns:
        str: A success or error message.
    """
    try:
        # Get current crontab
        existing_cron = subprocess.check_output(['crontab', '-l'], text=True)
        
        # Check if the cron job exists
        if cron_line not in existing_cron:
            return "Error: Cron job not found."
        
        # Remove the cron job
        new_cron = existing_cron.replace(f'{cron_line}\n', '')
        subprocess.run(['crontab', '-'], input=new_cron, text=True, check=True)
        
        return f"Cron job removed successfully: {cron_line}"
    except subprocess.CalledProcessError as e:
        return f"Error removing cron job: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
