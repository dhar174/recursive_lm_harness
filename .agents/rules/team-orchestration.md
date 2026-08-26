# Team Orchestration & Multi-Agent Protocol

This document defines the operating rules, role boundaries, and execution lifecycle for the multi-agent team in `recursive_lm_harness`.

## 1. Core Principle: Context Isolation Over Metaphor

Subagents exist primarily to partition context windows, prevent context saturation ("lost-in-middle" degradation), and isolate failure domains. The main coordinator must orchestrate work across specialist agents rather than attempting single-pass monolithic reasoning.

## 2. Team Roster & Specialist Roles

| Agent | Tier / Model | Policy | Primary Responsibility |
|---|---|---|---|
| `memory-scout` | `flash` | `off` | Pre-task memory retrieval from `mem0ry4ai`, recovering durable decisions, todos, gotchas. |
| `rlm-architect` | `inherit` | `sandbox` | Problem decomposition, DAG modeling, prompt externalization strategy, recursion budgeting. |
| `repl-sandbox-engineer` | `inherit` | `sandbox` | Python REPL sandbox implementation, stdout truncation enforcement, tool runtime (`llm_query`, `rlm_query`, `FINAL`). |
| `rlm-verifier` | `flash` | `sandbox` | Adversarial second-opinion verification, syntax checking, deadlock risk detection, layer gatekeeping. |
| `eval-specialist` | `inherit` | `sandbox` | Pytest suites, OOLONG/S-NIAH/LongCoT benchmark harness, token profiling, recursion metrics. |
| `archcore-assistant` | `flash` | `sandbox` | Structured documentation creation and relation linking (`.archcore/`). |
| `archcore-auditor` | `flash` | `sandbox` | Read-only documentation health checks and consistency audits. |
| `memory-steward` | `inherit` | `off` | Post-task memory curation in `mem0ry4ai`, preserving durable decisions and updating resumption state. |

## 3. Phased Execution Lifecycle

Every non-trivial task must follow this 5-phase lifecycle:

```
[Phase 1: Ingestion & Scouting]
       │
       ▼
[Phase 2: Architecture & DAG Planning] ──► [Verification Gate 1: Syntax & Plan Audit]
       │
       ▼
[Phase 3: Sandbox & Tool Engineering] ──► [Verification Gate 2: Code & Deadlock Check]
       │
       ▼
[Phase 4: Verification & Benchmarking]
       │
       ▼
[Phase 5: Curation & Documentation Closeout]
```

### Phase 1: Ingestion & Memory Scouting
- **Agent**: `memory-scout`
- **When**: Start of any non-trivial task or refactoring.
- **Action**: Query `project:recursive_lm_harness` for prior architectural decisions, gotchas, or pending todos.
- **Handoff Contract**: Compact memory brief detailing active constraints and disproved assumptions.

### Phase 2: Architecture & DAG Planning
- **Agent**: `rlm-architect` (and `archcore-assistant` if formal specs/ADRs are needed).
- **Action**: Partition complex prompt logic into a topological DAG. Identify variable buffers and sub-call batching.
- **Verification Gate**: `rlm-verifier` reviews the decomposition plan before code execution begins.

### Phase 3: Sandbox & Tool Runtime Engineering
- **Agent**: `repl-sandbox-engineer`
- **Action**: Implement or modify REPL sandbox hooks, tool bindings, stdout truncation handlers, or buffer logic.
- **Verification Gate**: `rlm-verifier` audits code syntax and ensures no stdout leakage or deadlock vulnerabilities exist.

### Phase 4: Independent Verification & Benchmarking
- **Agents**: `eval-specialist` & `archcore-auditor`
- **Action**: Execute deterministic pytest suites, run synthetic benchmark fixtures (OOLONG, S-NIAH, LongCoT-mini), and audit documentation coverage.
- **Handoff Contract**: Metric scorecard reporting Accuracy, Token Usage, Latency, and Cost.

### Phase 5: Curation & Knowledge Closeout
- **Agent**: `memory-steward`
- **Action**: Inspect verified outcomes. Record durable decisions, novel gotchas, and updated resumption todos into `mem0ry4ai`.
- **Constraint**: No execution logs or transient debugging noise in long-term memory.

## 4. Anti-Telephone Game & Direct Pass-Through

LangGraph benchmarks demonstrate that supervisor paraphrasing degrades reasoning fidelity by up to 50%. To prevent the "telephone game":
- **Pass Direct Evidence**: When forwarding subagent findings (such as benchmark scorecards or verification failure stacks), quote or forward the exact structured section without lossy summarization.
- **Preserve Output Contracts**: Require subagents to strictly adhere to their markdown section templates.

## 5. Circuit Breakers & Anti-Stall Triggers

- **Max Recursion Depth**: Default hard cap of $D_{max} = 5$ on recursive loops.
- **Fan-Out Budget**: Maximum of 20 concurrent sub-calls per DAG layer.
- **Sycophancy Intervention**: If `rlm-verifier` passes an unvalidated plan with zero critique, the coordinator must prompt for explicit edge-case evaluation.
- **Timeout Protection**: All subprocess and sub-call operations must enforce explicit timeout parameters.
