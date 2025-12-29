from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
import json

app = FastAPI()

class Message(BaseModel):
    type: str
    payload: dict
    metadata: dict = {}

with open('h:/Learning/BITS/Dissertation/Project/Week8/AIDrivenMeetingSummarizationWeek8/ModularMCP/config/mcp_config.json', 'r') as f:
    AGENT_CONFIG = json.load(f)

@app.post("/route")
async def route(msg: Message):
    agent = msg.metadata.get('agent')
    if agent not in AGENT_CONFIG['agents']:
        return {"error": f"Unknown agent: {agent}"}
    url = AGENT_CONFIG['agents'][agent]['url']
    response = requests.post(url, json=msg.dict())
    return response.json()
