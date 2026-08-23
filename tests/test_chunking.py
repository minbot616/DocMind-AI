import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_processor import DocumentProcessor

def test_chunking_metadata_preservation():
    pages = [
        {
            "text": "First page text content about machine learning and artificial intelligence.",
            "metadata": {"source": "report.pdf", "page": 1, "type": "pdf"}
        },
        {
            "text": "Second page text content about deep neural networks and transformer architecture.",
            "metadata": {"source": "report.pdf", "page": 2, "type": "pdf"}
        }
    ]

    chunks = DocumentProcessor.chunk_documents(pages, chunk_size=200, chunk_overlap=20, document_id=42)

    assert len(chunks) >= 2
    for idx, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        assert meta["document_id"] == 42
        assert meta["filename"] == "report.pdf"
        assert meta["chunk_id"] == f"doc_42_chk_{idx}"
        assert meta["chunk_index"] == idx
        assert "page" in meta
        assert "file_type" in meta
