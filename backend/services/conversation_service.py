import sys
from typing import List, Optional
from backend.core.config import settings

# Ensure root workspace modules are importable
if settings.BASE_DIR not in sys.path:
    sys.path.insert(0, settings.BASE_DIR)

from database import DatabaseManager
from chat_manager import ChatManager
from backend.schemas.conversations import (
    ConversationResponse,
    ConversationListResponse,
    MessageSchema
)
from backend.schemas.chat import CitationSchema

class ConversationService:

    @staticmethod
    def list_conversations(user_id: int = 1) -> ConversationListResponse:
        chats = DatabaseManager.get_chats(user_id)
        conversations = []
        for chat in chats:
            conversations.append(ConversationResponse(
                id=chat["id"],
                user_id=chat["user_id"],
                title=chat["title"],
                created_at=chat["created_at"],
                messages=None
            ))
        return ConversationListResponse(conversations=conversations, total=len(conversations))

    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[ConversationResponse]:
        chat = DatabaseManager.get_chat(conversation_id)
        if not chat:
            return None

        raw_messages = DatabaseManager.get_messages(conversation_id)
        messages = []
        for msg in raw_messages:
            sources = []
            if msg.get("sources"):
                for src in msg["sources"]:
                    sources.append(CitationSchema(**src))
            
            messages.append(MessageSchema(
                id=msg["id"],
                chat_id=msg["chat_id"],
                sender=msg["sender"],
                content=msg["content"],
                sources=sources,
                timestamp=msg["timestamp"],
                response_time=msg.get("response_time")
            ))

        return ConversationResponse(
            id=chat["id"],
            user_id=chat["user_id"],
            title=chat["title"],
            created_at=chat["created_at"],
            messages=messages
        )

    @staticmethod
    def create_conversation(title: str = "New Conversation", user_id: int = 1) -> ConversationResponse:
        chat_id = ChatManager.create_new_chat(user_id, title)
        chat = DatabaseManager.get_chat(chat_id)
        return ConversationResponse(
            id=chat["id"],
            user_id=chat["user_id"],
            title=chat["title"],
            created_at=chat["created_at"],
            messages=[]
        )

    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        return DatabaseManager.delete_chat(conversation_id)

conversation_service = ConversationService()
