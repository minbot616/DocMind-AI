import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.token_counter import TokenCounter

def test_token_counter_empty_and_short_strings():
    assert TokenCounter.count_tokens("") == 0
    assert TokenCounter.count_tokens(None) == 0

    tokens = TokenCounter.count_tokens("Hello world")
    assert tokens >= 2

def test_token_counter_long_text():
    long_text = "Python programming language features " * 50
    tokens = TokenCounter.count_tokens(long_text)
    assert tokens > 100

def test_token_counter_messages():
    messages = [
        {"sender": "user", "content": "What is Python?"},
        {"sender": "assistant", "content": "Python is a high-level programming language."}
    ]
    total = TokenCounter.count_messages_tokens(messages)
    assert total > 10
