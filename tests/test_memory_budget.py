import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.models import MemoryBudget
from memory.context_manager import ContextManager

def test_memory_budget_enforcement():
    budget = MemoryBudget(
        max_context_tokens=4096,
        system_prompt_budget=500,
        evidence_budget=2000,
        recent_messages_budget=1000,
        summary_budget=500
    )
    cm = ContextManager(budget=budget)

    messages = [{"sender": "user", "content": f"Message {i}"} for i in range(100)]
    trimmed = cm.fit_recent_messages(messages)

    # Must fit within 1000 token budget
    from memory.token_counter import TokenCounter
    total_tokens = TokenCounter.count_messages_tokens(trimmed)
    assert total_tokens <= budget.recent_messages_budget
