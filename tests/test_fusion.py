import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.models import RetrievedChunk
from retrieval.fusion import reciprocal_rank_fusion

def test_rrf_fusion_and_deduplication():
    dense_results = [
        RetrievedChunk(chunk_id="chk_1", document_id=1, text="Chunk 1 content", score=0.1, retrieval_method="dense"),
        RetrievedChunk(chunk_id="chk_2", document_id=1, text="Chunk 2 content", score=0.3, retrieval_method="dense"),
    ]

    lexical_results = [
        RetrievedChunk(chunk_id="chk_2", document_id=1, text="Chunk 2 content", score=4.5, retrieval_method="bm25"),
        RetrievedChunk(chunk_id="chk_3", document_id=1, text="Chunk 3 content", score=2.1, retrieval_method="bm25"),
    ]

    fused = reciprocal_rank_fusion(dense_results, lexical_results, k_rrf=60, top_k=3)

    assert len(fused) == 3
    # chk_2 is present in both lists (rank 2 in dense, rank 1 in lexical)
    # dense score: 1/(60+2) = 1/62 = 0.016129
    # lexical score: 1/(60+1) = 1/61 = 0.016393
    # sum = 0.032522 -> chk_2 should rank 1st!
    assert fused[0].chunk_id == "chk_2"
    assert fused[0].retrieval_method == "rrf_hybrid"
    assert fused[0].score > fused[1].score
