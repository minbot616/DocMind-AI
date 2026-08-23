import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.models import RetrievedChunk
from retrieval.citation_validator import CitationValidator

def test_citation_tag_regex_extraction():
    chunks = [
        RetrievedChunk(chunk_id="chk_1", document_id=1, text="FastAPI routes handle HTTP requests.", metadata={"source": "api.pdf", "page": 3}),
        RetrievedChunk(chunk_id="chk_2", document_id=1, text="Pydantic models validate JSON data.", metadata={"source": "api.pdf", "page": 5}),
    ]

    context_text, evidence_map = CitationValidator.build_evidence_context(chunks)

    assert "[DOC-1]" in context_text
    assert "[DOC-2]" in context_text
    assert "DOC-1" in evidence_map
    assert "DOC-2" in evidence_map

    sample_answer = "FastAPI processes web routes [CITE:DOC-1], and Pydantic handles request validation [DOC-2]."
    citations, validity_rate, coverage_rate = CitationValidator.extract_and_validate(sample_answer, evidence_map)

    assert len(citations) == 2
    assert citations[0]["citation_id"] == "DOC-1"
    assert citations[0]["document"] == "api.pdf"
    assert citations[0]["page"] == 3
    assert citations[0]["valid"] is True

    assert citations[1]["citation_id"] == "DOC-2"
    assert citations[1]["page"] == 5
    assert citations[1]["valid"] is True

    assert validity_rate == 1.0
    assert coverage_rate == 1.0
