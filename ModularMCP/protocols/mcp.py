"""
Core MCP protocol logic and utilities for ModularMCP.
"""
from .schemas import get_session, set_session
from typing import Dict, Any, Callable
import threading

def validate_message(message: Dict[str, Any]) -> bool:
    # No schema validation, just check it's a dict
    return isinstance(message, dict)

def route_message(message: dict, handlers: Dict[str, Callable]) -> dict:
    """Route message to the appropriate handler based on type."""
    msg_type = message.get('type')
    handler = handlers.get(msg_type)
    if not handler:
        return {"status": "error", "error": f"No handler for type: {msg_type}"}
    try:
        # Session management example
        session_id = message.get('session_id')
        if session_id:
            session_data = get_session(session_id)
            response = handler(message, session_data)
            set_session(session_id, session_data)
            return response
        else:
            return handler(message)
    except Exception as e:
        return {"status": "error", "error": f"Handler error: {e}"}

# Simple in-memory agent registry (for demo; use DB/service for production)
AGENT_REGISTRY = {}
AGENT_REGISTRY_LOCK = threading.Lock()

def register_agent(name: str, endpoint: str, meta: dict = None):
    with AGENT_REGISTRY_LOCK:
        AGENT_REGISTRY[name] = {"endpoint": endpoint, "meta": meta or {}}

def discover_agent(name: str) -> dict:
    with AGENT_REGISTRY_LOCK:
        return AGENT_REGISTRY.get(name)
