import os
import pytest
from unittest.mock import patch, MagicMock
from repositories.settings_repository import SettingsRepository
from llm_manager import LLMManager
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_settings_masks_api_key():
    """Test D: GET /settings never exposes plaintext credentials."""
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_test_secret_key_12345"
    })

    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["api_key"] == "••••••••"
    assert "gsk_test_secret_key_12345" not in response.text

def test_empty_api_key_submission_preserves_existing_credential():
    """Test that submitting an empty string for api_key preserves the existing encrypted credential."""
    user_id = 9988
    # 1. Save valid key
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_preserved_key_9988"
    })
    
    st1 = SettingsRepository.get_settings(user_id, mask_api_key=False)
    assert st1["groq_api_key"] == "gsk_preserved_key_9988"

    # 2. Save settings with empty api_key string ("")
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": ""
    })

    # 3. Verify key is preserved, NOT wiped!
    st2 = SettingsRepository.get_settings(user_id, mask_api_key=False)
    assert st2["groq_api_key"] == "gsk_preserved_key_9988"

def test_explicit_clear_api_key_removes_credential():
    """Test that setting clear_api_key=True explicitly removes stored credential."""
    user_id = 9987
    # 1. Save key
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_key_to_be_cleared"
    })

    # 2. Explicit clear
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "clear_api_key": True
    })

    # 3. Verify key is cleared
    st = SettingsRepository.get_settings(user_id, mask_api_key=False)
    assert st["groq_api_key"] == ""

def test_groq_key_saved_through_settings_resolved_by_llmmanager(monkeypatch):
    """Test A: Groq key saved through Settings can be resolved by LLMManager without environment variable."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_persisted_secret_groq_key"
    })

    with patch("llm_manager.ChatGroq") as mock_chat_groq:
        mock_chat_groq.return_value = MagicMock()
        llm = LLMManager.get_llm(user_id=1)
        assert mock_chat_groq.called
        call_kwargs = mock_chat_groq.call_args.kwargs
        assert call_kwargs["groq_api_key"] == "gsk_persisted_secret_groq_key"

def test_openai_key_saved_through_settings_resolved_by_llmmanager(monkeypatch):
    """Test B: OpenAI key saved through Settings can be resolved by LLMManager."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "OpenAI",
        "llm_model": "gpt-4o-mini",
        "api_key": "sk-persisted_secret_openai_key"
    })

    with patch("llm_manager.ChatOpenAI") as mock_chat_openai:
        mock_chat_openai.return_value = MagicMock()
        llm = LLMManager.get_llm(user_id=1)
        assert mock_chat_openai.called
        call_kwargs = mock_chat_openai.call_args.kwargs
        assert call_kwargs["openai_api_key"] == "sk-persisted_secret_openai_key"

def test_env_var_takes_precedence_over_saved_key(monkeypatch):
    """Test C: Environment variable credentials take precedence over saved keys."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_env_override_key")
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_saved_key"
    })

    with patch("llm_manager.ChatGroq") as mock_chat_groq:
        mock_chat_groq.return_value = MagicMock()
        LLMManager.get_llm(user_id=1)
        call_kwargs = mock_chat_groq.call_args.kwargs
        assert call_kwargs["groq_api_key"] == "gsk_env_override_key"

def test_test_connection_endpoint_uses_persisted_credentials(monkeypatch):
    """Test E: POST /settings/test-connection uses saved credentials if key is masked or omitted."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_valid_key_for_test"
    })

    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = MagicMock(content="ok")

    with patch("llm_manager.ChatGroq", return_value=mock_llm_instance):
        response = client.post("/settings/test-connection", json={
            "llm_provider": "Groq",
            "llm_model": "llama-3.1-8b-instant",
            "api_key": "••••••••"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

def test_switching_provider_clears_or_separates_credentials(monkeypatch):
    """Test G: Switching from Groq to Ollama does not require or attempt Groq key."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Ollama",
        "llm_model": "llama3",
        "clear_api_key": True
    })

    mock_response = MagicMock(status_code=200)
    with patch("requests.get", return_value=mock_response):
        with patch("llm_manager.ChatOllama") as mock_ollama:
            mock_ollama.return_value = MagicMock()
            LLMManager.get_llm(user_id=1)
            assert mock_ollama.called

def test_missing_credentials_produces_clean_error(monkeypatch):
    """Test H & I: Missing credentials produce clean ValueError without leaking API keys in traceback."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "clear_api_key": True
    })

    with pytest.raises(ValueError, match="Groq API Key is required"):
        LLMManager.get_llm(provider="Groq", model_name="llama-3.1-8b-instant", api_key="", user_id=1)
