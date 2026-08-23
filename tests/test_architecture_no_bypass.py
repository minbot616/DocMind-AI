import os
import re

def test_chat_route_has_no_direct_core_bypasses():
    """Architectural Integration Guardrail:
    Verifies that backend/api/routes/chat.py does NOT directly import RAGPipeline, VectorStoreManager,
    EmbeddingManager, or AgentOrchestrator, enforcing that Chat routes converge into
    the authoritative ChatService application core.
    """
    chat_route_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "api", "routes", "chat.py")
    assert os.path.exists(chat_route_path), "backend/api/routes/chat.py missing!"

    with open(chat_route_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Assert prohibited direct imports are absent
    prohibited = [
        r"from\s+rag_pipeline\s+import",
        r"import\s+rag_pipeline",
        r"from\s+vector_store\s+import",
        r"from\s+embeddings\s+import",
        r"RAGPipeline\.query"
    ]

    for pattern in prohibited:
        matches = re.findall(pattern, content)
        assert len(matches) == 0, f"Architectural Bypass Violation! Found prohibited pattern '{pattern}' in backend/api/routes/chat.py"

    # Assert ChatService is imported and used
    assert "from backend.services.chat_service import chat_service" in content
    assert "chat_service.process_message" in content

