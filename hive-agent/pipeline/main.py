"""End-to-end HIVE-AGENT pipeline entry point."""

import argparse
import logging
import os
import sys
import time
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline(repo_url: str) -> Dict[str, Any]:
    """Run full HIVE-AGENT pipeline. Imports from ALL modules."""

    from agents.graph import HiveAgentGraph

    from monitoring.usage_tracker import UsageTracker
    from monitoring.progress_tracker import ProgressTracker
    from monitoring.alert_manager import AlertManager

    from utils.config_loader import ConfigLoader
    from utils.seed import set_seed

    logger.info(f"Starting HIVE-AGENT pipeline for: {repo_url}")

    # Initialize infrastructure
    set_seed(42)
    progress = ProgressTracker()
    alerts = AlertManager()
    tracker = UsageTracker()
    config = ConfigLoader()  # noqa: F841

    # Check API keys
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not set. Doc generation will be limited.")
    if not os.environ.get("GITHUB_TOKEN"):
        logger.warning("GITHUB_TOKEN not set. API rate limits will be strict.")

    # Run LangGraph 8-node pipeline
    progress.start_stage("Fetch", f"Cloning {repo_url}")
    graph = HiveAgentGraph()

    start_time = time.time()
    try:
        state = graph.run(repo_url)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {"error": str(e), "repo_url": repo_url}

    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.1f}s")

    # Check alerts
    metrics = {
        "complexity_avg": sum(state.get("complexity_scores", {}).values())
        / max(len(state.get("complexity_scores", {})), 1),
        "security_high": sum(
            1 for i in state.get("security_issues", []) if i.get("severity") == "HIGH"
        ),
        "cost_usd": tracker.summary().total_cost_usd,
    }
    triggered = alerts.check(metrics)
    for alert in triggered:
        logger.warning(f"ALERT [{alert.level}]: {alert.message}")

    # Log summary
    trace = state.get("pipeline_trace", [])
    logger.info(f"Pipeline trace: {trace}")
    logger.info(f"Generated docs: {len(state.get('generated_docs', {}))}")
    logger.info(f"Generated tests: {len(state.get('generated_tests', {}))}")
    logger.info(f"Tokens used: {state.get('claude_tokens_used', 0)}")

    return dict(state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HIVE-AGENT Pipeline")
    parser.add_argument("--repo", type=str, default="psf/requests", help="owner/repo or full URL")
    parser.add_argument("--output", type=str, default="assets/results/", help="Output directory")
    args = parser.parse_args()

    repo_url = args.repo
    if not repo_url.startswith("https://"):
        repo_url = f"https://github.com/{repo_url}"

    result = run_pipeline(repo_url)
    if result.get("error"):
        logger.error(f"Pipeline failed: {result['error']}")
        sys.exit(1)
    logger.info("Pipeline completed successfully")
