"""Claude claude-sonnet-4-6 client with tool_use + streaming."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_SYSTEM = (
    "You are HIVE-AGENT, an expert software engineer specializing in "
    "code analysis, documentation generation, and code quality improvement. "
    "Provide precise, technical, production-quality responses."
)


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def total_cost_usd(self) -> float:
        # claude-sonnet-4-6 pricing: $3/1M input, $15/1M output
        return (self.input_tokens * 3 + self.output_tokens * 15) / 1_000_000


class ClaudeClient:
    """Anthropic claude-sonnet-4-6 with tool_use + streaming."""

    MODEL = "claude-sonnet-4-6"

    def __init__(self):
        import anthropic

        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        self.total_tokens = TokenUsage()

    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system: Optional[str] = None,
    ) -> Tuple[str, int]:
        """Generate response with tool_use. Returns (text, tokens_used)."""
        messages = [{"role": "user", "content": prompt}]
        total_tokens = 0

        for _ in range(5):  # max 5 tool-use rounds
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=4096,
                system=system or DEFAULT_SYSTEM,
                tools=tools,
                messages=messages,
            )
            usage = self.track_usage(response)
            total_tokens += usage.input_tokens + usage.output_tokens

            # Check stop reason
            if response.stop_reason == "end_turn":
                text = "".join(block.text for block in response.content if hasattr(block, "text"))
                return text, total_tokens

            if response.stop_reason == "tool_use":
                # Process tool calls (simulate tool execution)
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        # Simulate tool result
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Tool {block.name} executed successfully.",
                            }
                        )
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        # Fallback: extract text from last response
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return text, total_tokens

    def generate(self, prompt: str, system: Optional[str] = None) -> Tuple[str, int]:
        """Simple text generation without tools."""
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            system=system or DEFAULT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = self.track_usage(response)
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        return text, usage.input_tokens + usage.output_tokens

    def stream_generate(self, prompt: str) -> Iterator[str]:
        """Stream generation, yielding text chunks."""
        with self.client.messages.stream(
            model=self.MODEL,
            max_tokens=4096,
            system=DEFAULT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    def track_usage(self, response) -> TokenUsage:
        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        self.total_tokens.input_tokens += usage.input_tokens
        self.total_tokens.output_tokens += usage.output_tokens
        return usage
