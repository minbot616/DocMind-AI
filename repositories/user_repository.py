import os
import hashlib
from typing import Optional, Dict, Any, Tuple
from backend.database.config import get_db_session
from backend.database.models import UserModel
from utils import logger

class UserRepository:
    """Repository handling User registration and authentication."""

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
        username = username.strip().lower()
        if not username or not password:
            return False, "Username and password cannot be empty."

        password_hash = cls.hash_password(password)
        try:
            with get_db_session() as session:
                existing = session.query(UserModel).filter(UserModel.username == username).first()
                if existing:
                    return False, "Username already exists."
                user = UserModel(username=username, password_hash=password_hash)
                session.add(user)
            return True, "Registration successful."
        except Exception as e:
            logger.exception(f"Error registering user '{username}'")
            return False, f"Database error: {str(e)}"

    @classmethod
    def authenticate_user(cls, username: str, password: str) -> Optional[Dict[str, Any]]:
        username = username.strip().lower()
        try:
            with get_db_session() as session:
                user = session.query(UserModel).filter(UserModel.username == username).first()
                if user and cls.verify_password(user.password_hash, password):
                    logger.info(f"User '{username}' authenticated successfully.")
                    return {"id": user.id, "username": user.username}
        except Exception:
            logger.exception(f"Error authenticating user '{username}'")
        return None
