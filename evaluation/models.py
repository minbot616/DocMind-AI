from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class EvalCase:
    """Represents a single benchmark test case for evaluation."""
    id: str
    category: str  # factual, semantic, keyword, negative, calculation, metadata, memory, citation
    question: str
    expected_answer: Optional[str] = None
    expected_keywords: List[str] = field(default_factory=list)
    expected_doc_ids: List[int] = field(default_factory=list)
    expected_pages: List[int] = field(default_factory=list)
    requires_document_evidence: bool = True
    expected_refusal: bool = False

@dataclass
class RetrievalMetrics:
    """Retrieval accuracy metrics (Recall@K, MRR, Hit Rate) with exact numerators/denominators."""
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mrr: float = 0.0
    hit_rate: float = 0.0
    recall_1_hits: int = 0
    recall_1_total: int = 0
    recall_3_hits: int = 0
    recall_3_total: int = 0
    recall_5_hits: int = 0
    recall_5_total: int = 0

@dataclass
class CitationMetrics:
    """Citation accuracy and grounding metrics."""
    citation_validity: float = 0.0
    citation_coverage: float = 0.0
    unsupported_citation_rate: float = 0.0
    valid_citations: int = 0
    total_citations: int = 0

@dataclass
class AnswerMetrics:
    """Answer factual correctness and groundedness metrics."""
    correctness_score: float = 0.0
    relevance_score: float = 0.0
    unsupported_refusal_accuracy: float = 0.0

@dataclass
class EvalResult:
    """Complete evaluation result for a single test case."""
    case_id: str
    category: str
    question: str
    answer: str
    eval_mode: str = "offline"
    citations: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    retrieval_before_rerank: Optional[RetrievalMetrics] = None
    retrieval_after_rerank: Optional[RetrievalMetrics] = None
    citation_metrics: Optional[CitationMetrics] = None
    answer_metrics: Optional[AnswerMetrics] = None
    latency_seconds: float = 0.0

