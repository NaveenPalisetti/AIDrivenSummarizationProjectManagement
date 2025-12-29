
from pydantic import BaseModel
from typing import Any, Dict, Optional

class MCPMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None  # For session management

class MCPResponse(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Example session storage (in-memory, for demo)
SESSION_STORE = {}

def get_session(session_id: str) -> dict:
    return SESSION_STORE.get(session_id, {})

def set_session(session_id: str, data: dict):
    SESSION_STORE[session_id] = data
