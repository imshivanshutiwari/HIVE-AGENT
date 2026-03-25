"""Review agent: code review and suggestions."""
import logging
from typing import Any, Dict, List

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def review_node(state: HiveAgentState) -> HiveAgentState:
    """Review high-complexity functions and generate inline comments."""
    ast_results = state.get("ast_results", {})
    complexity_scores = state.get("complexity_scores", {})
    code_smells = state.get("code_smells", [])
    trace = list(state.get("pipeline_trace", []))
    trace.append("review_node:start")
    logger.info("[review_node] Reviewing high-complexity functions")

    from generation.claude_client import ClaudeClient
    from agents.tools import TOOLS_REVIEW

    claude = ClaudeClient()
    review_comments: List[Dict[str, Any]] = list(state.get("review_comments", []))
    tokens_used = state.get("claude_tokens_used", 0)

    # Find high-complexity functions
    high_complexity_funcs = []
    for filepath, result in ast_results.items():
        for func in result.get("functions", []):
            if func.get("cyclomatic_complexity", 0) >= 10:
                high_complexity_funcs.append((filepath, func))

    high_complexity_funcs.sort(key=lambda x: x[1].get("cyclomatic_complexity", 0), reverse=True)

    # Review top 5 most complex functions
    for filepath, func in high_complexity_funcs[:5]:
        try:
            prompt = (
                f"Review this Python function for code quality issues, "
                f"refactoring opportunities, and security concerns:\n\n"
                f"```python\n{func.get('source', '')}\n```\n\n"
                f"Complexity: {func.get('cyclomatic_complexity', 0)}\n"
                f"Please provide specific, actionable suggestions."
            )
            result_text, tokens = claude.generate_with_tools(prompt, TOOLS_REVIEW)
            tokens_used += tokens
            review_comments.append({
                "filepath": filepath,
                "function_name": func.get("name", ""),
                "complexity": func.get("cyclomatic_complexity", 0),
                "review": result_text,
                "lineno": func.get("lineno", 0),
            })
        except Exception as e:
            logger.warning(f"[review_node] Review failed for {func.get('name', '?')}: {e}")

    trace.append(f"review_node:complete:reviews={len(review_comments)}")
    return {
        **state,
        "review_comments": review_comments,
        "claude_tokens_used": tokens_used,
        "pipeline_trace": trace,
    }
