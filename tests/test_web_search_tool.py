import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools.web_search import WebSearchTool

def test_web_search_tool_provider_formatting():
    tool = WebSearchTool()
    res = tool.execute({"query": "Python 3.13 features"})

    assert res.status == "success"
    assert "count" in res.data
    assert len(res.data["results"]) >= 1
    assert "evidence_id" in res.data["results"][0]
    assert res.data["results"][0]["evidence_id"].startswith("WEB-")
