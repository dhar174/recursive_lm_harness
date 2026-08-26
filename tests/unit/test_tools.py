"""
Unit tests for RLM tools: llm_query, rlm_query, and termination hooks.
"""

import pytest
from recursive_lm.core.state import RLMState
from recursive_lm.telemetry.cost_tracker import TokenCostTracker
from recursive_lm.tools.llm_query import LLMQueryRuntime
from recursive_lm.tools.rlm_query import RLMQuerySpawner
from recursive_lm.tools.termination import TerminationSignal, create_termination_tools


def test_termination_tools():
    state = RLMState(context="")
    state.set_variable("my_var", "Alpha Omega")
    final_fn, final_var_fn = create_termination_tools(state)

    # Test FINAL raises TerminationSignal
    with pytest.raises(TerminationSignal) as exc_info:
        final_fn("direct_answer")
    assert exc_info.value.value == "direct_answer"
    assert state.is_terminated is True
    assert state.termination_value == "direct_answer"

    # Test FINAL_VAR raises TerminationSignal
    with pytest.raises(TerminationSignal) as exc_info_var:
        final_var_fn("my_var")
    assert exc_info_var.value.value == "Alpha Omega"
    assert state.termination_value == "Alpha Omega"


def test_llm_query_runtime():
    cost_tracker = TokenCostTracker()
    runtime = LLMQueryRuntime(cost_tracker=cost_tracker)

    # Test offline mock query
    result = runtime.query("Summarize this chunk of text", depth=0)
    assert "[Mock LLM Output" in result
    assert cost_tracker.total_tokens > 0

    # Test custom client
    custom_runtime = LLMQueryRuntime(
        client=lambda prompt, model, **kw: f"Echo: {prompt} via {model}",
        default_model="gemini-flash",
    )
    res = custom_runtime.query("Hello World")
    assert res == "Echo: Hello World via gemini-flash"


def test_rlm_query_spawner_execution():
    cost_tracker = TokenCostTracker()
    spawner = RLMQuerySpawner(max_depth=3, cost_tracker=cost_tracker)

    # Spawn isolated child loop
    result = spawner.spawn(
        sub_context="Child prompt content",
        sub_goal="Find target needle in child context",
        current_depth=1,
    )
    assert "Sub-goal resolved at depth 1" in str(result)


def test_rlm_query_spawner_max_depth_guardrail():
    spawner = RLMQuerySpawner(max_depth=3)

    with pytest.raises(RecursionError, match="Maximum recursive depth exceeded"):
        spawner.spawn(
            sub_context="Deep prompt",
            sub_goal="Deep recursion",
            current_depth=4,
        )
