from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List
from backend.api.dependencies import get_current_user_id
from repositories.settings_repository import SettingsRepository
from llm_manager import LLMManager

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("")
def get_settings(user_id: int = Depends(get_current_user_id)) -> Dict[str, Any]:
    """Retrieve application settings with masked API key."""
    return SettingsRepository.get_settings(user_id, mask_api_key=True)

@router.post("")
def update_settings(
    settings: Dict[str, Any],
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Update application settings."""
    success = SettingsRepository.update_settings(user_id, settings)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save settings."
        )
    return SettingsRepository.get_settings(user_id, mask_api_key=True)

@router.get("/models")
def get_provider_models(
    provider: str = Query(..., description="LLM Provider name: Ollama, Groq, or OpenAI"),
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Returns available models for the given LLM provider, dynamically querying Groq/Ollama APIs if accessible."""
    models = LLMManager.get_available_models(provider, user_id=user_id)
    return {"provider": provider, "models": models}

@router.post("/test-connection")
def test_llm_connection(
    payload: Dict[str, Any],
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Tests connection reachability for the given provider, model, and optional API key."""
    provider = payload.get("llm_provider", "Ollama")
    model_name = payload.get("llm_model", "")
    api_key = payload.get("api_key", "")

    return LLMManager.test_connection_detailed(provider, model_name, api_key, user_id=user_id)
