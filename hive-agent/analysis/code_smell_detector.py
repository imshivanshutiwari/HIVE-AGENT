"""Detect code smells and anti-patterns."""

import ast
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class CodeSmell:
    name: str
    filepath: str
    line: int
    description: str
    severity: str  # "low", "medium", "high"
    category: str  # "god_class", "long_method", "dead_code", etc.


class CodeSmellDetector:
    """Detect common code smells in Python source."""

    LONG_METHOD_THRESHOLD = 50  # lines
    LONG_PARAM_THRESHOLD = 6
    GOD_CLASS_THRESHOLD = 20  # methods
    NESTED_DEPTH_THRESHOLD = 4

    def detect_all(self, filepath: str) -> List[CodeSmell]:
        smells = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            return []

        smells.extend(self.detect_long_methods(tree, filepath))
        smells.extend(self.detect_god_classes(tree, filepath))
        smells.extend(self.detect_long_param_lists(tree, filepath))
        smells.extend(self.detect_deep_nesting(tree, filepath))
        smells.extend(self.detect_duplicate_code_patterns(tree, filepath, source))
        return smells

    def detect_long_methods(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno
                if length > self.LONG_METHOD_THRESHOLD:
                    smells.append(
                        CodeSmell(
                            name=f"Long method: {node.name}",
                            filepath=filepath,
                            line=node.lineno,
                            description=(
                                f"Method '{node.name}' has {length} lines"
                                f" (>{self.LONG_METHOD_THRESHOLD})"
                            ),
                            severity="medium",
                            category="long_method",
                        )
                    )
        return smells

    def detect_god_classes(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if len(methods) > self.GOD_CLASS_THRESHOLD:
                    smells.append(
                        CodeSmell(
                            name=f"God class: {node.name}",
                            filepath=filepath,
                            line=node.lineno,
                            description=(
                                f"Class '{node.name}' has {len(methods)} methods"
                                f" (>{self.GOD_CLASS_THRESHOLD})"
                            ),
                            severity="high",
                            category="god_class",
                        )
                    )
        return smells

    def detect_long_param_lists(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args) + len(node.args.posonlyargs)
                if param_count > self.LONG_PARAM_THRESHOLD:
                    smells.append(
                        CodeSmell(
                            name=f"Long param list: {node.name}",
                            filepath=filepath,
                            line=node.lineno,
                            description=f"Function '{node.name}' has {param_count} parameters",
                            severity="low",
                            category="long_param_list",
                        )
                    )
        return smells

    def detect_deep_nesting(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        smells = []

        def max_depth(node: ast.AST, current: int = 0) -> int:
            nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)
            if isinstance(node, nesting_nodes):
                current += 1
            return max(
                [current] + [max_depth(child, current) for child in ast.iter_child_nodes(node)]
            )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                depth = max_depth(node)
                if depth > self.NESTED_DEPTH_THRESHOLD:
                    smells.append(
                        CodeSmell(
                            name=f"Deep nesting: {node.name}",
                            filepath=filepath,
                            line=node.lineno,
                            description=f"Function '{node.name}' has nesting depth {depth}",
                            severity="medium",
                            category="deep_nesting",
                        )
                    )
        return smells

    def detect_duplicate_code_patterns(
        self, tree: ast.AST, filepath: str, source: str
    ) -> List[CodeSmell]:
        """Detect trivially duplicated code blocks."""
        smells = []
        lines = source.splitlines()
        seen_blocks: dict = {}
        block_size = 5
        for i in range(len(lines) - block_size):
            block = "\n".join(lines[i : i + block_size]).strip()
            if len(block) < 50:
                continue
            if block in seen_blocks:
                smells.append(
                    CodeSmell(
                        name="Duplicate code block",
                        filepath=filepath,
                        line=i + 1,
                        description=(
                            f"Duplicate code block also appears at line"
                            f" {seen_blocks[block] + 1}"
                        ),
                        severity="medium",
                        category="clone_code",
                    )
                )
            else:
                seen_blocks[block] = i
        return smells
