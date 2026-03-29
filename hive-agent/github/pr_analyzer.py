"""Analyze pull request data."""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PRInfo:
    number: int
    title: str
    author: str
    state: str
    created_at: str
    merged_at: str
    changed_files: int
    additions: int
    deletions: int
    review_count: int
    comment_count: int


class PRAnalyzer:
    """Analyze pull request patterns."""

    def __init__(self, rest_client):
        self.rest = rest_client

    def get_pr_info(self, owner: str, repo: str) -> List[PRInfo]:
        prs = self.rest.get_pulls(owner, repo, state="all")
        results = []
        for pr in prs:
            results.append(
                PRInfo(
                    number=pr.get("number", 0),
                    title=pr.get("title", ""),
                    author=(pr.get("user") or {}).get("login", ""),
                    state=pr.get("state", ""),
                    created_at=pr.get("created_at", ""),
                    merged_at=pr.get("merged_at") or "",
                    changed_files=pr.get("changed_files", 0),
                    additions=pr.get("additions", 0),
                    deletions=pr.get("deletions", 0),
                    review_count=pr.get("review_comments", 0),
                    comment_count=pr.get("comments", 0),
                )
            )
        return results

    def analyze_pr_patterns(self, prs: List[PRInfo]) -> Dict[str, Any]:
        if not prs:
            return {}
        merged = [p for p in prs if p.merged_at]
        merge_times = []
        for pr in merged:
            try:
                from datetime import datetime

                created = datetime.fromisoformat(pr.created_at.replace("Z", "+00:00"))
                merged_dt = datetime.fromisoformat(pr.merged_at.replace("Z", "+00:00"))
                merge_times.append((merged_dt - created).total_seconds() / 3600)
            except Exception:
                pass
        return {
            "total_prs": len(prs),
            "merged_prs": len(merged),
            "open_prs": sum(1 for p in prs if p.state == "open"),
            "avg_merge_time_hours": sum(merge_times) / len(merge_times) if merge_times else 0,
            "avg_changed_files": sum(p.changed_files for p in prs) / len(prs),
        }
