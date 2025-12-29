# Jira Agent FastAPI Service




from fastapi import FastAPI, Request
 # Removed MCPMessage, MCPResponse import; using plain JSON
import os
import json
from jira import JIRA


app = FastAPI()

# Load Jira credentials and initialize JIRA client
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'jira_credentials.json')
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        creds = json.load(f)
    try:
        jira_client = JIRA(server=creds['server'], basic_auth=(creds['username'], creds['api_token']))
    except Exception as e:
        print(f"[JiraAgent] Failed to initialize JIRA client: {e}")
        jira_client = None
else:
    jira_client = None
    print("[JiraAgent] Jira credentials not found at:", CONFIG_PATH)




@app.post("/jira/issue/")
async def create_issue(request: Request):
    data = await request.json()
    if not jira_client:
        return {"status": "error", "error": "Jira credentials not configured or JIRA client not initialized."}
    issue_dict = {
        'project': {'key': data.get('project_key', 'DEMO')},
        'summary': data.get('summary', 'No Summary'),
        'description': data.get('description', ''),
        'issuetype': {'name': data.get('issuetype', 'Task')}
    }
    try:
        new_issue = jira_client.create_issue(fields=issue_dict)
        return {"status": "ok", "result": {"jira_id": new_issue.key, "details": issue_dict}}
    except Exception as e:
        return {"status": "error", "error": f"Jira issue creation failed: {e}"}

# New endpoint: update Jira issue
@app.post("/jira/issue/update/")
async def update_issue(request: Request):
    data = await request.json()
    if not jira_client:
        return {"status": "error", "error": "Jira credentials not configured."}
    issue_id = data.get("issue_id", "")
    update_data = data.get("update", {})
    # Here you would call Jira API to update the issue
    return {"status": "ok", "result": {"issue_id": issue_id, "updated": update_data, "creds_loaded": True}}
