#!/usr/bin/env python3
"""
Create parent and child GitHub issues for Step 5: Lifecycle Hooks & Automated Runtime Guards.
"""

import json
import subprocess
import sys

REPO = "dhar174/recursive_lm_harness"

SUBISSUES = [
    {
        "title": "[Hook] PreToolUse AST Pre-Flight Safety Interceptor (scripts/hooks/pre_tool_ast_guard.py)",
        "body": r"""### Overview
Implement the `PreToolUse` hook script (`scripts/hooks/pre_tool_ast_guard.py`) to intercept and statically validate all Python code blocks emitted for tool execution (`repl_execute` or `python -c "..."`) before they reach execution runtimes.

### Core Objectives & Mechanics
1. **Event Matcher**: Matches tool calls with names `call_mcp_tool` (specifically `repl_execute`) and `run_command`.
2. **AST Static Parsing**: Parses the target Python code payload on `stdin` using Python's standard `ast.parse()`.
3. **Syntax Error Interception**: Automatically blocks malformed Python code (`SyntaxError`) with exact line and column diagnostic offsets before execution.
4. **Prohibited Pattern Auditing**: Flags unauthorized AST nodes (e.g. root filesystem deletions, arbitrary socket servers, obfuscated `__import__` strings).
5. **Loop Termination Verification**: Rejects unbounded `while True:` loops lacking break conditions or iteration counter guards.

### Input / Output Contract
- **Input (`stdin`)**:
  ```json
  {
    "toolCall": {
      "name": "call_mcp_tool",
      "args": {
        "ServerName": "rlm-repl-mcp",
        "ToolName": "repl_execute",
        "Arguments": {"code": "def process():\n  while True:\n    pass"}
      }
    }
  }
  ```
- **Output (`stdout`) on Failure**:
  ```json
  {
    "decision": "deny",
    "reason": "AST Safety Guard: Unbounded loop detected without iteration guard (while True at line 2). Execution blocked."
  }
  ```
- **Output (`stdout`) on Success**:
  ```json
  {
    "decision": "allow"
  }
  ```

### Acceptance Criteria
- [ ] Script executes via `python scripts/hooks/pre_tool_ast_guard.py` and returns in $< 200\text{ms}$.
- [ ] Automatically returns `"decision": "deny"` with descriptive diagnostic reason when passed syntactically invalid Python code.
- [ ] Automatically returns `"decision": "deny"` when detecting infinite loops or unauthorized module access.
- [ ] Returns `"decision": "allow"` for valid RLM REPL scripts (`context` slicing, `llm_query` invocation, `answers` updates).
- [ ] Handles non-Python tool calls gracefully without error (returns `"decision": "allow"`).
"""
    },
    {
        "title": "[Hook] PostToolUse Telemetry & Stdout Auto-Truncation Logger (scripts/hooks/post_tool_telemetry.py)",
        "body": r"""### Overview
Implement the `PostToolUse` hook script (`scripts/hooks/post_tool_telemetry.py`) to enforce constant-size stdout feedback and record execution telemetry to `.rlm_sessions/`.

### Core Objectives & Mechanics
1. **Event Matcher**: Matches all tool execution completions (`matcher: "*"` or `"call_mcp_tool|run_command"`).
2. **Stdout Archiving**: When tool outputs exceed 500 characters, automatically archives the full untruncated output to `.rlm_sessions/tool_output.log` for offline debugging.
3. **Constant-Size Tuple Enforcement**: Guarantees the coordinator context never receives raw token dumps, verifying the feedback format:
   $$\text{Feedback} = \langle \text{char\_count}, \text{line\_count}, \text{head}_{100}, \text{tail}_{100}, \text{exit\_code} \rangle$$
4. **Latency & Step Telemetry**: Logs step latency (wall-clock time), tool name, and exit statuses to `.rlm_sessions/telemetry.jsonl`.

### Input / Output Contract
- **Input (`stdin`)**: Common hook input payload including `stepIdx`, `toolCall`, and `output`.
- **Output (`stdout`)**: Empty JSON object `{}` with zero console pollution.

### Acceptance Criteria
- [ ] Script processes tool outputs in $< 50\text{ms}$.
- [ ] Creates and updates `.rlm_sessions/tool_output.log` and `.rlm_sessions/telemetry.jsonl` upon tool execution.
- [ ] Never blocks or crashes the agent loop on non-critical disk I/O errors.
- [ ] Verifies that execution outputs exceeding 500 chars are cleanly archived.
"""
    },
    {
        "title": "[Hook] PreInvocation Dynamic Context & Memory Injector (scripts/hooks/pre_invocation_memory.py)",
        "body": r"""### Overview
Implement the `PreInvocation` hook script (`scripts/hooks/pre_invocation_memory.py`) to query `mem0ry4ai` and dynamically inject high-priority project status, active todos, and architectural gotchas before every model reasoning turn.

### Core Objectives & Mechanics
1. **Pre-Invocation Trigger**: Fired synchronously before the model is called in each execution turn.
2. **Targeted Memory Retrieval**: Queries `mem0ry4ai` under scope `project:recursive_lm_harness` for active `todo` and `gotcha` items.
3. **Ephemeral Context Injection**: Emits an `ephemeralMessage` inside `injectSteps` containing the active constraints.
4. **Graceful Fallback**: If `mem0ry4ai` is unreachable or offline, exits cleanly with empty `injectSteps: []` without interrupting the model turn.

### Input / Output Contract
- **Output (`stdout`)**:
  ```json
  {
    "injectSteps": [
      {
        "ephemeralMessage": "[mem0ry4ai] Active Project Constraints:\n- REPL stdout must be truncated to constant-size metadata.\n- Reserve >=500 output tokens for FINAL_VAR emission."
      }
    ]
  }
  ```

### Acceptance Criteria
- [ ] Script completes retrieval in $< 500\text{ms}$.
- [ ] Successfully injects active todos/gotchas into `injectSteps` when mem0ry4ai is available.
- [ ] Gracefully falls back to `{"injectSteps": []}` with exit code `0` when mem0ry4ai is offline or uninstalled.
- [ ] Operates cleanly on Windows and POSIX without terminal encoding glitches.
"""
    },
    {
        "title": "[Hook] Stop Quality Gatekeeper & Regression Blocker (scripts/hooks/stop_quality_gate.py)",
        "body": r"""### Overview
Implement the `Stop` lifecycle hook script (`scripts/hooks/stop_quality_gate.py`) to act as an automated gatekeeper, preventing the agent from terminating a session if offline tests fail or documentation consistency errors are present.

### Core Objectives & Mechanics
1. **Stop Event Interception**: Fired when the agent attempts to stop or complete execution.
2. **Automated Unit Test Verification**: Executes fast offline unit tests (`pytest tests/unit -q`).
3. **Archcore Health Audit**: Verifies that `.archcore/` contains zero broken relations or orphaned document references.
4. **Execution Continuation Enforcement**: If tests fail, returns `"decision": "continue"` with the exact failure traceback, forcing the agent to fix regressions before completing.

### Input / Output Contract
- **Output (`stdout`) on Regression Failure**:
  ```json
  {
    "decision": "continue",
    "reason": "Quality Gate Blocked Stop: 2 unit tests failed in tests/unit/test_repl.py. Please fix regressions before concluding."
  }
  ```
- **Output (`stdout`) on Success**:
  ```json
  {
    "decision": "allow"
  }
  ```

### Acceptance Criteria
- [ ] Automatically blocks session termination (`"decision": "continue"`) when `pytest tests/unit` fails.
- [ ] Injects specific test failure summaries into the agent context to guide remediation.
- [ ] Allows session completion (`"decision": "allow"`) when all tests pass and documentation is consistent.
- [ ] Enforces a hard timeout cap of 30 seconds for test execution.
"""
    }
]

def run_gh(cmd_args):
    result = subprocess.run(
        ["gh"] + cmd_args,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        print(f"Error executing gh {' '.join(cmd_args)}:\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout.strip()

def main():
    print("Creating child sub-issues...")
    created_subissues = []
    
    for item in SUBISSUES:
        out = run_gh([
            "issue", "create",
            "--repo", REPO,
            "--title", item["title"],
            "--body", item["body"]
        ])
        print(f"  [+] Created: {out}")
        created_subissues.append({"title": item["title"], "url": out})
        
    print("\nCreating parent Epic issue...")
    parent_body = rf"""## Epic: Automated Lifecycle Hooks & Pre/Post Execution Runtime Guards

This issue tracks the implementation of **Step 5 of Part 2**: introducing automated lifecycle hooks (`.agents/hooks.json`) and runtime interceptor scripts (`scripts/hooks/`) to enforce RLM system contracts, safety boundaries, and offline verification gates programmatically.

---

### Architectural Context & Lifecycle Flow

```mermaid
graph TD
    subgraph Execution_Loop [Antigravity Agent Execution Loop]
        PI[PreInvocation] --> M[Model Generates Tool Call]
        M --> PTU[PreToolUse Hook]
        PTU -->|"Decision: allow"| TE[Tool Execution: REPL / Command]
        PTU -->|"Decision: deny"| ERR[Immediate AST Syntax Error Return]
        TE --> POST[PostToolUse Hook]
        POST --> POI[PostInvocation / Next Step]
        POI --> S[Stop Event]
        S --> STH[Stop Hook: Quality Gate]
    end

    subgraph Hook_Automations [Step 5 Automated Hook Scripts]
        H_MEM["scripts/hooks/pre_invocation_memory.py"]
        H_AST["scripts/hooks/pre_tool_ast_guard.py"]
        H_TEL["scripts/hooks/post_tool_telemetry.py"]
        H_GATE["scripts/hooks/stop_quality_gate.py"]
    end

    PI -.-> H_MEM
    PTU -.-> H_AST
    POST -.-> H_TEL
    S -.-> H_GATE
```

---

### Tracked Sub-Issues & Implementations

"""
    for sub in created_subissues:
        parent_body += f"- [ ] **{sub['title']}**\n  {sub['url']}\n"

    parent_body += r"""
---

### Configuration Blueprint (`.agents/hooks.json`)

```json
{
  "rlm-ast-guard": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "call_mcp_tool|run_command",
        "hooks": [
          {"type": "command", "command": "python scripts/hooks/pre_tool_ast_guard.py", "timeout": 5}
        ]
      }
    ]
  },
  "rlm-telemetry": {
    "enabled": true,
    "PostToolUse": [
      {
        "matcher": "call_mcp_tool|run_command",
        "hooks": [
          {"type": "command", "command": "python scripts/hooks/post_tool_telemetry.py", "timeout": 5}
        ]
      }
    ]
  },
  "mem0ry4ai": {
    "enabled": true,
    "PreInvocation": [
      {"type": "command", "command": "python scripts/hooks/pre_invocation_memory.py", "timeout": 30}
    ],
    "Stop": [
      {"type": "command", "command": "python scripts/run_mem0ry4ai_hook.py stop", "timeout": 30}
    ]
  },
  "rlm-quality-gate": {
    "enabled": true,
    "Stop": [
      {"type": "command", "command": "python scripts/hooks/stop_quality_gate.py", "timeout": 30}
    ]
  }
}
```

### Epic Acceptance Criteria
- [ ] All 4 hook scripts created under `scripts/hooks/` with executable cross-platform Python syntax.
- [ ] `.agents/hooks.json` configured with verified matchers, commands, and timeouts.
- [ ] AST PreToolUse interceptor prevents syntax errors and infinite loops from reaching REPL workers.
- [ ] PostToolUse telemetry logger preserves constant-size feedback while archiving full traces to `.rlm_sessions/`.
- [ ] Stop hook prevents session close when pytest unit tests fail.
"""

    parent_out = run_gh([
        "issue", "create",
        "--repo", REPO,
        "--title", "[Epic] Automated Lifecycle Hooks & Pre/Post Execution Runtime Guards",
        "--body", parent_body
    ])
    print(f"\n[+] Created Parent Epic Issue: {parent_out}")

if __name__ == "__main__":
    main()
