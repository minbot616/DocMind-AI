from pydantic import BaseModel
from typing import List, Optional
from backend.schemas.chat import CitationSchema

class MessageSchema(BaseModel):
    id: int
    chat_id: int
    sender: str
    content: str
    sources: Optional[List[CitationSchema]] = []
    timestamp: str
    response_time: Optional[float] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: str
    messages: Optional[List[MessageSchema]] = None

class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int

class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"
    user_id: int = 1
