import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools.document_metadata import DocumentMetadataTool

def test_document_metadata_tool_inventory_lookup():
    mock_docs = [
        {"id": 1, "filename": "report.pdf", "file_type": ".pdf", "pages_count": 10, "chunks_count": 25, "file_size": 20480, "created_at": "2026-08-22"},
        {"id": 2, "filename": "notes.txt", "file_type": ".txt", "pages_count": 2, "chunks_count": 4, "file_size": 1024, "created_at": "2026-08-22"}
    ]

    tool = DocumentMetadataTool()
    with patch("agent.tools.document_metadata.DatabaseManager.get_documents", return_value=mock_docs):
        res = tool.execute({}, context={"user_id": 1})

    assert res.status == "success"
    assert res.data["total_documents"] == 2
    assert res.data["total_pages"] == 12
    assert res.data["total_chunks"] == 29
    assert len(res.data["documents"]) == 2
    assert res.data["documents"][0]["filename"] == "report.pdf"
