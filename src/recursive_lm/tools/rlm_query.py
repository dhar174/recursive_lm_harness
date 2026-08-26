"""
Isolated recursive child loop spawner with depth caps and token budget decay.
"""

from typing import Any, Callable, Optional

from recursive_lm.core.repl import PersistentREPL
from recursive_lm.core.state import RLMState
from recursive_lm.telemetry.cost_tracker import TokenCostTracker
from recursive_lm.tools.termination import create_termination_tools


class RLMQuerySpawner:
    r"""
    Spawns isolated child REPL environments for complex sub-tasks.
    Enforces recursive depth ceilings ($D_{max} \le 5$) and budget decay ($\gamma = 0.70$).
    """

    def __init__(
        self,
        max_depth: int = 5,
        decay_factor: float = 0.70,
        cost_tracker: Optional[TokenCostTracker] = None,
    ):
        self.max_depth = max_depth
        self.decay_factor = decay_factor
        self.cost_tracker = cost_tracker

    def spawn(
        self,
        sub_context: str,
        sub_goal: str,
        current_depth: int = 1,
        parent_budget_tokens: int = 100_000,
        runner_fn: Optional[Callable[[PersistentREPL, str, int], Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Initializes an isolated child REPL loop and executes the sub-goal.
        """
        # Depth ceiling check
        if current_depth > self.max_depth:
            raise RecursionError(
                f"Maximum recursive depth exceeded: current {current_depth} > max {self.max_depth}"
            )

        # Calculate decayed token budget
        child_budget = int(parent_budget_tokens * (self.decay_factor ** current_depth))

        # Check cost tracker budget limits if configured
        if self.cost_tracker and not self.cost_tracker.check_budget_limit(current_depth, child_budget):
            raise RuntimeError(
                f"Token budget exhausted for recursive depth {current_depth} (budget: {child_budget})"
            )

        # Initialize isolated child state
        child_state = RLMState(context=sub_context)
        child_repl = PersistentREPL(state=child_state)

        # Bind termination tools
        final_fn, final_var_fn = create_termination_tools(child_state)
        child_repl.register_tool("FINAL", final_fn)
        child_repl.register_tool("FINAL_VAR", final_var_fn)

        # Bind self for further recursive delegation if below max_depth
        if current_depth < self.max_depth:
            child_repl.register_tool(
                "rlm_query",
                lambda c, g: self.spawn(
                    sub_context=c,
                    sub_goal=g,
                    current_depth=current_depth + 1,
                    parent_budget_tokens=child_budget,
                    runner_fn=runner_fn,
                    **kwargs,
                ),
            )

        # Execute sub-routine
        if runner_fn and callable(runner_fn):
            return runner_fn(child_repl, sub_goal, child_budget)

        # Default minimal mock execution
        mock_code = f"FINAL('Sub-goal resolved at depth {current_depth}: {sub_goal[:40]}')"
        feedback = child_repl.execute(mock_code)
        if child_state.is_terminated:
            return child_state.termination_value
        return feedback.formatted_output
