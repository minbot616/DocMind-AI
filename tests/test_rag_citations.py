import sys
import os
from unittest.mock import MagicMock, patch
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_pipeline import RAGPipeline
from embeddings import EmbeddingManager
from retrieval.bm25_store import BM25Index

def test_rag_pipeline_two_stage_with_validated_citations():
    embed_model = EmbeddingManager.get_embeddings("all-MiniLM-L6-v2")
    docs = [
        Document(page_content="FastAPI is an asynchronous Python web framework.", metadata={"document_id": 1, "chunk_id": "doc_1_chk_0", "source": "fastapi_guide.pdf", "page": 2})
    ]
    vector_store = FAISS.from_documents(docs, embed_model)

    bm25 = BM25Index()
    bm25.add_chunks([{
        "text": "FastAPI is an asynchronous Python web framework.",
        "metadata": {"document_id": 1, "chunk_id": "doc_1_chk_0", "source": "fastapi_guide.pdf", "page": 2}
    }])

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "FastAPI is an async framework [CITE:DOC-1]."
    mock_llm.invoke.return_value = mock_response

    with patch("rag_pipeline.LLMManager.get_llm", return_value=mock_llm):
        answer, citations, duration = RAGPipeline.query(
            query_text="What is FastAPI?",
            vector_store=vector_store,
            llm_provider="Ollama",
            llm_model="llama3",
            bm25_index=bm25,
            k=1,
            enable_reranker=False  # Disable model download in test for speed
        )

    assert "FastAPI is an async framework" in answer
    assert len(citations) == 1
    assert citations[0]["citation_id"] == "DOC-1"
    assert citations[0]["document"] == "fastapi_guide.pdf"
    assert citations[0]["page"] == 2
    assert citations[0]["valid"] is True
