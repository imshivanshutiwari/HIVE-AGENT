"""Analyze contributor statistics."""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ContributorStats:
    login: str
    avatar_url: str
    contributions: int
    html_url: str


class ContributorAnalyzer:
    """Analyze contributor patterns."""

    def __init__(self, rest_client):
        self.rest = rest_client

    def get_contributors(self, owner: str, repo: str) -> List[ContributorStats]:
        data = self.rest.get_contributors(owner, repo)
        return [
            ContributorStats(
                login=c.get("login", ""),
                avatar_url=c.get("avatar_url", ""),
                contributions=c.get("contributions", 0),
                html_url=c.get("html_url", ""),
            )
            for c in data
        ]

    def analyze_bus_factor(self, contributors: List[ContributorStats]) -> Dict[str, Any]:
        if not contributors:
            return {"bus_factor": 0, "top_contributors": []}
        total = sum(c.contributions for c in contributors)
        cumulative = 0
        bus_factor = 0
        for c in sorted(contributors, key=lambda x: x.contributions, reverse=True):
            cumulative += c.contributions
            bus_factor += 1
            if cumulative / total >= 0.5:
                break
        return {
            "bus_factor": bus_factor,
            "total_contributors": len(contributors),
            "top_contributors": [
                {"login": c.login, "contributions": c.contributions}
                for c in sorted(contributors, key=lambda x: x.contributions, reverse=True)[:10]
            ],
        }
