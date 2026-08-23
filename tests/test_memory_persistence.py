import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from chat_manager import ChatManager

def test_sqlite_summary_persistence():
    chat_id = ChatManager.create_new_chat(user_id=1, title="Test Memory Chat")

    # Initial summary should be None
    assert ChatManager.get_chat_summary(chat_id) is None

    # Update summary in DB
    test_summary = "User is evaluating Q3 financial revenue figures."
    success = ChatManager.update_chat_summary(chat_id, test_summary)
    assert success is True

    # Reload from DB and verify persistence
    loaded_summary = ChatManager.get_chat_summary(chat_id)
    assert loaded_summary == test_summary

    # Cleanup
    ChatManager.delete_chat(chat_id)
