"""
Persistent Python REPL execution sandbox with variable buffering and AST pre-flight checks.
"""

import contextlib
import io
import traceback
from typing import Any, Callable, Dict, Optional

from recursive_lm.core.ast_guard import ASTGuardResult, ASTSafetyGuard
from recursive_lm.core.state import RLMState
from recursive_lm.core.truncation import StdoutTruncator, TruncationFeedback


class PersistentREPL:
    """
    State-preserving Python REPL sandbox ($E$).
    Maintains persistent execution namespace across iterations.
    """

    def __init__(
        self,
        state: Optional[RLMState] = None,
        truncator: Optional[StdoutTruncator] = None,
        ast_guard: Optional[ASTSafetyGuard] = None,
        timeout_seconds: float = 5.0,
    ):
        self.state = state if state is not None else RLMState(context="")
        self.truncator = truncator or StdoutTruncator()
        self.ast_guard = ast_guard or ASTSafetyGuard()
        self.timeout_seconds = timeout_seconds

        self.globals_dict: Dict[str, Any] = {}
        self.locals_dict: Dict[str, Any] = {}
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._initialize_environment()

    def _initialize_environment(self) -> None:
        """Sets up default builtins and handles in the REPL namespace."""
        import builtins

        # Safe base globals
        self.globals_dict = {
            "__builtins__": builtins,
            "context": self.state.context,
            "answers": self.state.answers,
            "state": self.state,
        }
        self.locals_dict = self.state.variables

    def register_tool(self, name: str, tool_callable: Callable[..., Any]) -> None:
        """Binds a callable tool (e.g. llm_query, rlm_query, FINAL) into REPL globals."""
        self._tools[name] = tool_callable
        self.globals_dict[name] = tool_callable

    def update_context(self, new_context: str) -> None:
        """Updates the symbolic context handle."""
        self.state.context = new_context
        self.globals_dict["context"] = new_context

    def execute(self, code_str: str) -> TruncationFeedback:
        """
        Executes a Python code block within the persistent namespace.
        Performs pre-execution AST validation and constant-size stdout truncation.
        """
        # 1. Pre-execution AST Safety Guard
        ast_result: ASTGuardResult = self.ast_guard.validate_code(code_str)
        if not ast_result.is_safe:
            error_msg = f"[AST Security Block] {'; '.join(ast_result.errors + ast_result.prohibited_nodes)}"
            self.state.record_error(error_msg)
            return self.truncator.truncate(f"Error: {error_msg}\n", exit_code=1)

        # 2. Sync state references into namespace
        self.globals_dict["context"] = self.state.context
        self.globals_dict["answers"] = self.state.answers
        self.globals_dict["state"] = self.state

        # Re-inject tools
        for tool_name, tool_fn in self._tools.items():
            self.globals_dict[tool_name] = tool_fn

        # 3. Capture stdout & stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        exit_code = 0

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # Try eval first for simple expressions, fallback to exec
                try:
                    compiled_eval = compile(code_str, "<repl>", "eval")
                    res = eval(compiled_eval, self.globals_dict, self.locals_dict)
                    if res is not None:
                        print(repr(res))
                except SyntaxError:
                    compiled_exec = compile(code_str, "<repl>", "exec")
                    exec(compiled_exec, self.globals_dict, self.locals_dict)

            # Sync any variables mutated in locals_dict back to state
            for k, v in self.locals_dict.items():
                if not k.startswith("__"):
                    self.state.set_variable(k, v)

            self.state.clear_error()

        except Exception as e:
            # Check if this exception is a TerminationSignal (from tools/termination.py)
            if e.__class__.__name__ == "TerminationSignal":
                # Termination triggered cleanly
                term_val = getattr(e, "value", str(e))
                self.state.set_termination(term_val)
                raw_out = stdout_capture.getvalue() + stderr_capture.getvalue()
                raw_out += f"\n[TERMINATION] Loop terminated with value: {str(term_val)[:100]}"
                return self.truncator.truncate(raw_out, exit_code=0)

            # Trapped runtime error
            exit_code = 1
            err_tb = traceback.format_exc()
            err_line = f"Runtime Exception: {type(e).__name__}: {str(e)}"
            self.state.record_error(f"{err_line}\n{err_tb}")
            stderr_capture.write(f"\n{err_line}\n")

        # 4. Generate truncated feedback
        raw_output = stdout_capture.getvalue() + stderr_capture.getvalue()
        return self.truncator.truncate(raw_output, exit_code=exit_code)
