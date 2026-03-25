"""Tests for code analysis modules."""
import ast
import sys
import textwrap
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPythonASTParser:
    def test_ast_parses_real_file(self, real_python_file):
        """Parse a real Python file and verify functions are found."""
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        result = parser.parse_file(real_python_file)
        assert result.parse_error is None
        assert len(result.functions) > 0
        func_names = [f.name for f in result.functions]
        assert "simple_function" in func_names

    def test_cyclomatic_complexity_formula(self):
        """Test that cyclomatic complexity matches expected value."""
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        # Simple function: CC = 1
        simple = ast.parse("def foo():\n    return 1").body[0]
        cc = parser.compute_cyclomatic_complexity(simple)
        assert cc == 1

        # Function with one if: CC = 2
        with_if = ast.parse("def bar(x):\n    if x > 0:\n        return x\n    return 0").body[0]
        cc_if = parser.compute_cyclomatic_complexity(with_if)
        assert cc_if >= 2

    def test_extract_imports(self, real_python_file):
        """Test import extraction from real file."""
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        result = parser.parse_file(real_python_file)
        import_modules = [i.module for i in result.imports]
        assert "os" in import_modules or any("os" in m for m in import_modules)

    def test_function_info_fields(self, real_python_file):
        """Test FunctionInfo has all required fields."""
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        result = parser.parse_file(real_python_file)
        assert len(result.functions) > 0
        func = result.functions[0]
        assert hasattr(func, "name")
        assert hasattr(func, "args")
        assert hasattr(func, "cyclomatic_complexity")
        assert hasattr(func, "cognitive_complexity")
        assert func.cyclomatic_complexity >= 1

    def test_class_extraction(self, real_python_file):
        """Test class extraction from real file."""
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        result = parser.parse_file(real_python_file)
        assert len(result.classes) > 0
        cls = result.classes[0]
        assert cls.name == "SampleClass"
        assert len(cls.methods) > 0

    def test_call_graph_is_digraph(self, real_python_file):
        """Test that call graph is a NetworkX DiGraph."""
        from analysis.ast_parser import PythonASTParser
        parser = PythonASTParser()
        result = parser.parse_file(real_python_file)
        assert isinstance(result.call_graph, nx.DiGraph)


class TestDependencyGraph:
    def test_dependency_graph_has_nodes(self, dep_graph):
        """Test that dependency graph has nodes."""
        assert len(dep_graph.nodes()) > 0

    def test_pagerank_sums_to_one(self, dep_graph):
        """Test that PageRank scores sum approximately to 1.0."""
        from analysis.dependency_graph import DependencyGraphBuilder
        builder = DependencyGraphBuilder()
        pagerank = builder.compute_pagerank(dep_graph)
        if pagerank:
            total = sum(pagerank.values())
            assert abs(total - 1.0) < 0.01

    def test_coupling_metrics_exist(self, dep_graph):
        """Test that coupling metrics are computed for all nodes."""
        from analysis.dependency_graph import DependencyGraphBuilder
        builder = DependencyGraphBuilder()
        metrics = builder.compute_coupling_metrics(dep_graph)
        for node in dep_graph.nodes():
            assert node in metrics
            m = metrics[node]
            assert 0.0 <= m.instability <= 1.0

    def test_cytoscape_export_format(self, dep_graph):
        """Test that Cytoscape export has correct format."""
        from analysis.dependency_graph import DependencyGraphBuilder
        builder = DependencyGraphBuilder()
        elements = builder.export_to_cytoscape(dep_graph)
        assert isinstance(elements, list)
        for elem in elements:
            assert "data" in elem
            assert "group" in elem
            assert elem["group"] in ("nodes", "edges")


class TestCodeSimilarityEngine:
    def test_codebert_embedding_shape(self):
        """Test that CodeBERT embedding returns 768-dim vector."""
        from analysis.similarity_engine import CodeSimilarityEngine
        engine = CodeSimilarityEngine()
        emb = engine.embed_function("def foo(): pass")
        assert isinstance(emb, np.ndarray)
        assert emb.shape == (768,)

    def test_cosine_similarity_range(self):
        """Test that cosine similarity is in [-1, 1]."""
        from analysis.similarity_engine import CodeSimilarityEngine
        engine = CodeSimilarityEngine()
        a = engine.embed_function("def add(x, y): return x + y")
        b = engine.embed_function("def multiply(x, y): return x * y")
        sim = engine.cosine_similarity(a, b)
        assert -1.0 <= sim <= 1.0

    def test_identical_code_high_similarity(self):
        """Test that identical code has high similarity."""
        from analysis.similarity_engine import CodeSimilarityEngine
        engine = CodeSimilarityEngine()
        code = "def foo(x):\n    return x * 2\n"
        a = engine.embed_function(code)
        b = engine.embed_function(code)
        sim = engine.cosine_similarity(a, b)
        assert sim > 0.95
