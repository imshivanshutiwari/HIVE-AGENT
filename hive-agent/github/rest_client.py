"""GitHub REST API v3 client with full rate limit handling."""
import time
import logging
from typing import List, Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


class GitHubRESTClient:
    """Full GitHub REST API v3 client."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.BASE_URL}{path}"
        response = self.session.get(url, params=params)
        self.handle_rate_limit(response)
        response.raise_for_status()
        return response.json()

    def handle_rate_limit(self, response: requests.Response) -> None:
        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        if remaining == 0:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            sleep_time = max(reset_time - time.time(), 0) + 1
            logger.warning(f"Rate limit hit, sleeping {sleep_time:.0f}s")
            time.sleep(sleep_time)

    def get_repo(self, owner: str, repo: str) -> Dict:
        return self._get(f"/repos/{owner}/{repo}")

    def get_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        return self._get(f"/repos/{owner}/{repo}/contents/{path}")

    def get_commits(self, owner: str, repo: str, n: int = 100) -> List[Dict]:
        # GitHub REST API caps per_page at 100
        per_page = min(n, 100)
        return self._get(f"/repos/{owner}/{repo}/commits", params={"per_page": per_page})

    def get_pulls(self, owner: str, repo: str, state: str = "all") -> List[Dict]:
        return self._get(f"/repos/{owner}/{repo}/pulls", params={"state": state, "per_page": 100})

    def get_issues(self, owner: str, repo: str) -> List[Dict]:
        return self._get(f"/repos/{owner}/{repo}/issues", params={"per_page": 100})

    def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        return self._get(f"/repos/{owner}/{repo}/languages")

    def get_contributors(self, owner: str, repo: str) -> List[Dict]:
        return self._get(f"/repos/{owner}/{repo}/contributors", params={"per_page": 100})

    def get_releases(self, owner: str, repo: str) -> List[Dict]:
        return self._get(f"/repos/{owner}/{repo}/releases", params={"per_page": 30})
