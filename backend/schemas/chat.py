from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CitationSchema(BaseModel):
    document: str
    page: int
    snippet: str = ""
    score: float = 1.0


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user question or prompt")
    conversation_id: Optional[int] = Field(None, description="Optional conversation ID to append message to")
    user_id: Optional[int] = Field(1, description="ID of the user sending the chat")
    selected_doc_ids: Optional[List[int]] = Field(None, description="Optional list of document IDs to query against")

class ChatResponse(BaseModel):
    answer: str
    conversation_id: int
    sources: List[CitationSchema] = []
    tools_used: List[Dict[str, Any]] = []
    response_time: float = 0.0
