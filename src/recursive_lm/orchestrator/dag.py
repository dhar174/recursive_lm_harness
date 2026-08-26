"""
Layer-by-layer DAG model, dependency graph validation, and topological sorting.
"""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class NodeStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class SubcallType(str, Enum):
    LLM_QUERY = "llm_query"
    RLM_QUERY = "rlm_query"
    REPL_CODE = "repl_code"
    FINAL_VAR = "FINAL_VAR"
    FINAL = "FINAL"


@dataclass
class DAGNode:
    """Represents a discrete semantic task node in the Orchestration DAG."""
    id: str
    objective: str
    dependencies: List[str] = field(default_factory=list)
    subcall_type: SubcallType = SubcallType.REPL_CODE
    code_snippet: Optional[str] = None
    slice_expression: Optional[str] = None
    output_buffer: str = ""
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    is_verified: bool = False
    second_opinion_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "objective": self.objective,
            "dependencies": self.dependencies,
            "subcall_type": self.subcall_type.value,
            "code_snippet": self.code_snippet,
            "slice_expression": self.slice_expression,
            "output_buffer": self.output_buffer,
            "status": self.status.value,
            "is_verified": self.is_verified,
            "second_opinion_required": self.second_opinion_required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAGNode":
        subcall = SubcallType(data.get("subcall_type", "repl_code"))
        status = NodeStatus(data.get("status", "PENDING"))
        return cls(
            id=data["id"],
            objective=data.get("objective", ""),
            dependencies=data.get("dependencies", []),
            subcall_type=subcall,
            code_snippet=data.get("code_snippet"),
            slice_expression=data.get("slice_expression"),
            output_buffer=data.get("output_buffer", ""),
            status=status,
            is_verified=data.get("is_verified", False),
            second_opinion_required=data.get("second_opinion_required", False),
        )


class OrchestrationDAG:
    """
    Manages dependency relationships between reasoning sub-tasks.
    Enforces acyclic structure and computes topological execution layers.
    """

    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.adjacency: Dict[str, Set[str]] = {}       # parent -> children
        self.reverse_adjacency: Dict[str, Set[str]] = {} # child -> parents

    def add_node(self, node: DAGNode) -> None:
        """Adds a node to the DAG and sets up dependency edges."""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = set()
        if node.id not in self.reverse_adjacency:
            self.reverse_adjacency[node.id] = set()

        for dep in node.dependencies:
            if dep not in self.adjacency:
                self.adjacency[dep] = set()
            self.adjacency[dep].add(node.id)
            self.reverse_adjacency[node.id].add(dep)

    def validate_acyclic(self) -> bool:
        """
        Validates that the graph is a Directed Acyclic Graph.
        Raises ValueError if a cycle is detected.
        """
        in_degree = {nid: len(self.reverse_adjacency.get(nid, set())) for nid in self.nodes}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for child in self.adjacency.get(curr, set()):
                if child in in_degree:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)

        if visited_count != len(self.nodes):
            raise ValueError(f"Cycle detected in OrchestrationDAG: {visited_count}/{len(self.nodes)} nodes visited")
        return True

    def get_topological_order(self) -> List[str]:
        """Returns node IDs sorted in topological dependency order."""
        self.validate_acyclic()
        in_degree = {nid: len(self.reverse_adjacency.get(nid, set())) for nid in self.nodes}
        queue = deque(sorted([nid for nid, deg in in_degree.items() if deg == 0]))
        order: List[str] = []

        while queue:
            curr = queue.popleft()
            order.append(curr)
            for child in sorted(self.adjacency.get(curr, set())):
                if child in in_degree:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
        return order

    def get_execution_layers(self) -> List[List[DAGNode]]:
        """
        Partitions the DAG into parallelizable layers.
        Layer 0 nodes have 0 dependencies; Layer k nodes depend only on Layers < k.
        """
        self.validate_acyclic()
        layer_map: Dict[str, int] = {}
        for nid in self.get_topological_order():
            parents = self.reverse_adjacency.get(nid, set())
            if not parents:
                layer_map[nid] = 0
            else:
                layer_map[nid] = max(layer_map[p] for p in parents if p in layer_map) + 1

        max_layer = max(layer_map.values(), default=-1)
        layers: List[List[DAGNode]] = [[] for _ in range(max_layer + 1)]
        for nid, layer_idx in layer_map.items():
            layers[layer_idx].append(self.nodes[nid])

        return layers

    def get_ready_nodes(self, completed_node_ids: Set[str]) -> List[DAGNode]:
        """Returns all nodes whose dependencies are completely satisfied."""
        ready: List[DAGNode] = []
        for nid, node in self.nodes.items():
            if nid in completed_node_ids:
                continue
            parents = self.reverse_adjacency.get(nid, set())
            if parents.issubset(completed_node_ids):
                ready.append(node)
        return ready

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dag_version": "1.0",
            "nodes": [node.to_dict() for node in self.nodes.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrchestrationDAG":
        dag = cls()
        for node_data in data.get("nodes", []):
            node = DAGNode.from_dict(node_data)
            dag.add_node(node)
        return dag
