import os
import sqlite3
import hashlib
from datetime import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
from utils import logger

# Paths
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
USERS_DB = os.path.join(DB_DIR, "users.db")
HISTORY_DB = os.path.join(DB_DIR, "history.db")

# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)

class DatabaseManager:
    """Manages connections and transactions for DocMind AI SQLite databases."""
    USERS_DB = USERS_DB
    HISTORY_DB = HISTORY_DB
    
    @staticmethod
    def get_db_connection(db_path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes both users and history databases with the required tables."""
        # 1. Initialize Users Database
        with cls.get_db_connection(USERS_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

        # 2. Initialize History Database
        with cls.get_db_connection(HISTORY_DB) as conn:
            # Documents Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'processed',
                    pages INTEGER DEFAULT 0,
                    chunks INTEGER DEFAULT 0
                )
            """)
            
            # Chats Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Messages Table (sources is stored as JSON string)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    sender TEXT NOT NULL, -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    sources TEXT, -- JSON string of source citations
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time REAL DEFAULT NULL,
                    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
                )
            """)
            
            # Settings Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'Dark',
                    llm_provider TEXT DEFAULT 'Ollama',
                    llm_model TEXT DEFAULT 'llama3',
                    api_key TEXT DEFAULT '',
                    embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2',
                    chunk_size INTEGER DEFAULT 500,
                    chunk_overlap INTEGER DEFAULT 50,
                    temperature REAL DEFAULT 0.2,
                    max_tokens INTEGER DEFAULT 1024
                )
            """)
            conn.commit()

        # Database Schema Migrations: Alter existing tables dynamically if columns are missing
        with cls.get_db_connection(HISTORY_DB) as conn:
            # 1. Migrate documents table
            cursor = conn.execute("PRAGMA table_info(documents)")
            columns = [row['name'] for row in cursor.fetchall()]
            if 'pages' not in columns:
                conn.execute("ALTER TABLE documents ADD COLUMN pages INTEGER DEFAULT 0")
            if 'chunks' not in columns:
                conn.execute("ALTER TABLE documents ADD COLUMN chunks INTEGER DEFAULT 0")

            # 2. Migrate settings table
            cursor = conn.execute("PRAGMA table_info(settings)")
            settings_cols = [row['name'] for row in cursor.fetchall()]
            if 'chunk_size' not in settings_cols:
                conn.execute("ALTER TABLE settings ADD COLUMN chunk_size INTEGER DEFAULT 500")
            if 'chunk_overlap' not in settings_cols:
                conn.execute("ALTER TABLE settings ADD COLUMN chunk_overlap INTEGER DEFAULT 50")
            if 'temperature' not in settings_cols:
                conn.execute("ALTER TABLE settings ADD COLUMN temperature REAL DEFAULT 0.2")
            if 'max_tokens' not in settings_cols:
                conn.execute("ALTER TABLE settings ADD COLUMN max_tokens INTEGER DEFAULT 1024")

            # 3. Migrate messages table
            cursor = conn.execute("PRAGMA table_info(messages)")
            msg_cols = [row['name'] for row in cursor.fetchall()]
            if 'response_time' not in msg_cols:
                conn.execute("ALTER TABLE messages ADD COLUMN response_time REAL DEFAULT NULL")
            conn.commit()

    # --- User Authentication Functions ---
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return f"{salt.hex()}:{key.hex()}"

    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        try:
            salt_hex, key_hex = stored_password.split(':')
            salt = bytes.fromhex(salt_hex)
            key = bytes.fromhex(key_hex)
            new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return key == new_key
        except Exception:
            return False

    @classmethod
    def register_user(cls, username: str, password: str) -> Tuple[bool, str]:
        """Registers a new user. Returns (success, message)."""
        username = username.strip().lower()
        if not username or not password:
            return False, "Username and password cannot be empty."
        
        password_hash = cls.hash_password(password)
        try:
            with cls.get_db_connection(USERS_DB) as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
            return True, "Registration successful."
        except sqlite3.IntegrityError:
            return False, "Username already exists."
        except Exception as e:
            return False, f"Database error: {str(e)}"

    @classmethod
    def authenticate_user(cls, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies credentials. Returns user dict or None if invalid."""
        username = username.strip().lower()
        try:
            with cls.get_db_connection(USERS_DB) as conn:
                cursor = conn.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                if row and cls.verify_password(row['password_hash'], password):
                    logger.info(f"User '{username}' authenticated successfully.")
                    return {"id": row['id'], "username": row['username']}
        except Exception:
            logger.exception(f"Error authenticating user '{username}'")
        return None

    # --- Settings Management ---
    
    @classmethod
    def get_settings(cls, user_id: int) -> Dict[str, Any]:
        """Gets settings for a user. Creates default if none exist."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                cursor = conn.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    # Fill any missing keys in dict with defaults to prevent KeyErrors
                    d = dict(row)
                    d.setdefault("chunk_size", 500)
                    d.setdefault("chunk_overlap", 50)
                    d.setdefault("temperature", 0.2)
                    d.setdefault("max_tokens", 1024)
                    return d
                
                # Insert default settings
                conn.execute(
                    "INSERT INTO settings (user_id) VALUES (?)",
                    (user_id,)
                )
                conn.commit()
                return {
                    "user_id": user_id,
                    "theme": "Dark",
                    "llm_provider": "Ollama",
                    "llm_model": "llama3",
                    "api_key": "",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "chunk_size": 500,
                    "chunk_overlap": 50,
                    "temperature": 0.2,
                    "max_tokens": 1024
                }
        except Exception:
            logger.exception(f"Failed to get settings for user {user_id}")
            return {
                "user_id": user_id,
                "theme": "Dark",
                "llm_provider": "Ollama",
                "llm_model": "llama3",
                "api_key": "",
                "embedding_model": "all-MiniLM-L6-v2",
                "chunk_size": 500,
                "chunk_overlap": 50,
                "temperature": 0.2,
                "max_tokens": 1024
            }

    @classmethod
    def update_settings(cls, user_id: int, settings: Dict[str, Any]) -> bool:
        """Updates user settings."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute(
                    """
                    INSERT INTO settings (user_id, theme, llm_provider, llm_model, api_key, embedding_model, chunk_size, chunk_overlap, temperature, max_tokens)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        theme=excluded.theme,
                        llm_provider=excluded.llm_provider,
                        llm_model=excluded.llm_model,
                        api_key=excluded.api_key,
                        embedding_model=excluded.embedding_model,
                        chunk_size=excluded.chunk_size,
                        chunk_overlap=excluded.chunk_overlap,
                        temperature=excluded.temperature,
                        max_tokens=excluded.max_tokens
                    """,
                    (
                        user_id,
                        settings.get("theme", "Dark"),
                        settings.get("llm_provider", "Ollama"),
                        settings.get("llm_model", "llama3"),
                        settings.get("api_key", ""),
                        settings.get("embedding_model", "all-MiniLM-L6-v2"),
                        settings.get("chunk_size", 500),
                        settings.get("chunk_overlap", 50),
                        settings.get("temperature", 0.2),
                        settings.get("max_tokens", 1024)
                    )
                )
                conn.commit()
            logger.info(f"Settings updated for user {user_id}.")
            return True
        except Exception:
            logger.exception(f"Failed to update settings for user {user_id}")
            return False

    # --- Document Management ---

    @classmethod
    def add_document(cls, user_id: int, filename: str, file_path: str, file_type: str, file_size: int) -> int:
        """Adds a document metadata entry."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute(
                """
                INSERT INTO documents (user_id, filename, file_path, file_type, file_size)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, filename, file_path, file_type, file_size)
            )
            conn.commit()
            return cursor.lastrowid

    @classmethod
    def update_document_stats(cls, doc_id: int, pages: int, chunks: int) -> bool:
        """Updates pages and chunks counts for a document."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute(
                    "UPDATE documents SET pages = ?, chunks = ? WHERE id = ?",
                    (pages, chunks, doc_id)
                )
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to update stats for doc_id {doc_id}")
            return False

    @classmethod
    def get_documents(cls, user_id: int) -> List[Dict[str, Any]]:
        """Returns list of documents for a user."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE user_id = ? ORDER BY upload_time DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    @classmethod
    def get_document(cls, doc_id: int) -> Optional[Dict[str, Any]]:
        """Gets metadata for a specific document."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @classmethod
    def rename_document(cls, doc_id: int, new_name: str) -> bool:
        """Renames a document."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute(
                    "UPDATE documents SET filename = ? WHERE id = ?",
                    (new_name, doc_id)
                )
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to rename document {doc_id} to '{new_name}'")
            return False

    @classmethod
    def delete_document(cls, doc_id: int) -> bool:
        """Deletes a document from metadata."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to delete document metadata for doc_id {doc_id}")
            return False

    # --- Chat History Management ---

    @classmethod
    def create_chat(cls, user_id: int, title: str) -> int:
        """Creates a new chat session."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute(
                "INSERT INTO chats (user_id, title) VALUES (?, ?)",
                (user_id, title)
            )
            conn.commit()
            return cursor.lastrowid

    @classmethod
    def get_chats(cls, user_id: int) -> List[Dict[str, Any]]:
        """Gets all chats for a user."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute(
                "SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    @classmethod
    def get_chat(cls, chat_id: int) -> Optional[Dict[str, Any]]:
        """Gets a chat metadata by ID."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @classmethod
    def rename_chat(cls, chat_id: int, title: str) -> bool:
        """Renames a chat session."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute(
                    "UPDATE chats SET title = ? WHERE id = ?",
                    (title, chat_id)
                )
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to rename chat {chat_id} to '{title}'")
            return False

    @classmethod
    def delete_chat(cls, chat_id: int) -> bool:
        """Deletes a chat and its messages."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to delete chat {chat_id}")
            return False

    @classmethod
    def add_message(cls, chat_id: int, sender: str, content: str, sources: Optional[List[Dict[str, Any]]] = None, response_time: Optional[float] = None) -> int:
        """Saves a message."""
        sources_str = json.dumps(sources) if sources else None
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute(
                "INSERT INTO messages (chat_id, sender, content, sources, response_time) VALUES (?, ?, ?, ?, ?)",
                (chat_id, sender, content, sources_str, response_time)
            )
            conn.commit()
            return cursor.lastrowid

    @classmethod
    def get_messages(cls, chat_id: int) -> List[Dict[str, Any]]:
        """Gets messages for a chat session."""
        with cls.get_db_connection(HISTORY_DB) as conn:
            cursor = conn.execute(
                "SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
                (chat_id,)
            )
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                if msg['sources']:
                    try:
                        msg['sources'] = json.loads(msg['sources'])
                    except Exception:
                        msg['sources'] = []
                else:
                    msg['sources'] = []
                messages.append(msg)
            return messages

    @classmethod
    def clear_all_history(cls, user_id: int) -> bool:
        """Clears all chat logs and sessions for a user."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute(
                    "DELETE FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
                    (user_id,)
                )
                conn.execute("DELETE FROM chats WHERE user_id = ?", (user_id,))
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to clear history for user {user_id}")
            return False

    @classmethod
    def search_documents_by_name(cls, user_id: int, query: str) -> List[Dict[str, Any]]:
        """Finds documents by filename keyword match."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                cursor = conn.execute(
                    "SELECT * FROM documents WHERE user_id = ? AND filename LIKE ? ORDER BY upload_time DESC",
                    (user_id, f"%{query}%")
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            logger.exception(f"Failed to search documents for user {user_id} with query '{query}'")
            return []

    @classmethod
    def search_chat_messages(cls, user_id: int, query: str) -> List[Dict[str, Any]]:
        """Finds chat messages by keyword match."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                cursor = conn.execute(
                    """
                    SELECT m.*, c.title as chat_title 
                    FROM messages m
                    JOIN chats c ON m.chat_id = c.id
                    WHERE c.user_id = ? AND m.content LIKE ?
                    ORDER BY m.timestamp DESC
                    """,
                    (user_id, f"%{query}%")
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            logger.exception(f"Failed to search chat messages for user {user_id} with query '{query}'")
            return []

    @classmethod
    def delete_last_message(cls, chat_id: int) -> bool:
        """Deletes the last message of a chat session."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                conn.execute(
                    "DELETE FROM messages WHERE id = (SELECT MAX(id) FROM messages WHERE chat_id = ?)",
                    (chat_id,)
                )
                conn.commit()
            return True
        except Exception:
            logger.exception(f"Failed to delete last message of chat {chat_id}")
            return False

    @classmethod
    def get_total_questions(cls, user_id: int) -> int:
        """Counts total user queries across all chats."""
        try:
            with cls.get_db_connection(HISTORY_DB) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE sender = 'user' AND chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
                    (user_id,)
                )
                return cursor.fetchone()[0]
        except Exception:
            logger.exception(f"Failed to count total questions for user {user_id}")
            return 0

# Self-initialize databases on module load
DatabaseManager.init_db()
