# Evidence-Repair Progress Ledger — 2026-11-17

## Goal
Mission milestone: fail-closed actual-model experiment. Repair evidence chain so claims about the quantum LLM agent rest on verified, reproducible runs against the real model — no proxy, no memorizer, no embedded constants, no fail-open wrapper.

## Authorization
User mission text dated 2026-11-16 (evidence-repair mission). Local-only work on branch `research/audit-1587497`. No push, no secrets, no training.

## Branch / Commit
- Branch: `research/audit-1587497`
- Commit: `a3addab83791b9b2c39e8bb05a12e74fb1444f66`

## Checkout State (at ledger creation)
- Git status: clean except untracked `?? .sdlc/`
- Python: 3.12.3
- CPU / RAM: 12 CPU, 30 Gi
- pennylane: 0.44.1
- numpy: 2.4.4
- torch: absent

## Explorer Verdicts Summary
- #1 Verified: proxy MLP (claim of quantum model actually exercised a classical proxy)
- #2 Verified: memorizer (memorization behavior confirmed)
- #3 Verified: embedded constants (hard-coded constants embedded in path)
- #4 Verified: fail-open wrapper (wrapper fails open instead of fail-closed)
- #5 Verified: threshold / Bonferroni (thresholding + multiple-comparison correction issue confirmed)
- #6 Confirmed: same-token + classical fallback (same-token behavior with classical fallback confirmed)
- #7 NOT UPHELD, scoped correctly (claim #7 did not hold; scoping of the non-finding recorded)
- #8 Mechanics confirmed, repro by exclusion (mechanistic claim confirmed via reproduction-by-exclusion)

## Env Inventory
- `QuantumAttentionCircuit` — `quantum/circuits/core.py:212`
- `QuantumMultiHeadAttention` — `hybrid/attention/quantum_attention.py:19`
- `HybridQuantumLLM` — `hybrid/interfaces/model.py:85`
- Classical baselines — `benchmarks/tasks/`

## Next Step
Write `EVIDENCE_REPAIR.md` (fail-closed actual-model experiment plan + evidence checklist).

## Run-Once Preservation Note
Do NOT re-run confirmatory locks. Prior confirmatory runs are locked evidence — re-running them risks overwriting / invalidating preserved state. All further work must append new evidence, never mutate locked runs.

## Task Status 2026-11-17 UTC
- Task1 done: verdicts wording-preservation audit (proxy / memorizer / constants / fail-open / threshold-Bonferroni / same-token-fallback / #7 scoped / #8 exclusion) — exactness preserved, no rewording.
- Task2 done: superseding assessment appended to `research/FINAL_ASSESSMENT.md` (header "Superseding assessment 2026-11-17 (research/audit-1587497 @ a3addab) — authoritative, priors preserved below"); priors v1–v5 untouched; verify `grep -q "Superseding.*2026-11-17" + last-token-only + full-information` exit 0.
- Task3 done: evidence + checklist verification (M1–M3 covered; evidence json shape valid; no file outside `allow` touched) — verify `ls -l docs/plans/2026-11-17-evidence-repair-progress.md docs/plans/2026-11-17-evidence-repair-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-evidence-repair-evidence.json > /dev/null` exit 0.
