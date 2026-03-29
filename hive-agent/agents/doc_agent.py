"""Doc agent: documentation generation node."""

import logging
from typing import Dict

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def doc_agent_node(state: HiveAgentState) -> HiveAgentState:
    """Generate documentation for all functions, classes, modules, and repo."""
    ast_results = state.get("ast_results", {})
    repo_metadata = state.get("repo_metadata", {})
    trace = list(state.get("pipeline_trace", []))
    trace.append("doc_agent_node:start")
    logger.info(f"[doc_agent_node] Generating docs for {len(ast_results)} files")

    from generation.function_docgen import FunctionDocGenerator
    from generation.class_docgen import ClassDocGenerator
    from generation.module_docgen import ModuleDocGenerator
    from generation.repo_docgen import RepoDocGenerator

    func_docgen = FunctionDocGenerator()
    class_docgen = ClassDocGenerator()
    module_docgen = ModuleDocGenerator()
    repo_docgen = RepoDocGenerator()

    generated_docs: Dict[str, str] = dict(state.get("generated_docs", {}))
    tokens_used = state.get("claude_tokens_used", 0)

    # Generate function docs (limit to first 30 for speed)
    functions_processed = 0
    for filepath, result in ast_results.items():
        if result.get("parse_error"):
            continue
        for func in result.get("functions", [])[:5]:
            if func.get("docstring"):
                continue
            try:
                doc, tokens = func_docgen.generate(func, filepath)
                key = f"{filepath}::func::{func['name']}"
                generated_docs[key] = doc
                tokens_used += tokens
                functions_processed += 1
                if functions_processed >= 30:
                    break
            except Exception as e:
                logger.debug(f"Doc gen failed for {func.get('name', '?')}: {e}")
        if functions_processed >= 30:
            break

    # Generate class docs (limit to first 10)
    classes_processed = 0
    for filepath, result in ast_results.items():
        if result.get("parse_error"):
            continue
        for cls in result.get("classes", [])[:3]:
            if cls.get("docstring"):
                continue
            try:
                doc, tokens = class_docgen.generate(cls, filepath)
                key = f"{filepath}::class::{cls['name']}"
                generated_docs[key] = doc
                tokens_used += tokens
                classes_processed += 1
                if classes_processed >= 10:
                    break
            except Exception as e:
                logger.debug(f"Class doc gen failed for {cls.get('name', '?')}: {e}")
        if classes_processed >= 10:
            break

    # Generate module docs (first 5 files)
    for filepath in list(ast_results.keys())[:5]:
        try:
            doc, tokens = module_docgen.generate(filepath, ast_results[filepath])
            generated_docs[f"{filepath}::module"] = doc
            tokens_used += tokens
        except Exception as e:
            logger.debug(f"Module doc gen failed for {filepath}: {e}")

    # Generate README
    try:
        all_filepaths = list(ast_results.keys())
        readme, tokens = repo_docgen.generate(repo_metadata, all_filepaths, ast_results)
        generated_docs["README.md"] = readme
        tokens_used += tokens
    except Exception as e:
        logger.warning(f"[doc_agent_node] README generation failed: {e}")

    trace.append(f"doc_agent_node:complete:docs={len(generated_docs)}")
    return {
        **state,
        "generated_docs": generated_docs,
        "claude_tokens_used": tokens_used,
        "pipeline_trace": trace,
    }
