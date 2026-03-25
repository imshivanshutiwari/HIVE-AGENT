"""Full evaluation pipeline benchmark runner."""
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    repo: str
    bertscore_f1: float = 0.0
    rouge1: float = 0.0
    rouge2: float = 0.0
    rougeL: float = 0.0
    function_coverage_before: float = 0.0
    function_coverage_after: float = 0.0
    class_coverage_before: float = 0.0
    avg_rubric_score: float = 0.0
    total_docs_generated: int = 0
    total_tests_generated: int = 0
    security_issues_found: int = 0
    high_complexity_functions: int = 0
    clone_pairs: int = 0


class BenchmarkRunner:
    """Run full evaluation pipeline across multiple repositories."""

    def __init__(self):
        from evaluation.doc_evaluator import DocumentationEvaluator
        from evaluation.coverage_analyzer import CoverageAnalyzer
        from evaluation.quality_rubric import QualityRubric
        self.evaluator = DocumentationEvaluator()
        self.coverage = CoverageAnalyzer()
        self.rubric = QualityRubric()

    def run_for_repo(
        self,
        repo_path: str,
        generated_docs: Dict[str, str],
        ast_results: Dict[str, Any],
        pipeline_state: Dict[str, Any],
    ) -> BenchmarkResult:
        repo_name = os.path.basename(repo_path)
        result = BenchmarkResult(repo=repo_name)

        # Coverage before (without generated docs)
        coverage_before = self.coverage.summary(self.coverage.analyze_repo(repo_path))
        result.function_coverage_before = coverage_before.get("functions", 0.0)
        result.class_coverage_before = coverage_before.get("classes", 0.0)

        # Coverage after (using doc quality scores)
        doc_quality = pipeline_state.get("doc_quality_scores", {})
        result.function_coverage_after = doc_quality.get("coverage_functions", 0.0)
        result.bertscore_f1 = doc_quality.get("bertscore_f1", 0.0)
        result.rouge1 = doc_quality.get("rouge1", 0.0)
        result.rouge2 = doc_quality.get("rouge2", 0.0)
        result.rougeL = doc_quality.get("rougeL", 0.0)

        # Rubric scores
        rubric_scores = []
        for key, doc in list(generated_docs.items())[:20]:
            func_info = {}
            if "::func::" in key:
                func_name = key.split("::")[-1]
                for result_fp, ar in ast_results.items():
                    for func in ar.get("functions", []):
                        if func.get("name") == func_name:
                            func_info = func
                            break
            rubric_result = self.rubric.evaluate(doc, func_info)
            rubric_scores.append(rubric_result.total_score)
        result.avg_rubric_score = sum(rubric_scores) / len(rubric_scores) if rubric_scores else 0.0

        # Stats
        result.total_docs_generated = len(generated_docs)
        result.total_tests_generated = len(pipeline_state.get("generated_tests", {}))
        result.security_issues_found = len(pipeline_state.get("security_issues", []))
        complexity_scores = pipeline_state.get("complexity_scores", {})
        result.high_complexity_functions = sum(1 for v in complexity_scores.values() if v >= 10)
        result.clone_pairs = len(pipeline_state.get("similar_clusters", []))

        return result

    def run_all(self, target_repos: List[str], output_path: str = "results/benchmark.json"):
        from agents.graph import HiveAgentGraph
        graph = HiveAgentGraph()
        all_results = []

        for repo_url in target_repos:
            logger.info(f"Benchmarking {repo_url}")
            try:
                state = graph.run(repo_url)
                br = self.run_for_repo(
                    state.get("repo_path", ""),
                    state.get("generated_docs", {}),
                    state.get("ast_results", {}),
                    state,
                )
                all_results.append(asdict(br))
            except Exception as e:
                logger.error(f"Benchmark failed for {repo_url}: {e}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    runner = BenchmarkRunner()
    runner.run_all(
        ["https://github.com/psf/requests", "https://github.com/pallets/flask"],
        output_path="assets/results/benchmark.json",
    )
