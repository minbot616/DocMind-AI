import os
from typing import Any, Dict, List
import requests
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from utils import logger

class LLMManager:
    """Manages the creation and settings of the selected LLM provider (Ollama, Groq, OpenAI)."""

    DECOMMISSIONED_MODELS = {
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
        "distil-whisper-large-v3-en"
    }

    DEFAULT_SAFE_MODELS = {
        "Groq": [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "deepseek-r1-distill-llama-70b",
            "qwen-2.5-coder-32b"
        ],
        "OpenAI": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "Ollama": [
            "llama3",
            "llama3.1",
            "mistral",
            "gemma",
            "phi3"
        ]
    }

    # Pre-defined models list for backwards compatibility
    PROVIDER_MODELS = DEFAULT_SAFE_MODELS

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
    def get_available_models(cls, provider: str, api_key: str = "", user_id: int = 1) -> List[str]:
        """Returns a list of models available for a given provider.
        For Groq: Queries Groq's official GET /models API if credentials exist, filtering active text chat models.
        For Ollama: Queries local http://localhost:11434/api/tags.
        Fallback: Uses safe verified active model lists.
        """
        if provider == "Groq":
            effective_key = os.getenv("GROQ_API_KEY", "").strip()

            if not effective_key and api_key and not api_key.startswith("•") and api_key != "********":
                effective_key = api_key.strip()

            if not effective_key and user_id:
                try:
                    from repositories.settings_repository import SettingsRepository
                    saved = SettingsRepository.get_settings(user_id, mask_api_key=False)
                    candidate = saved.get("groq_api_key", "").strip() or (saved.get("api_key", "").strip() if saved.get("llm_provider") == "Groq" else "")
                    if candidate and not candidate.startswith("•") and candidate != "********":
                        effective_key = candidate
                except Exception:
                    pass

            if effective_key:
                try:
                    resp = requests.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {effective_key}"},
                        timeout=3
                    )
                    if resp.status_code == 200:
                        raw_data = resp.json().get("data", [])
                        active_models = []
                        for m in raw_data:
                            model_id = m.get("id", "")
                            is_active = m.get("active", True)
                            if is_active and not cls.is_invalid_or_whisper_model(model_id):
                                active_models.append(model_id)
                        
                        if active_models:
                            # Prioritize llama-3.1-8b-instant first if present
                            if "llama-3.1-8b-instant" in active_models:
                                active_models.remove("llama-3.1-8b-instant")
                                active_models.insert(0, "llama-3.1-8b-instant")
                            return active_models
                except Exception:
                    pass

            return cls.DEFAULT_SAFE_MODELS["Groq"]

        elif provider == "Ollama":
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    models_data = response.json().get("models", [])
                    dynamic_models = [m["name"].split(":")[0] for m in models_data]
                    if dynamic_models:
                        seen = set()
                        return [x for x in dynamic_models if not (x in seen or seen.add(x))]
            except Exception:
                pass
            return cls.DEFAULT_SAFE_MODELS["Ollama"]

        elif provider == "OpenAI":
            return cls.DEFAULT_SAFE_MODELS["OpenAI"]

        return cls.DEFAULT_SAFE_MODELS.get(provider, [])

    @classmethod
    def get_llm(
        cls,
        provider: str = None,
        model_name: str = None,
        api_key: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        user_id: int = 1
    ) -> Any:
        """Instantiates specified LLM client using environment variable -> explicit api_key -> decrypted persisted settings precedence."""
        from repositories.settings_repository import SettingsRepository

        saved_settings = {}
        if user_id:
            try:
                saved_settings = SettingsRepository.get_settings(user_id, mask_api_key=False)
            except Exception:
                saved_settings = {}

        if not provider:
            provider = saved_settings.get("llm_provider", "Ollama")
        
        if not model_name or cls.is_invalid_or_whisper_model(model_name):
            saved_m = saved_settings.get("llm_model")
            model_name = saved_m if saved_m and not cls.is_invalid_or_whisper_model(saved_m) else None

        # Fallback to safe defaults if model is missing, decommissioned, or whisper
        if not model_name or cls.is_invalid_or_whisper_model(model_name):
            if provider == "Groq":
                model_name = "llama-3.1-8b-instant"
            elif provider == "OpenAI":
                model_name = "gpt-4o-mini"
            else:
                model_name = "llama3"

        # Auto-detect fallback if provider is Ollama and local Ollama is offline
        if provider == "Ollama":
            ollama_online = False
            try:
                res = requests.get("http://localhost:11434/api/tags", timeout=1)
                if res.status_code == 200:
                    ollama_online = True
            except Exception:
                ollama_online = False

            if not ollama_online:
                groq_key = os.getenv("GROQ_API_KEY", "").strip() or saved_settings.get("groq_api_key", "").strip() or (saved_settings.get("api_key", "").strip() if saved_settings.get("llm_provider") == "Groq" else "")
                openai_key = os.getenv("OPENAI_API_KEY", "").strip() or saved_settings.get("openai_api_key", "").strip() or (saved_settings.get("api_key", "").strip() if saved_settings.get("llm_provider") == "OpenAI" else "")

                if groq_key and not groq_key.startswith("•") and groq_key != "********":
                    provider = "Groq"
                    api_key = groq_key
                    model_name = "llama-3.1-8b-instant"
                elif openai_key and not openai_key.startswith("•") and openai_key != "********":
                    provider = "OpenAI"
                    api_key = openai_key
                    model_name = "gpt-4o-mini"
                else:
                    raise RuntimeError(
                        "AI service unavailable. Local Ollama server is offline on http://localhost:11434 and no valid Groq/OpenAI credential is configured."
                    )

        if provider == "Ollama":
            return ChatOllama(
                base_url="http://localhost:11434",
                model=model_name,
                temperature=temperature,
                num_predict=max_tokens
            )

        elif provider == "Groq":
            effective_key = os.getenv("GROQ_API_KEY", "").strip()

            if not effective_key and api_key and not api_key.startswith("•") and api_key != "********":
                effective_key = api_key.strip()

            if not effective_key and saved_settings:
                candidate_key = saved_settings.get("groq_api_key", "").strip()
                if not candidate_key and saved_settings.get("llm_provider") == "Groq":
                    candidate_key = saved_settings.get("api_key", "").strip()
                if candidate_key and not candidate_key.startswith("•") and candidate_key != "********":
                    effective_key = candidate_key

            if not effective_key:
                raise ValueError("Groq API Key is required. Please save a valid API key in Settings or set the GROQ_API_KEY environment variable.")

            safe_groq_model = model_name if model_name and not cls.is_invalid_or_whisper_model(model_name) else "llama-3.1-8b-instant"

            return ChatGroq(
                groq_api_key=effective_key,
                model_name=safe_groq_model,
                temperature=temperature,
                max_tokens=max_tokens
            )

        elif provider == "OpenAI":
            effective_key = os.getenv("OPENAI_API_KEY", "").strip()

            if not effective_key and api_key and not api_key.startswith("•") and api_key != "********":
                effective_key = api_key.strip()

            if not effective_key and saved_settings:
                candidate_key = saved_settings.get("openai_api_key", "").strip()
                if not candidate_key and saved_settings.get("llm_provider") == "OpenAI":
                    candidate_key = saved_settings.get("api_key", "").strip()
                if candidate_key and not candidate_key.startswith("•") and candidate_key != "********":
                    effective_key = candidate_key

            if not effective_key:
                raise ValueError("OpenAI API Key is required. Please save a valid API key in Settings or set the OPENAI_API_KEY environment variable.")

            return ChatOpenAI(
                openai_api_key=effective_key,
                model_name=model_name if model_name else "gpt-4o-mini",
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @classmethod
    def test_connection_detailed(cls, provider: str, model_name: str, api_key: str = "", user_id: int = 1) -> Dict[str, Any]:
        """Tests if a provider connection works and returns clean diagnostic message with automatic model recovery."""
        from repositories.settings_repository import SettingsRepository

        safe_model = model_name
        if provider == "Groq" and cls.is_invalid_or_whisper_model(model_name):
            safe_model = "llama-3.1-8b-instant"
            if user_id:
                try:
                    SettingsRepository.update_settings(user_id, {"llm_model": safe_model})
                except Exception:
                    pass

        try:
            llm = cls.get_llm(provider, safe_model, api_key, temperature=0.0, user_id=user_id)
            response = llm.invoke("respond with 'ok' and nothing else.")
            text = str(response.content).strip().lower()
            if "ok" in text or len(text) > 0:
                return {
                    "success": True,
                    "message": f"Successfully connected to {provider} ({safe_model})",
                    "model": safe_model
                }
            return {"success": False, "message": f"Unexpected response from {provider}: {text}"}
        except Exception as e:
            err_str = str(e)
            err_lower = err_str.lower()
            
            # Automatic model recovery for decommissioned/whisper/model_not_found errors
            if "decommissioned" in err_lower or "not supported" in err_lower or "model_not_found" in err_lower or "400" in err_str or "404" in err_str:
                if provider == "Groq" and safe_model != "llama-3.1-8b-instant":
                    try:
                        safe_model = "llama-3.1-8b-instant"
                        if user_id:
                            SettingsRepository.update_settings(user_id, {"llm_model": safe_model})
                        retry_llm = cls.get_llm(provider, safe_model, api_key, temperature=0.0, user_id=user_id)
                        retry_resp = retry_llm.invoke("respond with 'ok' and nothing else.")
                        if retry_resp and retry_resp.content:
                            return {
                                "success": True,
                                "message": f"Successfully connected to {provider} ({safe_model})",
                                "model": safe_model
                            }
                    except Exception as retry_err:
                        err_str = str(retry_err)
                        err_lower = err_str.lower()

            if "401" in err_str or "invalid_api_key" in err_lower or "unauthorized" in err_lower or "authentication" in err_lower:
                return {
                    "success": False,
                    "message": f"Invalid {provider} API Key. Please verify your key in Settings."
                }
            elif "required" in err_lower:
                return {
                    "success": False,
                    "message": err_str
                }
            else:
                return {
                    "success": False,
                    "message": f"Could not establish connection to {provider} ({safe_model}). Please verify provider configuration."
                }

    @classmethod
    def test_connection(cls, provider: str, model_name: str, api_key: str = "", user_id: int = 1) -> bool:
        res = cls.test_connection_detailed(provider, model_name, api_key, user_id=user_id)
        return res.get("success", False)
