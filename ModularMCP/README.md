# Modular MCP System

This project implements a modular Model Context Protocol (MCP) system with the following components:

- Master Orchestrator (FastAPI)
- Agent Services (FastAPI microservices):
  - Transcript Service
  - Summarizer Service
  - Extractor Service
  - Jira Service
  - Risk Service
- MCPClient (HTTP REST communication)
- Streamlit UI (Client)
- Docker support for each service

## Structure

- `orchestrator/` - Master orchestrator FastAPI app
- `agents/` - Each agent as a FastAPI microservice
- `client/` - MCPClient for inter-service communication
- `ui/` - Streamlit UI
- `docker/` - Dockerfiles and docker-compose for services

## Getting Started

1. Install requirements for each service (see respective folders)
2. Run each FastAPI service (or use docker-compose)
3. Start the Streamlit UI

---

Replace placeholders and add your own logic as needed.
