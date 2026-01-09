# Modular MCP System


This project implements a modular, LLM-driven Model Context Protocol (MCP) system with the following components:

- **Monolithic or Modular FastAPI Orchestrator**: Hosts all agent endpoints under a single app or as microservices.
- **Agent Services**: Calendar, Summarizer, Extractor, Jira, Risk, Notification, Task, etc. (FastAPI-based)
- **MCPClient**: Python client for HTTP REST communication with all agents.
- **LangChain Agent**: LLM-powered orchestration, session memory, and dynamic tool use (see `langchain_agent.py`).
- **Streamlit UI**: Conversational chat interface for end users, powered by the LangChain agent.
- **Session Memory**: Conversation context is preserved for coherent multi-turn interactions.
- **Docker Support**: (Optional) for containerized deployment.


## Structure

- `orchestrator/` - FastAPI app (monolith or microservices)
- `agents/` - Agent endpoints (calendar, summary, extractor, jira, risk, etc.)
- `client/` - MCPClient for HTTP REST calls
- `ui/` - Streamlit LLM chat UI
- `langchain_agent.py` - LangChain agent for LLM-driven orchestration
- `config/` - Centralized agent config (URLs, credentials)
- `docker/` - (Optional) Dockerfiles and compose files


## Getting Started

1. Install all requirements:
  ```bash
  pip install -r requirements.txt
  ```
2. Start the FastAPI app (monolith or agents):
  ```bash
  uvicorn ModularMCP.orchestrator.monolith:app --reload
  # or run individual agents as needed
  ```
3. (Optional) Start the LangChain agent for LLM orchestration:
  ```bash
  python ModularMCP/langchain_agent.py
  ```
4. Start the Streamlit UI:
  ```bash
  streamlit run ModularMCP/ui/app.py
  ```
5. Configure agent endpoints and credentials in `config/mcp_config.json` and related files.

---


---

## Features

- Modular agent architecture (add/remove agents easily)
- LLM-driven orchestration and tool use (LangChain)
- Session memory for multi-turn chat
- REST API and Python client for all agents
- Extensible UI (Streamlit)

---

Replace placeholders and add your own logic as needed.
