# ModularMCP Monolithic FastAPI App

from fastapi import FastAPI
from ModularMCP.agents.calendar_agent import app as calendar_app
from ModularMCP.agents.jira_agent import app as jira_app
from ModularMCP.agents.mistral_summary_agent import app as summary_app
# Import other agent apps as needed

monolith = FastAPI()

monolith.mount("/calendar", calendar_app)
monolith.mount("/jira", jira_app)
monolith.mount("/summary", summary_app)
# monolith.mount("/extractor", extractor_app)
# monolith.mount("/task", task_app)
# monolith.mount("/risk", risk_app)
# monolith.mount("/notify", notify_app)

# Optionally, add orchestrator or MCPHost endpoints here as well

# To run: uvicorn ModularMCP.orchestrator.monolith:monolith --port 8000
