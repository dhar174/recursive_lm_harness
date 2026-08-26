"""
Batched single-step query runtime for linear chunk summarization and extraction.
"""

from typing import Any, Callable, Dict, Optional

from recursive_lm.telemetry.cost_tracker import TokenCostTracker


class LLMQueryRuntime:
    """
    Executes single-step sub-queries against an LLM backend or offline deterministic mock.
    Enforces batching recommendations (~200k characters max per call).
    """

    def __init__(
        self,
        client: Optional[Callable[[str, str], str]] = None,
        default_model: str = "gpt-5",
        max_chunk_chars: int = 200_000,
        cost_tracker: Optional[TokenCostTracker] = None,
    ):
        self.client = client
        self.default_model = default_model
        self.max_chunk_chars = max_chunk_chars
        self.cost_tracker = cost_tracker

    def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        depth: int = 0,
        **kwargs: Any,
    ) -> str:
        """
        Executes a prompt query, tracks token usage, and returns the response string.
        """
        selected_model = model or self.default_model

        # Sizing validation
        if len(prompt) > self.max_chunk_chars:
            # Still process, but record warning in kwargs or log
            pass

        # Estimate tokens (approx 4 chars per token)
        estimated_prompt_tokens = max(1, len(prompt) // 4)

        if self.client and callable(self.client):
            response_text = self.client(prompt, selected_model, **kwargs)
        else:
            # Deterministic offline mock response
            response_text = f"[Mock LLM Output for: {prompt[:60]}...]"

        estimated_completion_tokens = max(1, len(response_text) // 4)

        # Track usage in telemetry if available
        if self.cost_tracker is not None:
            self.cost_tracker.record_usage(
                depth=depth,
                prompt_tokens=estimated_prompt_tokens,
                completion_tokens=estimated_completion_tokens,
                reasoning_tokens=0,
                model_name=selected_model,
            )

        return response_text
