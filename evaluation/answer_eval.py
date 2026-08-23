import re
from typing import List
from evaluation.models import EvalCase, AnswerMetrics

class AnswerEvaluator:
    """Evaluates factual correctness, keyword matching, and negative refusal accuracy."""

    @staticmethod
    def evaluate_answer(case: EvalCase, answer_text: str) -> AnswerMetrics:
        if not answer_text:
            return AnswerMetrics()

        # Negative case refusal evaluation
        if case.category == "negative" or case.expected_refusal:
            refusal_indicators = ["not available", "not mentioned", "no information", "cannot find", "does not contain"]
            refused = any(ind in answer_text.lower() for ind in refusal_indicators)
            return AnswerMetrics(
                correctness_score=1.0 if refused else 0.0,
                relevance_score=1.0,
                unsupported_refusal_accuracy=1.0 if refused else 0.0
            )


        # Keyword presence evaluation
        if not case.expected_keywords:
            return AnswerMetrics(correctness_score=1.0, relevance_score=1.0)

        matched_keywords = 0
        answer_lower = answer_text.lower()
        for kw in case.expected_keywords:
            if kw.lower() in answer_lower:
                matched_keywords += 1

        correctness = matched_keywords / len(case.expected_keywords)
        relevance = 1.0 if matched_keywords > 0 else 0.0

        return AnswerMetrics(
            correctness_score=correctness,
            relevance_score=relevance,
            unsupported_refusal_accuracy=1.0
        )
