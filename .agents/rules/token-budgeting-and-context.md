# Token Budgeting & Recursive Context Pruning

This document enforces strict context management, token optimization, and communication precision across all agents in `recursive_lm_harness`.

## 1. The Gatekeeper Protocol

To prevent context window bloat and attention degradation over long workflows, agents must apply the **Gatekeeper Protocol**:

1. **Metadata Sharding**: Never inject full source files or raw documents into coordinator context. Scan for headers, structural indices, and size metrics; pull only narrowed fragments on explicit demand.
2. **Safe Response Budgeting**:
   - 30% budget for current step logic processing.
   - 20% budget for immediate output generation.
   - 50% buffer reserved for downstream conversation and tool responses.
3. **Atomic Precision Output**: Strip all conversational filler and bridge phrases. Responses start immediately with the solution, structured diff, or code block.

## 2. Forbidden Bridge Phrases

Agents and coordinators must NEVER use filler phrases such as:
- ❌ *"Sure, I can help with that!"*
- ❌ *"Here is the updated code you requested:"*
- ❌ *"Based on my analysis of the codebase..."*
- ❌ *"Let me know if you need any further assistance!"*

✅ **Direct Execution**: Begin responses directly with the actionable result, table, diff, or structured report.

## 3. Abstractive State Compression

Between execution turns and agent handoffs, summarize completed work into a standardized compressed state token:

```text
[Task: <Task Name> | Phase: <1-5> | State: <Status> | Unresolved: <Blockers>]
```

This ensures subsequent turns do not drag forward redundant conversational history.

## 4. Single-Turn Ambiguity Resolution

If a task lacks critical inputs (e.g. missing target dataset, undefined recursion limit, ambiguous file path):
- Do NOT guess or emit speculative code.
- Immediately ask **one concise, targeted clarifying question** to unblock execution.

## 5. Recursive Token Budget Allocation

When spawning recursive child loops via `rlm_query`:
- **Depth Decay Factor**: Enforce an exponential token budget decay across recursive depth $d$:
  $$B(d) = B_0 \cdot \gamma^d \quad (\text{where } \gamma = 0.7, \; d \le D_{max} = 5)$$
- **Leaf Node Hard Cap**: Leaf sub-queries ($d = D_{max}$) must not spawn further recursive loops and must terminate via `llm_query` or direct REPL computation.
- **Fan-Out Budget**: Maximum of 20 concurrent sub-calls per DAG layer.
