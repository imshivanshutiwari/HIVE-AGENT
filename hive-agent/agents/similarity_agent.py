"""Similarity agent: CodeBERT embeddings, clone detection, clustering."""
import logging
from typing import Any, Dict, List, Tuple

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def similarity_node(state: HiveAgentState) -> HiveAgentState:
    """Compute code similarity, detect clones, cluster functions."""
    ast_results = state.get("ast_results", {})
    trace = list(state.get("pipeline_trace", []))
    trace.append("similarity_node:start")
    logger.info(f"[similarity_node] Processing {len(ast_results)} files")

    from analysis.similarity_engine import CodeSimilarityEngine
    from analysis.dead_code_finder import DeadCodeFinder

    similarity_engine = CodeSimilarityEngine()
    dead_code_finder = DeadCodeFinder()

    # Collect all functions
    functions: List[Tuple[str, str, str]] = []
    for filepath, result in ast_results.items():
        for func in result.get("functions", []):
            source = func.get("source", "") or func.get("body", "")
            if source and len(source) > 10:
                functions.append((filepath, func.get("name", ""), source))

    logger.info(f"[similarity_node] Embedding {len(functions)} functions")

    # Detect clones (limit to first 200 for performance)
    clone_pairs = []
    try:
        sample = functions[:200]
        clone_results = similarity_engine.detect_code_clones(sample, threshold=0.9)
        clone_pairs = [
            {
                "file_a": cp.file_a,
                "func_a": cp.func_a,
                "file_b": cp.file_b,
                "func_b": cp.func_b,
                "similarity": cp.similarity,
            }
            for cp in clone_results
        ]
    except Exception as e:
        logger.warning(f"[similarity_node] Clone detection failed: {e}")

    # Cluster functions
    clusters = []
    try:
        sample = functions[:200]
        cluster_results = similarity_engine.cluster_functions(sample, n_clusters=min(20, len(sample)))
        clusters = [
            {
                "cluster_id": c.cluster_id,
                "functions": [
                    {"filepath": f.filepath, "name": f.function_name, "score": f.score}
                    for f in c.functions
                ],
            }
            for c in cluster_results
        ]
    except Exception as e:
        logger.warning(f"[similarity_node] Clustering failed: {e}")

    # Dead code detection
    dead_code = []
    for filepath in list(ast_results.keys())[:50]:
        if filepath.endswith(".py"):
            try:
                results = dead_code_finder.find_dead_code(filepath)
                dead_code.extend([
                    {
                        "filepath": r.filepath,
                        "function_name": r.function_name,
                        "lineno": r.lineno,
                        "reason": r.reason,
                    }
                    for r in results
                ])
            except Exception as e:
                logger.debug(f"Dead code finder failed for {filepath}: {e}")

    trace.append(f"similarity_node:complete:clones={len(clone_pairs)},clusters={len(clusters)}")
    return {
        **state,
        "similar_clusters": clusters,
        "pipeline_trace": trace,
        "code_smells": list(state.get("code_smells", [])) + [
            {
                "name": f"Dead code: {d['function_name']}",
                "filepath": d["filepath"],
                "line": d["lineno"],
                "description": d["reason"],
                "severity": "low",
                "category": "dead_code",
            }
            for d in dead_code
        ],
    }
