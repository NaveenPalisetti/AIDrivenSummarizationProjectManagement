# moved from core/data_models.py
from pydantic import BaseModel
from typing import List, Optional

class TaskModel(BaseModel):
	id: str
	title: str
	owner: Optional[str]
	status: str

class RiskModel(BaseModel):
	id: str
	description: str
	severity: str
# Data models for MCP (template)
