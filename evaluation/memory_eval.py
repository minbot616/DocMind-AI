from typing import List, Dict, Any
from memory.context_manager import ContextManager
from memory.token_counter import TokenCounter

class MemoryEvaluator:
    """Evaluates Phase 4 memory context budgeting and token management."""

    @staticmethod
    def evaluate_memory_budget(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        cm = ContextManager()
        fitted = cm.fit_recent_messages(messages)
        original_tokens = TokenCounter.count_messages_tokens(messages)
        fitted_tokens = TokenCounter.count_messages_tokens(fitted)

        return {
            "original_message_count": len(messages),
            "fitted_message_count": len(fitted),
            "original_token_count": original_tokens,
            "fitted_token_count": fitted_tokens,
            "budget_limit": cm.budget.recent_messages_budget,
            "budget_enforced": fitted_tokens <= cm.budget.recent_messages_budget
        }
