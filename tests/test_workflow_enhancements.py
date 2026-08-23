import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from repositories.document_repository import DocumentRepository
from repositories.conversation_repository import ConversationRepository
from backend.services.chat_service import ChatService
from backend.schemas.chat import ChatRequest

client = TestClient(app)

def test_multi_document_upload_valid_and_mixed():
    """Test multi-document batch upload with valid files and rejected formats."""
    files = [
        ("files", ("test1.pdf", b"%PDF-1.4 Mock PDF content 1", "application/pdf")),
        ("files", ("test2.docx", b"Mock DOCX content 2", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ("files", ("invalid.exe", b"binary content", "application/x-msdownload"))
    ]

    with patch("backend.api.routes.documents.document_service.upload_document") as mock_upload:
        mock_upload.side_effect = [
            {"id": 101, "filename": "test1.pdf", "file_type": "pdf", "pages": 1, "chunks": 2, "status": "ready"},
            {"id": 102, "filename": "test2.docx", "file_type": "docx", "pages": 1, "chunks": 3, "status": "ready"}
        ]
        response = client.post("/documents/upload-multiple", files=files)
        assert response.status_code == 200
        data = response.json()
        
        assert "uploaded" in data
        assert "failed" in data
        assert len(data["uploaded"]) == 2
        assert len(data["failed"]) == 1
        assert data["failed"][0]["filename"] == "invalid.exe"
        assert "Unsupported file format" in data["failed"][0]["reason"]

def test_auto_create_conversation_and_title_generation():
    """Test first message automatically creates conversation in PostgreSQL with generated title."""
    user_id = 1
    query = "What are the revenue predictions for Q4 fiscal year 2026?"

    mock_llm_response = MagicMock()
    mock_llm_response.answer = "Revenue predictions are $5.2M based on document evidence."
    mock_llm_response.citations = []
    mock_llm_response.tools_used = []
    mock_llm_response.duration = 0.12

    mock_memory_state = MagicMock()
    mock_memory_state.recent_messages = []
    mock_memory_state.summary = ""

    with patch("memory.context_manager.ContextManager.assemble_memory", return_value=(mock_memory_state, "")):
        with patch("agent.orchestrator.AgentOrchestrator.process", return_value=mock_llm_response):
            request = ChatRequest(message=query, conversation_id=None, user_id=user_id)
            chat_resp = ChatService.process_message(request)

            assert chat_resp.conversation_id is not None
            
            # Verify conversation persisted in DB with generated title
            conv = ConversationRepository.get_chat(chat_resp.conversation_id)
            assert conv is not None
            assert "What are the revenue predictions" in conv["title"]

def test_document_scoping_passed_to_orchestrator():
    """Test selected_doc_ids is correctly scoped during RAG processing."""
    user_id = 1
    selected_ids = [42, 43]
    query = "Summarize findings from selected reports"

    mock_llm_response = MagicMock()
    mock_llm_response.answer = "Findings summary from selected reports."
    mock_llm_response.citations = []
    mock_llm_response.tools_used = []
    mock_llm_response.duration = 0.08

    mock_memory_state = MagicMock()
    mock_memory_state.recent_messages = []
    mock_memory_state.summary = ""

    with patch("memory.context_manager.ContextManager.assemble_memory", return_value=(mock_memory_state, "")):
        with patch("agent.orchestrator.AgentOrchestrator.process") as mock_process:
            mock_process.return_value = mock_llm_response
            request = ChatRequest(message=query, conversation_id=None, user_id=user_id, selected_doc_ids=selected_ids)
            chat_resp = ChatService.process_message(request)

            assert mock_process.called
            call_kwargs = mock_process.call_args.kwargs
            context = call_kwargs["context"]
            assert context["selected_doc_ids"] == [42, 43]

def test_delete_conversation_cascades_without_deleting_documents():
    """Test deleting conversation removes conversation and messages without touching documents."""
    user_id = 1
    
    # 1. Create a conversation and document
    conv_id = ConversationRepository.create_chat(user_id, "Test Deletion Chat")
    ConversationRepository.add_message(conv_id, "user", "Hello world")
    
    doc_id = DocumentRepository.add_document(user_id, "safe_doc.pdf", "storage/safe_doc.pdf", "pdf", 1024)

    # 2. Delete conversation via API
    response = client.delete(f"/conversations/{conv_id}")
    assert response.status_code in [200, 204]

    # 3. Verify conversation is deleted
    assert ConversationRepository.get_chat(conv_id) is None
    assert len(ConversationRepository.get_messages(conv_id)) == 0

    # 4. Verify document remains intact
    doc = DocumentRepository.get_document(doc_id)
    assert doc is not None
    assert doc["filename"] == "safe_doc.pdf"
    
    # Clean up document
    DocumentRepository.delete_document(doc_id)
