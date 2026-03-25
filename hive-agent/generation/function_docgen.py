"""Per-function Google-style docstring generation."""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FunctionDocGenerator:
    """Generate Google-style docstrings per function using Claude."""

    def __init__(self):
        from generation.claude_client import ClaudeClient
        from agents.tools import TOOLS_DOC

        self.claude = ClaudeClient()
        self.tools = TOOLS_DOC

    def generate(
        self,
        func_info: Dict[str, Any],
        filepath: str,
        context: Optional[str] = None,
    ) -> Tuple[str, int]:
        """Generate docstring for a function. Returns (docstring, tokens)."""
        func_name = func_info.get("name", "unknown")
        func_source = func_info.get("source", "")
        args = func_info.get("args", [])
        return_type = func_info.get("return_type", "")
        calls_made = func_info.get("calls_made", [])

        if not func_source:
            return self._template_docstring(func_name, args, return_type), 0

        prompt = (
            f"Generate a complete Google-style Python docstring for this function.\n"
            f"Include: one-line summary, Args section, Returns section,"
            f" Raises section (if applicable), "
            f"and a usage Example.\n\n"
            f"Function:\n```python\n{func_source[:2000]}\n```\n\n"
            f"Args: {args}\nReturn type: {return_type}\nCalls: {calls_made[:5]}\n"
            f"{'Context: ' + context if context else ''}\n\n"
            f"Return ONLY the docstring content (without the triple quotes)."
        )
        try:
            text, tokens = self.claude.generate(prompt)
            return text.strip(), tokens
        except Exception as e:
            logger.warning(f"Claude docgen failed for {func_name}: {e}")
            return self._template_docstring(func_name, args, return_type), 0

    def _template_docstring(self, name: str, args: List[str], return_type: str) -> str:
        args_section = "\n".join(
            f"    {a}: Description of {a}." for a in args if a not in ("self", "cls")
        )
        return (
            f"{name.replace('_', ' ').capitalize()}.\n\n"
            f"Args:\n{args_section or '    None'}\n\n"
            f"Returns:\n    {return_type or 'None'}: Description of return value.\n"
        )

    def generate_batch(
        self, functions: List[Dict[str, Any]], filepath: str, max_concurrent: int = 5
    ) -> Dict[str, str]:
        results = {}
        for func in functions:
            doc, _ = self.generate(func, filepath)
            results[func.get("name", "")] = doc
        return results

    def improve_existing(self, func_info: Dict[str, Any], existing_doc: str) -> Tuple[str, int]:
        prompt = (
            f"Improve this existing docstring to be more complete and accurate.\n"
            f"Current docstring:\n{existing_doc}\n\n"
            f"Function source:\n```python\n{func_info.get('source', '')[:1000]}\n```\n\n"
            f"Return the improved docstring content only."
        )
        try:
            return self.claude.generate(prompt)
        except Exception as e:
            logger.warning(f"Improve docstring failed: {e}")
            return existing_doc, 0
