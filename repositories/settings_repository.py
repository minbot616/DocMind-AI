from typing import Dict, Any
from backend.database.config import get_db_session
from backend.database.models import SettingsModel
from backend.core.security import encrypt_credential, decrypt_credential, is_ciphertext
from utils import logger

class SettingsRepository:
    """Repository managing user configuration settings with encrypted credentials at rest."""

    DECOMMISSIONED_MODELS = {
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
        "distil-whisper-large-v3-en"
    }

    @classmethod
    def is_invalid_or_whisper_model(cls, model_name: str) -> bool:
        if not model_name:
            return True
        m = str(model_name).lower().strip()
        if m in cls.DECOMMISSIONED_MODELS:
            return True
        if m.startswith("whisper") or m.startswith("distil-whisper"):
            return True
        if m.endswith("-8192"):
            return True
        return False

    @classmethod
    def get_settings(cls, user_id: int, mask_api_key: bool = False) -> Dict[str, Any]:
        default_settings = {
            "user_id": user_id,
            "theme": "Dark",
            "llm_provider": "Ollama",
            "llm_model": "llama3",
            "api_key": "",
            "groq_api_key": "",
            "openai_api_key": "",
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "temperature": 0.2,
            "max_tokens": 1024
        }
        try:
            with get_db_session() as session:
                setting = session.query(SettingsModel).filter(SettingsModel.user_id == user_id).first()
                if setting:
                    dirty = False

                    # Auto-migration: if stored model is invalid/decommissioned/whisper, migrate to safe default without touching credentials
                    if cls.is_invalid_or_whisper_model(setting.llm_model):
                        if setting.llm_provider == "Groq":
                            setting.llm_model = "llama-3.1-8b-instant"
                        elif setting.llm_provider == "OpenAI":
                            setting.llm_model = "gpt-4o-mini"
                        else:
                            setting.llm_model = "llama3"
                        dirty = True

                    # Auto-migration: if any stored key is unencrypted plaintext, migrate it to ciphertext
                    if getattr(setting, "api_key", None) and not is_ciphertext(setting.api_key) and not setting.api_key.startswith("•"):
                        setting.api_key = encrypt_credential(setting.api_key)
                        dirty = True
                    if getattr(setting, "groq_api_key", None) and not is_ciphertext(setting.groq_api_key) and not setting.groq_api_key.startswith("•"):
                        setting.groq_api_key = encrypt_credential(setting.groq_api_key)
                        dirty = True
                    if getattr(setting, "openai_api_key", None) and not is_ciphertext(setting.openai_api_key) and not setting.openai_api_key.startswith("•"):
                        setting.openai_api_key = encrypt_credential(setting.openai_api_key)
                        dirty = True

                    if dirty:
                        session.commit()

                    data = setting.to_dict()

                    if mask_api_key:
                        if data.get("api_key"): data["api_key"] = "••••••••"
                        if data.get("groq_api_key"): data["groq_api_key"] = "••••••••"
                        if data.get("openai_api_key"): data["openai_api_key"] = "••••••••"
                    else:
                        # Return decrypted plaintext keys for trusted internal backend usage
                        if data.get("api_key"): data["api_key"] = decrypt_credential(data["api_key"])
                        if data.get("groq_api_key"): data["groq_api_key"] = decrypt_credential(data["groq_api_key"])
                        if data.get("openai_api_key"): data["openai_api_key"] = decrypt_credential(data["openai_api_key"])

                    return data

                # Insert default settings if none exist
                new_setting = SettingsModel(user_id=user_id)
                session.add(new_setting)
                return default_settings
        except Exception:
            logger.exception(f"Failed to get settings for user {user_id}")
            return default_settings

    @classmethod
    def get_raw_ciphertext_settings(cls, user_id: int) -> Dict[str, Any]:
        """Internal audit method returning raw ciphertext values directly from PostgreSQL."""
        with get_db_session() as session:
            setting = session.query(SettingsModel).filter(SettingsModel.user_id == user_id).first()
            return setting.to_dict() if setting else {}

    @classmethod
    def update_settings(cls, user_id: int, settings: Dict[str, Any]) -> bool:
        try:
            with get_db_session() as session:
                setting = session.query(SettingsModel).filter(SettingsModel.user_id == user_id).first()
                if not setting:
                    setting = SettingsModel(user_id=user_id)
                    session.add(setting)

                provider = settings.get("llm_provider", getattr(setting, "llm_provider", "Ollama") or "Ollama")
                model_name = settings.get("llm_model", getattr(setting, "llm_model", "llama3"))

                # Validate & sanitize decommissioned/whisper models
                if cls.is_invalid_or_whisper_model(model_name):
                    if provider == "Groq":
                        model_name = "llama-3.1-8b-instant"
                    elif provider == "OpenAI":
                        model_name = "gpt-4o-mini"
                    else:
                        model_name = "llama3"

                clear_requested = settings.get("clear_api_key", False) or settings.get("api_key") == "__CLEAR__"
                new_key = settings.get("api_key", "")
                
                if clear_requested:
                    setting.api_key = ""
                    if provider == "Groq" and hasattr(setting, "groq_api_key"):
                        setting.groq_api_key = ""
                    elif provider == "OpenAI" and hasattr(setting, "openai_api_key"):
                        setting.openai_api_key = ""
                elif isinstance(new_key, str) and new_key.strip() != "":
                    cleaned_key = new_key.strip()
                    if not cleaned_key.startswith("•") and cleaned_key != "********":
                        encrypted_key = encrypt_credential(cleaned_key)
                        setting.api_key = encrypted_key
                        if provider == "Groq" and hasattr(setting, "groq_api_key"):
                            setting.groq_api_key = encrypted_key
                        elif provider == "OpenAI" and hasattr(setting, "openai_api_key"):
                            setting.openai_api_key = encrypted_key
                # If new_key is empty ("") or masked ("••••••••") and clear_requested is False, existing stored key remains untouched!

                setting.theme = settings.get("theme", "Dark")
                setting.llm_provider = provider
                setting.llm_model = model_name
                setting.embedding_model = settings.get("embedding_model", "all-MiniLM-L6-v2")
                setting.chunk_size = settings.get("chunk_size", 500)
                setting.chunk_overlap = settings.get("chunk_overlap", 50)
                setting.temperature = settings.get("temperature", 0.2)
                setting.max_tokens = settings.get("max_tokens", 1024)

            logger.info(f"Settings updated for user {user_id}.")
            return True

        except Exception:
            logger.exception(f"Failed to update settings for user {user_id}")
            return False
