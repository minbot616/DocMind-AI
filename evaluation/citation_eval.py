import re
from typing import List, Dict, Any
from evaluation.models import CitationMetrics

class CitationEvaluator:
    """Calculates citation validity, coverage, and unsupported citation rate metrics."""

    @staticmethod
    def evaluate_citations(citations: List[Dict[str, Any]], answer_text: str) -> CitationMetrics:
        if not citations:
            has_cite_tags = bool(re.search(r'\[CITE:DOC-\d+\]', answer_text))
            return CitationMetrics(
                citation_validity=1.0 if not has_cite_tags else 0.0,
                citation_coverage=0.0,
                unsupported_citation_rate=0.0
            )

        valid_count = sum(1 for c in citations if c.get("valid", True))
        total = len(citations)

        validity = valid_count / total if total > 0 else 1.0
        unsupported_rate = (total - valid_count) / total if total > 0 else 0.0
        coverage = 1.0 if bool(re.search(r'\[CITE:DOC-\d+\]', answer_text)) or citations else 0.0

        return CitationMetrics(
            citation_validity=validity,
            citation_coverage=coverage,
            unsupported_citation_rate=unsupported_rate,
            valid_citations=valid_count,
            total_citations=total
        )

