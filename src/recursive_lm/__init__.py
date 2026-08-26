"""
Recursive Language Model (RLM) Harness
Extends LLM semantic horizons through symbolic REPL handles, layer-by-layer DAG decomposition, and programmatic recursion.
"""

from recursive_lm.core.ast_guard import ASTGuardResult, ASTSafetyGuard
from recursive_lm.core.repl import PersistentREPL
from recursive_lm.core.state import NodeOutput, RLMState
from recursive_lm.core.truncation import StdoutTruncator, TruncationFeedback
from recursive_lm.orchestrator.dag import DAGNode, NodeStatus, OrchestrationDAG, SubcallType
from recursive_lm.orchestrator.memoization import MemoizationTable
from recursive_lm.orchestrator.scheduler import DAGScheduler
from recursive_lm.telemetry.cost_tracker import DepthUsage, TokenCostTracker
from recursive_lm.telemetry.tracer import ExecutionTracer, TraceEvent
from recursive_lm.tools.llm_query import LLMQueryRuntime
from recursive_lm.tools.rlm_query import RLMQuerySpawner
from recursive_lm.tools.termination import TerminationSignal, create_termination_tools

__version__ = "0.1.0"

__all__ = [
    "ASTGuardResult",
    "ASTSafetyGuard",
    "DAGNode",
    "DAGScheduler",
    "DepthUsage",
    "ExecutionTracer",
    "LLMQueryRuntime",
    "MemoizationTable",
    "NodeOutput",
    "NodeStatus",
    "OrchestrationDAG",
    "PersistentREPL",
    "RLMQuerySpawner",
    "RLMState",
    "StdoutTruncator",
    "SubcallType",
    "TerminationSignal",
    "TokenCostTracker",
    "TraceEvent",
    "TruncationFeedback",
    "create_termination_tools",
]
