# Spec B-1 — Phase 1 Rigor / Equivariant Spec

**Date:** 2026-11-14  
**Phase:** 1 (Major fixes)  
**Scope:** docs/specs + docs/plans only. No code changes in this spec.  
**License / cost:** No secrets, free-only tooling (PennyLane + NumPy). No paid APIs, no GPU required.

---

## 1. Purpose

Establish the tracking IDs (M1–M4 major, m minor) and file:line references for Phase 1 rigor/equivariant hardening of the quantum-llm-agent proof of concept. This spec defines *what* is tracked; the plan (`docs/plans/2026-11-14-phase1-1-major-fixes-progress.md`) defines *when* each is addressed.

---

## 2. Tracked fix IDs

| ID | Severity | Issue | File:line |
|----|----------|-------|-----------|
| M1 | Major | Non-deterministic parameter init (no seed) | quantum/circuits/core.py:86, quantum/circuits/core.py:154 |
| M2 | Major | Bare `except Exception:` swallows backend device errors, no log/re-raise | quantum/circuits/core.py:253 |
| M3 | Major | Silent `except Exception:` in quantum-activation fallback (debug-only log) | hybrid/feedforward/hybrid_ff.py:67 |
| M4 | Major | Attention forward assumes Q/K/V share d_model with no shape validation | classical/nn.py:251–253, hybrid/attention/quantum_attention.py:110–112 |
| m1 | Minor | Type-ignored optional `yaml` import | quantum/backends/manager.py:21 |

---

## 3. Out of scope (this spec / phase 1)

- All runtime code changes (out-of-scope per task boundary: docs only).
- GPU / lightning.gpu backend fixes (Bug 2 in RUN_LOG.md is a known environment mismatch, workaround already in place).
- PennyLane plugin syntax (Bug 1) and NumPy ComplexWarning (Bug 3) — already fixed in setup_gpu.sh / train_gpu.py.
- Coherent text generation, production-scale training, or quantum-advantage claims (proof of concept only).
- Any secrets, paid APIs, or non-free tooling.

---

## 4. Acceptance (smoke only)

- `docs/specs/2026-11-14-phase1-rigor-equivariant.md` exists and lists M1, M2, M3, M4, and m IDs with file:line refs.
- `grep -rn "M1\|M2\|M3\|M4" docs/specs/2026-11-14-phase1-rigor-equivariant.md` returns matches (exit code 0).
- No secrets or paid-service references present in the spec.
- No source files modified under this spec.
