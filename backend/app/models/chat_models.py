from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    documents: Optional[List[str]] = None
    json_schema: Optional[Dict[str, Any]] = None
    max_tokens: int = 2048

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    error: bool = False

class Conversation(BaseModel):
    id: str
    title: str
    created_at: str
    messages: List[Dict[str, Any]]
    parent_id: Optional[str] = None

class BranchRequest(BaseModel):
    conversation_id: str
    branch_point: int
