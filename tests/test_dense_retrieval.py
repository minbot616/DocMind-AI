import sys
import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.dense_retriever import DenseRetriever
from embeddings import EmbeddingManager

def test_dense_retriever_query():
    embed_model = EmbeddingManager.get_embeddings("all-MiniLM-L6-v2")
    docs = [
        Document(page_content="Python is a high-level programming language.", metadata={"document_id": 1, "chunk_id": "doc_1_chk_0", "source": "test.txt", "page": 1}),
        Document(page_content="Database indexing speeds up SQL query performance.", metadata={"document_id": 1, "chunk_id": "doc_1_chk_1", "source": "test.txt", "page": 1})
    ]

    vector_store = FAISS.from_documents(docs, embed_model)
    retriever = DenseRetriever(vector_store)

    results = retriever.retrieve("programming language", top_k=1)
    assert len(results) == 1
    assert "Python" in results[0].text
    assert results[0].retrieval_method == "dense"
    assert results[0].chunk_id == "doc_1_chk_0"
    assert isinstance(results[0].score, float)
