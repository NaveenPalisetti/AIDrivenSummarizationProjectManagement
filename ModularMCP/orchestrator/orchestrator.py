from fastapi import FastAPI, Request
from pydantic import BaseModel

import requests
import json
import os

app = FastAPI()

class Message(BaseModel):
    type: str
    payload: dict
    metadata: dict = {}


# Use environment variable for config path, fallback to default
CONFIG_PATH = os.environ.get('MCP_CONFIG_PATH', 'h:/Learning/BITS/Dissertation/Project/Week8/AIDrivenMeetingSummarizationWeek8/ModularMCP/config/mcp_config.json')
with open(CONFIG_PATH, 'r') as f:
    AGENT_CONFIG = json.load(f)

@app.post("/route")
async def route(msg: Message):
    agent = msg.metadata.get('agent')
    if agent not in AGENT_CONFIG['agents']:
        return {"error": f"Unknown agent: {agent}"}
    url = AGENT_CONFIG['agents'][agent]['url']
    response = requests.post(url, json=msg.dict())
    return response.json()
