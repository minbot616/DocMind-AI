import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.models import RetrievedChunk
from retrieval.reranker import Reranker

def test_reranker_graceful_fallback_on_model_failure():
    candidates = [
        RetrievedChunk(chunk_id="c1", document_id=1, text="Chunk 1", score=0.05, retrieval_method="rrf_hybrid"),
        RetrievedChunk(chunk_id="c2", document_id=1, text="Chunk 2", score=0.03, retrieval_method="rrf_hybrid"),
    ]

    reranker = Reranker(enabled=True)
    
    # Mock model loading failure
    reranker._load_model = MagicMock(return_value=None)

    reranked = reranker.rerank("any query", candidates, top_k=2)

    # Should fall back cleanly to original candidates without raising an exception
    assert len(reranked) == 2
    assert reranked[0].chunk_id == "c1"
    assert reranked[1].chunk_id == "c2"

def test_reranker_graceful_fallback_on_predict_exception():
    candidates = [
        RetrievedChunk(chunk_id="c1", document_id=1, text="Chunk 1", score=0.05, retrieval_method="rrf_hybrid"),
    ]

    reranker = Reranker(enabled=True)
    mock_model = MagicMock()
    mock_model.predict.side_effect = RuntimeError("CUDA OOM / inference error")
    reranker._model = mock_model

    reranked = reranker.rerank("any query", candidates, top_k=1)

    assert len(reranked) == 1
    assert reranked[0].chunk_id == "c1"
