from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from retrieval.models import RetrievedChunk

class DenseRetriever:
    """Handles dense vector similarity search using FAISS."""

    def __init__(self, vector_store: FAISS):
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Queries FAISS vector store and returns standardized RetrievedChunk results."""
        if not query or not self.vector_store:
            return []

        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
        results = []

        for idx, (doc, score) in enumerate(docs_with_scores):
            meta = doc.metadata.copy() if doc.metadata else {}
            doc_id = meta.get("document_id", 0)
            chunk_id = meta.get("chunk_id") or f"doc_{doc_id}_chk_{idx}"
            
            results.append(RetrievedChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                text=doc.page_content,
                metadata=meta,
                score=float(score),  # Preserve raw distance / similarity metric
                retrieval_method="dense"
            ))

        return results
