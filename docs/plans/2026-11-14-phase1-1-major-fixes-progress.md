# Plan — Phase 1.1 Major Fixes Progress

**Date:** 2026-11-14  
**Spec:** docs/specs/2026-11-14-phase1-rigor-equivariant.md (Spec B-1)  
**Scope:** docs/specs + docs/plans only. No code changes in this plan.  
**Cost:** No secrets, free-only.

## Progress tracking (M1–M4 major, m minor)

| ID | Status | File:line | Owner | Notes |
|----|--------|-----------|-------|-------|
| M1 | Not started | quantum/circuits/core.py:86, :154 | — | Add seeded init |
| M2 | Not started | quantum/circuits/core.py:253 | — | Replace bare except with logged, scoped handling |
| M3 | Not started | hybrid/feedforward/hybrid_ff.py:67 | — | Replace silent except with warning + re-raise path |
| M4 | Not started | classical/nn.py:251–253, hybrid/attention/quantum_attention.py:110–112 | — | Add Q/K/V shape validation |
| m1 | Not started | quantum/backends/manager.py:21 | — | Remove/replace type: ignore |

## Out of scope

- All code changes (docs only in Phase 1.1).
- GPU / lightning.gpu, PennyLane plugin, NumPy ComplexWarning (already addressed in RUN_LOG).
- Paid APIs, secrets, non-free tooling.

## Definition of done (smoke only)

- Spec lists M1–M4 and m IDs with file:line refs.
- `grep -rn "M1\|M2\|M3\|M4" docs/specs/2026-11-14-phase1-rigor-equivariant.md` returns exit code 0.
- No secrets or paid-service references in docs.
