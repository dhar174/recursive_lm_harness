"""
Token usage and inference cost telemetry across recursive depths.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DepthUsage:
    """Aggregated token and cost metrics at a specific recursive depth."""
    depth: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_cost_usd: float = 0.0
    subcall_count: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens + self.reasoning_tokens


class TokenCostTracker:
    """
    Tracks token economics, recursion depth usage, and cost efficiencies.
    """

    # Estimated pricing per 1M tokens (input, output) in USD
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "gpt-5": {"input": 5.00, "output": 15.00},
        "gpt-5-reasoning": {"input": 10.00, "output": 30.00},
        "gemini-flash": {"input": 0.10, "output": 0.40},
        "rlm-qwen3-8b": {"input": 0.20, "output": 0.60},
        "default": {"input": 2.00, "output": 6.00},
    }

    def __init__(self):
        self.depth_metrics: Dict[int, DepthUsage] = {}

    def record_usage(
        self,
        depth: int,
        prompt_tokens: int,
        completion_tokens: int,
        reasoning_tokens: int = 0,
        model_name: str = "default",
    ) -> None:
        """Records token consumption and accumulates USD cost for a given recursion depth."""
        if depth not in self.depth_metrics:
            self.depth_metrics[depth] = DepthUsage(depth=depth)

        usage = self.depth_metrics[depth]
        usage.prompt_tokens += prompt_tokens
        usage.completion_tokens += completion_tokens
        usage.reasoning_tokens += reasoning_tokens
        usage.subcall_count += 1

        pricing = self.MODEL_PRICING.get(model_name, self.MODEL_PRICING["default"])
        cost = (prompt_tokens / 1_000_000.0) * pricing["input"] + (
            (completion_tokens + reasoning_tokens) / 1_000_000.0
        ) * pricing["output"]
        usage.total_cost_usd += cost

    @property
    def total_cost_usd(self) -> float:
        return sum(u.total_cost_usd for u in self.depth_metrics.values())

    @property
    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self.depth_metrics.values())

    def check_budget_limit(self, depth: int, max_budget_tokens: int) -> bool:
        """Checks if depth token consumption is within allocated budget."""
        current = self.depth_metrics.get(depth)
        if current is None:
            return True
        return current.total_tokens <= max_budget_tokens

    def get_summary(self) -> Dict[str, Any]:
        """Produces a structured profile dictionary of token economics."""
        depth_dist = {f"d{d}": u.total_tokens for d, u in self.depth_metrics.items()}
        max_d = max(self.depth_metrics.keys(), default=0)
        return {
            "total_tokens_consumed": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "depth_distribution": depth_dist,
            "max_depth_reached": max_d,
            "total_subcalls": sum(u.subcall_count for u in self.depth_metrics.values()),
        }

    def compute_efficiency_vs_baseline(self, vanilla_tokens: int, model_name: str = "default") -> float:
        """
        Calculates Cost Multiplier = Cost_RLM / Cost_Vanilla.
        A ratio < 1.0 indicates cost savings.
        """
        if vanilla_tokens <= 0:
            return 1.0
        pricing = self.MODEL_PRICING.get(model_name, self.MODEL_PRICING["default"])
        vanilla_cost = (vanilla_tokens / 1_000_000.0) * pricing["input"]
        if vanilla_cost == 0:
            return 1.0
        return self.total_cost_usd / vanilla_cost
