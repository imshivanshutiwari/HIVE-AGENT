"""Cyclomatic and cognitive complexity scoring using radon."""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class FunctionComplexity:
    name: str
    filepath: str
    cyclomatic: int
    cognitive: int
    loc: int
    rank: str  # A-F per radon scale


@dataclass
class FileComplexity:
    filepath: str
    avg_cyclomatic: float
    max_cyclomatic: int
    avg_cognitive: float
    functions: List[FunctionComplexity] = field(default_factory=list)
    total_loc: int = 0


class ComplexityScorer:
    """Compute code complexity metrics using radon."""

    RANK_THRESHOLDS = {
        "A": (1, 5),
        "B": (6, 10),
        "C": (11, 15),
        "D": (16, 20),
        "E": (21, 25),
        "F": (26, 9999),
    }

    def rank_complexity(self, complexity: int) -> str:
        for rank, (low, high) in self.RANK_THRESHOLDS.items():
            if low <= complexity <= high:
                return rank
        return "F"

    def score_file(self, filepath: str) -> Optional[FileComplexity]:
        try:
            from radon.complexity import cc_visit, cc_rank
        except ImportError:
            logger.warning("radon not installed; using AST-based complexity")
            return self._score_file_ast(filepath)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except OSError:
            return None

        try:
            results = cc_visit(source)
        except Exception as e:
            logger.debug(f"radon failed on {filepath}: {e}")
            return None

        functions = []
        for r in results:
            functions.append(
                FunctionComplexity(
                    name=r.name,
                    filepath=filepath,
                    cyclomatic=r.complexity,
                    cognitive=r.complexity,  # radon doesn't have cognitive; use cyclomatic
                    loc=r.endline - r.lineno + 1,
                    rank=cc_rank(r.complexity),
                )
            )

        if functions:
            avg_cc = sum(f.cyclomatic for f in functions) / len(functions)
            max_cc = max(f.cyclomatic for f in functions)
        else:
            avg_cc = 0.0
            max_cc = 0

        return FileComplexity(
            filepath=filepath,
            avg_cyclomatic=avg_cc,
            max_cyclomatic=max_cc,
            avg_cognitive=avg_cc,
            functions=functions,
            total_loc=source.count("\n") + 1,
        )

    def _score_file_ast(self, filepath: str) -> Optional[FileComplexity]:
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        result = parser.parse_file(filepath)
        if result.parse_error:
            return None
        functions = []
        for func in result.functions:
            functions.append(
                FunctionComplexity(
                    name=func.name,
                    filepath=filepath,
                    cyclomatic=func.cyclomatic_complexity,
                    cognitive=func.cognitive_complexity,
                    loc=func.body_lines,
                    rank=self.rank_complexity(func.cyclomatic_complexity),
                )
            )
        for cls in result.classes:
            for method in cls.methods:
                functions.append(
                    FunctionComplexity(
                        name=f"{cls.name}.{method.name}",
                        filepath=filepath,
                        cyclomatic=method.cyclomatic_complexity,
                        cognitive=method.cognitive_complexity,
                        loc=method.body_lines,
                        rank=self.rank_complexity(method.cyclomatic_complexity),
                    )
                )
        if functions:
            avg_cc = sum(f.cyclomatic for f in functions) / len(functions)
            max_cc = max(f.cyclomatic for f in functions)
        else:
            avg_cc = 0.0
            max_cc = 0
        return FileComplexity(
            filepath=filepath,
            avg_cyclomatic=avg_cc,
            max_cyclomatic=max_cc,
            avg_cognitive=sum(f.cognitive for f in functions) / len(functions) if functions else 0.0,
            functions=functions,
        )

    def score_repo(self, py_files: List[str]) -> Dict[str, FileComplexity]:
        results = {}
        for filepath in py_files:
            fc = self.score_file(filepath)
            if fc:
                results[filepath] = fc
        return results
