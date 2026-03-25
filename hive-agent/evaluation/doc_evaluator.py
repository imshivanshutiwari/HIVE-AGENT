"""BERTScore + ROUGE documentation quality evaluation."""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RubricScore:
    completeness: int = 0
    accuracy: int = 0
    clarity: int = 0
    examples: int = 0
    edge_cases: int = 0
    consistency: int = 0

    @property
    def total_score(self) -> int:
        return (
            self.completeness + self.accuracy + self.clarity
            + self.examples + self.edge_cases + self.consistency
        )

    @property
    def max_score(self) -> int:
        return 30


@dataclass
class CoverageReport:
    functions: float = 0.0
    classes: float = 0.0
    modules: float = 0.0
    per_file: Dict[str, float] = field(default_factory=dict)


class DocumentationEvaluator:
    """BERTScore + ROUGE evaluation of generated documentation."""

    def compute_bertscore(
        self, generated: List[str], reference: List[str]
    ) -> Dict[str, Any]:
        try:
            from bert_score import score as bert_score_fn
            P, R, F1 = bert_score_fn(
                generated,
                reference,
                lang="en",
                model_type="microsoft/deberta-xlarge-mnli",
                verbose=False,
            )
            return {
                "precision": P.tolist(),
                "recall": R.tolist(),
                "f1": F1.tolist(),
            }
        except Exception as e:
            logger.warning(f"BERTScore failed: {e}. Using fallback.")
            return self._bertscore_fallback(generated, reference)

    def _bertscore_fallback(
        self, generated: List[str], reference: List[str]
    ) -> Dict[str, Any]:
        """Simple word-overlap fallback for BERTScore."""
        f1_scores = []
        for gen, ref in zip(generated, reference):
            gen_tokens = set(gen.lower().split())
            ref_tokens = set(ref.lower().split())
            if not gen_tokens or not ref_tokens:
                f1_scores.append(0.0)
                continue
            intersection = gen_tokens & ref_tokens
            precision = len(intersection) / len(gen_tokens)
            recall = len(intersection) / len(ref_tokens)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            f1_scores.append(f1)
        return {
            "precision": f1_scores,
            "recall": f1_scores,
            "f1": f1_scores,
        }

    def compute_rouge(self, generated: str, reference: str) -> Dict[str, float]:
        try:
            from rouge_score import rouge_scorer
            scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
            scores = scorer.score(reference, generated)
            return {
                "rouge1": scores["rouge1"].fmeasure,
                "rouge2": scores["rouge2"].fmeasure,
                "rougeL": scores["rougeL"].fmeasure,
            }
        except Exception as e:
            logger.warning(f"ROUGE failed: {e}")
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    def apply_quality_rubric(
        self, doc: str, func_info: Dict[str, Any]
    ) -> RubricScore:
        score = RubricScore()
        doc_lower = doc.lower()

        # Completeness: has Args + Returns
        if "args:" in doc_lower or "arguments:" in doc_lower:
            score.completeness += 2
        if "returns:" in doc_lower or "return:" in doc_lower:
            score.completeness += 2
        if len(doc) > 100:
            score.completeness += 1

        # Accuracy: has type info
        if any(t in doc for t in ["int", "str", "dict", "list", "bool", "float", "None"]):
            score.accuracy += 3
        if "raises:" in doc_lower or "raise:" in doc_lower:
            score.accuracy += 2

        # Clarity: readable English
        sentences = [s.strip() for s in doc.split(".") if len(s.strip()) > 10]
        if len(sentences) >= 2:
            score.clarity += 3
        if len(doc.split()) >= 20:
            score.clarity += 2

        # Examples: has example
        if "example" in doc_lower or ">>>" in doc or "usage" in doc_lower:
            score.examples = 5

        # Edge cases: mentions edge cases
        if any(w in doc_lower for w in ["edge", "empty", "none", "null", "zero", "negative"]):
            score.edge_cases += 3

        # Consistency: has proper structure
        if ":" in doc and len(doc.splitlines()) >= 3:
            score.consistency = 5

        return score

    def compute_coverage(
        self, repo_path: str, ast_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        if ast_results is None:
            return {"functions": 0.0, "classes": 0.0, "modules": 0.0}

        total_funcs = 0
        documented_funcs = 0
        total_classes = 0
        documented_classes = 0
        total_modules = 0
        documented_modules = 0

        for filepath, result in ast_results.items():
            if result.get("parse_error"):
                continue
            # Module
            total_modules += 1
            if result.get("module_docstring"):
                documented_modules += 1

            # Functions
            for func in result.get("functions", []):
                total_funcs += 1
                if func.get("docstring"):
                    documented_funcs += 1

            # Classes
            for cls in result.get("classes", []):
                total_classes += 1
                if cls.get("docstring"):
                    documented_classes += 1

        return {
            "functions": documented_funcs / total_funcs if total_funcs > 0 else 0.0,
            "classes": documented_classes / total_classes if total_classes > 0 else 0.0,
            "modules": documented_modules / total_modules if total_modules > 0 else 0.0,
        }
