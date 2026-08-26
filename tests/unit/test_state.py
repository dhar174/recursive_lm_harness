"""
Unit tests for RLMState and NodeOutput data models.
"""

from recursive_lm.core.state import NodeOutput, RLMState


def test_state_initialization():
    state = RLMState(context="Initial prompt text")
    assert state.context == "Initial prompt text"
    assert state.answers == {}
    assert state.variables == {}
    assert state.last_error is None
    assert state.is_terminated is False
    assert state.termination_value is None


def test_variable_buffering():
    state = RLMState(context="sample")
    state.set_variable("counter", 10)
    state.set_variable("summary", "Processed 10 items")

    assert state.has_variable("counter") is True
    assert state.has_variable("missing") is False
    assert state.get_variable("counter") == 10
    assert state.get_variable("missing", default="default_val") == "default_val"


def test_error_recording_and_clearing():
    state = RLMState(context="")
    assert state.last_error is None

    state.record_error("Syntax error at line 1")
    assert state.last_error == "Syntax error at line 1"

    state.clear_error()
    assert state.last_error is None


def test_termination_state():
    state = RLMState(context="sample")
    assert state.is_terminated is False

    state.set_termination({"answer": 42, "confidence": 0.99})
    assert state.is_terminated is True
    assert state.termination_value == {"answer": 42, "confidence": 0.99}


def test_metadata_and_export():
    state = RLMState(context="Line 1\nLine 2\nLine 3")
    state.set_variable("var1", "val1")
    state.answers["node_1"] = "res_1"

    meta = state.get_metadata()
    assert meta["char_count"] == len(state.context)
    assert meta["line_count"] == 3
    assert "var1" in meta["variable_keys"]
    assert "node_1" in meta["answers_keys"]
    assert meta["is_terminated"] is False

    exported = state.export_state()
    assert "metadata" in exported
    assert "answers" in exported
    assert "variables" in exported


def test_node_output_dataclass():
    node = NodeOutput(
        node_id="node_extract",
        value={"records": [1, 2, 3]},
        provenance={"subcall": "llm_query"},
        is_verified=True,
        execution_time_ms=12.5,
    )
    assert node.node_id == "node_extract"
    assert node.value == {"records": [1, 2, 3]}
    assert node.is_verified is True
    assert node.execution_time_ms == 12.5
