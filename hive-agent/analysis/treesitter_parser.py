"""tree-sitter parser for 9 languages beyond Python."""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    "javascript",
    "typescript",
    "go",
    "rust",
    "java",
    "cpp",
    "c",
    "ruby",
    "php",
]

EXTENSION_TO_LANG = {
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".rb": "ruby",
    ".php": "php",
}

FUNCTION_QUERIES = {
    "javascript": "(function_declaration name: (identifier) @name) @func",
    "typescript": "(function_declaration name: (identifier) @name) @func",
    "go": "(function_declaration name: (identifier) @name) @func",
    "rust": "(function_item name: (identifier) @name) @func",
    "java": "(method_declaration name: (identifier) @name) @func",
    "cpp": (
        "(function_definition declarator:"
        " (function_declarator declarator: (identifier) @name)) @func"
    ),
    "c": (
        "(function_definition declarator:"
        " (function_declarator declarator: (identifier) @name)) @func"
    ),
    "ruby": "(method name: (identifier) @name) @func",
    "php": "(function_definition name: (name) @name) @func",
}


@dataclass
class FunctionNode:
    name: str
    params: List[str]
    start_line: int
    end_line: int
    body: str = ""


@dataclass
class TreeSitterResult:
    filepath: str
    language: str
    functions: List[FunctionNode] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    complexity_estimate: int = 0
    line_count: int = 0
    parse_error: Optional[str] = None


class TreeSitterParser:
    """tree-sitter parser for 9 languages."""

    def __init__(self):
        self.parsers: Dict = {}
        self.languages: Dict = {}
        self._init_parsers()

    def _init_parsers(self):
        """Initialize tree-sitter parsers for all supported languages."""
        try:
            from tree_sitter import Parser, Language
        except ImportError:
            logger.warning("tree-sitter not available; parsers disabled")
            return

        build_dir = os.path.join(os.path.dirname(__file__), "..", "build")
        os.makedirs(build_dir, exist_ok=True)

        lang_map = {
            "javascript": "tree_sitter_javascript",
            "typescript": "tree_sitter_typescript",
            "go": "tree_sitter_go",
            "rust": "tree_sitter_rust",
            "java": "tree_sitter_java",
            "cpp": "tree_sitter_cpp",
            "c": "tree_sitter_c",
            "ruby": "tree_sitter_ruby",
            "php": "tree_sitter_php",
        }

        for lang_name, module_name in lang_map.items():
            try:
                import importlib

                lang_module = importlib.import_module(module_name)
                parser = Parser()
                if hasattr(lang_module, "language"):
                    language = Language(lang_module.language())
                    parser.set_language(language)
                    self.parsers[lang_name] = parser
                    self.languages[lang_name] = language
            except Exception as e:
                logger.warning(f"Could not load tree-sitter grammar for {lang_name}: {e}")

    def detect_language(self, filepath: str) -> str:
        ext = Path(filepath).suffix.lower()
        return EXTENSION_TO_LANG.get(ext, "unknown")

    def parse_file(self, filepath: str, language: Optional[str] = None) -> TreeSitterResult:
        if language is None:
            language = self.detect_language(filepath)

        try:
            with open(filepath, "rb") as f:
                source_bytes = f.read()
        except OSError as e:
            return TreeSitterResult(filepath=filepath, language=language, parse_error=str(e))

        source_str = source_bytes.decode("utf-8", errors="ignore")
        line_count = source_str.count("\n") + 1

        result = TreeSitterResult(filepath=filepath, language=language, line_count=line_count)

        if language not in self.parsers:
            result.parse_error = f"No parser for language: {language}"
            result.complexity_estimate = self._estimate_complexity(source_str)
            return result

        try:
            parser = self.parsers[language]
            tree = parser.parse(source_bytes)
            result.functions = self.extract_functions(tree, source_bytes, language)
            result.imports = self.extract_dependencies(tree, source_bytes, language)
            result.complexity_estimate = self._estimate_complexity(source_str)
        except Exception as e:
            result.parse_error = str(e)

        return result

    def extract_functions(self, tree, source: bytes, language: str) -> List[FunctionNode]:
        functions = []
        try:
            pass

            query_str = FUNCTION_QUERIES.get(language, "")
            if not query_str or language not in self.parsers:
                return []
            ts_lang = self.languages.get(language)
            if ts_lang is None:
                return self._extract_functions_fallback(tree, source)
            query = ts_lang.query(query_str)
            captures = query.captures(tree.root_node)
            for node, name in captures:
                if name == "func":
                    func_name = ""
                    for child, child_name in captures:
                        if child_name == "name" and child.parent == node:
                            func_name = source[child.start_byte : child.end_byte].decode(
                                "utf-8", errors="ignore"
                            )
                            break
                    body = source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
                    functions.append(
                        FunctionNode(
                            name=func_name,
                            params=[],
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            body=body[:500],
                        )
                    )
        except Exception as e:
            logger.debug(f"Query-based extraction failed: {e}")
            return self._extract_functions_fallback(tree, source)
        return functions

    def _extract_functions_fallback(self, tree, source: bytes) -> List[FunctionNode]:
        """Fallback: walk tree looking for function nodes."""
        functions = []
        function_node_types = {
            "function_declaration",
            "function_definition",
            "function_item",
            "method_declaration",
            "method_definition",
            "arrow_function",
        }

        def walk(node):
            if node.type in function_node_types:
                name_child = None
                for child in node.children:
                    if child.type in ("identifier", "name", "property_identifier"):
                        name_child = child
                        break
                func_name = (
                    source[name_child.start_byte : name_child.end_byte].decode(
                        "utf-8", errors="ignore"
                    )
                    if name_child
                    else "<anonymous>"
                )
                body = source[node.start_byte : min(node.end_byte, node.start_byte + 500)].decode(
                    "utf-8", errors="ignore"
                )
                functions.append(
                    FunctionNode(
                        name=func_name,
                        params=[],
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        body=body,
                    )
                )
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return functions

    def extract_dependencies(self, tree, source: bytes, language: str) -> List[str]:
        imports = []
        import_node_types = {
            "javascript": ["import_statement", "import_declaration"],
            "typescript": ["import_statement", "import_declaration"],
            "go": ["import_declaration", "import_spec"],
            "rust": ["use_declaration"],
            "java": ["import_declaration"],
            "cpp": ["preproc_include"],
            "c": ["preproc_include"],
            "ruby": ["call"],
            "php": ["require_expression", "include_expression", "use_declaration"],
        }

        node_types = import_node_types.get(language, [])

        def walk(node):
            if node.type in node_types:
                text = source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
                imports.append(text.strip()[:200])
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return imports

    def _estimate_complexity(self, source: str) -> int:
        keywords = ["if", "else", "for", "while", "case", "catch", "&&", "||", "?"]
        return 1 + sum(source.count(kw) for kw in keywords)
