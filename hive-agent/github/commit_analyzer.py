"""Analyze commit history from GitHub repos."""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class CommitStats:
    sha: str
    author: str
    author_email: str
    date: str
    message: str
    additions: int
    deletions: int
    files_changed: int


class CommitAnalyzer:
    """Analyze commit history patterns."""

    def __init__(self, rest_client):
        self.rest = rest_client

    def get_commit_stats(self, owner: str, repo: str, n: int = 100) -> List[CommitStats]:
        commits = self.rest.get_commits(owner, repo, n)
        stats = []
        for c in commits:
            commit_data = c.get("commit", {})
            author = commit_data.get("author", {})
            stats.append(
                CommitStats(
                    sha=c.get("sha", "")[:8],
                    author=author.get("name", "unknown"),
                    author_email=author.get("email", ""),
                    date=author.get("date", ""),
                    message=commit_data.get("message", "").split("\n")[0][:80],
                    additions=c.get("stats", {}).get("additions", 0),
                    deletions=c.get("stats", {}).get("deletions", 0),
                    files_changed=len(c.get("files", [])),
                )
            )
        return stats

    def analyze_commit_patterns(self, commits: List[CommitStats]) -> Dict[str, Any]:
        if not commits:
            return {}

        from collections import Counter

        authors = Counter(c.author for c in commits)
        dates = [c.date for c in commits if c.date]
        by_hour: Dict[int, int] = Counter()
        by_day: Dict[int, int] = Counter()

        for d in dates:
            try:
                dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
                by_hour[dt.hour] += 1
                by_day[dt.weekday()] += 1
            except ValueError:
                pass

        return {
            "total_commits": len(commits),
            "unique_authors": len(authors),
            "top_authors": dict(authors.most_common(10)),
            "commits_by_hour": dict(by_hour),
            "commits_by_day": dict(by_day),
            "avg_additions": sum(c.additions for c in commits) / len(commits),
            "avg_deletions": sum(c.deletions for c in commits) / len(commits),
        }
