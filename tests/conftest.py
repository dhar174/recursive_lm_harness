"""
Pytest configuration and shared fixtures for recursive_lm test suites.
"""

import pytest
from recursive_lm.core.ast_guard import ASTSafetyGuard
from recursive_lm.core.repl import PersistentREPL
from recursive_lm.core.state import RLMState
from recursive_lm.core.truncation import StdoutTruncator
from recursive_lm.orchestrator.memoization import MemoizationTable
from recursive_lm.telemetry.cost_tracker import TokenCostTracker
from recursive_lm.telemetry.tracer import ExecutionTracer


@pytest.fixture
def sample_context() -> str:
    return "Alpha: 100\nBeta: 200\nGamma: 300\nTarget Needle: 4242"


@pytest.fixture
def empty_state() -> RLMState:
    return RLMState(context="")


@pytest.fixture
def populated_state(sample_context: str) -> RLMState:
    return RLMState(context=sample_context)


@pytest.fixture
def stdout_truncator() -> StdoutTruncator:
    return StdoutTruncator(head_limit=50, tail_limit=50, max_untruncated_chars=120)


@pytest.fixture
def ast_guard() -> ASTSafetyGuard:
    return ASTSafetyGuard()


@pytest.fixture
def repl_instance(populated_state: RLMState, stdout_truncator: StdoutTruncator, ast_guard: ASTSafetyGuard) -> PersistentREPL:
    return PersistentREPL(
        state=populated_state,
        truncator=stdout_truncator,
        ast_guard=ast_guard,
    )


@pytest.fixture
def memo_table() -> MemoizationTable:
    return MemoizationTable()


@pytest.fixture
def cost_tracker() -> TokenCostTracker:
    return TokenCostTracker()


@pytest.fixture
def tracer() -> ExecutionTracer:
    return ExecutionTracer()
