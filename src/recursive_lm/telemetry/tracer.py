"""
Execution tree tracer and structured telemetry visualization.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TraceEvent:
    """Represents a discrete execution event in the RLM harness."""
    event_id: str
    node_id: Optional[str]
    depth: int
    event_type: str  # "NODE_START", "NODE_END", "NODE_ERROR", "CODE_EXEC", "LLM_QUERY", "TERMINATION"
    timestamp_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionTracer:
    """
    Captures step-by-step telemetry events for DAG nodes, tool calls, and REPL operations.
    """

    def __init__(self):
        self.events: List[TraceEvent] = []

    def log_event(
        self,
        event_type: str,
        node_id: Optional[str] = None,
        depth: int = 0,
        **metadata: Any,
    ) -> TraceEvent:
        """Appends a timestamped trace event."""
        event = TraceEvent(
            event_id=str(uuid.uuid4())[:8],
            node_id=node_id,
            depth=depth,
            event_type=event_type,
            timestamp_ms=time.time() * 1000.0,
            metadata=metadata,
        )
        self.events.append(event)
        return event

    def render_ascii_tree(self) -> str:
        """Generates an ASCII visualization of execution events by depth."""
        lines = ["[RLM Execution Trace]"]
        for ev in self.events:
            indent = "  " * (ev.depth + 1)
            node_str = f"[{ev.node_id}] " if ev.node_id else ""
            meta_str = f" | {ev.metadata}" if ev.metadata else ""
            lines.append(f"{indent}└── {node_str}{ev.event_type}{meta_str}")
        return "\n".join(lines)

    def export_jsonl(self) -> str:
        """Exports all events formatted as newline-delimited JSON."""
        return "\n".join(json.dumps(asdict(ev)) for ev in self.events)

    def to_dict(self) -> Dict[str, Any]:
        """Returns structured dictionary representation of all events."""
        return {
            "total_events": len(self.events),
            "events": [asdict(ev) for ev in self.events],
        }

    def clear(self) -> None:
        """Clears all logged events."""
        self.events.clear()
