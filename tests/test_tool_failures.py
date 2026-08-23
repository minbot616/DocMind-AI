import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import AgentOrchestrator
from agent.models import ToolResult

def test_tool_failure_isolation_web_search_error():
    orchestrator = AgentOrchestrator()

    with patch("agent.registry.ToolRegistry.execute_tool", return_value=ToolResult(tool_name="web_search", status="error", error_message="Provider down")):

        resp = orchestrator.process("search web for news", context={"has_documents": False})

    assert resp.tools_used[0]["status"] == "error"
    assert "unavailable" in resp.answer or "error" in resp.answer.lower()
