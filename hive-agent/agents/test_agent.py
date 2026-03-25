"""Test agent: auto-generate pytest + Hypothesis tests."""
import logging
from typing import Any, Dict, List

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def test_agent_node(state: HiveAgentState) -> HiveAgentState:
    """Generate pytest unit tests and Hypothesis property tests."""
    ast_results = state.get("ast_results", {})
    trace = list(state.get("pipeline_trace", []))
    trace.append("test_agent_node:start")
    logger.info("[test_agent_node] Generating tests")

    from generation.test_generator import TestGenerator

    test_gen = TestGenerator()
    generated_tests: Dict[str, str] = dict(state.get("generated_tests", {}))
    tokens_used = state.get("claude_tokens_used", 0)

    tests_generated = 0
    for filepath, result in ast_results.items():
        if result.get("parse_error"):
            continue
        functions = result.get("functions", [])
        if not functions:
            continue

        try:
            # Generate unit tests for first 3 functions per file
            unit_tests, tokens = test_gen.generate_unit_tests_for_file(functions[:3], filepath)
            if unit_tests:
                test_key = f"tests/generated/test_{filepath.replace('/', '_').replace('.', '_')}.py"
                generated_tests[test_key] = unit_tests
                tokens_used += tokens
                tests_generated += 1

            # Generate hypothesis tests
            hyp_tests, tokens2 = test_gen.generate_hypothesis_tests_for_file(functions[:2], filepath)
            if hyp_tests:
                hyp_key = f"tests/generated/test_hypothesis_{filepath.replace('/', '_').replace('.', '_')}.py"
                generated_tests[hyp_key] = hyp_tests
                tokens_used += tokens2

        except Exception as e:
            logger.debug(f"Test generation failed for {filepath}: {e}")

        if tests_generated >= 5:
            break

    trace.append(f"test_agent_node:complete:tests={len(generated_tests)}")
    return {
        **state,
        "generated_tests": generated_tests,
        "claude_tokens_used": tokens_used,
        "pipeline_trace": trace,
    }
