"""
Unit tests for MemoizationTable.
"""

from recursive_lm.orchestrator.memoization import MemoizationTable


def test_memoization_store_and_get():
    table = MemoizationTable()
    entry = table.store(
        node_id="node_summary",
        value="Document summary here",
        provenance={"model": "gpt-5"},
        is_verified=False,
        execution_time_ms=45.0,
    )
    assert entry.node_id == "node_summary"
    assert table.contains("node_summary") is True
    assert table.get("node_summary") == "Document summary here"
    assert table.get("missing_node", default="fallback") == "fallback"


def test_memoization_verification():
    table = MemoizationTable()
    table.store(node_id="node_calc", value=42, is_verified=False)

    assert table.get_entry("node_calc").is_verified is False

    # Mark verified manually
    table.mark_verified("node_calc", True)
    assert table.get_entry("node_calc").is_verified is True

    # Verification function
    table.store(node_id="node_text", value="alpha beta", is_verified=False)
    passed = table.verify_entry("node_text", lambda val: "alpha" in val)
    assert passed is True
    assert table.get_entry("node_text").is_verified is True


def test_memoization_as_dict():
    table = MemoizationTable()
    table.store("n1", "val1")
    table.store("n2", "val2")

    exported = table.as_dict()
    assert exported == {"n1": "val1", "n2": "val2"}
