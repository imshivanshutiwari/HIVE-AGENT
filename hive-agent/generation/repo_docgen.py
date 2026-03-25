"""Full repository README generation."""
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class RepoDocGenerator:
    """Generate full repository README using Claude."""

    def __init__(self):
        from generation.claude_client import ClaudeClient
        self.claude = ClaudeClient()

    def generate(
        self,
        repo_metadata: Dict[str, Any],
        file_list: List[str],
        ast_results: Dict[str, Any],
    ) -> Tuple[str, int]:
        owner = repo_metadata.get("owner", "")
        repo = repo_metadata.get("repo", "")
        stars = repo_metadata.get("stars", 0)
        language = repo_metadata.get("primary_language", "Python")
        languages = list(repo_metadata.get("languages", {}).keys())
        topics = repo_metadata.get("topics", [])

        all_functions = []
        all_classes = []
        for result in list(ast_results.values())[:10]:
            all_functions.extend(f.get("name", "") for f in result.get("functions", [])[:5])
            all_classes.extend(c.get("name", "") for c in result.get("classes", [])[:3])

        prompt = (
            f"Generate a comprehensive README.md for the GitHub repository {owner}/{repo}.\n\n"
            f"Repository details:\n"
            f"- Stars: {stars}\n"
            f"- Primary language: {language}\n"
            f"- Languages: {languages}\n"
            f"- Topics: {topics}\n"
            f"- Files: {len(file_list)}\n"
            f"- Key functions: {all_functions[:15]}\n"
            f"- Key classes: {all_classes[:10]}\n\n"
            f"Include sections: ## Overview, ## Installation, ## Usage, ## Architecture, "
            f"## API Reference, ## Contributing, ## License\n\n"
            f"Return complete Markdown."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"README generation failed: {e}")
            return f"# {repo}\n\nRepository documentation.\n", 0
