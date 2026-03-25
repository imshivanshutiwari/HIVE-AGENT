"""Analyzer agent: complexity, dependency graph, smells, security."""

import logging
from typing import Any, Dict, List

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def analyzer_node(state: HiveAgentState) -> HiveAgentState:
    """Build dependency graph, compute complexity, detect smells, run security scan."""
    repo_path = state.get("repo_path", "")
    ast_results = state.get("ast_results", {})
    trace = list(state.get("pipeline_trace", []))
    trace.append("analyzer_node:start")
    logger.info(f"[analyzer_node] Analyzing {repo_path}")

    from analysis.dependency_graph import DependencyGraphBuilder
    from analysis.complexity_scorer import ComplexityScorer
    from analysis.code_smell_detector import CodeSmellDetector
    from analysis.security_scanner import SecurityScanner

    dep_builder = DependencyGraphBuilder()
    complexity_scorer = ComplexityScorer()
    smell_detector = CodeSmellDetector()
    security_scanner = SecurityScanner()

    # Build dependency graph
    dep_graph = None
    pagerank_scores: Dict[str, float] = {}
    try:
        dep_graph = dep_builder.build_graph(repo_path)
        pagerank_scores = dep_builder.compute_pagerank(dep_graph)
        logger.info(f"[analyzer_node] Dep graph: {dep_graph.number_of_nodes()} nodes")
    except Exception as e:
        logger.warning(f"[analyzer_node] Dep graph failed: {e}")

    # Complexity scoring
    complexity_scores: Dict[str, float] = {}
    py_files = [fp for fp in ast_results.keys() if fp.endswith(".py")]
    for fp in py_files:
        try:
            fc = complexity_scorer.score_file(fp)
            if fc:
                complexity_scores[fp] = fc.avg_cyclomatic
        except Exception as e:
            logger.debug(f"Complexity score failed for {fp}: {e}")

    # Code smell detection
    code_smells: List[Dict[str, Any]] = []
    for fp in py_files[:50]:  # Limit to first 50 files for speed
        try:
            smells = smell_detector.detect_all(fp)
            for smell in smells:
                code_smells.append(
                    {
                        "name": smell.name,
                        "filepath": smell.filepath,
                        "line": smell.line,
                        "description": smell.description,
                        "severity": smell.severity,
                        "category": smell.category,
                    }
                )
        except Exception as e:
            logger.debug(f"Smell detection failed for {fp}: {e}")

    # Security scan (bandit)
    security_issues: List[Dict[str, Any]] = []
    try:
        scan_results = security_scanner.scan_directory(repo_path)
        for sr in scan_results:
            for issue in sr.issues:
                security_issues.append(
                    {
                        "filepath": issue.filepath,
                        "line": issue.line,
                        "severity": issue.severity,
                        "confidence": issue.confidence,
                        "test_id": issue.test_id,
                        "test_name": issue.test_name,
                        "description": issue.description,
                        "cwe": issue.cwe,
                    }
                )
    except Exception as e:
        logger.warning(f"[analyzer_node] Security scan failed: {e}")

    trace.append(
        f"analyzer_node:complete:smells={len(code_smells)},security={len(security_issues)}"
    )
    return {
        **state,
        "dependency_graph": dep_graph,
        "complexity_scores": complexity_scores,
        "code_smells": code_smells,
        "security_issues": security_issues,
        "pagerank_scores": pagerank_scores,
        "pipeline_trace": trace,
    }
