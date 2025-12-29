
# MCPClient for HTTP REST communication with modular agents
import requests
import json
import os

class MCPClient:
    # Extractor agent
    def extract(self, data):
        url = self.config["extractor"]["url"]
        resp = requests.post(url, json={"type": "extract", "payload": data})
        return resp.json()

    # Task agent
    def task(self, data):
        url = self.config["task"]["url"]
        resp = requests.post(url, json={"type": "task", "payload": data})
        return resp.json()

    # Risk agent
    def risk(self, data):
        url = self.config["risk"]["url"]
        resp = requests.post(url, json={"type": "risk", "payload": data})
        return resp.json()

    # Notify agent
    def notify(self, data):
        url = self.config["notify"]["url"]
        resp = requests.post(url, json={"type": "notify", "payload": data})
        return resp.json()
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'mcp_config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)["agents"]

    # Calendar agent
    def create_calendar_event(self, summary, description, start, end):
        url = self.config["calendar"]["create_event"]
        payload = {"summary": summary, "description": description, "start": start, "end": end}
        resp = requests.post(url, json={"type": "calendar_event", "payload": payload})
        return resp.json()

    def get_calendar_event(self, event_id):
        url = self.config["calendar"]["get_event"].replace("{event_id}", event_id)
        resp = requests.get(url)
        return resp.json()

    # Mistral summary agent
    def summarize_transcript(self, transcript):
        url = self.config["mistral_summary"]["summarize"]
        payload = {"transcript": transcript}
        resp = requests.post(url, json={"type": "summarize", "payload": payload})
        return resp.json()

    # Jira agent
    def create_jira_issue(self, project_key, summary, description, issuetype="Task"):
        url = self.config["jira"]["create_issue"]
        payload = {
            "project_key": project_key,
            "summary": summary,
            "description": description,
            "issuetype": issuetype
        }
        resp = requests.post(url, json={"type": "jira_issue", "payload": payload})
        return resp.json()

    def update_jira_issue(self, issue_id, update_data):
        url = self.config["jira"]["update_issue"]
        payload = {"issue_id": issue_id, "update": update_data}
        resp = requests.post(url, json={"type": "jira_update", "payload": payload})
        return resp.json()

    # Add more methods for other agents (extractor, task, risk, notify, etc.) as needed
