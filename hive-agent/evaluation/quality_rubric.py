"""Structured quality rubric for documentation scoring."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class RubricDimension:
    name: str
    score: int
    max_score: int
    explanation: str


@dataclass
class RubricResult:
    dimensions: Dict[str, RubricDimension]

    @property
    def total_score(self) -> int:
        return sum(d.score for d in self.dimensions.values())

    @property
    def max_score(self) -> int:
        return 30

    @property
    def grade(self) -> str:
        pct = self.total_score / self.max_score
        if pct >= 0.9:
            return "A"
        elif pct >= 0.8:
            return "B"
        elif pct >= 0.7:
            return "C"
        elif pct >= 0.6:
            return "D"
        return "F"


class QualityRubric:
    """6-dimension quality rubric (0-5 each = 30 max)."""

    MAX_PER_DIMENSION = 5

    def evaluate(self, doc: str, func_info: Dict[str, Any]) -> RubricResult:
        dimensions = {}

        # 1. Completeness
        complete_score = 0
        doc_lower = doc.lower()
        if "args:" in doc_lower or "parameters:" in doc_lower:
            complete_score += 2
        if "returns:" in doc_lower:
            complete_score += 2
        if len(doc) > 50:
            complete_score += 1
        dimensions["completeness"] = RubricDimension(
            name="completeness",
            score=min(complete_score, 5),
            max_score=5,
            explanation="Presence of Args, Returns sections",
        )

        # 2. Accuracy
        acc_score = 0
        args = func_info.get("args", [])
        for arg in args:
            if arg in doc and arg not in ("self", "cls"):
                acc_score += 1
        acc_score = min(acc_score, 4)
        if "raises:" in doc_lower:
            acc_score += 1
        dimensions["accuracy"] = RubricDimension(
            name="accuracy",
            score=min(acc_score, 5),
            max_score=5,
            explanation="Args mentioned, raises documented",
        )

        # 3. Clarity
        clarity_score = 0
        sentences = [s for s in doc.split(".") if len(s.strip()) > 10]
        if sentences:
            clarity_score += min(len(sentences), 3)
        if 20 <= len(doc.split()) <= 200:
            clarity_score += 2
        dimensions["clarity"] = RubricDimension(
            name="clarity",
            score=min(clarity_score, 5),
            max_score=5,
            explanation="Readable, appropriately sized",
        )

        # 4. Examples
        example_score = 0
        if ">>>" in doc:
            example_score = 5
        elif "example" in doc_lower or "usage" in doc_lower:
            example_score = 3
        dimensions["examples"] = RubricDimension(
            name="examples",
            score=example_score,
            max_score=5,
            explanation="Has usage examples",
        )

        # 5. Edge cases
        edge_score = 0
        edge_words = ["none", "empty", "null", "zero", "negative", "edge", "corner", "boundary"]
        for w in edge_words:
            if w in doc_lower:
                edge_score += 1
        dimensions["edge_cases"] = RubricDimension(
            name="edge_cases",
            score=min(edge_score, 5),
            max_score=5,
            explanation="Edge cases mentioned",
        )

        # 6. Consistency
        cons_score = 0
        if doc.startswith(tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
            cons_score += 2
        if any(section in doc for section in ["Args:", "Returns:", "Raises:"]):
            cons_score += 3
        dimensions["consistency"] = RubricDimension(
            name="consistency",
            score=min(cons_score, 5),
            max_score=5,
            explanation="Follows Google docstring style",
        )

        return RubricResult(dimensions=dimensions)
