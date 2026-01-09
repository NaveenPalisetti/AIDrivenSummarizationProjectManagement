

from mcp.core.utils import gen_id
import os, json
from mcp.tools.llm_task_extraction import extract_tasks_jira_format
import re
from datetime import datetime


# Try to load credentials from Google Drive path first, then local folder
import pathlib
drive_cred_path = pathlib.Path('/content/drive/MyDrive/credentials.json')
local_cred_path = pathlib.Path('mcp/config/credentials.json')

if drive_cred_path.exists():
    print(f"[INFO] Loading credentials from Google Drive: {drive_cred_path}")
    with open(drive_cred_path, 'r') as f:
        creds = json.load(f)
elif local_cred_path.exists():
    print(f"[INFO] Loading credentials from local folder: {local_cred_path}")
    with open(local_cred_path, 'r') as f:
        creds = json.load(f)
else:
    print("[ERROR] No credentials.json found in Google Drive or local folder.")
    raise FileNotFoundError("No credentials.json found in Google Drive or local folder.")
jira = creds.get("jira", {})
print(f"[DEBUG] Loaded Jira credentials: {jira}")

os.environ["JIRA_URL"] = jira.get("base_url", "")
os.environ["JIRA_USER"] = jira.get("user", "")
os.environ["JIRA_TOKEN"] = jira.get("token", "")
os.environ["JIRA_PROJECT"] = jira.get("project", "PROJ")
try:
    from jira import JIRA
except ImportError:
    JIRA = None

import re
from datetime import datetime

def clean_due_date(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    # Try to match YYYY-MM-DD
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str
    # Try to parse common formats (e.g., '14 Dec 2025')
    for fmt in ("%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

class LLMTaskManagerAgent:

    def create_jira_tasks_from_list(self, tasks, meeting_id=None):
        """
        Create Jira issues from a list of task dicts, trigger notifications, and return result.
        Args:
            tasks: list of dicts (each with at least 'title', optionally 'owner', 'due', 'description')
            meeting_id: meeting/session identifier (optional)
        Returns:
            dict: {'created': [issue_keys], 'errors': [error_msgs]}
        """
        from mcp.tools.notification import send_notification
        from mcp.tools.jira_monitor import notify_due_tasks, notify_sprints_ending_soon
        created = []
        errors = []
        MAX_SUMMARY_LEN = 255
        # Load existing tasks file
        with open(self.tasks_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        for t in tasks:
            title = t.get('title') or t.get('Summary') or t.get('task') or str(t)
            owner = t.get('owner') or t.get('assignee') or t.get('Assignee')
            due = t.get('due') or t.get('due_date') or t.get('Due Date') or t.get('deadline')
            description = t.get('description') or t.get('Description') or f"Auto-created from meeting {meeting_id}"
            jira_title = title.replace('\n', ' ').replace('\r', ' ')[:MAX_SUMMARY_LEN]
            # Save to local file
            task_obj = {
                'id': gen_id('task'),
                'meeting_id': meeting_id,
                'title': title,
                'owner': owner,
                'status': 'open',
                'description': description,
                'due': due
            }
            existing.append(task_obj)
            # --- JIRA Integration ---
            if self.jira:
                issue_dict = {
                    'project': {'key': self.jira_project},
                    'summary': jira_title,
                    'description': description,
                    'issuetype': {'name': 'Task'},
                }
                if owner:
                    issue_dict['assignee'] = {'name': owner}
                if due:
                    issue_dict['duedate'] = due
                try:
                    issue = self.jira.create_issue(fields=issue_dict)
                    task_obj['jira_issue'] = issue.key
                    created.append(issue.key)
                    # Notify if due date is within 2 days
                    from datetime import datetime, timedelta
                    if due:
                        try:
                            due_dt = datetime.strptime(due[:10], '%Y-%m-%d')
                            if due_dt - datetime.utcnow() <= timedelta(days=2):
                                send_notification(f"Jira Task '{jira_title}' is due soon: {due}")
                        except Exception as e:
                            errors.append(f"Error parsing due date for notification: {e}")
                except Exception as e:
                    task_obj['jira_error'] = str(e)
                    errors.append(str(e))
            else:
                task_obj['jira_error'] = "Jira connection not configured."
                errors.append("Jira connection not configured.")
        # Save updated tasks file
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)
        # After creating tasks, trigger due/sprint notifications
        try:
            notify_due_tasks(days=2)
            notify_sprints_ending_soon(days=2)
        except Exception as e:
            errors.append(f"Notification error: {e}")
        return {'created': created, 'errors': errors}
        return {'created': created, 'errors': errors}

    def __init__(self):
        self.tasks_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'tasks', 'llm_tasks.json')
        os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        self.jira_url = os.environ.get("JIRA_URL")
        self.jira_user = os.environ.get("JIRA_USER")
        self.jira_token = os.environ.get("JIRA_TOKEN")
        self.jira_project = os.environ.get("JIRA_PROJECT")
        self.jira = None
        print(f"LLMTaskManagerAgent: JIRA_URL={self.jira_url}, JIRA_USER={self.jira_user}, JIRA_PROJECT={self.jira_project}")
        if not JIRA:
            print("[ERROR][LLMTaskManagerAgent] Jira package not imported (JIRA is None)")
        if not self.jira_url:
            print("[ERROR][LLMTaskManagerAgent] JIRA_URL is missing or empty")
        if not self.jira_user:
            print("[ERROR][LLMTaskManagerAgent] JIRA_USER is missing or empty")
        if not self.jira_token:
            print("[ERROR][LLMTaskManagerAgent] JIRA_TOKEN is missing or empty")
        if not self.jira_project:
            print("[ERROR][LLMTaskManagerAgent] JIRA_PROJECT is missing or empty")
        if JIRA and self.jira_url and self.jira_user and self.jira_token:
            print("LLMTaskManagerAgent: Initializing JIRA connection")
            try:
                self.jira = JIRA(server=self.jira_url, basic_auth=(self.jira_user, self.jira_token))
                print("LLMTaskManagerAgent:  ", self.jira)
            except Exception as e:
                print(f"[ERROR][LLMTaskManagerAgent] Failed to initialize JIRA connection: {e}")
                self.jira = None


    def extract_tasks_from_transcript_llm(self, meeting_id: str, transcript: str):
        """
        Extract tasks from transcript using LLM (Jira format) and create tasks/Jira issues.
        """
        jira_text = extract_tasks_jira_format(transcript)
        tasks = self._parse_jira_formatted_tasks(jira_text, meeting_id)
        with open(self.tasks_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        for t in tasks:
            # Clean due date before sending to Jira
            if 'due' in t:
                t['due'] = clean_due_date(t['due'])
            existing.append(t)
            if self.jira:
                issue_dict = {
                    'project': {'key': self.jira_project},
                    'summary': t['title'][:255],
                    'description': t.get('description', f"Auto-created from meeting {meeting_id}"),
                    'issuetype': {'name': 'Task'},
                }
                if t.get('owner'):
                    issue_dict['assignee'] = {'name': t['owner']}
                if t.get('due'):
                    issue_dict['duedate'] = t['due']
                try:
                    print(f"[DEBUG][LLMTaskManagerAgent] Creating Jira issue with fields: {issue_dict}")
                    issue = self.jira.create_issue(fields=issue_dict)
                    print(f"[DEBUG][LLMTaskManagerAgent] Created Jira issue: {issue.key}")
                    t['jira_issue'] = issue.key
                except Exception as e:
                    print(f"[ERROR][LLMTaskManagerAgent] Jira issue creation failed: {e}")
                    t['jira_error'] = str(e)
            else:
                print("[ERROR][LLMTaskManagerAgent] JIRA not configured")
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)
        return tasks

    def _parse_jira_formatted_tasks(self, jira_text, meeting_id):
        print(f"[DEBUG][_parse_jira_formatted_tasks] Raw jira_text input:\n{jira_text}")
        tasks = []
        lines = [l.strip() for l in jira_text.splitlines() if l.strip()]
        print(f"[DEBUG][_parse_jira_formatted_tasks] Split lines: {lines}")
        current = {}
        for line in lines:
            print(f"[DEBUG][_parse_jira_formatted_tasks] Processing line: {line}")
            if line.startswith('- Summary:'):
                if current:
                    print(f"[DEBUG][_parse_jira_formatted_tasks] Appending task: {current}")
                    tasks.append(current)
                current = {'meeting_id': meeting_id, 'title': line.replace('- Summary:', '').strip()}
            elif line.startswith('- Description:'):
                current['description'] = line.replace('- Description:', '').strip()
            elif line.startswith('- Assignee:'):
                owner = line.replace('- Assignee:', '').strip()
                current['owner'] = owner if owner and owner.lower() != 'none' else None
            elif line.startswith('- Due Date:'):
                due = line.replace('- Due Date:', '').strip()
                current['due'] = due if due and due.lower() != 'none' else None
        if current:
            tasks.append(current)
        return tasks
