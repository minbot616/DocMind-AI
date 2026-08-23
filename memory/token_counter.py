import math
from typing import List, Dict, Any

class TokenCounter:
    """Token counter using tiktoken if installed, with robust word-ratio fallback approximation."""

    _encoder = None

    @classmethod
    def _get_encoder(cls):
        if cls._encoder is None:
            try:
                import tiktoken
                cls._encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                cls._encoder = False
        return cls._encoder

    @classmethod
    def count_tokens(cls, text: str) -> int:
        """Counts or estimates the number of tokens in a string."""
        if not text:
            return 0

        encoder = cls._get_encoder()
        if encoder:
            try:
                return len(encoder.encode(text))
            except Exception:
                pass

        # Fallback approximation: 1 word ~ 1.33 tokens, min 1 token per 4 chars
        words = len(text.split())
        chars = len(text)
        return max(1, int(math.ceil(words * 1.33)), int(math.ceil(chars / 4.0)))

    @classmethod
    def count_messages_tokens(cls, messages: List[Dict[str, Any]]) -> int:
        """Counts total tokens across a list of message dicts."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            sender = msg.get("sender", "")
            total += cls.count_tokens(f"{sender}: {content}") + 4  # overhead per message turn
        return total
