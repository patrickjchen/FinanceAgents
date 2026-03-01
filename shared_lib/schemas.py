from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


class MCPContext(BaseModel):
    """Shared context for all agents"""
    user_query: str = ""
    companies: List[str] = Field(default_factory=list)
    tickers: List[str] = Field(default_factory=list)
    extracted_terms: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"


class MCPRequest(BaseModel):
    """Standardized request format"""
    context: MCPContext
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "router"
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class MCPResponse(BaseModel):
    """Standardized response format"""
    request_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    context_updates: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)
