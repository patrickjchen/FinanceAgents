# Pydantic models
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uuid

class MCPContext(BaseModel):
    """Shared context for all agents"""
    user_query: str
    companies: List[str] = []
    tickers: List[str] = []
    extracted_terms: Dict[str, List[str]] = {}
    version: int = 1  # Context versioning

class MCPRequest(BaseModel):
    """Standardized request format"""
    context: MCPContext
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "router"
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class MCPResponse(BaseModel):
    """Standardized response format"""
    request_id: Optional[str]
    data: Dict
    context_updates: Optional[Dict]
    status: str = "success"  # success/failed
    timestamp: datetime = Field(default_factory=datetime.now)

