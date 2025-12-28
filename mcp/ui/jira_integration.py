"""
Jira integration logic for MCP Streamlit App
"""
from mcp.agents.task_manager_agent import TaskManagerAgent

def create_jira_tasks(meeting_id, action_items):
    task_manager = TaskManagerAgent()
    tasks = task_manager.extract_and_create_tasks(meeting_id, {"action_items": action_items})
    return tasks
