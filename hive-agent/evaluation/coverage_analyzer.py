"""Documentation coverage analysis per codebase."""
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List

from analysis.ast_parser import PythonASTParser

logger = logging.getLogger(__name__)


@dataclass
class FileCoverageReport:
    filepath: str
    total_functions: int = 0
    documented_functions: int = 0
    total_classes: int = 0
    documented_classes: int = 0
    has_module_docstring: bool = False

    @property
    def function_coverage(self) -> float:
        return self.documented_functions / self.total_functions if self.total_functions > 0 else 1.0

    @property
    def class_coverage(self) -> float:
        return self.documented_classes / self.total_classes if self.total_classes > 0 else 1.0


class CoverageAnalyzer:
    """Analyze documentation coverage per file and across the codebase."""

    def __init__(self):
        self.parser = PythonASTParser()

    def analyze_file(self, filepath: str) -> FileCoverageReport:
        result = self.parser.parse_file(filepath)
        report = FileCoverageReport(filepath=filepath)
        if result.parse_error:
            return report

        report.has_module_docstring = bool(result.module_docstring)
        for func in result.functions:
            report.total_functions += 1
            if func.docstring:
                report.documented_functions += 1
        for cls in result.classes:
            report.total_classes += 1
            if cls.docstring:
                report.documented_classes += 1
            for method in cls.methods:
                report.total_functions += 1
                if method.docstring:
                    report.documented_functions += 1
        return report

    def analyze_repo(self, repo_path: str) -> Dict[str, FileCoverageReport]:
        reports = {}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    reports[filepath] = self.analyze_file(filepath)
        return reports

    def summary(self, reports: Dict[str, FileCoverageReport]) -> Dict[str, float]:
        if not reports:
            return {"functions": 0.0, "classes": 0.0, "modules": 0.0}
        total_f = sum(r.total_functions for r in reports.values())
        doc_f = sum(r.documented_functions for r in reports.values())
        total_c = sum(r.total_classes for r in reports.values())
        doc_c = sum(r.documented_classes for r in reports.values())
        doc_m = sum(1 for r in reports.values() if r.has_module_docstring)
        return {
            "functions": doc_f / total_f if total_f > 0 else 1.0,
            "classes": doc_c / total_c if total_c > 0 else 1.0,
            "modules": doc_m / len(reports),
        }
