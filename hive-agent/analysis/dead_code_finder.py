"""Detect unreachable / dead code via reachability analysis."""

import ast
import logging
from dataclasses import dataclass
from typing import List, Set

logger = logging.getLogger(__name__)


@dataclass
class DeadCodeResult:
    filepath: str
    function_name: str
    lineno: int
    reason: str  # "unreachable_after_return", "unused_function", "unused_import"


class DeadCodeFinder:
    """Find dead code in Python files."""

    def find_dead_code(self, filepath: str) -> List[DeadCodeResult]:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            return []

        results = []
        results.extend(self._find_unreachable_statements(tree, filepath))
        results.extend(self._find_unused_functions(tree, filepath))
        results.extend(self._find_unused_imports(tree, filepath))
        return results

    def _find_unreachable_statements(self, tree: ast.AST, filepath: str) -> List[DeadCodeResult]:
        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                for i, stmt in enumerate(body[:-1]):
                    if isinstance(stmt, (ast.Return, ast.Raise)):
                        remaining = body[i + 1 :]
                        if remaining and not all(
                            isinstance(s, (ast.Pass, ast.Expr)) for s in remaining
                        ):
                            results.append(
                                DeadCodeResult(
                                    filepath=filepath,
                                    function_name=node.name,
                                    lineno=body[i + 1].lineno,
                                    reason="unreachable_after_return",
                                )
                            )
                        break
        return results

    def _find_unused_functions(self, tree: ast.AST, filepath: str) -> List[DeadCodeResult]:
        defined: dict = {}
        called: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_") and not node.name.startswith("test"):
                    defined[node.name] = node.lineno
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)

        results = []
        for fname, lineno in defined.items():
            if fname not in called and fname not in {"main", "__init__", "__call__"}:
                results.append(
                    DeadCodeResult(
                        filepath=filepath,
                        function_name=fname,
                        lineno=lineno,
                        reason="unused_function",
                    )
                )
        return results

    def _find_unused_imports(self, tree: ast.AST, filepath: str) -> List[DeadCodeResult]:
        imported: dict = {}
        used: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported[name] = node.lineno
            elif isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used.add(node.value.id)

        results = []
        for imp_name, lineno in imported.items():
            if imp_name not in used and imp_name != "*":
                results.append(
                    DeadCodeResult(
                        filepath=filepath,
                        function_name=imp_name,
                        lineno=lineno,
                        reason="unused_import",
                    )
                )
        return results
