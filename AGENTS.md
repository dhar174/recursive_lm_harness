# AGENTS.md - Repository Operating Guidelines & Architecture

This repository implements **Recursive Language Models (RLMs)**: a framework that extends the semantic horizon of LLMs by treating prompts as external environment variables in a Python REPL sandbox, enabling programmatic $O(n^2)$ reasoning, symbolic DAG decomposition, and unbounded inference scaling.

## 1. Repository Structure

```text
recursive_lm_harness/
├── .agents/
│   ├── agents/               # Antigravity 2.0+ custom subagents
│   │   ├── memory-scout/     # Read-only mem0ry4ai retrieval specialist
│   │   ├── memory-steward/   # Durable memory curation specialist
│   │   ├── rlm-architect/    # DAG decomposition & recursion modeling specialist
│   │   ├── repl-sandbox-engineer/ # Python REPL sandbox & tool runtime specialist
│   │   ├── rlm-verifier/     # Syntax checking & deadlock prevention specialist
│   │   ├── ast-safety-guard/ # Pre-execution Python AST static analyzer
│   │   ├── token-profiler/   # Recursion telemetry & cost optimization specialist
│   │   ├── synthetic-dataset-generator/ # Deterministic S-NIAH / OOLONG fixture generator
│   │   ├── eval-specialist/  # Pytest & OOLONG/S-NIAH benchmark specialist
│   │   ├── archcore-assistant/ # Structured documentation creation specialist
│   │   └── archcore-auditor/ # Documentation health & consistency auditor
│   ├── rules/                # Modular repository rules
│   │   ├── team-orchestration.md
│   │   ├── rlm-system-contracts.md
│   │   ├── token-budgeting-and-context.md
│   │   ├── quality-and-testing.md
│   │   ├── windows-runtime-contracts.md
│   │   ├── repl-security-and-isolation.md
│   │   └── model-tiering-and-routing.md
│   ├── skills/               # Custom & bundled Antigravity skills
│   ├── hooks.json            # Lifecycle hooks (mem0ry4ai pre-invocation / stop)
│   └── mcp_config.json       # MCP server configuration (archcore, aas-core)
├── scripts/                  # Operational scripts & hook runners
├── GEMINI.md                 # Antigravity lead coordinator entrypoint
├── README.md                 # Technical architecture specification
└── LICENSE                   # MIT License
```

## 2. Core Architectural Pillars

1. **Symbolic Handles**: Prompts ($P$) are stored as external variables (`context`) in a persistent REPL, preventing attention saturation.
2. **Decoupled Output Generation**: Long-form answers accumulate in environment variables (`FINAL_VAR`) rather than single output streams.
3. **Programmatic Recursion**: Sub-tasks delegate through `llm_query` (~200k chars) or isolated recursive loops (`rlm_query`).
4. **Layer-by-Layer DAG Resolution**: Task dependencies resolve into a persistent memoization table (`answers`) with independent second-opinion verification.

## 3. Operational Conventions

- **Offline-First Testing**: Run `pytest -q` using synthetic fixtures. Live LLM calls require explicit test flags.
- **Zero Bridge Phrases**: Follow atomic precision protocol; omit introductory and concluding conversational filler.
- **Least-Privilege Isolation**: Read and verification agents operate in restricted sandboxes; modification agents operate in workspace write sandboxes.
