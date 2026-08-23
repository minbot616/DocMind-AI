import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools.document_search import DocumentSearchTool

def test_document_search_tool_execution():
    tool = DocumentSearchTool()

    mock_rag_response = ("FastAPI processes asynchronous HTTP requests [CITE:DOC-1].", [{"citation_id": "DOC-1", "document": "api.pdf", "page": 1, "valid": True}], 0.12)

    with patch("agent.tools.document_search.DatabaseManager.get_documents", return_value=[{"id": 1}]), \
         patch("agent.tools.document_search.DatabaseManager.get_settings", return_value={}), \
         patch("agent.tools.document_search.EmbeddingManager.get_embeddings", return_value=MagicMock()), \
         patch("agent.tools.document_search.VectorStoreManager.load_merged_vector_store", return_value=MagicMock()), \
         patch("agent.tools.document_search.VectorStoreManager.load_merged_bm25_store", return_value=MagicMock()), \
         patch("agent.tools.document_search.RAGPipeline.query", return_value=mock_rag_response):

        res = tool.execute({"query": "What is FastAPI?"}, context={"user_id": 1, "selected_doc_ids": [1]})

    assert res.status == "success"
    assert "FastAPI processes" in res.data["answer"]
    assert len(res.data["citations"]) == 1
    assert res.data["citations"][0]["document"] == "api.pdf"
