---
name: rlm-repl-sandbox-engineering
description: Guide and architectural patterns for implementing persistent Python REPL sandboxes with stdout truncation, variable buffering, and AST security.
---

# RLM REPL Sandbox Engineering

This skill provides implementation patterns for building the persistent Python REPL environment ($\mathcal{E}$) that powers Recursive Language Models.

## Core Architectural Components

1. **State Persistence**: Using `code.InteractiveConsole` or custom execution namespaces to retain variables across turns.
2. **Constant-Size Stdout Interception**: Intercepting `sys.stdout` and truncating to metadata tuples $\\langle\\text{char\\_count}, \\text{lines}, \\text{head}, \\text{tail}, \\text{exit}\\rangle$.
3. **Primitive Tool Bindings**: Injecting `llm_query`, `rlm_query`, `FINAL`, and `FINAL_VAR` into execution globals.
4. **AST Pre-Execution Validation**: Validating Python AST prior to `exec()` to prevent syntax crashes and deadlock.
