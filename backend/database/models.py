import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.config import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="processed")
    pages = Column(Integer, default=0)
    chunks = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_time": self.upload_time.strftime("%Y-%m-%d %H:%M:%S") if self.upload_time else None,
            "status": self.status,
            "pages": self.pages,
            "chunks": self.chunks
        }

class ChatModel(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("MessageModel", back_populates="chat", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string of source citations
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float, nullable=True)

    chat = relationship("ChatModel", back_populates="messages")

    def to_dict(self):
        parsed_sources = []
        if self.sources:
            try:
                parsed_sources = json.loads(self.sources)
            except Exception:
                parsed_sources = []
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "sender": self.sender,
            "content": self.content,
            "sources": parsed_sources,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "response_time": self.response_time
        }

class SettingsModel(Base):
    __tablename__ = "settings"

    user_id = Column(Integer, primary_key=True)
    theme = Column(String(50), default="Dark")
    llm_provider = Column(String(50), default="Ollama")
    llm_model = Column(String(100), default="llama3")
    api_key = Column(String(512), default="")
    groq_api_key = Column(String(512), default="")
    openai_api_key = Column(String(512), default="")
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    temperature = Column(Float, default=0.2)
    max_tokens = Column(Integer, default=1024)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "theme": self.theme,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "api_key": self.api_key,
            "groq_api_key": self.groq_api_key,
            "openai_api_key": self.openai_api_key,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

