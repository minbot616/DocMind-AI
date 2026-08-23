import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.summarizer import ConversationSummarizer

def test_summary_failure_preserves_existing_summary():
    summarizer = ConversationSummarizer(summarization_threshold=10)
    messages = [{"sender": "user", "content": "Question content"}]
    old_summary = "User discussed Q3 financial report."

    # Simulate LLM exception during summarization
    with patch("memory.summarizer.LLMManager.get_llm", side_effect=RuntimeError("LLM connection timeout")):
        result_summary = summarizer.summarize_messages(messages, existing_summary=old_summary)

    # Must preserve old summary without raising exception or returning None
    assert result_summary == old_summary
