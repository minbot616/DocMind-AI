import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schemas.chat import ChatRequest
from backend.services.chat_service import ChatService
from database import DatabaseManager
from chat_manager import ChatManager

def test_end_to_end_memory_rag_integration():
    chat_id = ChatManager.create_new_chat(user_id=1, title="RAG Memory Integration")

    req = ChatRequest(
        message="search web for AI trends",
        conversation_id=chat_id,
        user_id=1
    )

    mock_llm_response = MagicMock()
    mock_llm_response.answer = "Current AI trends focus on agentic systems."
    mock_llm_response.citations = []
    mock_llm_response.tools_used = [{"name": "web_search", "status": "success"}]
    mock_llm_response.duration = 0.05

    with patch("agent.orchestrator.AgentOrchestrator.process", return_value=mock_llm_response):
        resp = ChatService.process_message(req)

    assert resp.conversation_id == chat_id
    assert "agentic" in resp.answer.lower()

    # Cleanup
    ChatManager.delete_chat(chat_id)
