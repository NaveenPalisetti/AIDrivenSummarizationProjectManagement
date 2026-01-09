from mcp.protocols.a2a import a2a_endpoint
from mcp.agents.task_manager_agent import TaskManagerAgent

class JiraAgent:
    def __init__(self):
        self.task_manager = TaskManagerAgent()

    @a2a_endpoint
    def create_jira(self, summary, user=None, date=None):
        """
        Create Jira issues from a meeting summary using TaskManagerAgent logic.
        summary: can be a string or dict (expects dict with 'action_items' or 'summary_text')
        user, date: optional, for logging or assignment
        Returns: list of created tasks (with Jira keys if successful)
        """
        meeting_id = date or "meeting"
        # If summary is a string, wrap as dict
        if isinstance(summary, str):
            summary = {"summary_text": summary}
        tasks = self.task_manager.extract_and_create_tasks(meeting_id, summary)
        return {"created_tasks": tasks, "user": user, "date": date}
