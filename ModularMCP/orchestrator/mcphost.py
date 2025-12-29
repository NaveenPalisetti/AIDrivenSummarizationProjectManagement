# MCPHost: Central Orchestrator and API Gateway for ModularMCP

from fastapi import FastAPI, Request
 # Removed MCPMessage, MCPResponse import; using plain JSON
from ModularMCP.protocols.mcp import register_agent, discover_agent
import json

app = FastAPI()

# Example: Register MCPHost itself (could be extended for all agents)
register_agent("mcphost", "http://localhost:9000/")

# Example handler registry (add your own handlers here)
HANDLERS = {}

def example_handler(message, session_data=None):
    # Example handler logic
    return {"status": "ok", "result": {"echo": message.get('payload', {}), "session": session_data}}

HANDLERS["example"] = example_handler

@app.post("/mcp/message/")
async def mcp_message(request: Request):
    data = await request.json()
    # No schema validation, just pass dict
    try:
        message = data
    except Exception as e:
        return {"status": "error", "error": f"Invalid message: {e}"}
    response = example_handler(message)
    return response

@app.post("/mcp/register_agent/")
async def register_agent_endpoint(request: Request):
    data = await request.json()
    name = data.get("name")
    endpoint = data.get("endpoint")
    meta = data.get("meta", {})
    register_agent(name, endpoint, meta)
    return {"status": "ok", "registered": name}

@app.get("/mcp/discover_agent/{name}")
async def discover_agent_endpoint(name: str):
    agent = discover_agent(name)
    if agent:
        return {"status": "ok", "agent": agent}
    else:
        return {"status": "error", "error": f"Agent '{name}' not found"}
