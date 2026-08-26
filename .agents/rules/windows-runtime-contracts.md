# Windows Runtime & Shell Reliability Contracts

This document defines execution standards and compatibility rules for Windows environments within `recursive_lm_harness`.

## 1. PowerShell & Shell Invocation
- All terminal operations run in PowerShell (`pwsh`).
- Never assume POSIX shell syntax (e.g. avoid naked `&&` or bash builtins without PowerShell equivalents).
- Use `python` instead of `python3` for Python script executions.

## 2. Character Encoding & Path Normalization
- Enforce **UTF-8** encoding across all stdio, file reading, and test execution commands (`PYTHONIOENCODING=utf-8`).
- Normalize file paths using forward slashes (`/`) or `pathlib.Path.resolve()` to avoid backslash escaping issues in regex and JSON.

## 3. Process Lifetime & Timeout Management
- Subprocess executions must enforce explicit timeouts ($T \le 30.0\text{s}$) to prevent orphaned background processes.
- For long-running benchmark sweeps, use Antigravity background task execution with progress logging.
