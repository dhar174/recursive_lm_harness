"""
Unit tests for OrchestrationDAG and DAGNode graph model.
"""

import pytest
from recursive_lm.orchestrator.dag import DAGNode, NodeStatus, OrchestrationDAG, SubcallType


def test_dag_node_creation_and_serialization():
    node = DAGNode(
        id="node_1",
        objective="Extract keywords",
        dependencies=[],
        subcall_type=SubcallType.LLM_QUERY,
        slice_expression="context[0:100]",
        output_buffer="answers['node_1']",
    )
    data = node.to_dict()
    assert data["id"] == "node_1"
    assert data["subcall_type"] == "llm_query"

    deserialized = DAGNode.from_dict(data)
    assert deserialized.id == "node_1"
    assert deserialized.subcall_type == SubcallType.LLM_QUERY


def test_dag_topological_sort():
    dag = OrchestrationDAG()
    n1 = DAGNode(id="n1", objective="Root task 1", dependencies=[])
    n2 = DAGNode(id="n2", objective="Root task 2", dependencies=[])
    n3 = DAGNode(id="n3", objective="Join task", dependencies=["n1", "n2"])
    n4 = DAGNode(id="n4", objective="Final sink", dependencies=["n3"])

    dag.add_node(n1)
    dag.add_node(n2)
    dag.add_node(n3)
    dag.add_node(n4)

    order = dag.get_topological_order()
    assert order.index("n1") < order.index("n3")
    assert order.index("n2") < order.index("n3")
    assert order.index("n3") < order.index("n4")


def test_dag_cycle_detection():
    dag = OrchestrationDAG()
    n1 = DAGNode(id="n1", objective="Task 1", dependencies=["n2"])
    n2 = DAGNode(id="n2", objective="Task 2", dependencies=["n1"])

    dag.add_node(n1)
    dag.add_node(n2)

    with pytest.raises(ValueError, match="Cycle detected"):
        dag.validate_acyclic()


def test_dag_execution_layers():
    dag = OrchestrationDAG()
    n1 = DAGNode(id="n1", objective="Layer 0 A", dependencies=[])
    n2 = DAGNode(id="n2", objective="Layer 0 B", dependencies=[])
    n3 = DAGNode(id="n3", objective="Layer 1 A", dependencies=["n1"])
    n4 = DAGNode(id="n4", objective="Layer 2 A", dependencies=["n3", "n2"])

    dag.add_node(n1)
    dag.add_node(n2)
    dag.add_node(n3)
    dag.add_node(n4)

    layers = dag.get_execution_layers()
    assert len(layers) == 3

    layer0_ids = {n.id for n in layers[0]}
    layer1_ids = {n.id for n in layers[1]}
    layer2_ids = {n.id for n in layers[2]}

    assert layer0_ids == {"n1", "n2"}
    assert layer1_ids == {"n3"}
    assert layer2_ids == {"n4"}


def test_dag_ready_nodes():
    dag = OrchestrationDAG()
    n1 = DAGNode(id="n1", objective="Root", dependencies=[])
    n2 = DAGNode(id="n2", objective="Child", dependencies=["n1"])

    dag.add_node(n1)
    dag.add_node(n2)

    ready_init = dag.get_ready_nodes(set())
    assert [n.id for n in ready_init] == ["n1"]

    ready_after_n1 = dag.get_ready_nodes({"n1"})
    assert [n.id for n in ready_after_n1] == ["n2"]
