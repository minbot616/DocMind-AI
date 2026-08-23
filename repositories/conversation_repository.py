import json
from typing import List, Dict, Any, Optional
from backend.database.config import get_db_session
from backend.database.models import ChatModel, MessageModel
from utils import logger

class ConversationRepository:
    """Repository managing chat sessions, messages, and persistent summaries with explicit PostgreSQL transaction commits."""

    @classmethod
    def create_chat(cls, user_id: int, title: str = "New Conversation") -> int:
        with get_db_session() as session:
            chat = ChatModel(user_id=user_id, title=title)
            session.add(chat)
            session.flush()
            chat_id = chat.id
            session.commit()
        return chat_id

    @classmethod
    def get_chats(cls, user_id: int) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            chats = session.query(ChatModel).filter(ChatModel.user_id == user_id).order_by(ChatModel.created_at.desc()).all()
            return [c.to_dict() for c in chats]

    @classmethod
    def get_chat(cls, chat_id: int) -> Optional[Dict[str, Any]]:
        with get_db_session() as session:
            chat = session.query(ChatModel).filter(ChatModel.id == chat_id).first()
            return chat.to_dict() if chat else None

    @classmethod
    def rename_chat(cls, chat_id: int, title: str) -> bool:
        try:
            with get_db_session() as session:
                chat = session.query(ChatModel).filter(ChatModel.id == chat_id).first()
                if chat:
                    chat.title = title
                    session.commit()
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to rename chat {chat_id} to '{title}'")
            return False

    @classmethod
    def update_chat_title(cls, chat_id: int, title: str) -> bool:
        return cls.rename_chat(chat_id, title)

    @classmethod
    def delete_chat(cls, chat_id: int) -> bool:
        try:
            with get_db_session() as session:
                chat = session.query(ChatModel).filter(ChatModel.id == chat_id).first()
                if chat:
                    session.delete(chat)
                    session.commit()
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to delete chat {chat_id}")
            return False

    @classmethod
    def add_message(
        cls,
        chat_id: int,
        sender: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        response_time: Optional[float] = None
    ) -> int:
        with get_db_session() as session:
            sources_json = json.dumps(sources) if sources else None
            msg = MessageModel(
                chat_id=chat_id,
                sender=sender,
                content=content,
                sources=sources_json,
                response_time=response_time
            )
            session.add(msg)
            session.flush()
            msg_id = msg.id
            session.commit()
        return msg_id

    @classmethod
    def get_messages(cls, chat_id: int) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            messages = session.query(MessageModel).filter(MessageModel.chat_id == chat_id).order_by(MessageModel.timestamp.asc()).all()
            return [m.to_dict() for m in messages]

    @classmethod
    def clear_all_history(cls, user_id: int) -> bool:
        try:
            with get_db_session() as session:
                chats = session.query(ChatModel).filter(ChatModel.user_id == user_id).all()
                for c in chats:
                    session.delete(c)
                session.commit()
                return True
        except Exception:
            logger.exception(f"Failed to clear history for user {user_id}")
            return False

    @classmethod
    def search_chat_messages(cls, user_id: int, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        with get_db_session() as session:
            user_chats = session.query(ChatModel).filter(ChatModel.user_id == user_id).all()
            chat_ids = [c.id for c in user_chats]
            if not chat_ids:
                return []
            
            messages = session.query(MessageModel).filter(MessageModel.chat_id.in_(chat_ids)).all()
            for msg in messages:
                if query_lower in msg.content.lower():
                    results.append(msg.to_dict())
        return results

    @classmethod
    def delete_last_message(cls, chat_id: int) -> bool:
        try:
            with get_db_session() as session:
                last_msg = session.query(MessageModel).filter(MessageModel.chat_id == chat_id).order_by(MessageModel.timestamp.desc()).first()
                if last_msg:
                    session.delete(last_msg)
                    session.commit()
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to delete last message for chat {chat_id}")
            return False

    @classmethod
    def get_total_questions(cls, user_id: int) -> int:
        with get_db_session() as session:
            user_chats = session.query(ChatModel).filter(ChatModel.user_id == user_id).all()
            chat_ids = [c.id for c in user_chats]
            if not chat_ids:
                return 0
            return session.query(MessageModel).filter(
                MessageModel.chat_id.in_(chat_ids),
                MessageModel.sender == "user"
            ).count()

    @classmethod
    def get_chat_summary(cls, chat_id: int) -> Optional[str]:
        with get_db_session() as session:
            chat = session.query(ChatModel).filter(ChatModel.id == chat_id).first()
            return chat.summary if chat else None

    @classmethod
    def update_chat_summary(cls, chat_id: int, summary: str) -> bool:
        try:
            with get_db_session() as session:
                chat = session.query(ChatModel).filter(ChatModel.id == chat_id).first()
                if chat:
                    chat.summary = summary
                    session.commit()
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to update summary for chat {chat_id}")
            return False
