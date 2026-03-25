"""Tests for documentation evaluation modules."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDocumentationEvaluator:
    def test_bertscore_perfect_match_is_one(self):
        """BERTScore of identical strings should be close to 1.0."""
        from evaluation.doc_evaluator import DocumentationEvaluator
        evaluator = DocumentationEvaluator()
        result = evaluator.compute_bertscore(["hello world"], ["hello world"])
        assert "f1" in result
        f1 = result["f1"][0]
        assert f1 > 0.9

    def test_rouge_recall_correct(self):
        """ROUGE recall should be > 0 when generated contains reference tokens."""
        from evaluation.doc_evaluator import DocumentationEvaluator
        evaluator = DocumentationEvaluator()
        scores = evaluator.compute_rouge("a b c d e f", "a b c")
        assert scores["rouge1"] > 0
        assert scores["rougeL"] > 0

    def test_coverage_zero_for_undocumented(self, tmp_path):
        """Coverage should be 0 for undocumented functions."""
        from evaluation.doc_evaluator import DocumentationEvaluator
        evaluator = DocumentationEvaluator()
        ast_results = {
            "test.py": {
                "functions": [
                    {"name": "undoc_func", "docstring": "", "source": "def undoc_func(): pass"},
                ],
                "classes": [],
                "module_docstring": "",
            }
        }
        coverage = evaluator.compute_coverage(str(tmp_path), ast_results)
        assert coverage["functions"] == 0.0

    def test_rubric_max_score_is_30(self):
        """Quality rubric max score should be 30."""
        from evaluation.doc_evaluator import RubricScore
        rubric = RubricScore()
        assert rubric.max_score == 30

    def test_rubric_perfect_doc_scores_high(self):
        """A well-formatted docstring should score above 15/30."""
        from evaluation.doc_evaluator import DocumentationEvaluator
        evaluator = DocumentationEvaluator()
        perfect_doc = (
            "Add two integers together.\n\n"
            "Args:\n    x: First integer.\n    y: Second integer.\n\n"
            "Returns:\n    int: Sum of x and y.\n\n"
            "Raises:\n    TypeError: If args are not integers.\n\n"
            "Example:\n    >>> add(1, 2)\n    3\n"
        )
        score = evaluator.apply_quality_rubric(perfect_doc, {"args": ["x", "y"]})
        assert score.total_score > 15
