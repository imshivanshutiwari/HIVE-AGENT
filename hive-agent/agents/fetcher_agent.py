"""Fetcher agent: GitHub data collection node."""

import logging
import os

from dotenv import load_dotenv

from agents.state import HiveAgentState

load_dotenv()
logger = logging.getLogger(__name__)


def fetcher_node(state: HiveAgentState) -> HiveAgentState:
    """Fetch repository data: clone, metadata, files, commit history."""
    repo_url = state.get("repo_url", "")
    logger.info(f"[fetcher_node] Processing {repo_url}")

    trace = list(state.get("pipeline_trace", []))
    trace.append("fetcher_node:start")

    try:
        # Parse owner/repo from URL
        if "/" in repo_url:
            parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
            owner, repo_name = parts[0], parts[1]
        else:
            raise ValueError(f"Invalid repo URL: {repo_url}")

        from github.repo_fetcher import RepoFetcher
        from github.commit_analyzer import CommitAnalyzer
        from github.rest_client import GitHubRESTClient

        token = os.environ.get("GITHUB_TOKEN", "")
        fetcher = RepoFetcher(token)

        # Clone repository
        repo_path = fetcher.clone_repo(owner, repo_name, dest="data/repos/")
        logger.info(f"[fetcher_node] Cloned to {repo_path}")

        # Fetch all code files
        all_files = fetcher.fetch_all_files(repo_path)
        logger.info(f"[fetcher_node] Found {len(all_files)} files")

        # Fetch metadata
        try:
            metadata = fetcher.fetch_repo_metadata(owner, repo_name)
            meta_dict = {
                "owner": metadata.owner,
                "repo": metadata.repo,
                "stars": metadata.stars,
                "forks": metadata.forks,
                "watchers": metadata.watchers,
                "primary_language": metadata.primary_language,
                "languages": metadata.languages,
                "topics": metadata.topics,
                "license": metadata.license,
                "total_commits": metadata.total_commits,
                "open_issues": metadata.open_issues,
                "open_prs": metadata.open_prs,
                "contributors": metadata.contributors,
                "disk_usage_kb": metadata.disk_usage_kb,
            }
        except Exception as e:
            logger.warning(f"[fetcher_node] Metadata fetch failed: {e}")
            meta_dict = {"owner": owner, "repo": repo_name}

        # Commit history
        commit_history = []
        try:
            rest = GitHubRESTClient(token)
            analyzer = CommitAnalyzer(rest)
            commits = analyzer.get_commit_stats(owner, repo_name, n=50)
            commit_history = [
                {
                    "sha": c.sha,
                    "author": c.author,
                    "date": c.date,
                    "message": c.message,
                    "additions": c.additions,
                    "deletions": c.deletions,
                }
                for c in commits
            ]
        except Exception as e:
            logger.warning(f"[fetcher_node] Commit history failed: {e}")

        meta_dict["commit_history"] = commit_history

        trace.append("fetcher_node:complete")
        return {
            **state,
            "repo_path": repo_path,
            "repo_metadata": meta_dict,
            "all_files": [
                {
                    "path": f.path,
                    "content": f.content,
                    "language": f.language,
                    "size_bytes": f.size_bytes,
                }
                for f in all_files
            ],
            "pipeline_trace": trace,
        }

    except Exception as e:
        logger.error(f"[fetcher_node] Error: {e}", exc_info=True)
        trace.append(f"fetcher_node:error:{e}")
        return {**state, "pipeline_trace": trace, "error": str(e)}
