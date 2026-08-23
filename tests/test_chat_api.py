from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from database import DatabaseManager
from chat_manager import ChatManager
from repositories.conversation_repository import ConversationRepository
from backend.services.chat_service import ChatService
from backend.schemas.chat import ChatRequest

client = TestClient(app)

def test_chat_empty_message_validation():
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BAD_REQUEST"

def test_list_conversations_endpoint():
    response = client.get("/conversations")
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert "total" in data
    assert isinstance(data["conversations"], list)

def test_database_manager_rename_chat_and_update_title():
    user_id = 9991
    chat_id = DatabaseManager.create_chat(user_id, "Initial Title")
    assert chat_id is not None

    # Test DatabaseManager.rename_chat
    res1 = DatabaseManager.rename_chat(chat_id, "Renamed Title 1")
    assert res1 is True
    chat_data = DatabaseManager.get_chat(chat_id)
    assert chat_data["title"] == "Renamed Title 1"

    # Test DatabaseManager.update_chat_title
    res2 = DatabaseManager.update_chat_title(chat_id, "Renamed Title 2")
    assert res2 is True
    chat_data2 = DatabaseManager.get_chat(chat_id)
    assert chat_data2["title"] == "Renamed Title 2"

    # Cleanup
    DatabaseManager.delete_chat(chat_id)

def test_chat_service_process_message_resilient_to_title_failure():
    user_id = 9992
    req = ChatRequest(message="What is financial inflation?", user_id=user_id)

    mock_resp = MagicMock()
    mock_resp.answer = "Inflation is the rate at which the general level of prices for goods and services is rising."
    mock_resp.citations = []
    mock_resp.tools_used = [{"name": "document_search"}]
    mock_resp.duration = 0.5

    with patch("backend.services.chat_service.AgentOrchestrator.process", return_value=mock_resp), \
         patch("chat_manager.ChatManager.rename_chat", side_effect=Exception("Simulated rename error")):
        response = ChatService.process_message(req)
        assert response is not None
        assert "Inflation" in response.answer
        assert response.conversation_id is not None

        # Confirm conversation and message were persisted
        msgs = ChatManager.get_chat_messages(response.conversation_id)
        assert len(msgs) >= 2
        # Cleanup
        ChatManager.delete_chat(response.conversation_id)
