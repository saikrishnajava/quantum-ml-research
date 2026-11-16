# Parity / Efficiency Pivot (Spec P,F6-docs)

**Date:** 2026-11-14  
**Spec:** P,F6-docs — docs efficiency-only pivot  
**Depends on:** T1–T2 (Tie winner, boolean significance flag, N=3 exploratory, moe_6_9 naming)  
**License / cost:** No secrets, free-only tooling (PennyLane + NumPy). No paid APIs, no GPU required.  
**Scope:** Docs only. No code changes.

## Summary

The parity experiment is **capacity-matched** and run for **20 epochs** across **N=3 exploratory** seeds (42, 99, 137) — not N=5. All configurations finish **at chance (48–50%)** test accuracy.

There is **no quantum advantage** at capacity/20 epochs. The paired t-test is not significant (p = 0.535, `significant = false`), so the winner is **Tie** — never Classical by default.

The only defensible claim is **param-efficiency**: the quantum and moe_6_9 variants reach the same chance accuracy with fewer quantum parameters, not better accuracy.

## Experimental setup

| Setting | Value |
|---|---|
| Task | 8-bit Boolean parity (classical control — no quantum advantage expected) |
| n_train / n_test | 800 / 200 |
| n_epochs | 20 |
| Seeds | 42, 99, 137 (N=3 exploratory, not N=5) |
| Capacity match | total params held ~constant across configs |
| Significance | paired t-test; boolean `significant` flag |

## Results

All models at chance (~48–50%); every 95% CI straddles 50%.

| Model | Params total | Params quantum | Mean test acc | 95% CI | Winner |
|---|---|---|---|---|---|
| Classical (0 quantum heads) | 2352 | 0 | 0.485 | [0.442, 0.528] | Tie |
| Quantum (1 fixed 6-qubit head) | 2370 | 18 | 0.500 | [0.390, 0.610] | Tie |
| MoE (moe_6_9, 6/9 qubit router) | 2406 | 16 | 0.475 | [0.432, 0.518] | Tie |

- classical_vs_quantum: p = 0.535, significant = false, mean diff = +0.015
- Winner: **Tie** (no model is statistically ahead; never Classical by default)

## Naming

The capacity-matched MoE configuration is named **moe_6_9** — "MoE (6/9 qubit router)". It uses 6-qubit and 9-qubit experts only; the 12-qubit expert is excluded (returns NaN on the CPU simulator, see RUN_LOG Run 4/8). Do not write `moe_6_9_12` or "6/9/12" for this experiment.

## Source

Data: `examples/demos/parity_results.json` (n_seeds = 3, n_epochs = 20, capacity_match).
