"""Tests for GitHub API clients and analyzers."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGitHubRESTClient:
    def test_rest_client_initialization(self):
        """Test REST client initializes with correct headers."""
        from github.rest_client import GitHubRESTClient
        client = GitHubRESTClient("test_token")
        assert "Authorization" in client.headers
        assert "token test_token" in client.headers["Authorization"]

    def test_handle_rate_limit_no_sleep_when_remaining(self):
        """Test rate limit handler does not sleep when remaining > 0."""
        import time
        from github.rest_client import GitHubRESTClient
        client = GitHubRESTClient("test")
        mock_response = MagicMock()
        mock_response.headers = {"X-RateLimit-Remaining": "100", "X-RateLimit-Reset": str(int(time.time()) + 60)}
        start = time.time()
        client.handle_rate_limit(mock_response)
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should not sleep

    def test_get_repo_constructs_correct_url(self):
        """Test get_repo makes request to correct endpoint."""
        from github.rest_client import GitHubRESTClient
        client = GitHubRESTClient("test")
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "requests", "stargazers_count": 1000}
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_response.raise_for_status = MagicMock()
        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            result = client.get_repo("psf", "requests")
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "repos/psf/requests" in called_url
        assert result["name"] == "requests"

    def test_get_commits_returns_list(self):
        """Test get_commits returns list of commit dicts."""
        from github.rest_client import GitHubRESTClient
        client = GitHubRESTClient("test")
        mock_response = MagicMock()
        mock_response.json.return_value = [{"sha": "abc123", "commit": {"message": "fix: bug"}}]
        mock_response.headers = {"X-RateLimit-Remaining": "100"}
        mock_response.raise_for_status = MagicMock()
        with patch.object(client.session, "get", return_value=mock_response):
            commits = client.get_commits("psf", "requests", n=10)
        assert isinstance(commits, list)
        assert len(commits) == 1
        assert commits[0]["sha"] == "abc123"

    def test_commit_analyzer_patterns(self):
        """Test CommitAnalyzer.analyze_commit_patterns returns correct keys."""
        from github.commit_analyzer import CommitAnalyzer, CommitStats
        mock_rest = MagicMock()
        analyzer = CommitAnalyzer(mock_rest)
        commits = [
            CommitStats(
                sha="abc123",
                author="alice",
                author_email="a@b.com",
                date="2024-01-15T10:30:00Z",
                message="feat: add feature",
                additions=50,
                deletions=10,
                files_changed=3,
            ),
            CommitStats(
                sha="def456",
                author="bob",
                author_email="b@c.com",
                date="2024-01-16T14:00:00Z",
                message="fix: resolve bug",
                additions=5,
                deletions=2,
                files_changed=1,
            ),
        ]
        patterns = analyzer.analyze_commit_patterns(commits)
        assert "total_commits" in patterns
        assert patterns["total_commits"] == 2
        assert "unique_authors" in patterns
        assert patterns["unique_authors"] == 2
        assert "top_authors" in patterns
