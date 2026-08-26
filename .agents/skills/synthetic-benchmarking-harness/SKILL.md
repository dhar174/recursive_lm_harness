---
name: synthetic-benchmarking-harness
description: Framework and templates for generating deterministic, zero-cost offline benchmark fixtures for S-NIAH, OOLONG-Pairs, and LongCoT-mini.
---

# Synthetic Benchmarking Harness

This skill defines procedures for creating reproducible, offline benchmark evaluation fixtures.

## 1. S-NIAH (Synthetic Needle-in-a-Haystack)
- Synthesizes haystack text of variable token length (64k to 1M+ tokens).
- Places unique retrieval needles at precise depth percentiles (10%, 25%, 50%, 75%, 90%).

## 2. OOLONG-Pairs Evaluation
- Generates combinatorial record sets where single-pass models collapse ($\le 0.1\%$) but recursive models maintain high fidelity ($\ge 58\%$).
- Evaluates pairwise comparison aggregation and token cost efficiency.
