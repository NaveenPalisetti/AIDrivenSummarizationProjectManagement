# MCP API for summarization (mcep_api.py)
from fastapi import FastAPI
from pydantic import BaseModel
from mcp.core.mcp import MCPHost
from mcp.tools.summarization_tool import SummarizationTool

app = FastAPI()
mcp_host = MCPHost()
summ_tool = SummarizationTool()
mcp_host.register_tool(summ_tool)

class TranscriptIn(BaseModel):
    transcript: str
    meeting_id: str = "ui_session"

@app.post("/mcp/summarize")
async def summarize(transcript_in: TranscriptIn):
    session_id = mcp_host.create_session(agent_id="ui_agent")
    params = {"transcript": transcript_in.transcript, "meeting_id": transcript_in.meeting_id}
    result = await mcp_host.execute_tool(session_id, tool_id="summarization", parameters=params)
    mcp_host.end_session(session_id)
    return result
