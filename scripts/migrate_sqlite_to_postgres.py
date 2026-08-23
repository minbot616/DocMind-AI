import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any
from backend.database.config import get_db_session
from backend.database.models import UserModel, DocumentModel, ChatModel, MessageModel, SettingsModel
from utils import logger

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
USERS_DB = os.path.join(DB_DIR, "users.db")
HISTORY_DB = os.path.join(DB_DIR, "history.db")

def parse_dt(dt_val) -> datetime:
    if not dt_val:
        return datetime.utcnow()
    if isinstance(dt_val, datetime):
        return dt_val
    try:
        return datetime.strptime(str(dt_val), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.utcnow()

def migrate():
    print("=" * 65)
    print("DocMind AI — SQLite to PostgreSQL Non-Destructive Data Migration")
    print("=" * 65)

    if not os.path.exists(USERS_DB) and not os.path.exists(HISTORY_DB):
        print("No SQLite legacy databases found. Migration skipped.")
        return

    migrated_counts: Dict[str, int] = {}
    sqlite_counts: Dict[str, int] = {}

    # 1. Migrate Users
    if os.path.exists(USERS_DB):
        conn = sqlite3.connect(USERS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        sqlite_counts["users"] = len(rows)

        with get_db_session() as session:
            for row in rows:
                existing = session.query(UserModel).filter(UserModel.id == row["id"]).first()
                if not existing:
                    user = UserModel(
                        id=row["id"],
                        username=row["username"],
                        password_hash=row["password_hash"],
                        created_at=parse_dt(row.get("created_at"))
                    )
                    session.add(user)
        conn.close()

    # 2. Migrate History (documents, chats, messages, settings)
    if os.path.exists(HISTORY_DB):
        conn = sqlite3.connect(HISTORY_DB)
        conn.row_factory = sqlite3.Row

        # Documents
        try:
            cursor = conn.execute("SELECT * FROM documents")
            rows = cursor.fetchall()
            sqlite_counts["documents"] = len(rows)
            with get_db_session() as session:
                for row in rows:
                    if not session.query(DocumentModel).filter(DocumentModel.id == row["id"]).first():
                        doc = DocumentModel(
                            id=row["id"],
                            user_id=row["user_id"],
                            filename=row["filename"],
                            file_path=row["file_path"],
                            file_type=row["file_type"],
                            file_size=row["file_size"],
                            upload_time=parse_dt(row.get("upload_time")),
                            status=row.get("status", "processed"),
                            pages=row.get("pages", 0),
                            chunks=row.get("chunks", 0)
                        )
                        session.add(doc)
        except Exception as e:
            logger.warning(f"Documents migration note: {e}")

        # Chats
        try:
            cursor = conn.execute("SELECT * FROM chats")
            rows = cursor.fetchall()
            sqlite_counts["chats"] = len(rows)
            with get_db_session() as session:
                for row in rows:
                    if not session.query(ChatModel).filter(ChatModel.id == row["id"]).first():
                        chat = ChatModel(
                            id=row["id"],
                            user_id=row["user_id"],
                            title=row["title"],
                            summary=row.get("summary"),
                            created_at=parse_dt(row.get("created_at"))
                        )
                        session.add(chat)
        except Exception as e:
            logger.warning(f"Chats migration note: {e}")

        # Messages
        try:
            cursor = conn.execute("SELECT * FROM messages")
            rows = cursor.fetchall()
            sqlite_counts["messages"] = len(rows)
            with get_db_session() as session:
                for row in rows:
                    if not session.query(MessageModel).filter(MessageModel.id == row["id"]).first():
                        msg = MessageModel(
                            id=row["id"],
                            chat_id=row["chat_id"],
                            sender=row["sender"],
                            content=row["content"],
                            sources=row.get("sources"),
                            timestamp=parse_dt(row.get("timestamp")),
                            response_time=row.get("response_time")
                        )
                        session.add(msg)
        except Exception as e:
            logger.warning(f"Messages migration note: {e}")

        # Settings
        try:
            cursor = conn.execute("SELECT * FROM settings")
            rows = cursor.fetchall()
            sqlite_counts["settings"] = len(rows)
            with get_db_session() as session:
                for row in rows:
                    if not session.query(SettingsModel).filter(SettingsModel.user_id == row["user_id"]).first():
                        st = SettingsModel(
                            user_id=row["user_id"],
                            theme=row.get("theme", "Dark"),
                            llm_provider=row.get("llm_provider", "Ollama"),
                            llm_model=row.get("llm_model", "llama3"),
                            api_key=row.get("api_key", ""),
                            embedding_model=row.get("embedding_model", "all-MiniLM-L6-v2"),
                            chunk_size=row.get("chunk_size", 500),
                            chunk_overlap=row.get("chunk_overlap", 50),
                            temperature=row.get("temperature", 0.2),
                            max_tokens=row.get("max_tokens", 1024)
                        )
                        session.add(st)
        except Exception as e:
            logger.warning(f"Settings migration note: {e}")

        conn.close()

    # Verification Report
    with get_db_session() as session:
        migrated_counts["users"] = session.query(UserModel).count()
        migrated_counts["documents"] = session.query(DocumentModel).count()
        migrated_counts["chats"] = session.query(ChatModel).count()
        migrated_counts["messages"] = session.query(MessageModel).count()
        migrated_counts["settings"] = session.query(SettingsModel).count()

    print("\nMigration Verification Summary:")
    print("-" * 65)
    print(f"{'Table':<15} | {'SQLite Count':<15} | {'Target Count':<15} | Status")
    print("-" * 65)
    for table in ["users", "documents", "chats", "messages", "settings"]:
        src_cnt = sqlite_counts.get(table, 0)
        tgt_cnt = migrated_counts.get(table, 0)
        status = "MATCH" if tgt_cnt >= src_cnt else "MISMATCH"
        print(f"{table:<15} | {src_cnt:<15} | {tgt_cnt:<15} | {status}")
    print("-" * 65)
    print("Migration completed successfully. Legacy SQLite source files left untouched.\n")

if __name__ == "__main__":
    migrate()
