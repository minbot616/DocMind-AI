import logging
from typing import List, Optional
from retrieval.models import RetrievedChunk

logger = logging.getLogger("DocMindBackend")

class Reranker:
    """Second-stage ranking system using a local Cross-Encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", enabled: bool = True):
        self.model_name = model_name
        self.enabled = enabled
        self._model = None

    def _load_model(self):
        if not self.enabled or self._model is not None:
            return self._model
        
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Cross-Encoder reranker model '{self.model_name}'...")
            self._model = CrossEncoder(self.model_name)
            logger.info("Cross-Encoder reranker loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load Cross-Encoder model '{self.model_name}': {str(e)}. Fallback to RRF candidate order.")
            self._model = None
            self.enabled = False
            
        return self._model

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int = 5) -> List[RetrievedChunk]:
        """Scores (query, candidate_chunk) pairs and returns top-k reranked chunks.
        
        Falls back smoothly to RRF candidate order if reranker execution fails.
        """
        if not query or not candidates:
            return candidates[:top_k] if candidates else []

        model = self._load_model()
        if not model:
            # Fallback path
            return candidates[:top_k]

        try:
            pairs = [(query, chunk.text) for chunk in candidates]
            scores = model.predict(pairs)

            reranked_chunks = []
            for chunk, score in zip(candidates, scores):
                # Create a copy with rerank_score attached
                c_copy = RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    metadata=chunk.metadata.copy(),
                    score=chunk.score,
                    retrieval_method="cross_encoder_rerank",
                    rerank_score=float(score),
                    evidence_id=chunk.evidence_id
                )
                reranked_chunks.append(c_copy)

            # Sort by Cross-Encoder score descending
            reranked_chunks.sort(key=lambda c: c.rerank_score if c.rerank_score is not None else -999.0, reverse=True)
            return reranked_chunks[:top_k]

        except Exception as e:
            logger.warning(f"Error during Cross-Encoder reranking: {str(e)}. Falling back to hybrid RRF order.")
            return candidates[:top_k]
