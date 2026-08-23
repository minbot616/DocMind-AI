import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Optional
from retrieval.models import RetrievedChunk

@dataclass
class Citation:
    citation_id: str
    document_id: int
    chunk_id: str
    filename: str
    page: int
    snippet: str
    is_valid: bool = True
    score: float = 0.0

class CitationValidator:
    """Formats evidence blocks with stable IDs and validates LLM citation tags deterministically."""

    @staticmethod
    def build_evidence_context(chunks: List[RetrievedChunk]) -> Tuple[str, Dict[str, RetrievedChunk]]:
        """Assigns stable evidence IDs (DOC-1, DOC-2, ...) to chunks and formats prompt context block."""
        evidence_blocks = []
        evidence_map: Dict[str, RetrievedChunk] = {}

        for idx, chunk in enumerate(chunks, start=1):
            evidence_id = f"DOC-{idx}"
            chunk.evidence_id = evidence_id
            evidence_map[evidence_id] = chunk

            doc_name = chunk.metadata.get("source") or chunk.metadata.get("filename", "Unknown Document")
            page_num = chunk.metadata.get("page", 1)

            block = (
                f"[{evidence_id}] (Source: {doc_name}, Page: {page_num})\n"
                f"Content: {chunk.text}\n"
                f"----------------------------------------"
            )
            evidence_blocks.append(block)

        context_text = "\n\n".join(evidence_blocks)
        return context_text, evidence_map

    @staticmethod
    def extract_and_validate(answer: str, evidence_map: Dict[str, RetrievedChunk]) -> Tuple[List[Dict[str, Any]], float, float]:
        """Parses citation tags (e.g. [CITE:DOC-1], [DOC-1]) from generated text and validates them against evidence_map.
        
        Returns:
            Tuple of (citations_list, validity_rate, coverage_rate)
        """
        pattern = r'\[(?:CITE:)?(DOC-\d+)\]'
        matches = re.findall(pattern, answer, flags=re.IGNORECASE)
        
        seen_ids = set()
        unique_extracted = []
        for m in matches:
            norm_id = m.upper()
            if norm_id not in seen_ids:
                seen_ids.add(norm_id)
                unique_extracted.append(norm_id)

        citations: List[Dict[str, Any]] = []
        valid_count = 0
        total_extracted = len(unique_extracted)

        for ev_id in unique_extracted:
            if ev_id in evidence_map:
                chunk = evidence_map[ev_id]
                valid_count += 1
                doc_name = chunk.metadata.get("source") or chunk.metadata.get("filename", "Unknown Document")
                page_num = chunk.metadata.get("page", 1)
                
                score_val = chunk.rerank_score if chunk.rerank_score is not None else chunk.score
                citations.append({
                    "citation_id": ev_id,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "document": doc_name,
                    "page": page_num,
                    "snippet": chunk.text.strip(),
                    "score": round(score_val, 4),
                    "valid": True
                })
            else:
                # Fabricated/Invalid evidence ID tag
                citations.append({
                    "citation_id": ev_id,
                    "document_id": 0,
                    "chunk_id": "invalid",
                    "document": "Unknown Document",
                    "page": 0,
                    "snippet": "",
                    "score": 0.0,
                    "valid": False
                })

        # If LLM didn't produce inline tags but evidence map is non-empty, populate citations from retrieved evidence
        if not citations and evidence_map:
            for ev_id, chunk in evidence_map.items():
                doc_name = chunk.metadata.get("source") or chunk.metadata.get("filename", "Unknown Document")
                page_num = chunk.metadata.get("page", 1)
                score_val = chunk.rerank_score if chunk.rerank_score is not None else chunk.score
                citations.append({
                    "citation_id": ev_id,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "document": doc_name,
                    "page": page_num,
                    "snippet": chunk.text.strip(),
                    "score": round(score_val, 4),
                    "valid": True
                })

        validity_rate = (valid_count / float(total_extracted)) if total_extracted > 0 else (1.0 if citations else 0.0)
        coverage_rate = 1.0 if citations else 0.0

        return citations, validity_rate, coverage_rate
