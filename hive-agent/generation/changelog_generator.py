"""Generate CHANGELOG from commit history."""
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ChangelogGenerator:
    """Generate structured CHANGELOG from commit history."""

    def __init__(self):
        from generation.claude_client import ClaudeClient
        self.claude = ClaudeClient()

    def generate(self, commits: List[Dict[str, Any]], repo_name: str) -> Tuple[str, int]:
        if not commits:
            return "# CHANGELOG\n\nNo commits available.\n", 0

        commit_messages = "\n".join(
            f"- {c.get('sha', '')[:8]} {c.get('message', '')} ({c.get('author', '')} {c.get('date', '')[:10]})"
            for c in commits[:50]
        )
        prompt = (
            f"Generate a structured CHANGELOG.md for repository '{repo_name}' "
            f"from these commits:\n\n{commit_messages}\n\n"
            f"Group by: Breaking Changes, Features, Bug Fixes, Documentation, Other.\n"
            f"Follow Keep a Changelog format. Return complete Markdown."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"Changelog generation failed: {e}")
            return f"# CHANGELOG\n\n{commit_messages}\n", 0
