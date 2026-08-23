import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.models import RetrievedChunk
from retrieval.citation_validator import CitationValidator

def test_citation_validation_rejection_of_hallucinated_tags():
    chunks = [
        RetrievedChunk(chunk_id="chk_1", document_id=1, text="Database connections are pooled.", metadata={"source": "db.pdf", "page": 10})
    ]

    _, evidence_map = CitationValidator.build_evidence_context(chunks)

    # DOC-1 is valid, DOC-99 is fabricated by LLM
    hallucinated_answer = "Database pooling is supported [CITE:DOC-1], but quantum storage requires special hardware [CITE:DOC-99]."

    citations, validity_rate, _ = CitationValidator.extract_and_validate(hallucinated_answer, evidence_map)

    assert len(citations) == 2
    assert citations[0]["citation_id"] == "DOC-1"
    assert citations[0]["valid"] is True

    assert citations[1]["citation_id"] == "DOC-99"
    assert citations[1]["valid"] is False
    assert citations[1]["chunk_id"] == "invalid"

    assert validity_rate == 0.5  # 1 valid out of 2 total
