import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from repositories.settings_repository import SettingsRepository
from backend.core.security import encrypt_credential, decrypt_credential, is_ciphertext
from llm_manager import LLMManager

client = TestClient(app)

def test_plaintext_key_is_encrypted_before_persistence():
    """Test plaintext key is encrypted before being stored in PostgreSQL."""
    plaintext_key = "gsk_test_secret_key_99999"
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": plaintext_key
    })

    # Read raw ciphertext directly from database
    raw_db = SettingsRepository.get_raw_ciphertext_settings(1)
    stored_val = raw_db.get("api_key")

    assert stored_val != plaintext_key
    assert is_ciphertext(stored_val)
    assert stored_val.startswith("gAAAAA")

def test_encrypted_credential_can_be_decrypted_by_backend():
    """Test backend can decrypt Fernet ciphertext correctly."""
    original_key = "sk-proj-test_openai_key_88888"
    ciphertext = encrypt_credential(original_key)
    
    assert is_ciphertext(ciphertext)
    decrypted = decrypt_credential(ciphertext)
    assert decrypted == original_key

def test_api_never_exposes_plaintext_or_ciphertext():
    """Test GET /settings and POST /settings return masked string '••••••••'."""
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_super_secret_key_777"
    })

    # GET /settings
    res_get = client.get("/settings")
    assert res_get.status_code == 200
    get_json = res_get.json()
    assert get_json["api_key"] == "••••••••"
    assert "gsk_super_secret_key_777" not in res_get.text

    # POST /settings
    res_post = client.post("/settings", json={
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_new_super_secret_key_888"
    })
    assert res_post.status_code == 200
    post_json = res_post.json()
    assert post_json["api_key"] == "••••••••"
    assert "gsk_new_super_secret_key_888" not in res_post.text

def test_groq_and_openai_chat_with_decrypted_credential(monkeypatch):
    """Test Groq and OpenAI chat utilize decrypted credentials from Settings."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Groq test
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_decrypted_groq_key"
    })
    with patch("llm_manager.ChatGroq") as mock_groq:
        mock_groq.return_value = MagicMock()
        LLMManager.get_llm(user_id=1)
        assert mock_groq.called
        assert mock_groq.call_args.kwargs["groq_api_key"] == "gsk_decrypted_groq_key"

    # OpenAI test
    SettingsRepository.update_settings(1, {
        "llm_provider": "OpenAI",
        "llm_model": "gpt-4o-mini",
        "api_key": "sk-decrypted_openai_key"
    })
    with patch("llm_manager.ChatOpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        LLMManager.get_llm(user_id=1)
        assert mock_openai.called
        assert mock_openai.call_args.kwargs["openai_api_key"] == "sk-decrypted_openai_key"

def test_environment_variable_precedence_over_encrypted_key(monkeypatch):
    """Test environment variable overrides encrypted stored credential."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_env_override_secret")
    
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_stored_encrypted_key"
    })

    with patch("llm_manager.ChatGroq") as mock_groq:
        mock_groq.return_value = MagicMock()
        LLMManager.get_llm(user_id=1)
        assert mock_groq.call_args.kwargs["groq_api_key"] == "gsk_env_override_secret"

def test_clearing_credential_removes_encrypted_key(monkeypatch):
    """Test sending explicit clear_api_key=True removes stored encrypted key and produces clear error."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    # 1. Set key
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_key_to_clear"
    })

    # 2. Clear key with clear_api_key=True
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "clear_api_key": True
    })

    raw_db = SettingsRepository.get_raw_ciphertext_settings(1)
    assert raw_db.get("api_key") == ""

    with pytest.raises(ValueError, match="Groq API Key is required"):
        LLMManager.get_llm(provider="Groq", model_name="llama-3.1-8b-instant", api_key="", user_id=1)

def test_provider_credential_isolation(monkeypatch):
    """Test provider switching does not send Groq key to OpenAI or vice versa."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Save Groq key
    SettingsRepository.update_settings(1, {
        "llm_provider": "Groq",
        "llm_model": "llama-3.1-8b-instant",
        "api_key": "gsk_groq_only_key"
    })

    # Switch provider to OpenAI without entering OpenAI key
    SettingsRepository.update_settings(1, {
        "llm_provider": "OpenAI",
        "llm_model": "gpt-4o-mini",
        "clear_api_key": True
    })

    # Attempt OpenAI LLM resolution - must fail safely rather than using Groq key
    with pytest.raises(ValueError, match="OpenAI API Key is required"):
        LLMManager.get_llm(provider="OpenAI", model_name="gpt-4o-mini", api_key="", user_id=1)

def test_legacy_plaintext_migration(monkeypatch):
    """Test safe auto-migration of legacy plaintext keys to ciphertext upon access."""
    # Force legacy plaintext write directly to DB for test
    from backend.database.config import get_db_session
    from backend.database.models import SettingsModel
    
    with get_db_session() as session:
        setting = session.query(SettingsModel).filter(SettingsModel.user_id == 1).first()
        if not setting:
            setting = SettingsModel(user_id=1)
            session.add(setting)
        setting.api_key = "legacy_unencrypted_plaintext_key_123"

    # Access via SettingsRepository trigger auto-migration
    st = SettingsRepository.get_settings(1, mask_api_key=False)
    assert st["api_key"] == "legacy_unencrypted_plaintext_key_123"

    # Verify DB now contains ciphertext
    raw_db = SettingsRepository.get_raw_ciphertext_settings(1)
    assert is_ciphertext(raw_db["api_key"])
    assert raw_db["api_key"].startswith("gAAAAA")
