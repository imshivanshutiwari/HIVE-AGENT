"""Tests for documentation and test generation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFunctionDocGenerator:
    def test_function_docgen_produces_google_style(self, mock_claude_client, sample_function_info):
        """Generated docstring should have Args: and Returns: sections."""
        from generation.function_docgen import FunctionDocGenerator

        docgen = FunctionDocGenerator()
        docgen.claude = mock_claude_client
        doc, tokens = docgen.generate(sample_function_info, "test.py")
        assert isinstance(doc, str)
        assert len(doc) > 0
        assert "Args:" in doc or "Returns:" in doc

    def test_template_docstring_fallback(self, sample_function_info):
        """Template docstring fallback should include function name."""
        from generation.function_docgen import FunctionDocGenerator

        docgen = FunctionDocGenerator.__new__(FunctionDocGenerator)
        doc = docgen._template_docstring("my_function", ["x", "y"], "int")
        assert "x" in doc
        assert "y" in doc
        assert "int" in doc


class TestTestGenerator:
    def test_test_generator_valid_syntax(self, mock_claude_client, sample_function_info):
        """Generated test code must be syntactically valid Python."""
        from generation.test_generator import TestGenerator

        gen = TestGenerator()
        gen.claude = mock_claude_client

        # Mock returns code that should be valid
        mock_claude_client.generate.return_value = (
            "import pytest\n\ndef test_add_numbers_basic():\n    assert 1 + 1 == 2\n",
            100,
        )
        code, _ = gen.generate_unit_tests(sample_function_info)
        assert gen.validate_generated_tests(code)

    def test_hypothesis_test_uses_given_decorator(self, mock_claude_client, sample_function_info):
        """Hypothesis test generation should include @given decorator."""
        from generation.test_generator import TestGenerator

        gen = TestGenerator()
        gen.claude = mock_claude_client
        mock_claude_client.generate.return_value = (
            "from hypothesis import given, strategies as st\n\n"
            "@given(st.integers())\ndef test_prop(n):\n    assert isinstance(n, int)\n",
            150,
        )
        code, _ = gen.generate_hypothesis_tests(sample_function_info)
        assert "@given" in code

    def test_validate_syntax_detects_errors(self):
        """validate_generated_tests should detect syntax errors."""
        from generation.test_generator import TestGenerator

        gen = TestGenerator()
        assert not gen.validate_generated_tests("def broken(:\n    pass\n")
        assert gen.validate_generated_tests("def valid():\n    pass\n")

    def test_readme_generation_has_sections(self, mock_claude_client):
        """Generated README should have ## headers."""
        from generation.repo_docgen import RepoDocGenerator

        docgen = RepoDocGenerator()
        docgen.claude = mock_claude_client
        mock_claude_client.generate.return_value = (
            "# requests\n\n## Overview\nHTTP library.\n\n"
            "## Installation\npip install\n\n## Usage\nexamples here\n",
            200,
        )
        readme, tokens = docgen.generate(
            {"owner": "psf", "repo": "requests", "stars": 50000},
            ["api.py", "sessions.py"],
            {},
        )
        assert "##" in readme


class TestClaudeClient:
    def test_stream_generate_yields_chunks(self):
        """stream_generate should yield multiple text chunks."""
        from generation.claude_client import ClaudeClient

        client = ClaudeClient.__new__(ClaudeClient)

        mock_anthropic = MagicMock()
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Hello", " World", "!"])
        mock_anthropic.messages.stream.return_value = mock_stream
        client.client = mock_anthropic

        chunks = list(client.stream_generate("Test prompt"))
        assert len(chunks) > 1
        assert "Hello" in chunks
