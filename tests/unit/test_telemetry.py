"""
Unit tests for telemetry modules: TokenCostTracker and ExecutionTracer.
"""

from recursive_lm.telemetry.cost_tracker import TokenCostTracker
from recursive_lm.telemetry.tracer import ExecutionTracer


def test_cost_tracker_usage_and_depth_distribution():
    tracker = TokenCostTracker()

    tracker.record_usage(depth=0, prompt_tokens=1000, completion_tokens=200, model_name="gpt-5")
    tracker.record_usage(depth=1, prompt_tokens=4000, completion_tokens=800, model_name="gpt-5")

    assert tracker.total_tokens == 6000
    assert tracker.total_cost_usd > 0.0

    summary = tracker.get_summary()
    assert summary["total_tokens_consumed"] == 6000
    assert summary["max_depth_reached"] == 1
    assert summary["depth_distribution"]["d0"] == 1200
    assert summary["depth_distribution"]["d1"] == 4800
    assert summary["total_subcalls"] == 2


def test_cost_tracker_budget_limit():
    tracker = TokenCostTracker()
    tracker.record_usage(depth=0, prompt_tokens=5000, completion_tokens=5000)

    assert tracker.check_budget_limit(depth=0, max_budget_tokens=15000) is True
    assert tracker.check_budget_limit(depth=0, max_budget_tokens=5000) is False


def test_cost_tracker_efficiency_ratio():
    tracker = TokenCostTracker()
    # 10k tokens consumed in RLM
    tracker.record_usage(depth=0, prompt_tokens=8000, completion_tokens=2000, model_name="gpt-5")

    # Baseline brute-force transformer requires 1M tokens
    efficiency = tracker.compute_efficiency_vs_baseline(vanilla_tokens=1_000_000, model_name="gpt-5")
    assert 0.0 < efficiency < 1.0


def test_execution_tracer():
    tracer = ExecutionTracer()

    ev1 = tracer.log_event(event_type="NODE_START", node_id="node_1", depth=0)
    ev2 = tracer.log_event(event_type="NODE_END", node_id="node_1", depth=0, duration_ms=25.0)

    assert len(tracer.events) == 2
    assert ev1.event_type == "NODE_START"
    assert ev2.event_type == "NODE_END"

    ascii_tree = tracer.render_ascii_tree()
    assert "[RLM Execution Trace]" in ascii_tree
    assert "[node_1] NODE_START" in ascii_tree

    jsonl = tracer.export_jsonl()
    assert '"node_id": "node_1"' in jsonl
    assert len(jsonl.splitlines()) == 2

    tracer.clear()
    assert len(tracer.events) == 0
