
from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import requests

app = FastAPI()

class Message(BaseModel):
    type: str
    payload: dict
    metadata: dict = {}

# Set your Slack webhook URL as an environment variable or in a config file
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def send_slack_notification(message: str) -> bool:
    if not SLACK_WEBHOOK_URL:
        return False
    payload = {"text": message}
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload)
        return resp.status_code == 200
    except Exception:
        return False

@app.post("/notify")
async def notify(msg: Message):
    message = msg.payload.get('message', '')
    sent = send_slack_notification(message)
    notification = f"Notification sent to Slack: {message}" if sent else "Failed to send Slack notification."
    return {"type": "notify_response", "payload": {"notification": notification}, "metadata": msg.metadata}
