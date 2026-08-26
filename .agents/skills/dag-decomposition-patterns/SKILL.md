---
name: dag-decomposition-patterns
description: Design catalog of canonical problem decomposition patterns for Recursive Language Models (Map-Reduce, Pairwise Matrix, Layer-by-Layer DAG).
---

# DAG Decomposition Patterns

This skill catalogs proven architectural patterns for recursive prompt decomposition.

## 1. Map-Reduce (Linear Scanning)
- **Use Case**: Filtering, keyword extraction, or entity discovery across large texts.
- **Pattern**: Partition prompt $P$ into $K$ chunks of ~200k chars $\to$ parallel `llm_query` $\to$ aggregate into `answers`.

## 2. Pairwise Matrix Cross-Product ($O(n^2)$)
- **Use Case**: OOLONG-Pairs, cross-document entity coreference, or contradiction detection.
- **Pattern**: Generate $\binom{N}{2}$ comparison matrix $\to$ batch comparisons in blocks $\to$ recursive `rlm_query` reduction.

## 3. Layer-by-Layer Dependency DAG
- **Use Case**: Deep reasoning chains (LongCoT-mini), hierarchical multi-step proofs.
- **Pattern**: Construct topological DAG $\to$ execute ready nodes $\to$ 2nd-opinion verify $\to$ memoize $\to$ final convergence.
