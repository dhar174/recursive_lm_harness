"""
Unit tests for DAGScheduler and layer-by-layer resolution.
"""

import pytest
from recursive_lm.core.repl import PersistentREPL
from recursive_lm.core.state import RLMState
from recursive_lm.orchestrator.dag import DAGNode, OrchestrationDAG, SubcallType
from recursive_lm.orchestrator.memoization import MemoizationTable
from recursive_lm.orchestrator.scheduler import DAGScheduler
from recursive_lm.tools.llm_query import LLMQueryRuntime
from recursive_lm.tools.rlm_query import RLMQuerySpawner
from recursive_lm.tools.termination import create_termination_tools


def test_scheduler_sequential_execution():
    state = RLMState(context="Alpha: 10, Beta: 20")
    repl = PersistentREPL(state=state)
    final_fn, final_var_fn = create_termination_tools(state)
    repl.register_tool("FINAL", final_fn)
    repl.register_tool("FINAL_VAR", final_var_fn)

    dag = OrchestrationDAG()
    n1 = DAGNode(
        id="n1",
        objective="Set base values",
        dependencies=[],
        subcall_type=SubcallType.REPL_CODE,
        code_snippet="a = 10\nb = 20\nres1 = a + b",
        output_buffer="res1",
    )
    n2 = DAGNode(
        id="n2",
        objective="Multiply sum",
        dependencies=["n1"],
        subcall_type=SubcallType.REPL_CODE,
        code_snippet="res2 = answers['n1'] * 2",
        output_buffer="res2",
    )
    n3 = DAGNode(
        id="n3",
        objective="Final termination",
        dependencies=["n2"],
        subcall_type=SubcallType.FINAL_VAR,
        output_buffer="res2",
    )

    dag.add_node(n1)
    dag.add_node(n2)
    dag.add_node(n3)

    scheduler = DAGScheduler(dag=dag, repl=repl)
    final_result = scheduler.run()

    assert final_result == 60
    assert state.is_terminated is True
    assert state.termination_value == 60


def test_scheduler_with_llm_and_rlm_subcalls():
    state = RLMState(context="Target: 999")
    repl = PersistentREPL(state=state)
    llm_runtime = LLMQueryRuntime(client=lambda prompt, model, **kw: f"Extracted from: {prompt[:10]}")
    rlm_spawner = RLMQuerySpawner(max_depth=3)

    repl.register_tool("llm_query", llm_runtime.query)
    repl.register_tool("rlm_query", rlm_spawner.spawn)

    dag = OrchestrationDAG()
    n_llm = DAGNode(
        id="n_llm",
        objective="Extract target",
        dependencies=[],
        subcall_type=SubcallType.LLM_QUERY,
        slice_expression="context",
    )
    n_rlm = DAGNode(
        id="n_rlm",
        objective="Deep sub-reasoning",
        dependencies=["n_llm"],
        subcall_type=SubcallType.RLM_QUERY,
        slice_expression="Target context",
    )
    n_final = DAGNode(
        id="n_final",
        objective="Final termination",
        dependencies=["n_rlm"],
        subcall_type=SubcallType.FINAL,
        output_buffer="Direct final string",
    )

    dag.add_node(n_llm)
    dag.add_node(n_rlm)
    dag.add_node(n_final)

    scheduler = DAGScheduler(dag=dag, repl=repl)
    result = scheduler.run()

    assert result == "Direct final string"
    assert state.is_terminated is True


def test_scheduler_fan_out_limit():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)
    dag = OrchestrationDAG()

    # Create 5 nodes in layer 0 with max_fan_out=3
    for i in range(5):
        dag.add_node(DAGNode(id=f"n_{i}", objective="Fan-out node", dependencies=[]))

    scheduler = DAGScheduler(dag=dag, repl=repl, max_fan_out=3)
    with pytest.raises(ValueError, match="Fan-out budget exceeded"):
        scheduler.run()


def test_scheduler_verification_gate():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)
    dag = OrchestrationDAG()

    n1 = DAGNode(
        id="n1",
        objective="Compute target",
        dependencies=[],
        subcall_type=SubcallType.REPL_CODE,
        code_snippet="out = 'valid_string'",
        output_buffer="out",
        second_opinion_required=True,
    )
    dag.add_node(n1)

    verifier_called = []

    def custom_verifier(node: DAGNode, result: str) -> bool:
        verifier_called.append(node.id)
        return "valid" in result

    scheduler = DAGScheduler(dag=dag, repl=repl, verifier_fn=custom_verifier)
    scheduler.run()

    assert "n1" in verifier_called
    assert dag.nodes["n1"].is_verified is True


def test_scheduler_node_failure_raises():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)
    dag = OrchestrationDAG()

    n_fail = DAGNode(
        id="n_fail",
        objective="Fail task",
        dependencies=[],
        subcall_type=SubcallType.REPL_CODE,
        code_snippet="raise RuntimeError('Intentional node error')",
    )
    dag.add_node(n_fail)

    scheduler = DAGScheduler(dag=dag, repl=repl)
    # The REPL traps exception into last_error and returns exit_code=1 feedback
    scheduler.run()
    assert state.last_error is not None


def test_scheduler_empty_dag():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)
    dag = OrchestrationDAG()

    scheduler = DAGScheduler(dag=dag, repl=repl)
    result = scheduler.run()
    assert result is None
