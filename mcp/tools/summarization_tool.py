from mcp.core.mcp import MCPTool, MCPToolType
from mcp.agents.summarization_agent import SummarizationAgent
import asyncio

class SummarizationTool(MCPTool):
    def __init__(self, mode="auto"):
        super().__init__(
            tool_id="summarization",
            tool_type=MCPToolType.SUMMARIZATION,
            name="Meeting Summarizer",
            description="Summarizes meeting transcripts into concise bullet points and action items.",
            api_endpoint="/mcp/summarize",
            auth_required=False,
            parameters={"transcript": "str", "mode": "str"}
        )
        self.mode = mode
        self.agent = SummarizationAgent(mode=mode)

    async def execute(self, params):
        transcript = params.get("transcript", "")
        meeting_id = params.get("meeting_id", "mcp_demo")
        mode = params.get("mode", self.mode)
        if mode != self.mode:
            self.agent = SummarizationAgent(mode=mode)
            self.mode = mode
        summary_obj = await self.agent.summarize(meeting_id, transcript)
        return {
            "status": "success",
            "summary": summary_obj.get("summary_text", summary_obj)
        }
