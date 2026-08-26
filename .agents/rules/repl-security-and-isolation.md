# REPL Security, Memory Limits & Execution Isolation

This document defines safety constraints and isolation boundaries for the Python REPL sandbox ($\mathcal{E}$).

## 1. Namespace & Variable Isolation
- Prompts ($P$) are stored under the symbolic variable `context`.
- Intermediate results accumulate in `answers = {}`.
- Termination values are bound to `FINAL_VAR`.
- Execution exceptions are trapped into `state["last_error"]`.
- Prohibit direct access to unsafe builtins (`eval`, `exec` on unvalidated strings, `__import__` outside approved modules).

## 2. Resource Caps & Timeouts
- **Execution Step Timeout**: Maximum 5.0 seconds per Python execution block.
- **Memory Limit**: Maximum 512MB heap allocation per REPL sandbox instance.
- **Iteration Cap**: Maximum 1000 iterations for any internal REPL loop.

## 3. Pre-Execution AST Gate
- Every emitted code block must pass `ast.parse()` and AST safety inspection by `ast-safety-guard` or runtime AST visitor before execution.
