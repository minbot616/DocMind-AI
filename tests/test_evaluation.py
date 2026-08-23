import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.dataset import DatasetLoader
from evaluation.retrieval_eval import RetrievalEvaluator
from evaluation.citation_eval import CitationEvaluator
from evaluation.answer_eval import AnswerEvaluator
from evaluation.models import EvalCase
from retrieval.models import RetrievedChunk

def test_dataset_loading():
    cases = DatasetLoader.load_dataset()
    assert len(cases) == 25
    assert cases[0].id == "case_001"
    cats = {c.category for c in cases}
    assert "factual" in cats
    assert "semantic" in cats
    assert "keyword" in cats
    assert "negative" in cats
    assert "calculation" in cats
    assert "metadata" in cats
    assert "memory" in cats
    assert "citation" in cats

def test_retrieval_metrics_calculation():
    chunks = [
        RetrievedChunk(chunk_id="chk1", document_id=1, text="text1", score=0.9, metadata={"document_id": 1}),
        RetrievedChunk(chunk_id="chk2", document_id=2, text="text2", score=0.8, metadata={"document_id": 2}),
    ]
    metrics = RetrievalEvaluator.evaluate_retrieval(chunks, expected_doc_ids=[2])

    assert metrics.recall_at_1 == 0.0
    assert metrics.recall_at_3 == 1.0
    assert metrics.mrr == 0.5
    assert metrics.recall_1_hits == 0
    assert metrics.recall_3_hits == 1
    assert metrics.recall_3_total == 1


def test_citation_metrics_calculation():
    citations = [{"citation_id": "[CITE:DOC-1]", "valid": True}]
    metrics = CitationEvaluator.evaluate_citations(citations, "Answer with [CITE:DOC-1]")
    assert metrics.citation_validity == 1.0
    assert metrics.citation_coverage == 1.0

def test_answer_metrics_factual():
    case = EvalCase(
        id="c1", category="factual", question="What is X?", expected_keywords=["RAG", "FAISS"]
    )
    metrics = AnswerEvaluator.evaluate_answer(case, "DocMind uses RAG with FAISS search.")
    assert metrics.correctness_score == 1.0
    assert metrics.relevance_score == 1.0

def test_answer_metrics_negative_refusal():
    case = EvalCase(
        id="c2", category="negative", question="What is salary?", expected_keywords=[]
    )
    metrics = AnswerEvaluator.evaluate_answer(case, "The requested information is not available in the documents.")
    assert metrics.unsupported_refusal_accuracy == 1.0
