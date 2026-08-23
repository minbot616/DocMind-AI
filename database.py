import os
import sys
from typing import List, Dict, Any, Optional
from sqlalchemy import text

from repositories.user_repository import UserRepository
from repositories.document_repository import DocumentRepository
from repositories.conversation_repository import ConversationRepository
from repositories.settings_repository import SettingsRepository
from utils import logger

class DatabaseManager:
    """Facade providing backwards-compatible unified database access delegating to repositories."""

    @classmethod
    def init_db(cls):
        from backend.database.config import Base, engine
        Base.metadata.create_all(bind=engine)

        # Auto-migrate schema columns for existing PostgreSQL / SQLite databases
        try:
            with engine.connect() as conn:
                if engine.name == "postgresql":
                    conn.execute(text("ALTER TABLE settings ADD COLUMN IF NOT EXISTS groq_api_key VARCHAR(512) DEFAULT ''"))
                    conn.execute(text("ALTER TABLE settings ADD COLUMN IF NOT EXISTS openai_api_key VARCHAR(512) DEFAULT ''"))
                    conn.execute(text("ALTER TABLE settings ALTER COLUMN api_key TYPE VARCHAR(512)"))
                    conn.commit()
                elif engine.name == "sqlite":
                    try:
                        conn.execute(text("ALTER TABLE settings ADD COLUMN groq_api_key VARCHAR(512) DEFAULT ''"))
                    except Exception:
                        pass
                    try:
                        conn.execute(text("ALTER TABLE settings ADD COLUMN openai_api_key VARCHAR(512) DEFAULT ''"))
                    except Exception:
                        pass
                    conn.commit()
        except Exception as e:
            logger.warning(f"Database schema column migration notice: {e}")

    # --- User Management ---
    @classmethod
    def get_or_create_default_user(cls) -> Dict[str, Any]:
        return UserRepository.get_or_create_default_user()

    @classmethod
    def create_user(cls, username: str, email: str, password_hash: str) -> Optional[int]:
        return UserRepository.create_user(username, email, password_hash)

    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        return UserRepository.get_user_by_email(email)

    @classmethod
    def get_user_id(cls, user_id: int) -> Optional[Dict[str, Any]]:
        return UserRepository.get_user_by_id(user_id)

    @classmethod
    def update_user_profile(cls, user_id: int, full_name: Optional[str] = None, avatar_url: Optional[str] = None) -> bool:
        return UserRepository.update_user_profile(user_id, full_name, avatar_url)

    # --- Document Management ---
    @classmethod
    def add_document(cls, user_id: int, filename: str, file_path: str, file_type: str, file_size: int) -> int:
        return DocumentRepository.add_document(user_id, filename, file_path, file_type, file_size)

    @classmethod
    def update_document_stats(cls, doc_id: int, pages: int, chunks: int) -> bool:
        return DocumentRepository.update_document_stats(doc_id, pages, chunks)

    @classmethod
    def get_documents(cls, user_id: int) -> List[Dict[str, Any]]:
        return DocumentRepository.get_documents(user_id)

    @classmethod
    def get_document(cls, doc_id: int) -> Optional[Dict[str, Any]]:
        return DocumentRepository.get_document(doc_id)

    @classmethod
    def rename_document(cls, doc_id: int, new_name: str) -> bool:
        return DocumentRepository.rename_document(doc_id, new_name)

    @classmethod
    def delete_document(cls, doc_id: int) -> bool:
        return DocumentRepository.delete_document(doc_id)

    @classmethod
    def search_documents_by_name(cls, user_id: int, query: str) -> List[Dict[str, Any]]:
        return DocumentRepository.search_documents_by_name(user_id, query)

    # --- Chat & Conversation Management ---
    @classmethod
    def create_chat(cls, user_id: int, title: str = "New Conversation") -> int:
        return ConversationRepository.create_chat(user_id, title)

    @classmethod
    def get_chats(cls, user_id: int) -> List[Dict[str, Any]]:
        return ConversationRepository.get_chats(user_id)

    @classmethod
    def get_chat(cls, chat_id: int) -> Optional[Dict[str, Any]]:
        return ConversationRepository.get_chat(chat_id)

    @classmethod
    def rename_chat(cls, chat_id: int, title: str) -> bool:
        return ConversationRepository.rename_chat(chat_id, title)

    @classmethod
    def update_chat_title(cls, chat_id: int, title: str) -> bool:
        return ConversationRepository.rename_chat(chat_id, title)

    @classmethod
    def delete_chat(cls, chat_id: int) -> bool:
        return ConversationRepository.delete_chat(chat_id)

    @classmethod
    def add_message(
        cls,
        chat_id: int,
        sender: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        response_time: Optional[float] = None
    ) -> int:
        return ConversationRepository.add_message(chat_id, sender, content, sources, response_time)

    @classmethod
    def get_messages(cls, chat_id: int) -> List[Dict[str, Any]]:
        return ConversationRepository.get_messages(chat_id)

    @classmethod
    def clear_all_history(cls, user_id: int) -> bool:
        return ConversationRepository.clear_all_history(user_id)

    @classmethod
    def search_chat_messages(cls, user_id: int, query: str) -> List[Dict[str, Any]]:
        return ConversationRepository.search_chat_messages(user_id, query)

    @classmethod
    def delete_last_message(cls, chat_id: int) -> bool:
        return ConversationRepository.delete_last_message(chat_id)

    @classmethod
    def get_total_questions(cls, user_id: int) -> int:
        return ConversationRepository.get_total_questions(user_id)

    @classmethod
    def get_chat_summary(cls, chat_id: int) -> Optional[str]:
        return ConversationRepository.get_chat_summary(chat_id)

    @classmethod
    def update_chat_summary(cls, chat_id: int, summary: str) -> bool:
        return ConversationRepository.update_chat_summary(chat_id, summary)

    @classmethod
    def get_settings(cls, user_id: int, mask_api_key: bool = False) -> Dict[str, Any]:
        return SettingsRepository.get_settings(user_id, mask_api_key=mask_api_key)

    @classmethod
    def update_settings(cls, user_id: int, settings: Dict[str, Any]) -> bool:
        return SettingsRepository.update_settings(user_id, settings)

# Initialize database schema on load
DatabaseManager.init_db()
