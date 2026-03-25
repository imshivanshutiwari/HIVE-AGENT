"""Per-class documentation generation."""
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ClassDocGenerator:
    """Generate class documentation using Claude."""

    def __init__(self):
        from generation.claude_client import ClaudeClient
        self.claude = ClaudeClient()

    def generate(self, class_info: Dict[str, Any], filepath: str) -> Tuple[str, int]:
        class_name = class_info.get("name", "Unknown")
        bases = class_info.get("bases", [])
        methods = class_info.get("methods", [])
        method_names = [m.get("name", "") for m in methods[:10]]

        prompt = (
            f"Generate a complete Google-style docstring for this Python class.\n"
            f"Include: class description, Attributes section, and usage Example.\n\n"
            f"Class name: {class_name}\n"
            f"Base classes: {bases}\n"
            f"Methods: {method_names}\n\n"
            f"Return ONLY the docstring content."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"Class doc gen failed for {class_name}: {e}")
            return f"{class_name} class.", 0
