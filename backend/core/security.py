import os
import base64
import hashlib
from cryptography.fernet import Fernet
from utils import logger

DEV_SECRET_FALLBACK = "docmind_default_development_secret_key_32bytes="

def _get_fernet_key() -> bytes:
    raw_secret = os.getenv("DOCMIND_SECRET_KEY", "").strip()
    if not raw_secret:
        key_bytes = DEV_SECRET_FALLBACK.encode("utf-8")
    else:
        key_bytes = raw_secret.encode("utf-8")

    try:
        Fernet(key_bytes)
        return key_bytes
    except Exception:
        hashed = hashlib.sha256(key_bytes).digest()
        return base64.urlsafe_b64encode(hashed)

def encrypt_credential(plaintext: str) -> str:
    """Encrypts a plaintext credential string into Fernet ciphertext."""
    if not plaintext or not isinstance(plaintext, str):
        return ""
    plaintext = plaintext.strip()
    if not plaintext or plaintext.startswith("•") or plaintext == "********":
        return ""
    if is_ciphertext(plaintext):
        return plaintext
    try:
        fernet = Fernet(_get_fernet_key())
        token = fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as e:
        logger.error(f"Credential encryption failure: {e}")
        return ""

def decrypt_credential(ciphertext: str) -> str:
    """Decrypts a Fernet ciphertext credential into plaintext."""
    if not ciphertext or not isinstance(ciphertext, str):
        return ""
    ciphertext = ciphertext.strip()
    if not ciphertext or ciphertext.startswith("•") or ciphertext == "********":
        return ""
    if not is_ciphertext(ciphertext):
        # Migration fallback: treat unencrypted legacy string as plaintext
        return ciphertext
    try:
        fernet = Fernet(_get_fernet_key())
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception:
        logger.error("Credential decryption failure.")
        return ""

def is_ciphertext(value: str) -> bool:
    """Checks if a string value is a Fernet ciphertext token."""
    if not value or not isinstance(value, str):
        return False
    if value.startswith("gAAAAA") and len(value) > 50:
        return True
    return False
