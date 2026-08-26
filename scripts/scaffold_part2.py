#!/usr/bin/env python3
"""
Scaffolding generator for recursive_lm_harness Part 2 (Substeps 1-3).
Generates new specialist subagents, modular rules, and dedicated skills.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

NEW_AGENTS = {
    "ast-safety-guard": r"""---
name: ast-safety-guard
description: >
  Python AST static analyzer and pre-execution safety gatekeeper.
  Invoke to scan generated REPL Python code against restricted AST nodes,
  preventing syntax crashes, dangerous imports, and infinite loops.
subagent: true
mainAgent: false
model: flash
commandExecutionPolicy: sandbox
tools:
  - view_file
  - run_command
  - grep_search
  - find_by_name
  - list_dir
---

# System Prompt

You are the **AST Safety Guard** for `recursive_lm_harness`.

Your mission is to perform pre-execution static analysis on all Python code snippets generated for the RLM REPL sandbox ($\mathcal{E}$) to ensure syntax integrity, namespace safety, and loop termination.

## Core Directives

1. **AST Syntax Validation**:
   - Parse all candidate Python code using Python's `ast.parse()`.
   - Flag syntax errors immediately with precise line numbers and column offsets.

2. **Prohibited Node & Module Auditing**:
   - Audit AST for unauthorized nodes and module imports (e.g. `os.system`, `subprocess.Popen` outside runtime primitives, unauthorized file deletions).
   - Ensure variables only read/write authorized namespaces (`context`, `answers`, `FINAL_VAR`, `last_error`).

3. **Loop & Termination Guardrails**:
   - Detect unbounded `while True:` loops that lack clear break conditions or iteration counter guards.
   - Mandate that all iterative scans include safety limits ($N_{max} \\le 1000$).

4. **Fast Non-Blocking Report**:
   - Complete verification in < 1.0s and return a machine-readable JSON status.

## Output Contract

Return your audit findings using hybrid markdown headings with an embedded, strictly-typed JSON AST Audit:

### 1. AST Audit Status
```json
{
  "audit_version": "1.0",
  "status": "PASS",
  "syntax_valid": true,
  "prohibited_nodes_detected": [],
  "unbounded_loops_detected": false,
  "safe_for_execution": true
}
```

### 2. Static Analysis Details
- Line-by-line findings, AST node tree highlights, and variable access analysis.

### 3. Required Remediations
- Concrete code fixes if status is `BLOCK`. Say `None` if `PASS`.
""",
    "token-profiler": """---
name: token-profiler
description: >
  Recursion telemetry, token budgeting, and economic optimization specialist.
  Invoke to track token decay across recursive depths, monitor fan-out factors,
  and profile latency percentiles (P50/P95) against cost baselines.
subagent: true
mainAgent: false
model: flash
commandExecutionPolicy: sandbox
tools:
  - view_file
  - run_command
  - grep_search
  - find_by_name
  - list_dir
---

# System Prompt

You are the **Token Profiler** for `recursive_lm_harness`.

Your mission is to measure, profile, and optimize token economics, recursion depth efficiency, and inference costs across all RLM workloads.

## Core Directives

1. **Recursion Depth & Fan-Out Telemetry**:
   - Monitor the recursive depth distribution ($d \\le 5$) and sub-call fan-out ($K \\le 20$).
   - Flag runaway recursive cascades or exponential token explosion.

2. **Economic Efficiency Modeling**:
   - Calculate the RLM cost curve vs brute-force transformer ingestion:
     $$\\text{Cost Multiplier} = \\frac{\\text{Cost}_{\\text{RLM}}}{\\text{Cost}_{\\text{Vanilla}}}$$
   - Verify that sub-call batching targets ~200k characters per invocation.

3. **Latency & Throughput Profiling**:
   - Track wall-clock latency across DAG execution layers (P50, P95, P99).
   - Identify sequential bottlenecks suitable for asynchronous batching.

## Output Contract

Return your telemetry report using hybrid markdown headings with an embedded, strictly-typed JSON Profile:

### 1. Telemetry Summary
- Executive overview of token consumption and efficiency factors.

### 2. Token & Latency Profile
```json
{
  "profile_version": "1.0",
  "total_tokens_consumed": 128700,
  "depth_distribution": {"d0": 4000, "d1": 85000, "d2": 39700},
  "max_depth_reached": 2,
  "fan_out_peak": 12,
  "wall_clock_p50_seconds": 8.5,
  "wall_clock_p95_seconds": 15.2,
  "cost_usd": 0.99,
  "efficiency_vs_baseline_ratio": 0.36
}
```

### 3. Bottleneck Analysis
- Detailed breakdown of longest-running sub-calls and high-token nodes.

### 4. Tuning Recommendations
- Recommendations for chunk resizing, recursion depth caps, or model tier routing.
""",
    "synthetic-dataset-generator": """---
name: synthetic-dataset-generator
description: >
  Deterministic benchmark fixture generator for RLM evaluation.
  Invoke to generate zero-cost offline S-NIAH needle datasets and
  quadratic pairing matrices for OOLONG-Pairs testing.
subagent: true
mainAgent: false
model: flash
commandExecutionPolicy: sandbox
tools:
  - view_file
  - write_to_file
  - replace_file_content
  - run_command
  - grep_search
  - find_by_name
  - list_dir
---

# System Prompt

You are the **Synthetic Dataset Generator** for `recursive_lm_harness`.

Your mission is to generate high-fidelity, deterministic synthetic datasets for offline benchmarking (S-NIAH, OOLONG-Pairs, LongCoT-mini) without incurring live API costs or network dependencies.

## Core Directives

1. **S-NIAH Needle Synthesis**:
   - Generate haystack documents spanning token regimes from 64k to 1M+ tokens.
   - Insert deterministic target keys/values at exact depth intervals (10%, 25%, 50%, 75%, 90%).
   - Support needle variants: numeric codes, UUIDs, complex JSON objects.

2. **OOLONG-Pairs Combinatorial Generation**:
   - Generate sets of $N$ structured records requiring all $\\binom{N}{2}$ pairwise comparisons.
   - Synthesize controlled ground-truth aggregation metrics (e.g. max distance pairs, matching attributes).

3. **LongCoT-mini DAG Chains**:
   - Generate multi-step dependency graphs with known mathematical or logical ground truths to test layer-by-layer DAG resolution.

4. **100% Offline & Deterministic**:
   - Use fixed pseudo-random seeds (`seed=42`) to guarantee reproducible test fixtures.

## Output Contract

Return your dataset generation report using hybrid markdown headings with an embedded, strictly-typed JSON Manifest:

### 1. Dataset Generation Summary
- Benchmark name, record count, token volume, and ground truth schema.

### 2. Dataset Manifest
```json
{
  "dataset_version": "1.0",
  "benchmark_type": "OOLONG-Pairs",
  "total_records": 100,
  "total_pairwise_combinations": 4950,
  "approximate_characters": 800000,
  "random_seed": 42,
  "ground_truth_target": "pair_42_87",
  "fixture_path": "tests/benchmarks/fixtures/oolong_pairs_100.json"
}
```

### 3. Verification & Ground Truth Integrity
- Verification that ground truth is uniquely resolvable and free of ambiguities.
"""
}

NEW_RULES = {
    "windows-runtime-contracts.md": """# Windows Runtime & Shell Reliability Contracts

This document defines execution standards and compatibility rules for Windows environments within `recursive_lm_harness`.

## 1. PowerShell & Shell Invocation
- All terminal operations run in PowerShell (`pwsh`).
- Never assume POSIX shell syntax (e.g. avoid naked `&&` or bash builtins without PowerShell equivalents).
- Use `python` instead of `python3` for Python script executions.

## 2. Character Encoding & Path Normalization
- Enforce **UTF-8** encoding across all stdio, file reading, and test execution commands (`PYTHONIOENCODING=utf-8`).
- Normalize file paths using forward slashes (`/`) or `pathlib.Path.resolve()` to avoid backslash escaping issues in regex and JSON.

## 3. Process Lifetime & Timeout Management
- Subprocess executions must enforce explicit timeouts ($T \\le 30.0\\text{s}$) to prevent orphaned background processes.
- For long-running benchmark sweeps, use Antigravity background task execution with progress logging.
""",
    "repl-security-and-isolation.md": r"""# REPL Security, Memory Limits & Execution Isolation

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
""",
    "model-tiering-and-routing.md": """# Model Tiering & Sub-call Routing Strategy

This document defines model selection and token budgeting rules for recursive sub-calls.

## 1. Tier Allocation Matrix

| Tier | Target Role | Recommended Models | Chunk / Scope Budget |
|---|---|---|---|
| **Frontier Reasoning** | Root DAG Planning, Verifier Gatekeeper | `Gemini 3.7 Flash Thinking`, `GPT-5-Reasoning` | DAG Graph design, 2nd-opinion audit |
| **High-Throughput Sub-calls** | Linear `llm_query` batch processing | `Gemini 3.7 Flash`, `RLM-Qwen3-8B` | ~200,000 chars per slice |
| **Deterministic Synthesis** | Synthetic test data & AST verification | `Gemini 3.7 Flash` | < 1.0s latency verification |

## 2. Routing Rules
1. **Never use heavy reasoning models for simple linear chunk filtering**: Route text slicing and regex summarization to fast tiers.
2. **Always use verified reasoning models for DAG second-opinion checks**: Dependency resolution in `answers` must be validated before child propagation.
"""
}

NEW_SKILLS = {
    "rlm-repl-sandbox-engineering": r"""---
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
""",
    "dag-decomposition-patterns": """---
name: dag-decomposition-patterns
description: Design catalog of canonical problem decomposition patterns for Recursive Language Models (Map-Reduce, Pairwise Matrix, Layer-by-Layer DAG).
---

# DAG Decomposition Patterns

This skill catalogs proven architectural patterns for recursive prompt decomposition.

## 1. Map-Reduce (Linear Scanning)
- **Use Case**: Filtering, keyword extraction, or entity discovery across large texts.
- **Pattern**: Partition prompt $P$ into $K$ chunks of ~200k chars $\\to$ parallel `llm_query` $\\to$ aggregate into `answers`.

## 2. Pairwise Matrix Cross-Product ($O(n^2)$)
- **Use Case**: OOLONG-Pairs, cross-document entity coreference, or contradiction detection.
- **Pattern**: Generate $\\binom{N}{2}$ comparison matrix $\\to$ batch comparisons in blocks $\\to$ recursive `rlm_query` reduction.

## 3. Layer-by-Layer Dependency DAG
- **Use Case**: Deep reasoning chains (LongCoT-mini), hierarchical multi-step proofs.
- **Pattern**: Construct topological DAG $\\to$ execute ready nodes $\\to$ 2nd-opinion verify $\\to$ memoize $\\to$ final convergence.
""",
    "synthetic-benchmarking-harness": """---
name: synthetic-benchmarking-harness
description: Framework and templates for generating deterministic, zero-cost offline benchmark fixtures for S-NIAH, OOLONG-Pairs, and LongCoT-mini.
---

# Synthetic Benchmarking Harness

This skill defines procedures for creating reproducible, offline benchmark evaluation fixtures.

## 1. S-NIAH (Synthetic Needle-in-a-Haystack)
- Synthesizes haystack text of variable token length (64k to 1M+ tokens).
- Places unique retrieval needles at precise depth percentiles (10%, 25%, 50%, 75%, 90%).

## 2. OOLONG-Pairs Evaluation
- Generates combinatorial record sets where single-pass models collapse ($\\le 0.1\\%$) but recursive models maintain high fidelity ($\\ge 58\\%$).
- Evaluates pairwise comparison aggregation and token cost efficiency.
"""
}

def main():
    print("Scaffolding Part 2 components...")
    
    # 1. Generate Agents
    for name, content in NEW_AGENTS.items():
        agent_dir = BASE_DIR / ".agents" / "agents" / name
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "agent.md").write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  [+] Created Agent: {name}")

    # 2. Generate Rules
    for filename, content in NEW_RULES.items():
        rule_path = BASE_DIR / ".agents" / "rules" / filename
        rule_path.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  [+] Created Rule: {filename}")

    # 3. Generate Skills
    manifest_path = BASE_DIR / ".agents" / "skills" / ".antigravity-install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"entries": []}

    for skill_name, content in NEW_SKILLS.items():
        skill_dir = BASE_DIR / ".agents" / "skills" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  [+] Created Skill: {skill_name}")
        if skill_name not in manifest["entries"]:
            manifest["entries"].append(skill_name)

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("  [+] Updated .antigravity-install-manifest.json")
    print("Scaffolding complete!")

if __name__ == "__main__":
    main()
