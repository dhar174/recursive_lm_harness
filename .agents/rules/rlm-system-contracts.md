# RLM System Contracts & Architectural Principles

This document defines the authoritative technical contracts for Recursive Language Model (RLM) implementations within this repository.

## 1. The Environmental Prompt Paradigm

- **Prompt Externalization**: The user prompt ($P$) is treated as an external environment variable in the persistent REPL sandbox ($\mathcal{E}$), accessible via symbolic variable handles (`context`).
- **Zero Raw Context Ingestion**: Never dump massive prompt texts (100k+ chars) directly into model hidden states. The root model acts as a symbolic orchestrator, inspecting slices and metadata.
- **State Persistence**: The REPL environment persists across iterations, allowing the model to build data transformations incrementally.

## 2. Decoupled Output Generation & Variable Buffering

- **Variable Accumulation**: Long-form answers and intermediate analyses must be stored inside REPL memory variables (e.g. `answers["node_1"]`, `summary_buffer`) rather than emitted in a single autoregressive pass.
- **Explicit Exit Signals**: Termination occurs exclusively via `FINAL(answer_string)` or `FINAL_VAR("var_name")`.

## 3. Mandatory Stdout Truncation Strategy

- **Attention Saturation Prevention**: The REPL must never echo full execution output to the coordinator context window.
- **Constant-Size Feedback**: Stdout returns must be truncated to constant-size metadata (e.g. character count, line count, first 200 characters, exit code).
- **Programmatic Inspection**: If an agent needs deeper output inspection, it must write code to slice or search the variable within the REPL.

## 4. Layer-by-Layer DAG Decomposition

- **DAG Structure**: Complex reasoning must be modeled as a Directed Acyclic Graph where:
  * Nodes represent atomic semantic transformations or batched sub-queries.
  * Edges represent data dependencies.
- **Memoization Table**: Intermediate outputs are stored in a persistent `answers` dictionary keyed by unique node IDs.
- **Ready Node Scheduling**: A node is only scheduled for execution when all parent dependency keys are present and validated in `answers`.
- **Second-Opinion Verification**: Critical dependency values must undergo verification before downstream propagation.

## 5. Sub-call Batching & Token Economics

- **Chunk Sizing**: Batch data at approximately **200,000 characters** per `llm_query` invocation. Avoid launching hundreds of trivial micro-calls.
- **Linear vs Quadratic Work**:
  * For linear extraction ($O(n)$): Use batched `llm_query` calls across partitioned slices.
  * For quadratic comparisons ($O(n^2)$): Form pairwise matrix batches and recursively aggregate via `rlm_query`.

## 6. Deadlock & Token Starvation Safeguards

- **Reasoning Horizon Buffer**: Ensure reasoning/thinking tokens do not exhaust the output limit before Python code or termination tags are emitted.
- **Fallback Traps**: If code generation encounters a syntax error or exception, the loop must catch the exception into a state variable rather than crashing the REPL process.
