import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.models import MemoryBudget
from memory.context_manager import ContextManager

def test_context_manager_message_trimming():
    budget = MemoryBudget(recent_messages_budget=30)
    cm = ContextManager(budget=budget)

    # 4 messages totaling more than 30 tokens
    messages = [
        {"sender": "user", "content": "Turn 1: Very long question about machine learning architectures."},
        {"sender": "assistant", "content": "Turn 1 answer: Machine learning architectures include transformers and CNNs."},
        {"sender": "user", "content": "Turn 2: What about CNNs?"},
        {"sender": "assistant", "content": "Turn 2 answer: CNNs are used for computer vision."}
    ]

    trimmed = cm.fit_recent_messages(messages)
    assert len(trimmed) < 4
    # Oldest turn 1 dropped to fit budget, recent turn 2 preserved
    assert trimmed[-1]["content"] == "Turn 2 answer: CNNs are used for computer vision."
