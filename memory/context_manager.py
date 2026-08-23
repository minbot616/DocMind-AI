import logging
from typing import List, Dict, Any, Tuple, Optional
from memory.models import MemoryBudget, ConversationMemory
from memory.token_counter import TokenCounter
from memory.summarizer import ConversationSummarizer

logger = logging.getLogger("DocMindBackend")

class ContextManager:
    """Token-aware context manager assembling prompt memory layers under strict token budgets."""

    def __init__(self, budget: Optional[MemoryBudget] = None):
        self.budget = budget or MemoryBudget()
        self.summarizer = ConversationSummarizer()

    def fit_recent_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trims oldest messages turn-by-turn until recent messages fit within recent_messages_budget."""
        if not messages:
            return []

        recent = list(messages)
        while recent and TokenCounter.count_messages_tokens(recent) > self.budget.recent_messages_budget:
            recent.pop(0)  # Drop oldest message turn

        return recent

    def assemble_memory(
        self,
        conversation_id: int,
        all_messages: List[Dict[str, Any]],
        existing_summary: Optional[str] = None,
        llm_provider: str = "Ollama",
        llm_model: str = "llama3",
        api_key: str = ""
    ) -> Tuple[ConversationMemory, Optional[str]]:
        """Assembles token-budgeted memory state and updates conversation summary when threshold is exceeded.
        
        Returns:
            Tuple of (ConversationMemory, updated_summary_if_changed)
        """
        if not all_messages:
            return ConversationMemory(
                conversation_id=conversation_id,
                summary=existing_summary,
                summary_token_count=TokenCounter.count_tokens(existing_summary or ""),
                recent_messages=[],
                estimated_token_count=TokenCounter.count_tokens(existing_summary or "")
            ), existing_summary

        updated_summary = existing_summary

        # Check if conversation history token count exceeds threshold
        if self.summarizer.should_summarize(all_messages):
            # Split messages: older messages to summarize, recent messages to keep in active context
            recent_kept = self.fit_recent_messages(all_messages)
            split_idx = len(all_messages) - len(recent_kept)
            
            if split_idx > 0:
                older_messages = all_messages[:split_idx]
                new_summary = self.summarizer.summarize_messages(
                    older_messages=older_messages,
                    existing_summary=existing_summary,
                    llm_provider=llm_provider,
                    llm_model=llm_model,
                    api_key=api_key
                )
                if new_summary != existing_summary:
                    updated_summary = new_summary

        recent_messages = self.fit_recent_messages(all_messages)
        summary_tokens = TokenCounter.count_tokens(updated_summary or "")
        recent_tokens = TokenCounter.count_messages_tokens(recent_messages)

        mem = ConversationMemory(
            conversation_id=conversation_id,
            summary=updated_summary,
            summary_token_count=summary_tokens,
            recent_messages=recent_messages,
            estimated_token_count=summary_tokens + recent_tokens
        )

        return mem, updated_summary
