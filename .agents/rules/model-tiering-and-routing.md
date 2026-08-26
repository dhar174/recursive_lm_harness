# Model Tiering & Sub-call Routing Strategy

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
