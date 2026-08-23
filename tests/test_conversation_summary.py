import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.summarizer import ConversationSummarizer

def test_conversation_summarizer_trigger_and_generation():
    summarizer = ConversationSummarizer(summarization_threshold=50)

    short_msgs = [{"sender": "user", "content": "hi"}]
    assert not summarizer.should_summarize(short_msgs)

    long_msgs = [{"sender": "user", "content": "Detailed query about system architecture " * 10}]
    assert summarizer.should_summarize(long_msgs)

    mock_llm = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "User is analyzing system architecture components."
    mock_llm.invoke.return_value = mock_resp

    with patch("memory.summarizer.LLMManager.get_llm", return_value=mock_llm):
        summary = summarizer.summarize_messages(long_msgs)

    assert summary == "User is analyzing system architecture components."
