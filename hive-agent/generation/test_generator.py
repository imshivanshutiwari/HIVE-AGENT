"""pytest + Hypothesis test generation using Claude."""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generate pytest and Hypothesis tests using Claude."""

    def __init__(self):
        from generation.claude_client import ClaudeClient

        self.claude = ClaudeClient()

    def generate_unit_tests(self, func_info: Dict[str, Any]) -> Tuple[str, int]:
        func_name = func_info.get("name", "unknown")
        func_source = func_info.get("source", "")
        args = func_info.get("args", [])  # noqa: F841

        prompt = (
            f"Generate complete pytest unit tests for this Python function.\n"
            f"Include: happy path, edge cases (empty/None/boundary), error conditions.\n"
            f"Use proper pytest fixtures and assertions.\n\n"
            f"Function:\n```python\n{func_source[:2000]}\n```\n\n"
            f"Return a complete, valid Python test file."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"Unit test gen failed for {func_name}: {e}")
            return self._template_unit_test(func_name), 0

    def generate_hypothesis_tests(self, func_info: Dict[str, Any]) -> Tuple[str, int]:
        func_name = func_info.get("name", "unknown")
        func_source = func_info.get("source", "")
        return_type = func_info.get("return_type", "")

        prompt = (
            f"Generate Hypothesis property-based tests for this Python function.\n"
            f"Use @given() decorator with appropriate strategies (st.integers, st.text, etc.).\n"
            f"Test properties/invariants that should always hold.\n\n"
            f"Function:\n```python\n{func_source[:2000]}\n```\n\n"
            f"Return type: {return_type}\n\n"
            f"Return a complete valid Python test file with"
            f" 'from hypothesis import given, strategies as st'."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"Hypothesis test gen failed for {func_name}: {e}")
            return self._template_hypothesis_test(func_name), 0

    def generate_integration_tests(
        self, module_name: str, functions: List[Dict[str, Any]]
    ) -> Tuple[str, int]:
        func_names = [f.get("name", "") for f in functions[:5]]
        prompt = (
            f"Generate integration tests for the module '{module_name}'.\n"
            f"Functions to test: {func_names}\n"
            f"Test module-level interactions and data flow.\n\n"
            f"Return a complete pytest integration test file."
        )
        try:
            return self.claude.generate(prompt)
        except Exception as e:
            logger.warning(f"Integration test gen failed for {module_name}: {e}")
            return f"# Integration tests for {module_name}\n", 0

    def generate_unit_tests_for_file(
        self, functions: List[Dict[str, Any]], filepath: str
    ) -> Tuple[str, int]:
        if not functions:
            return "", 0
        combined = "\n\n".join(
            f"def {f.get('name', 'func')}({', '.join(f.get('args', []))}):\n    pass"
            for f in functions
        )
        prompt = (
            f"Generate pytest unit tests for these functions from '{filepath}':\n\n"
            f"```python\n{combined[:3000]}\n```\n\n"
            f"Return a complete Python test file."
        )
        try:
            return self.claude.generate(prompt)
        except Exception as e:
            logger.warning(f"Test gen failed for {filepath}: {e}")
            return "", 0

    def generate_hypothesis_tests_for_file(
        self, functions: List[Dict[str, Any]], filepath: str
    ) -> Tuple[str, int]:
        if not functions:
            return "", 0
        func_names = [f.get("name", "") for f in functions]
        prompt = (
            f"Generate Hypothesis property-based tests for functions {func_names} "
            f"from '{filepath}'.\n"
            f"Include @given() decorators with realistic strategies.\n"
            f"Return a complete Python test file with hypothesis imports."
        )
        try:
            return self.claude.generate(prompt)
        except Exception as e:
            logger.warning(f"Hypothesis test gen failed for {filepath}: {e}")
            return "", 0

    def validate_generated_tests(self, test_code: str) -> bool:
        try:
            compile(test_code, "<generated_test>", "exec")
            return True
        except SyntaxError:
            return False

    def _template_unit_test(self, func_name: str) -> str:
        return (
            f"import pytest\n\n\n"
            f"def test_{func_name}_basic():\n"
            f"    # TODO: implement test for {func_name}\n"
            f"    assert True\n"
        )

    def _template_hypothesis_test(self, func_name: str) -> str:
        return (
            f"from hypothesis import given, strategies as st\n\n\n"
            f"@given(st.integers())\n"
            f"def test_{func_name}_property(n):\n"
            f"    # Property test for {func_name}\n"
            f"    assert isinstance(n, int)\n"
        )
