"""
Unit tests for PersistentREPL execution sandbox.
"""

from recursive_lm.core.repl import PersistentREPL
from recursive_lm.core.state import RLMState
from recursive_lm.tools.termination import create_termination_tools


def test_repl_variable_persistence():
    state = RLMState(context="Line A\nLine B\nLine C")
    repl = PersistentREPL(state=state)

    res1 = repl.execute("x = 100")
    assert res1.exit_code == 0
    assert state.get_variable("x") == 100

    res2 = repl.execute("y = x * 2")
    assert res2.exit_code == 0
    assert state.get_variable("y") == 200


def test_repl_context_access_and_slicing():
    state = RLMState(context="ABCDEFGHIJ")
    repl = PersistentREPL(state=state)

    res = repl.execute("sliced = context[2:5]")
    assert res.exit_code == 0
    assert state.get_variable("sliced") == "CDE"


def test_repl_stdout_capture():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)

    feedback = repl.execute("print('Hello from REPL')")
    assert feedback.exit_code == 0
    assert "Hello from REPL" in feedback.formatted_output


def test_repl_ast_guard_rejection():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)

    feedback = repl.execute("import os\nos.system('echo dangerous')")
    assert feedback.exit_code == 1
    assert "AST Security Block" in feedback.formatted_output
    assert state.last_error is not None


def test_repl_runtime_exception_recovery():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)

    feedback = repl.execute("undefined_variable + 1")
    assert feedback.exit_code == 1
    assert state.last_error is not None
    assert "NameError" in state.last_error

    # Ensure REPL is still operational after exception
    recovered = repl.execute("recovered_val = 42")
    assert recovered.exit_code == 0
    assert state.get_variable("recovered_val") == 42
    assert state.last_error is None


def test_repl_termination_tools():
    state = RLMState(context="")
    repl = PersistentREPL(state=state)
    final_fn, final_var_fn = create_termination_tools(state)

    repl.register_tool("FINAL", final_fn)
    repl.register_tool("FINAL_VAR", final_var_fn)

    # Test FINAL_VAR
    repl.execute("final_buf = 'Complete Result'")
    res = repl.execute("FINAL_VAR('final_buf')")

    assert res.exit_code == 0
    assert state.is_terminated is True
    assert state.termination_value == "Complete Result"
