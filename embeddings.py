import os
from typing import Any
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

class EmbeddingManager:
    """Manages the creation and configuration of embedding models (local and cloud-based)."""

    @staticmethod
    def get_embeddings(model_name: str, api_key: str = "") -> Any:
        """Returns the appropriate embedding model based on settings.
        
        Args:
            model_name: The name of the embedding model, e.g. 'all-MiniLM-L6-v2', 'openai'
            api_key: Optional API key for OpenAI embeddings
        """
        # If OpenAI is selected or if the model name indicates OpenAI
        if model_name.lower() == "openai" or model_name.startswith("text-embedding"):
            if api_key:
                return OpenAIEmbeddings(openai_api_key=api_key)
            else:
                # Fallback to local if no API key is set
                return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Local Sentence Transformers
        # Safe options: 'all-MiniLM-L6-v2' (default), 'all-mpnet-base-v2'
        local_model = model_name if model_name else "all-MiniLM-L6-v2"
        try:
            return HuggingFaceEmbeddings(
                model_name=local_model,
                model_kwargs={'device': 'cpu'},  # Default to CPU for maximum compatibility
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception:
            # Fallback to standard lightweight model if loading fails
            return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
