from typing import List, Dict, Any, Optional
from evaluation.models import RetrievalMetrics

class RetrievalEvaluator:
    """Calculates Recall@K, MRR, and Hit Rate metrics for retrieval candidate lists."""

    @staticmethod
    def evaluate_retrieval(
        retrieved_chunks: List[Any],
        expected_doc_ids: List[int],
        expected_pages: Optional[List[int]] = None
    ) -> RetrievalMetrics:
        if not expected_doc_ids or not retrieved_chunks:
            return RetrievalMetrics()

        first_hit_rank = 0
        hit_at_1 = False
        hit_at_3 = False
        hit_at_5 = False

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            doc_id = getattr(chunk, "document_id", None)
            if doc_id is None:
                meta = getattr(chunk, "metadata", {}) if hasattr(chunk, "metadata") else chunk.get("metadata", {})
                doc_id = meta.get("document_id")
            if doc_id is None and isinstance(chunk, dict):
                doc_id = chunk.get("document_id")

            if doc_id in expected_doc_ids:

                if first_hit_rank == 0:
                    first_hit_rank = idx
                if idx <= 1:
                    hit_at_1 = True
                if idx <= 3:
                    hit_at_3 = True
                if idx <= 5:
                    hit_at_5 = True

        mrr = (1.0 / first_hit_rank) if first_hit_rank > 0 else 0.0
        hit_rate = 1.0 if first_hit_rank > 0 else 0.0

        return RetrievalMetrics(
            recall_at_1=1.0 if hit_at_1 else 0.0,
            recall_at_3=1.0 if hit_at_3 else 0.0,
            recall_at_5=1.0 if hit_at_5 else 0.0,
            mrr=mrr,
            hit_rate=hit_rate,
            recall_1_hits=1 if hit_at_1 else 0,
            recall_1_total=1,
            recall_3_hits=1 if hit_at_3 else 0,
            recall_3_total=1,
            recall_5_hits=1 if hit_at_5 else 0,
            recall_5_total=1
        )

