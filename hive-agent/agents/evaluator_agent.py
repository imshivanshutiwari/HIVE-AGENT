"""Evaluator agent: BERTScore + ROUGE + coverage evaluation."""
import logging
from typing import Any, Dict, List

from agents.state import HiveAgentState

logger = logging.getLogger(__name__)


def evaluator_node(state: HiveAgentState) -> HiveAgentState:
    """Evaluate documentation quality with BERTScore, ROUGE, and rubric."""
    generated_docs = state.get("generated_docs", {})
    ast_results = state.get("ast_results", {})
    repo_path = state.get("repo_path", "")
    trace = list(state.get("pipeline_trace", []))
    trace.append("evaluator_node:start")
    logger.info(f"[evaluator_node] Evaluating {len(generated_docs)} docs")

    from evaluation.doc_evaluator import DocumentationEvaluator

    evaluator = DocumentationEvaluator()
    doc_quality_scores: Dict[str, float] = {}

    # Collect generated and reference docs
    generated_list = []
    reference_list = []

    for key, doc in generated_docs.items():
        if "::func::" in key:
            # Use the function source as reference proxy
            parts = key.split("::")
            filepath = parts[0]
            func_name = parts[-1]
            result = ast_results.get(filepath, {})
            for func in result.get("functions", []):
                if func.get("name") == func_name:
                    ref = func.get("source", doc)
                    generated_list.append(doc)
                    reference_list.append(ref[:512])
                    break

    # BERTScore
    bertscore_f1 = 0.0
    if generated_list and reference_list:
        try:
            bert_results = evaluator.compute_bertscore(generated_list[:10], reference_list[:10])
            bertscore_f1 = float(bert_results.get("f1", [0.0])[0]) if bert_results.get("f1") else 0.0
        except Exception as e:
            logger.warning(f"[evaluator_node] BERTScore failed: {e}")

    # ROUGE
    rouge_scores = {}
    if generated_list and reference_list:
        try:
            rouge_scores = evaluator.compute_rouge(generated_list[0], reference_list[0])
        except Exception as e:
            logger.warning(f"[evaluator_node] ROUGE failed: {e}")

    # Coverage
    coverage_report = {}
    if repo_path:
        try:
            coverage_report = evaluator.compute_coverage(repo_path, ast_results)
        except Exception as e:
            logger.warning(f"[evaluator_node] Coverage failed: {e}")

    # Rubric
    rubric_scores = []
    for key, doc in list(generated_docs.items())[:5]:
        try:
            score = evaluator.apply_quality_rubric(doc, {})
            rubric_scores.append(score.total_score)
        except Exception as e:
            logger.debug(f"Rubric failed for {key}: {e}")

    doc_quality_scores = {
        "bertscore_f1": bertscore_f1,
        "rouge1": rouge_scores.get("rouge1", 0.0),
        "rouge2": rouge_scores.get("rouge2", 0.0),
        "rougeL": rouge_scores.get("rougeL", 0.0),
        "coverage_functions": coverage_report.get("functions", 0.0),
        "coverage_classes": coverage_report.get("classes", 0.0),
        "coverage_modules": coverage_report.get("modules", 0.0),
        "avg_rubric_score": sum(rubric_scores) / len(rubric_scores) if rubric_scores else 0.0,
        "total_docs_generated": len(generated_docs),
    }

    trace.append("evaluator_node:complete")
    return {
        **state,
        "doc_quality_scores": doc_quality_scores,
        "pipeline_trace": trace,
    }
