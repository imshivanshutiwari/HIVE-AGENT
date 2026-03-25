"""Fetch and clone real GitHub repositories."""
import os
import logging
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import git
from dotenv import load_dotenv

from github.rest_client import GitHubRESTClient
from github.graphql_client import GitHubGraphQLClient

load_dotenv()
logger = logging.getLogger(__name__)

EXTENSION_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".rb": "ruby",
    ".php": "php",
}

TARGET_REPOS = {
    "python": [
        "psf/requests",
        "pallets/flask",
        "django/django",
        "scikit-learn/scikit-learn",
        "tiangolo/fastapi",
        "langchain-ai/langchain",
        "huggingface/transformers",
        "numpy/numpy",
        "pandas-dev/pandas",
    ],
    "javascript": [
        "facebook/react",
        "vuejs/vue",
        "expressjs/express",
        "axios/axios",
    ],
    "go": ["golang/go", "gin-gonic/gin"],
    "rust": ["rust-lang/rust", "tokio-rs/tokio"],
    "other": ["microsoft/vscode", "torvalds/linux"],
}


@dataclass
class CodeFile:
    path: str
    content: str
    language: str
    size_bytes: int


@dataclass
class RepoMetadata:
    owner: str
    repo: str
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    primary_language: str = ""
    languages: dict = field(default_factory=dict)
    topics: List[str] = field(default_factory=list)
    license: str = ""
    total_commits: int = 0
    open_issues: int = 0
    open_prs: int = 0
    contributors: int = 0
    disk_usage_kb: int = 0


class RepoFetcher:
    """Fetch real GitHub repos via GitPython + REST + GraphQL."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.rest = GitHubRESTClient(self.token)
        self.gql = GitHubGraphQLClient(self.token)

    def clone_repo(self, owner: str, repo: str, dest: str = "data/repos/") -> str:
        dest_path = os.path.join(dest, f"{owner}_{repo}")
        if os.path.exists(dest_path):
            logger.info(f"Repo already cloned at {dest_path}")
            return dest_path
        url = f"https://github.com/{owner}/{repo}.git"
        if self.token:
            url = f"https://{self.token}@github.com/{owner}/{repo}.git"
        os.makedirs(dest, exist_ok=True)
        logger.info(f"Cloning {owner}/{repo} to {dest_path}")
        git.Repo.clone_from(url, dest_path, depth=50)
        return dest_path

    def fetch_all_files(
        self,
        repo_path: str,
        extensions: Optional[List[str]] = None,
        max_size_kb: int = 500,
    ) -> List[CodeFile]:
        if extensions is None:
            extensions = list(EXTENSION_TO_LANG.keys())
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__"}]
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext not in extensions:
                    continue
                fpath = os.path.join(root, fname)
                size = os.path.getsize(fpath)
                if size > max_size_kb * 1024:
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    files.append(
                        CodeFile(
                            path=fpath,
                            content=content,
                            language=EXTENSION_TO_LANG.get(ext, "unknown"),
                            size_bytes=size,
                        )
                    )
                except OSError as e:
                    logger.warning(f"Cannot read {fpath}: {e}")
        return files

    def fetch_repo_metadata(self, owner: str, repo: str) -> RepoMetadata:
        rest_data = self.rest.get_repo(owner, repo)
        gql_stats = self.gql.get_repo_stats(owner, repo)
        languages = self.rest.get_languages(owner, repo)
        issues = self.rest.get_issues(owner, repo)
        prs = self.rest.get_pulls(owner, repo, state="open")
        contributors = self.rest.get_contributors(owner, repo)
        return RepoMetadata(
            owner=owner,
            repo=repo,
            stars=rest_data.get("stargazers_count", 0),
            forks=rest_data.get("forks_count", 0),
            watchers=rest_data.get("watchers_count", 0),
            primary_language=rest_data.get("language", ""),
            languages=languages,
            topics=rest_data.get("topics", []),
            license=(rest_data.get("license") or {}).get("name", ""),
            total_commits=gql_stats.total_commits,
            open_issues=rest_data.get("open_issues_count", 0),
            open_prs=len(prs),
            contributors=len(contributors),
            disk_usage_kb=rest_data.get("size", 0),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clone-targets", action="store_true")
    parser.add_argument("--repo", type=str, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    fetcher = RepoFetcher()

    if args.clone_targets:
        for lang, repos in TARGET_REPOS.items():
            for r in repos[:2]:
                owner, name = r.split("/")
                try:
                    path = fetcher.clone_repo(owner, name)
                    logger.info(f"Cloned {r} → {path}")
                except Exception as e:
                    logger.error(f"Failed {r}: {e}")
    elif args.repo:
        owner, name = args.repo.split("/")
        path = fetcher.clone_repo(owner, name)
        logger.info(f"Cloned to {path}")
