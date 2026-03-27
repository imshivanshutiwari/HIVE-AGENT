"""Hypothesis property-based tests for HIVE-AGENT."""

import sys
from pathlib import Path
from typing import Dict, List

import hypothesis
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent))


@given(st.text(min_size=1))
@settings(max_examples=50)
def test_ast_parser_never_crashes(code_str: str):
    """AST parser should handle any string without unhandled exceptions."""
    from analysis.ast_parser import PythonASTParser

    parser = PythonASTParser()
    result = parser.parse_source(code_str)
    # Should either parse successfully or return error; never raise
    assert result is not None
    assert hasattr(result, "functions")
    assert hasattr(result, "parse_error")


@given(
    st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=768,
        max_size=768,
    )
)
@settings(
    max_examples=30,
    suppress_health_check=[
        hypothesis.HealthCheck.data_too_large,
        hypothesis.HealthCheck.large_base_example,
        hypothesis.HealthCheck.too_slow,
    ],
)
def test_cosine_similarity_range(vector: List[float]):
    """Cosine similarity should always be in [-1.0, 1.0]."""
    import numpy as np
    from analysis.similarity_engine import CodeSimilarityEngine

    engine = CodeSimilarityEngine()
    a = np.array(vector, dtype=np.float32)
    b = np.array(list(reversed(vector)), dtype=np.float32)
    sim = engine.cosine_similarity(a, b)
    assert -1.0001 <= sim <= 1.0001


@given(
    st.dictionaries(
        st.text(
            min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))
        ),
        st.integers(min_value=0, max_value=100),
        min_size=2,
        max_size=10,
    )
)
@settings(max_examples=30)
def test_pagerank_always_sums_to_one(graph_dict: Dict[str, int]):
    """PageRank should sum to approximately 1.0 for any valid graph."""
    import networkx as nx
    from analysis.dependency_graph import DependencyGraphBuilder

    builder = DependencyGraphBuilder()
    graph = nx.DiGraph()
    nodes = list(graph_dict.keys())
    if len(nodes) < 2:
        return
    for node in nodes:
        graph.add_node(node)
    for i in range(len(nodes) - 1):
        graph.add_edge(nodes[i], nodes[i + 1])

    pagerank = builder.compute_pagerank(graph)
    if pagerank:
        total = sum(pagerank.values())
        assert abs(total - 1.0) < 0.05


@given(st.integers(min_value=1, max_value=20))
@settings(max_examples=30)
def test_complexity_score_positive(n_branches: int):
    """Cyclomatic complexity should be >= 1 for any function."""
    import ast as ast_mod
    from analysis.ast_parser import PythonASTParser

    # Build a function with n_branches if/else
    conditions = "\n    ".join(f"if x == {i}: pass" for i in range(n_branches))
    source = f"def func(x):\n    {conditions}\n"
    parser = PythonASTParser()
    try:
        tree = ast_mod.parse(source)
        func_node = tree.body[0]
        cc = parser.compute_cyclomatic_complexity(func_node)
        assert cc >= 1
    except SyntaxError:
        pass  # Some generated code may have syntax issues
