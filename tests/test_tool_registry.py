import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.registry import ToolRegistry

def test_tool_registry_registration_and_lookup():
    registry = ToolRegistry()
    
    assert registry.get_tool("document_search") is not None
    assert registry.get_tool("document_metadata") is not None
    assert registry.get_tool("web_search") is not None

    tools_list = registry.list_tools()
    assert len(tools_list) == 3
    tool_names = [t["name"] for t in tools_list]
    assert "document_search" in tool_names
    assert "web_search" in tool_names

def test_tool_registry_unknown_tool_rejection():
    registry = ToolRegistry()
    res = registry.execute_tool("unknown_fake_tool", {"query": "test"})
    assert res.status == "error"
    assert "not registered" in res.error_message
