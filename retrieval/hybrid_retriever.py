import re
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from retrieval.models import RetrievedChunk
from retrieval.bm25_store import BM25Index
from retrieval.dense_retriever import DenseRetriever
from retrieval.fusion import reciprocal_rank_fusion

class HybridRetriever:
    """Combines Dense FAISS Vector Retrieval and Lexical BM25 Search using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, vector_store: Optional[FAISS] = None, bm25_index: Optional[BM25Index] = None):
        self.vector_store = vector_store
        self.bm25_index = bm25_index

    @staticmethod
    def preprocess_query(query: str) -> str:
        """Normalizes query whitespace while preserving case and technical characters."""
        if not query:
            return ""
        return " ".join(query.strip().split())

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Runs hybrid search over dense and lexical indexes and returns fused top-k chunks."""
        cleaned_query = self.preprocess_query(query)
        if not cleaned_query:
            return []

        # 1. Execute Dense Vector Retrieval
        dense_results: List[RetrievedChunk] = []
        if self.vector_store:
            dense_retriever = DenseRetriever(self.vector_store)
            dense_results = dense_retriever.retrieve(cleaned_query, top_k=top_k * 2)

        # 2. Execute Lexical BM25 Retrieval
        lexical_results: List[RetrievedChunk] = []
        if self.bm25_index:
            lexical_results = self.bm25_index.search(cleaned_query, top_k=top_k * 2)

        # 3. Handle Single Engine Fallbacks
        if dense_results and not lexical_results:
            return dense_results[:top_k]
        if lexical_results and not dense_results:
            return lexical_results[:top_k]
        if not dense_results and not lexical_results:
            return []

        # 4. Execute Reciprocal Rank Fusion (RRF)
        return reciprocal_rank_fusion(
            dense_results=dense_results,
            lexical_results=lexical_results,
            k_rrf=60,
            top_k=top_k
        )
