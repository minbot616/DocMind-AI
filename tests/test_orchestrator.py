import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import AgentOrchestrator
from agent.models import ToolResult

def test_orchestrator_metadata_query():
    orchestrator = AgentOrchestrator()
    mock_docs = [{"id": 1, "filename": "spec.pdf", "file_type": ".pdf", "pages": 5, "chunks": 12, "file_size_kb": 5, "created_at": "2026-08-22"}]

    with patch("agent.tools.document_metadata.DatabaseManager.get_documents", return_value=mock_docs):
        resp = orchestrator.process("how many documents do I have in my library?", context={"user_id": 1, "has_documents": True})

    assert "Knowledge Base Summary" in resp.answer
    assert "spec.pdf" in resp.answer
    assert resp.tools_used[0]["name"] == "document_metadata"

def test_orchestrator_max_tool_calls_bounding():
    orchestrator = AgentOrchestrator(max_tool_calls=1)

    with patch("agent.router.IntentRouter.route") as mock_route, \
         patch.object(orchestrator.registry, "execute_tool", return_value=ToolResult(tool_name="t1", status="success")) as mock_exec:


        mock_route.return_value = MagicMock(intent="test", recommended_tools=["t1", "t2", "t3"])
        resp = orchestrator.process("query", context={"has_documents": False})

        assert mock_exec.call_count == 1
