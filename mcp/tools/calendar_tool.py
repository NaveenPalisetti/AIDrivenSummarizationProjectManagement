from mcp.core.mcp import MCPTool, MCPToolType
from mcp.agents.mcp_google_calendar import MCPGoogleCalendar
import datetime

class CalendarTool(MCPTool):
    def __init__(self):
        super().__init__(
            tool_id="calendar",
            tool_type=MCPToolType.OTHER,
            name="Calendar Transcript Fetcher",
            description="Fetches transcripts from Google Calendar events.",
            api_endpoint="/mcp/calendar",
            auth_required=False,
            parameters={"days_back": "int", "days_forward": "int", "calendar_id": "str"}
        )

    async def execute(self, params):
        days_back = params.get("days_back", 7)
        days_forward = params.get("days_forward", 1)
        calendar_id = params.get("calendar_id", "primary")
        cal = MCPGoogleCalendar(calendar_id=calendar_id)
        now = datetime.datetime.utcnow()
        start = now - datetime.timedelta(days=days_back)
        end = now + datetime.timedelta(days=days_forward)
        events = cal.fetch_events(start, end)
        transcripts = cal.get_transcripts_from_events(events)
        return {"status": "success", "transcripts": transcripts}
