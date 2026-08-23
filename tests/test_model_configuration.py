import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_manager import LLMManager
from repositories.settings_repository import SettingsRepository

def test_deprecated_groq_model_rejection_and_fallback():
    with patch("llm_manager.ChatGroq") as mock_groq, patch("os.getenv", return_value="gsk_dummykey"):
        mock_groq.return_value = MagicMock()
        LLMManager.get_llm("Groq", "llama3-70b-8192", api_key="gsk_dummykey", user_id=None)
        assert mock_groq.called
        assert mock_groq.call_args.kwargs["model_name"] == "llama-3.1-8b-instant"

def test_whisper_model_auto_recovery_and_rejection():
    with patch("llm_manager.ChatGroq") as mock_groq, patch("os.getenv", return_value="gsk_dummykey"):
        mock_groq.return_value = MagicMock()
        LLMManager.get_llm("Groq", "whisper-large-v3", api_key="gsk_dummykey", user_id=None)
        assert mock_groq.called
        assert mock_groq.call_args.kwargs["model_name"] == "llama-3.1-8b-instant"

def test_active_groq_model_accepted():
    with patch("llm_manager.ChatGroq") as mock_groq, patch("os.getenv", return_value="gsk_dummykey"):
        mock_groq.return_value = MagicMock()
        LLMManager.get_llm("Groq", "llama-3.3-70b-versatile", api_key="gsk_dummykey", user_id=None)
        assert mock_groq.called
        assert mock_groq.call_args.kwargs["model_name"] == "llama-3.3-70b-versatile"

def test_available_model_discovery_groq_excludes_whisper():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "llama-3.1-8b-instant", "active": True},
            {"id": "llama-3.3-70b-versatile", "active": True},
            {"id": "whisper-large-v3", "active": True},
            {"id": "llama3-70b-8192", "active": False}
        ]
    }
    with patch("requests.get", return_value=mock_resp), patch("os.getenv", return_value="gsk_dummy"):
        models = LLMManager.get_available_models("Groq", api_key="gsk_dummy")
        assert "llama-3.1-8b-instant" in models
        assert "llama-3.3-70b-versatile" in models
        assert "whisper-large-v3" not in models
        assert "llama3-70b-8192" not in models

def test_whisper_saved_model_auto_migrated_with_key_preserved():
    user_id = 9999
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "Groq",
        "llm_model": "whisper-large-v3",
        "api_key": "gsk_test_migration_key_123"
    })

    st = SettingsRepository.get_settings(user_id, mask_api_key=False)
    assert st["llm_model"] == "llama-3.1-8b-instant"
    assert st["api_key"] == "gsk_test_migration_key_123"

def test_provider_switching_preserves_keys():
    user_id = 9998
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_groq_key"
    })
    SettingsRepository.update_settings(user_id, {
        "llm_provider": "OpenAI",
        "llm_model": "gpt-4o-mini",
        "api_key": "sk-openai_key"
    })

    st = SettingsRepository.get_settings(user_id, mask_api_key=False)
    assert st["llm_provider"] == "OpenAI"
    assert st["openai_api_key"] == "sk-openai_key"
    assert st["groq_api_key"] == "gsk_groq_key"

def test_test_connection_auto_recovers_whisper_model():
    mock_llm = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "ok"
    mock_llm.invoke.return_value = mock_resp

    with patch("llm_manager.LLMManager.get_llm", return_value=mock_llm):
        res = LLMManager.test_connection_detailed("Groq", "whisper-large-v3", api_key="gsk_key", user_id=9997)
        assert res["success"] is True
        assert "llama-3.1-8b-instant" in res["message"]

def test_ollama_model_discovery():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3:latest"}, {"name": "mistral:latest"}]
    }
    with patch("requests.get", return_value=mock_resp):
        models = LLMManager.get_available_models("Ollama")
        assert "llama3" in models
        assert "mistral" in models

def test_openai_model_selection():
    models = LLMManager.get_available_models("OpenAI")
    assert "gpt-4o-mini" in models
    assert "gpt-4o" in models
