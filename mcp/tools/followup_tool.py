from mcp.core.mcp import MCPTool, MCPToolType
from mcp.tools.followup_meeting import check_and_create_followup_meeting

class FollowupTool(MCPTool):
    def __init__(self):
        super().__init__(
            tool_id="followup",
            tool_type=MCPToolType.OTHER,
            name="Followup Meeting Creator",
            description="Detects and creates follow-up meetings from transcripts.",
            api_endpoint="/mcp/followup",
            auth_required=False,
            parameters={"transcript": "str", "calendar_id": "str"}
        )

    async def execute(self, params):
        transcript = params.get("transcript", "")
        calendar_id = params.get("calendar_id", "primary")
        result = check_and_create_followup_meeting(transcript, calendar_id=calendar_id)
        return {"status": "success", "result": result}
