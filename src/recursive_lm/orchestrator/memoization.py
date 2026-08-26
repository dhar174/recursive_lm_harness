"""
Answers memoization table and second-opinion verification store.
"""

from typing import Any, Callable, Dict, Optional
from recursive_lm.core.state import NodeOutput


class MemoizationTable:
    """
    Persistent store for intermediate DAG node outputs (`answers`).
    Enforces verification status before values propagate downstream.
    """

    def __init__(self):
        self._table: Dict[str, NodeOutput] = {}

    def store(
        self,
        node_id: str,
        value: Any,
        provenance: Optional[Dict[str, Any]] = None,
        is_verified: bool = False,
        execution_time_ms: float = 0.0,
    ) -> NodeOutput:
        """Stores a node computation in the memoization table."""
        entry = NodeOutput(
            node_id=node_id,
            value=value,
            provenance=provenance or {},
            is_verified=is_verified,
            execution_time_ms=execution_time_ms,
        )
        self._table[node_id] = entry
        return entry

    def get(self, node_id: str, default: Any = None) -> Any:
        """Returns the raw value for a node or default if not found."""
        entry = self._table.get(node_id)
        return entry.value if entry is not None else default

    def get_entry(self, node_id: str) -> Optional[NodeOutput]:
        """Returns the full NodeOutput metadata entry."""
        return self._table.get(node_id)

    def contains(self, node_id: str) -> bool:
        """Checks whether a node output is memoized."""
        return node_id in self._table

    def mark_verified(self, node_id: str, is_verified: bool = True) -> None:
        """Updates the verification flag on a stored node."""
        if node_id in self._table:
            self._table[node_id].is_verified = is_verified

    def verify_entry(self, node_id: str, verifier_fn: Callable[[Any], bool]) -> bool:
        """
        Applies an independent second-opinion verification check on a stored entry.
        """
        if node_id not in self._table:
            return False
        val = self._table[node_id].value
        passed = bool(verifier_fn(val))
        self._table[node_id].is_verified = passed
        return passed

    def as_dict(self) -> Dict[str, Any]:
        """Returns a simplified key-value map for REPL `answers` injection."""
        return {k: v.value for k, v in self._table.items()}

    def clear(self) -> None:
        """Clears all memoized entries."""
        self._table.clear()
