from typing import List, Dict, Tuple, Any
from retrieval.models import RetrievedChunk

def get_chunk_key(chunk: RetrievedChunk) -> str:
    """Generates a unique deduplication key for a retrieved chunk."""
    if chunk.chunk_id:
        return chunk.chunk_id
    doc_name = chunk.metadata.get("source", "unknown")
    page = chunk.metadata.get("page", 1)
    snippet = chunk.text[:100].strip()
    return f"{doc_name}_p{page}_{hash(snippet)}"

def reciprocal_rank_fusion(
    dense_results: List[RetrievedChunk],
    lexical_results: List[RetrievedChunk],
    k_rrf: int = 60,
    top_k: int = 5
) -> List[RetrievedChunk]:
    """Combines Dense Vector and Lexical BM25 search results using Reciprocal Rank Fusion (RRF).
    
    Formula:
        RRF_Score(d) = sum(1.0 / (k_rrf + rank(d))) for each retrieval list
    
    Args:
        dense_results: Ordered list of chunks retrieved via vector search.
        lexical_results: Ordered list of chunks retrieved via BM25 lexical search.
        k_rrf: Smoothing constant (default 60).
        top_k: Number of final merged chunks to return.
    """
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, RetrievedChunk] = {}

    # Process Dense Results
    for rank, chunk in enumerate(dense_results, start=1):
        key = get_chunk_key(chunk)
        chunk_map[key] = chunk
        score = 1.0 / (k_rrf + rank)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + score

    # Process Lexical Results
    for rank, chunk in enumerate(lexical_results, start=1):
        key = get_chunk_key(chunk)
        if key not in chunk_map:
            chunk_map[key] = chunk
        score = 1.0 / (k_rrf + rank)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + score

    # Sort keys by merged RRF score descending
    sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]

    fused_chunks: List[RetrievedChunk] = []
    for key in sorted_keys:
        base_chunk = chunk_map[key]
        fused_chunks.append(RetrievedChunk(
            chunk_id=base_chunk.chunk_id,
            document_id=base_chunk.document_id,
            text=base_chunk.text,
            metadata=base_chunk.metadata.copy(),
            score=rrf_scores[key],
            retrieval_method="rrf_hybrid"
        ))

    return fused_chunks
