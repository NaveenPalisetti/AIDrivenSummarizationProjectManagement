# Google Calendar Agent FastAPI Service

from fastapi import FastAPI, Request
 # Removed MCPMessage, MCPResponse import; using plain JSON

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()


# Load Google Calendar credentials and initialize service
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'google_calendar_credentials.json')
if os.path.exists(CONFIG_PATH):
    try:
        creds = service_account.Credentials.from_service_account_file(CONFIG_PATH, scopes=['https://www.googleapis.com/auth/calendar'])
        calendar_service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"[CalendarAgent] Failed to initialize Google Calendar service: {e}")
        calendar_service = None
else:
    calendar_service = None
    print("[CalendarAgent] Google Calendar credentials not found at:", CONFIG_PATH)


@app.post("/calendar/event/")
async def create_event(request: Request):
    data = await request.json()
    if not calendar_service:
        return {"status": "error", "error": "Google Calendar credentials not configured or service not initialized."}
    event = {
        'summary': data.get('summary', 'No Title'),
        'description': data.get('description', ''),
        'start': {'dateTime': data.get('start')},
        'end': {'dateTime': data.get('end')}
    }
    try:
        created_event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        return {"status": "ok", "result": {"event_id": created_event['id'], "details": created_event}}
    except Exception as e:
        return {"status": "error", "error": f"Google Calendar event creation failed: {e}"}


# New endpoint: fetch event transcript
@app.get("/calendar/event/{event_id}")
async def get_event(event_id: str):
    if not calendar_service:
        return {"status": "error", "error": "Google Calendar credentials not configured or service not initialized."}
    try:
        event = calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
        transcript = event.get('description', '')  # Assuming transcript is stored in description
        return {"status": "ok", "result": {"event_id": event_id, "transcript": transcript, "details": event}}
    except Exception as e:
        return {"status": "error", "error": f"Google Calendar event fetch failed: {e}"}
