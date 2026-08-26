"""
Symbolic prompt handles, memoization, and variable state management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class NodeOutput:
    """Represents the output and provenance metadata of a DAG node."""
    node_id: str
    value: Any
    provenance: Dict[str, Any] = field(default_factory=dict)
    is_verified: bool = False
    execution_time_ms: float = 0.0


@dataclass
class RLMState:
    """
    Persistent state container for Recursive Language Models.
    Externalizes prompts ($P$) as symbolic variable `context`.
    """
    context: str
    answers: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    last_error: Optional[str] = None
    is_terminated: bool = False
    termination_value: Optional[Any] = None

    def set_variable(self, name: str, value: Any) -> None:
        """Stores a named variable in the REPL persistence layer."""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Retrieves a named variable or defaults if absent."""
        return self.variables.get(name, default)

    def has_variable(self, name: str) -> bool:
        """Checks if a named variable exists in state."""
        return name in self.variables

    def record_error(self, error_msg: str) -> None:
        """Traps runtime or AST errors without crashing the REPL."""
        self.last_error = error_msg

    def clear_error(self) -> None:
        """Clears the last recorded error."""
        self.last_error = None

    def set_termination(self, value: Any) -> None:
        """Sets the terminal answer and marks state as terminated."""
        self.termination_value = value
        self.is_terminated = True

    def get_metadata(self) -> Dict[str, Any]:
        """Returns constant-size metadata descriptor of the prompt context."""
        return {
            "char_count": len(self.context),
            "line_count": len(self.context.splitlines()) if self.context else 0,
            "variable_keys": list(self.variables.keys()),
            "answers_keys": list(self.answers.keys()),
            "is_terminated": self.is_terminated,
            "has_error": self.last_error is not None,
        }

    def export_state(self) -> Dict[str, Any]:
        """Serializes current execution state for logging or telemetry."""
        return {
            "metadata": self.get_metadata(),
            "answers": {k: str(v)[:200] for k, v in self.answers.items()},
            "variables": {k: str(v)[:200] for k, v in self.variables.items()},
            "last_error": self.last_error,
            "is_terminated": self.is_terminated,
            "termination_value": str(self.termination_value)[:500] if self.termination_value is not None else None,
        }
