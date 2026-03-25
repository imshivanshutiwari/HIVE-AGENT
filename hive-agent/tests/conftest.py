"""pytest fixtures for HIVE-AGENT tests."""
import os
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Add hive-agent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


SAMPLE_PYTHON_SOURCE = textwrap.dedent('''
    """Sample module for testing."""
    import os
    import sys
    from typing import List, Optional


    GLOBAL_VAR = "hello"


    def simple_function(x: int, y: int) -> int:
        """Add two integers.

        Args:
            x: First integer.
            y: Second integer.

        Returns:
            int: Sum of x and y.
        """
        return x + y


    def complex_function(items: List[int], threshold: int = 10) -> List[int]:
        result = []
        for item in items:
            if item > threshold:
                if item % 2 == 0:
                    result.append(item * 2)
                else:
                    result.append(item * 3)
            elif item == 0:
                continue
            else:
                result.append(item)
        return result


    class SampleClass:
        """A sample class for testing.

        Attributes:
            value: The stored value.
        """

        def __init__(self, value: int):
            self.value = value

        def double(self) -> int:
            return self.value * 2

        def is_positive(self) -> bool:
            return self.value > 0


    def undocumented_function(a, b):
        return a + b
''')


@pytest.fixture
def sample_python_source() -> str:
    return SAMPLE_PYTHON_SOURCE


@pytest.fixture
def real_python_file(tmp_path):
    """Create a real Python file for testing."""
    filepath = tmp_path / "sample.py"
    filepath.write_text(SAMPLE_PYTHON_SOURCE)
    return str(filepath)


@pytest.fixture
def ast_result(real_python_file):
    """Parsed AST result from real Python file."""
    from analysis.ast_parser import PythonASTParser
    parser = PythonASTParser()
    return parser.parse_file(real_python_file)


@pytest.fixture
def dep_graph(tmp_path):
    """Build a real NetworkX dependency graph from sample files."""
    import networkx as nx
    # Create a mini repo structure
    (tmp_path / "mymod").mkdir()
    (tmp_path / "mymod" / "__init__.py").write_text("")
    (tmp_path / "mymod" / "core.py").write_text("import os\n")
    (tmp_path / "mymod" / "utils.py").write_text("from mymod import core\n")

    from analysis.dependency_graph import DependencyGraphBuilder
    builder = DependencyGraphBuilder()
    return builder.build_graph(str(tmp_path))


@pytest.fixture
def mock_claude_client():
    """Mock Claude client to avoid API calls in tests."""
    mock = MagicMock()
    mock.generate.return_value = (
        "Summary of function.\n\nArgs:\n    x: First param.\n\nReturns:\n    int: Result.\n\nExample:\n    >>> func(1)\n",
        150,
    )
    mock.generate_with_tools.return_value = (
        "Review: This function looks good. Consider adding type hints.",
        200,
    )
    return mock


@pytest.fixture
def sample_function_info():
    """Sample function info dict for testing."""
    return {
        "name": "add_numbers",
        "args": ["x", "y"],
        "return_type": "int",
        "decorators": [],
        "docstring": "",
        "body_lines": 5,
        "calls_made": [],
        "raises": [],
        "yields": False,
        "is_async": False,
        "cyclomatic_complexity": 1,
        "cognitive_complexity": 0,
        "lineno": 1,
        "source": "def add_numbers(x: int, y: int) -> int:\n    return x + y\n",
    }
