from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class MemoryBudget:
    """Configurable token budget allocation for prompt context layers."""
    max_context_tokens: int = 4096
    system_prompt_budget: int = 500
    evidence_budget: int = 2000
    recent_messages_budget: int = 1000
    summary_budget: int = 500

@dataclass
class ConversationMemory:
    """Container holding token-budgeted conversation memory state."""
    conversation_id: int
    summary: Optional[str] = None
    summary_token_count: int = 0
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    estimated_token_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "summary": self.summary,
            "summary_token_count": self.summary_token_count,
            "recent_messages_count": len(self.recent_messages),
            "estimated_token_count": self.estimated_token_count
        }
