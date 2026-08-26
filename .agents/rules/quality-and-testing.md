# Quality Standards & Testing Protocols

This document defines testing requirements, verification gates, and evaluation standards for `recursive_lm_harness`.

## 1. Testing Hierarchy

1. **Unit Tests (`tests/unit/`)**:
   - Fast, isolated tests for REPL sandboxing, variable buffering, stdout truncation, and parser logic.
   - 100% offline; zero network calls.
2. **Integration Tests (`tests/integration/`)**:
   - End-to-end multi-step recursive loops using synthetic mock LLM responders.
   - Validates termination signals (`FINAL`, `FINAL_VAR`), state persistence, and error recovery.
3. **Benchmark Evaluations (`tests/benchmarks/`)**:
   - Standardized evaluation suites:
     * `OOLONG-Pairs`: Quadratic aggregation and cross-entry comparison.
     * `S-NIAH`: Needle-in-a-haystack retrieval across variable token depths (64k to 1M+).
     * `LongCoT-mini`: Layer-by-layer reasoning DAG execution.

## 2. Mandatory Verification Gates

No code change or architectural refactor may be merged or marked complete without passing these gates:

| Gate | Verifier | Criteria |
|---|---|---|
| **Syntax & Lint** | `rlm-verifier` | Code passes syntax check with zero unhandled exceptions. |
| **Deadlock & Output Cap** | `rlm-verifier` | Output tokens budgeted; termination paths guaranteed. |
| **Deterministic Tests** | `eval-specialist` | `pytest` suite passes with zero regressions. |
| **Documentation Health** | `archcore-auditor` | No broken relations or orphaned `.archcore/` specs. |

## 3. Offline-First Mandate

- Standard test suites (`pytest`) and CI workflows MUST run offline using synthetic fixtures and deterministic mocks.
- Live LLM calls or network execution require explicit test flags (e.g. `pytest --live-llm`) and must never be triggered by default test runs.

## 4. Pytest Execution Conventions

```bash
# Run standard offline unit & integration tests
pytest -q

# Run with coverage report
pytest --cov=src -q

# Run benchmark suite
pytest tests/benchmarks/ -q
```
