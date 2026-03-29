"""GitHub GraphQL API v4 client."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"


@dataclass
class RepoStats:
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    disk_usage: int = 0
    primary_language: str = ""
    topics: List[str] = field(default_factory=list)
    license: str = ""
    total_commits: int = 0


@dataclass
class Contributor:
    login: str = ""
    name: str = ""
    contribution_count: int = 0
    avatar_url: str = ""


@dataclass
class PRReview:
    pr_number: int = 0
    pr_title: str = ""
    author: str = ""
    state: str = ""
    comment_count: int = 0


@dataclass
class WeeklyStats:
    week_start: str = ""
    additions: int = 0
    deletions: int = 0
    commit_count: int = 0


class GitHubGraphQLClient:
    """GitHub GraphQL API v4 client."""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def query(self, gql_query: str, variables: Optional[Dict] = None) -> Dict:
        payload: Dict[str, Any] = {"query": gql_query}
        if variables:
            payload["variables"] = variables
        response = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            raise RuntimeError(f"GraphQL query failed: {data['errors']}")
        return data.get("data", {})

    def get_repo_stats(self, owner: str, repo: str) -> RepoStats:
        gql = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            stargazerCount
            forkCount
            watchers { totalCount }
            diskUsage
            primaryLanguage { name }
            repositoryTopics(first: 10) {
              nodes { topic { name } }
            }
            licenseInfo { name }
            defaultBranchRef {
              target {
                ... on Commit {
                  history { totalCount }
                }
              }
            }
          }
        }
        """
        data = self.query(gql, {"owner": owner, "repo": repo})
        r = data.get("repository", {})
        return RepoStats(
            stars=r.get("stargazerCount", 0),
            forks=r.get("forkCount", 0),
            watchers=r.get("watchers", {}).get("totalCount", 0),
            disk_usage=r.get("diskUsage", 0),
            primary_language=(r.get("primaryLanguage") or {}).get("name", ""),
            topics=[n["topic"]["name"] for n in r.get("repositoryTopics", {}).get("nodes", [])],
            license=(r.get("licenseInfo") or {}).get("name", ""),
            total_commits=(
                (r.get("defaultBranchRef") or {})
                .get("target", {})
                .get("history", {})
                .get("totalCount", 0)
            ),
        )

    def get_contributor_graph(self, owner: str, repo: str) -> List[Contributor]:
        gql = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            mentionableUsers(first: 50) {
              nodes {
                login
                name
                avatarUrl
                contributionsCollection {
                  totalCommitContributions
                }
              }
            }
          }
        }
        """
        data = self.query(gql, {"owner": owner, "repo": repo})
        users = data.get("repository", {}).get("mentionableUsers", {}).get("nodes", [])
        return [
            Contributor(
                login=u.get("login", ""),
                name=u.get("name") or u.get("login", ""),
                contribution_count=(
                    u.get("contributionsCollection", {}).get("totalCommitContributions", 0)
                ),
                avatar_url=u.get("avatarUrl", ""),
            )
            for u in users
        ]

    def get_pr_reviews(self, owner: str, repo: str) -> List[PRReview]:
        gql = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            pullRequests(first: 20, states: [MERGED, OPEN]) {
              nodes {
                number
                title
                author { login }
                reviews(first: 10) {
                  nodes {
                    state
                    comments { totalCount }
                  }
                }
              }
            }
          }
        }
        """
        data = self.query(gql, {"owner": owner, "repo": repo})
        prs = data.get("repository", {}).get("pullRequests", {}).get("nodes", [])
        results = []
        for pr in prs:
            for review in pr.get("reviews", {}).get("nodes", []):
                results.append(
                    PRReview(
                        pr_number=pr.get("number", 0),
                        pr_title=pr.get("title", ""),
                        author=(pr.get("author") or {}).get("login", ""),
                        state=review.get("state", ""),
                        comment_count=review.get("comments", {}).get("totalCount", 0),
                    )
                )
        return results

    def get_code_frequency(self, owner: str, repo: str) -> List[WeeklyStats]:
        gql = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 10) {
                    nodes {
                      committedDate
                      additions
                      deletions
                    }
                  }
                }
              }
            }
          }
        }
        """
        data = self.query(gql, {"owner": owner, "repo": repo})
        history = (
            data.get("repository", {})
            .get("defaultBranchRef", {})
            .get("target", {})
            .get("history", {})
            .get("nodes", [])
        )
        return [
            WeeklyStats(
                week_start=n.get("committedDate", "")[:10],
                additions=n.get("additions", 0),
                deletions=n.get("deletions", 0),
                commit_count=1,
            )
            for n in history
        ]
