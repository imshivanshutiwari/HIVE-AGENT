"""Module-level documentation generation."""

import logging
import os
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class ModuleDocGenerator:
    """Generate module-level documentation using Claude."""

    def __init__(self):
        from generation.claude_client import ClaudeClient

        self.claude = ClaudeClient()

    def generate(self, filepath: str, ast_result: Dict[str, Any]) -> Tuple[str, int]:
        module_name = os.path.basename(filepath)
        functions = [f.get("name", "") for f in ast_result.get("functions", [])[:10]]
        classes = [c.get("name", "") for c in ast_result.get("classes", [])[:5]]
        imports = [i.get("module", "") for i in ast_result.get("imports", [])[:5]]

        prompt = (
            f"Generate a Python module docstring for '{module_name}'.\n"
            f"The module contains:\n"
            f"- Functions: {functions}\n"
            f"- Classes: {classes}\n"
            f"- Key imports: {imports}\n\n"
            f"Return a concise, informative module docstring."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"Module doc gen failed for {filepath}: {e}")
            return f"Module: {module_name}.", 0
