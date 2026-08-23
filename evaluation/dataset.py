import os
import json
from typing import List
from evaluation.models import EvalCase

class DatasetLoader:
    """Loader and validator for structured evaluation datasets."""

    @staticmethod
    def load_dataset(dataset_path: str = None) -> List[EvalCase]:
        if dataset_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            dataset_path = os.path.join(base_dir, "datasets", "eval_cases.json")

        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Evaluation dataset not found at '{dataset_path}'.")

        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cases = []
        for item in data:
            case = EvalCase(
                id=item["id"],
                category=item["category"],
                question=item["question"],
                expected_answer=item.get("expected_answer"),
                expected_keywords=item.get("expected_keywords", []),
                expected_doc_ids=item.get("expected_doc_ids", []),
                expected_pages=item.get("expected_pages", []),
                requires_document_evidence=item.get("requires_document_evidence", True),
                expected_refusal=item.get("expected_refusal", False)
            )

            cases.append(case)

        return cases
