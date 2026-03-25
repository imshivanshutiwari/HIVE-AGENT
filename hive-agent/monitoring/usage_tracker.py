"""Claude API token usage tracking."""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

LOG_PATH = "assets/results/usage_log.jsonl"


@dataclass
class APICall:
    timestamp: float
    model: str
    input_tokens: int
    output_tokens: int
    agent: str
    cost_usd: float


@dataclass
class UsageSummary:
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    calls_by_agent: Dict[str, int] = field(default_factory=dict)
    tokens_by_agent: Dict[str, int] = field(default_factory=dict)


class UsageTracker:
    """Track Claude API token usage and costs."""

    COST_PER_INPUT_TOKEN = 3 / 1_000_000  # $3/1M
    COST_PER_OUTPUT_TOKEN = 15 / 1_000_000  # $15/1M

    def __init__(self):
        self.calls: List[APICall] = []
        Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> APICall:
        cost = input_tokens * self.COST_PER_INPUT_TOKEN + output_tokens * self.COST_PER_OUTPUT_TOKEN
        call = APICall(
            timestamp=time.time(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            agent=agent,
            cost_usd=cost,
        )
        self.calls.append(call)
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(asdict(call)) + "\n")
        except OSError as e:
            logger.warning(f"Could not write usage log: {e}")
        return call

    def summary(self) -> UsageSummary:
        summary = UsageSummary(total_calls=len(self.calls))
        for call in self.calls:
            summary.total_input_tokens += call.input_tokens
            summary.total_output_tokens += call.output_tokens
            summary.total_cost_usd += call.cost_usd
            summary.calls_by_agent[call.agent] = summary.calls_by_agent.get(call.agent, 0) + 1
            tokens = call.input_tokens + call.output_tokens
            summary.tokens_by_agent[call.agent] = (
                summary.tokens_by_agent.get(call.agent, 0) + tokens
            )
        return summary
