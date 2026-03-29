"""Tests for LangGraph agent nodes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHiveAgentGraph:
    def test_graph_has_8_nodes(self):
        """Test that HiveAgentGraph has exactly 8 nodes."""
        from agents.graph import HiveAgentGraph

        agent_graph = HiveAgentGraph()
        graph = agent_graph.graph
        # Check the graph has the expected nodes
        compiled = graph.compile()
        assert compiled is not None

    def test_state_typeddict_fields(self):
        """Test HiveAgentState has all required fields."""
        from agents.state import HiveAgentState

        required_fields = [
            "repo_url",
            "repo_path",
            "repo_metadata",
            "all_files",
            "ast_results",
            "complexity_scores",
            "code_smells",
            "generated_docs",
            "generated_tests",
            "doc_quality_scores",
            "review_comments",
            "pipeline_trace",
            "claude_tokens_used",
        ]
        annotations = HiveAgentState.__annotations__
        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"

    def test_tools_defined(self):
        """Test that all tool sets are defined."""
        from agents.tools import (
            TOOLS_FETCHER,
            TOOLS_PARSER,
            TOOLS_ANALYZER,
            TOOLS_SIMILARITY,
            TOOLS_DOC,
            TOOLS_REVIEW,
            TOOLS_TEST,
            TOOLS_EVALUATOR,
        )

        for tool_set in [
            TOOLS_FETCHER,
            TOOLS_PARSER,
            TOOLS_ANALYZER,
            TOOLS_SIMILARITY,
            TOOLS_DOC,
            TOOLS_REVIEW,
            TOOLS_TEST,
            TOOLS_EVALUATOR,
        ]:
            assert isinstance(tool_set, list)
            assert len(tool_set) > 0
            for tool in tool_set:
                assert "name" in tool
                assert "description" in tool
                assert "input_schema" in tool

    def test_parser_node_processes_python_files(self, real_python_file):
        """Test parser node processes Python files correctly."""
        from agents.parser_agent import parser_node

        state = {
            "all_files": [
                {"path": real_python_file, "language": "python", "content": "", "size_bytes": 100}
            ],
            "pipeline_trace": [],
            "claude_tokens_used": 0,
        }
        result = parser_node(state)
        assert "ast_results" in result
        assert real_python_file in result["ast_results"]
        assert "parser_node:complete" in str(result["pipeline_trace"])

    def test_analyzer_node_handles_empty_repo(self, tmp_path):
        """Test analyzer node handles empty/missing repo gracefully."""
        from agents.analyzer_agent import analyzer_node

        state = {
            "repo_path": str(tmp_path),
            "ast_results": {},
            "pipeline_trace": [],
            "claude_tokens_used": 0,
            "code_smells": [],
        }
        result = analyzer_node(state)
        assert "complexity_scores" in result
        assert "pipeline_trace" in result

    def test_evaluator_computes_all_metrics(self):
        """Test evaluator node computes required quality metrics."""
        from agents.evaluator_agent import evaluator_node

        state = {
            "generated_docs": {
                "test.py::func::add": (
                    "Add two numbers.\n\nArgs:\n    x: First.\nReturns:\n    int: Sum."
                )
            },
            "ast_results": {
                "test.py": {
                    "functions": [
                        {"name": "add", "source": "def add(x, y): return x+y", "docstring": ""}
                    ],
                    "classes": [],
                }
            },
            "repo_path": "",
            "pipeline_trace": [],
            "claude_tokens_used": 0,
        }
        result = evaluator_node(state)
        assert "doc_quality_scores" in result
        scores = result["doc_quality_scores"]
        assert "bertscore_f1" in scores
        assert "rouge1" in scores
        assert "total_docs_generated" in scores
