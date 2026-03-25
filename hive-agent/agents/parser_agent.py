"""Parser agent: AST + tree-sitter parsing node."""
import logging
from typing import Any, Dict, List

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def parser_node(state: HiveAgentState) -> HiveAgentState:
    """Parse all code files: Python AST + tree-sitter for others."""
    all_files = state.get("all_files", [])
    trace = list(state.get("pipeline_trace", []))
    trace.append("parser_node:start")
    logger.info(f"[parser_node] Parsing {len(all_files)} files")

    from analysis.ast_parser import PythonASTParser
    from analysis.treesitter_parser import TreeSitterParser

    ast_parser = PythonASTParser()
    ts_parser = TreeSitterParser()
    ast_results: Dict[str, Any] = {}

    for file_info in all_files:
        filepath = file_info["path"]
        language = file_info.get("language", "unknown")

        try:
            if language == "python":
                result = ast_parser.parse_file(filepath)
                ast_results[filepath] = {
                    "language": "python",
                    "functions": [
                        {
                            "name": f.name,
                            "args": f.args,
                            "return_type": f.return_type,
                            "decorators": f.decorators,
                            "docstring": f.docstring,
                            "body_lines": f.body_lines,
                            "calls_made": f.calls_made,
                            "raises": f.raises,
                            "yields": f.yields,
                            "is_async": f.is_async,
                            "cyclomatic_complexity": f.cyclomatic_complexity,
                            "cognitive_complexity": f.cognitive_complexity,
                            "lineno": f.lineno,
                            "source": f.source,
                        }
                        for f in result.functions
                    ],
                    "classes": [
                        {
                            "name": c.name,
                            "bases": c.bases,
                            "docstring": c.docstring,
                            "methods": [
                                {
                                    "name": m.name,
                                    "args": m.args,
                                    "return_type": m.return_type,
                                    "docstring": m.docstring,
                                    "cyclomatic_complexity": m.cyclomatic_complexity,
                                    "source": m.source,
                                }
                                for m in c.methods
                            ],
                        }
                        for c in result.classes
                    ],
                    "imports": [
                        {"module": i.module, "names": i.names, "is_from": i.is_from}
                        for i in result.imports
                    ],
                    "module_docstring": result.module_docstring,
                    "parse_error": result.parse_error,
                }
            elif language in ts_parser.parsers or language in [
                "javascript", "typescript", "go", "rust", "java", "cpp", "c", "ruby", "php"
            ]:
                ts_result = ts_parser.parse_file(filepath, language)
                ast_results[filepath] = {
                    "language": language,
                    "functions": [
                        {
                            "name": f.name,
                            "args": f.params,
                            "start_line": f.start_line,
                            "end_line": f.end_line,
                            "source": f.body[:200],
                        }
                        for f in ts_result.functions
                    ],
                    "imports": ts_result.imports,
                    "complexity_estimate": ts_result.complexity_estimate,
                    "line_count": ts_result.line_count,
                    "parse_error": ts_result.parse_error,
                }
        except Exception as e:
            logger.warning(f"[parser_node] Failed to parse {filepath}: {e}")
            ast_results[filepath] = {"language": language, "parse_error": str(e)}

    trace.append(f"parser_node:complete:{len(ast_results)}_files")
    return {**state, "ast_results": ast_results, "pipeline_trace": trace}
