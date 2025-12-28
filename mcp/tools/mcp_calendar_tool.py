"""
MCP Calendar Transcript Tool

Provides a function to fetch and return transcripts from Google Calendar events for MCP workflows.
"""
from mcp.agents.mcp_google_calendar import MCPGoogleCalendar
import datetime

def get_calendar_transcripts(days_back=7, days_forward=1, calendar_id='primary'):
    cal = MCPGoogleCalendar(calendar_id=calendar_id)
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(days=days_back)
    end = now + datetime.timedelta(days=days_forward)
    events = cal.fetch_events(start, end)
    transcripts = cal.get_transcripts_from_events(events)
    return transcripts


