from mcp.core.utils import gen_id
import os, json
with open('mcp/config/credentials.json') as f:
	creds = json.load(f)
jira = creds.get("jira", {})

os.environ["JIRA_URL"] = jira.get("base_url", "")
os.environ["JIRA_USER"] = jira.get("user", "")
os.environ["JIRA_TOKEN"] = jira.get("token", "")
os.environ["JIRA_PROJECT"] = jira.get("project", "PROJ")
try:
	from jira import JIRA
except ImportError:
	JIRA = None

class TaskManagerAgent:
	def __init__(self):
		self.tasks_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'tasks', 'tasks.json')
		os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
		if not os.path.exists(self.tasks_file):
			with open(self.tasks_file, 'w', encoding='utf-8') as f:
				json.dump([], f)
		# Jira config (set these as env vars or config)
		self.jira_url = os.environ.get("JIRA_URL")
		self.jira_user = os.environ.get("JIRA_USER")
		self.jira_token = os.environ.get("JIRA_TOKEN")
		self.jira_project = os.environ.get("JIRA_PROJECT")
		self.jira = None
		print(f"TaskManagerAgent: JIRA_URL={self.jira_url}, JIRA_USER={self.jira_user}, JIRA_PROJECT={self.jira_project}")  
		if JIRA and self.jira_url and self.jira_user and self.jira_token:
			self.jira = JIRA(server=self.jira_url, basic_auth=(self.jira_user, self.jira_token))

	def extract_and_create_tasks(self, meeting_id: str, summary: dict):
		tasks = []
		raw_actions = summary.get('action_items') or []
		if not raw_actions and 'summary_text' in summary:
			st = summary['summary_text']
			raw_actions = [st] if len(st) < 200 else st.split(';')[:1]

		with open(self.tasks_file, 'r', encoding='utf-8') as f:
			existing = json.load(f)

		MAX_SUMMARY_LEN = 255

		for a in raw_actions:
			# ...existing code...
			if isinstance(a, dict):
				title = a.get('description') or a.get('task') or str(a)
				owner = a.get('assignee') or a.get('owner')
				due = a.get('due_date') or a.get('deadline')
			else:
				title = str(a)
				owner = None
				due = None

			# Truncate title for Jira summary
			jira_title = title.replace('\n', ' ').replace('\r', ' ')[:MAX_SUMMARY_LEN]

			t = {
				'id': gen_id('task'),
				'meeting_id': meeting_id,
				'title': title,
				'owner': owner,
				'status': 'open'
			}
			existing.append(t)
			tasks.append(t)

			# --- JIRA Integration ---
			if self.jira:
				issue_dict = {
					'project': {'key': self.jira_project},
					'summary': jira_title,
					'description': f"Auto-created from meeting {meeting_id}",
					'issuetype': {'name': 'Task'},
				}
				if owner:
					issue_dict['assignee'] = {'name': owner}
				if due:
					issue_dict['duedate'] = due
				try:
					issue = self.jira.create_issue(fields=issue_dict)
					t['jira_issue'] = issue.key
				except Exception as e:
					t['jira_error'] = str(e)

		with open(self.tasks_file, 'w', encoding='utf-8') as f:
			json.dump(existing, f, indent=2)
		return tasks
