# Orchestrator FastAPI App

from fastapi import FastAPI, Request
from client.mcp_client import MCPClient

app = FastAPI()
client = MCPClient()

@app.post("/process_meeting/")
async def process_meeting(request: Request):
    data = await request.json()
    # Example: send transcript to transcript agent, get summary, etc.
    transcript_id = client.send_transcript(data["transcript"])
    summary = client.get_summary(transcript_id)
    # ... call other agents as needed
    return {"transcript_id": transcript_id, "summary": summary}
