import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.models import RetrievedChunk
from retrieval.reranker import Reranker

def test_reranker_rescoring_and_top_k():
    candidates = [
        RetrievedChunk(chunk_id="c1", document_id=1, text="Unrelated text about baking cakes.", score=0.05, retrieval_method="rrf_hybrid"),
        RetrievedChunk(chunk_id="c2", document_id=1, text="FastAPI framework endpoints using Pydantic schemas.", score=0.03, retrieval_method="rrf_hybrid"),
        RetrievedChunk(chunk_id="c3", document_id=1, text="Python programming language features.", score=0.01, retrieval_method="rrf_hybrid"),
    ]

    reranker = Reranker(enabled=True)
    
    # Mock cross encoder predict to return higher score for c2 (FastAPI)
    mock_model = MagicMock()
    mock_model.predict.return_value = [-1.5, 3.8, 0.4]
    reranker._model = mock_model

    reranked = reranker.rerank("FastAPI endpoints", candidates, top_k=2)

    assert len(reranked) == 2
    assert reranked[0].chunk_id == "c2"
    assert reranked[0].rerank_score == 3.8
    assert reranked[0].retrieval_method == "cross_encoder_rerank"
    assert reranked[1].chunk_id == "c3"
    assert reranked[1].rerank_score == 0.4
