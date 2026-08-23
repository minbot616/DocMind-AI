from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class RetrievedChunk:
    """Standard container for a retrieved document chunk across vector, BM25, hybrid, and reranked search engines."""
    chunk_id: str
    document_id: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    retrieval_method: str = "dense"
    rerank_score: Optional[float] = None
    evidence_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "text": self.text,
            "metadata": self.metadata,
            "score": self.score,
            "retrieval_method": self.retrieval_method,
            "rerank_score": self.rerank_score,
            "evidence_id": self.evidence_id
        }
