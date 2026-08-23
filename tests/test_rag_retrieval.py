import sys
import os
from unittest.mock import MagicMock, patch
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_pipeline import RAGPipeline
from embeddings import EmbeddingManager
from retrieval.bm25_store import BM25Index

def test_rag_pipeline_hybrid_query():
    embed_model = EmbeddingManager.get_embeddings("all-MiniLM-L6-v2")
    docs = [
        Document(page_content="Vector databases index embeddings for fast ANN search.", metadata={"document_id": 1, "chunk_id": "doc_1_chk_0", "source": "rag_doc.pdf", "page": 1})
    ]
    vector_store = FAISS.from_documents(docs, embed_model)

    bm25 = BM25Index()
    bm25.add_chunks([{
        "text": "Vector databases index embeddings for fast ANN search.",
        "metadata": {"document_id": 1, "chunk_id": "doc_1_chk_0", "source": "rag_doc.pdf", "page": 1}
    }])

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Vector databases enable fast similarity search."
    mock_llm.invoke.return_value = mock_response

    with patch("rag_pipeline.LLMManager.get_llm", return_value=mock_llm):
        answer, citations, duration = RAGPipeline.query(
            query_text="vector search",
            vector_store=vector_store,
            llm_provider="Ollama",
            llm_model="llama3",
            bm25_index=bm25,
            k=1,
            enable_reranker=False
        )


    assert answer == "Vector databases enable fast similarity search."
    assert len(citations) == 1
    assert citations[0]["document"] == "rag_doc.pdf"
    assert citations[0]["page"] == 1
    assert duration >= 0.0
