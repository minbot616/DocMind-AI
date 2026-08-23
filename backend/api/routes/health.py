from fastapi import APIRouter
from typing import Dict, Any
from repositories.settings_repository import SettingsRepository
from llm_manager import LLMManager
from backend.database.config import get_engine

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health() -> Dict[str, Any]:
    """Returns real-time health checks for Database and configured LLM Provider."""
    db_connected = False
    try:
        engine = get_engine()
        with engine.connect() as conn:
            db_connected = True
    except Exception:
        db_connected = False

    st = SettingsRepository.get_settings(1)
    provider = st.get("llm_provider", "Ollama")
    model_name = st.get("llm_model", "llama3")
    api_key = st.get("api_key", "")

    llm_connected = False
    try:
        llm_connected = LLMManager.test_connection(provider, model_name, api_key)
    except Exception:
        llm_connected = False

    status_text = "AI Connected" if llm_connected else "AI Offline"

    return {
        "status": "healthy" if (db_connected and llm_connected) else "degraded",
        "database": {
            "connected": db_connected,
            "status_text": "PostgreSQL Connected" if db_connected else "PostgreSQL Offline"
        },
        "llm": {
            "connected": llm_connected,
            "provider": provider,
            "model": model_name,
            "status_text": status_text,
            "display_label": f"{provider} · {model_name}"
        }
    }
