"""Analyze GitHub issues."""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class IssueInfo:
    number: int
    title: str
    author: str
    state: str
    created_at: str
    closed_at: str
    labels: List[str]
    comment_count: int


class IssueAnalyzer:
    """Analyze issue patterns."""

    def __init__(self, rest_client):
        self.rest = rest_client

    def get_issues(self, owner: str, repo: str) -> List[IssueInfo]:
        issues = self.rest.get_issues(owner, repo)
        return [
            IssueInfo(
                number=i.get("number", 0),
                title=i.get("title", ""),
                author=(i.get("user") or {}).get("login", ""),
                state=i.get("state", ""),
                created_at=i.get("created_at", ""),
                closed_at=i.get("closed_at") or "",
                labels=[lbl.get("name", "") for lbl in i.get("labels", [])],
                comment_count=i.get("comments", 0),
            )
            for i in issues
            if "pull_request" not in i
        ]

    def analyze_issue_patterns(self, issues: List[IssueInfo]) -> Dict[str, Any]:
        if not issues:
            return {}
        label_counts = Counter(lbl for i in issues for lbl in i.labels)
        return {
            "total_issues": len(issues),
            "open_issues": sum(1 for i in issues if i.state == "open"),
            "closed_issues": sum(1 for i in issues if i.state == "closed"),
            "top_labels": dict(label_counts.most_common(10)),
            "avg_comments": sum(i.comment_count for i in issues) / len(issues),
        }
