from typing import Any, Dict, List
import requests
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

class LLMManager:
    """Manages the creation and settings of the selected LLM provider (Ollama, Groq, OpenAI)."""

    # Pre-defined models list for each provider
    PROVIDER_MODELS = {
        "Ollama": ["llama3", "mistral", "gemma", "phi3", "llama2"],
        "Groq": ["llama-3.1-8b-instant", "llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "OpenAI": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    }

    @classmethod
    def get_available_models(cls, provider: str, api_key: str = "") -> List[str]:
        """Returns a list of models available for a given provider.
        For Ollama, it will attempt to fetch downloaded models dynamically from localhost.
        """
        if provider == "Ollama":
            try:
                # Try to fetch downloaded Ollama models
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    models_data = response.json().get("models", [])
                    dynamic_models = [m["name"].split(":")[0] for m in models_data]
                    if dynamic_models:
                        # Return unique values maintaining order
                        seen = set()
                        return [x for x in dynamic_models if not (x in seen or seen.add(x))]
            except Exception:
                pass
            return cls.PROVIDER_MODELS["Ollama"]
            
        return cls.PROVIDER_MODELS.get(provider, [])

    @classmethod
    def get_llm(cls, provider: str, model_name: str, api_key: str = "", temperature: float = 0.2, max_tokens: int = 1024) -> Any:
        """Instantiates the specified LLM client.
        
        Args:
            provider: 'Ollama', 'Groq', or 'OpenAI'
            model_name: The name of the model
            api_key: The API key for Groq or OpenAI
            temperature: Temperature settings (default 0.2 for factual answers)
            max_tokens: Maximum tokens to generate
        """
        if provider == "Ollama":
            # Set up Ollama Chat Client
            return ChatOllama(
                base_url="http://localhost:11434",
                model=model_name if model_name else "llama3",
                temperature=temperature,
                num_predict=max_tokens
            )
            
        elif provider == "Groq":
            if not api_key:
                raise ValueError("Groq API Key is required. Please set it in Settings.")
            return ChatGroq(
                groq_api_key=api_key,
                model_name=model_name if model_name else "llama-3.1-8b-instant",
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        elif provider == "OpenAI":
            if not api_key:
                raise ValueError("OpenAI API Key is required. Please set it in Settings.")
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model_name if model_name else "gpt-4o-mini",
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @classmethod
    def test_connection(cls, provider: str, model_name: str, api_key: str = "") -> bool:
        """Quickly tests if a provider connection works by sending a simple prompt."""
        try:
            llm = cls.get_llm(provider, model_name, api_key, temperature=0.0)
            # A simple invoke to see if it responds
            response = llm.invoke("respond with 'ok' and nothing else.")
            text = response.content.strip().lower()
            return "ok" in text
        except Exception:
            return False
