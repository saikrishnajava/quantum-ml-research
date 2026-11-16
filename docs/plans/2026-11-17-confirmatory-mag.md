---
spec: N/A-fail-open-frozen-inline
status: approved
approved_by: user
approved_at: 2026-11-16T02:32:53Z
files:
  - tests/test_confirmatory_mag.py
allow:
  - docs/plans/2026-11-17-confirmatory-mag-progress.md
  - docs/plans/2026-11-17-confirmatory-mag-evidence.json
Authorization: user "keep on continue", frozen-then-once, no peeking before freeze
---

# Plan — Confirmatory Magnitude Lock

Branch: `research/audit-1587497`.

User approval transcribed 2026-11-16: "keep on continue".
No gate fail-open. Confirmatory magnitude frozen-then-once only; no peeking before freeze.

> Correction 2026-11-17 (RED, pre-results, doc-text only — no rerun, run-once consumed): held-out XOR typo fixed (1,2,1,2)→(1,3,1,2) to match frozen test constants; no result/evidence numbers changed.

## Goal

Run one frozen confirmatory magnitude check via `tests/test_confirmatory_mag.py` to record whether the frozen F-1/F-2/F-3 magnitude claims hold under caps. No advantage claim; record outcome only.

```mermaid
flowchart LR
  Spec[Spec frozen inline F-1/F-2/F-3] --> Run[Mag run-once fresh 11,33,55 <=5 epochs]
  Run --> Test[tests/test_confirmatory_mag.py checks]
  Test --> Evidence[progress + evidence only]
```

## Arch

- Single-file: `tests/test_confirmatory_mag.py` (frozen magnitude checks only, no sweeps).
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- python 3.12 venv (`.venv/bin/python`)
- pytest
- numpy / PennyLane CPU only (local-only)

## Spec

- Spec: N/A-fail-open-frozen-inline — explicitly no approved spec file. Frozen inline claims below are record-only, fail-open (no gate).
- F-1 (frozen): magnitude run completes within caps using ONLY fresh seeds [11,33,55] (forbidden seed 6 never used), held-out XOR(1,3,1,2)+EQ(2,1,1), model 64 hidden / 5 epochs max / lr 1e-2, local-only run-once.
- F-2 (frozen): PRIMARY outcome is diff recorded vs THRESHOLD 0.20 with BONFERRONI 2 correction, record-only fail-open, no gated advantage claim.
- F-3 (frozen): evidence written only to `allow` paths; no file outside `files` touched; run-once honored.
- No fail-closed gate is wired; outcomes are recorded, not gated.
- Out of scope: code changes beyond frozen magnitude run, secrets, push/PR.

## Constraints

- Time cap 10-15m total; reversible.
- <=5 epochs per run; exactly fresh seeds [11,33,55]; forbidden 6 never used; run-once.
- Model locked: 64 hidden / 5 epochs max / lr 1e-2; PRIMARY diff; THRESHOLD 0.20; BONFERRONI 2.
- Held-out locked: XOR(1,3,1,2)+EQ(2,1,1); no peeking before freeze.
- Local-only CPU; no GPU, no paid APIs, no sweeps, no spend.
- Scope locked to `files` list above; evidence only to `allow` list above.

## Lean

- Minimum single-file rerun that answers magnitude check; no refactors, no new modules.
- Reuse existing frozen checks and configs; no perf tuning, no API changes.

## Review Focus

- HIGH-1: No approved spec file — must stay N/A fail-open frozen-inline, no gated claim.
- HIGH-2: Caps enforced (fresh [11,33,55], forbidden 6, <=5 epochs, 10-15m, local-only, run-once).
- HIGH-3: No file outside `files` touched; evidence only to `allow`; held-out + model + PRIMARY/THRESHOLD/BONFERRONI frozen.
- HIGH-4: Frozen-then-once honored; no peeking before freeze.

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Magnitude frozen run-once | F-1 frozen, caps-only | `tests/test_confirmatory_mag.py` | fresh [11,33,55] only, forbidden 6 unused, XOR(1,3,1,2)+EQ(2,1,1), 64/5/1e-2, local run-once, outcome observed | `.venv/bin/python -m py_compile tests/test_confirmatory_mag.py && grep -n "FRESH_SEEDS\|FORBIDDEN_SEEDS\|HELD_OUT" tests/test_confirmatory_mag.py` |
| 2 | Magnitude frozen checks | F-2 frozen, record-only | `tests/test_confirmatory_mag.py` | PRIMARY diff vs THRESHOLD 0.20 BONFERRONI 2, fail-open record, no gate, numbers visible via pytest -s tail | `.venv/bin/python -m pytest tests/test_confirmatory_mag.py -s -q 2>&1 | tail -n 20` |
| 3 | evidence + caps verification | F-3 frozen, evidence-only | `docs/plans/2026-11-17-confirmatory-mag-progress.md`, `docs/plans/2026-11-17-confirmatory-mag-evidence.json` | outcome recorded, caps honored, no sweep/spend | `ls -l -s docs/plans/2026-11-17-confirmatory-mag-progress.md docs/plans/2026-11-17-confirmatory-mag-evidence.json` |

## Per-task notes

- 1: fresh seeds 11,33,55 only, forbidden 6 never used; <=5 epochs; model 64/5/1e-2; held-out XOR(1,3,1,2)+EQ(2,1,1); run-once; if frozen outcome does not hold, record only, no gate.
- 2: PRIMARY diff vs THRESHOLD 0.20 with BONFERRONI 2; checks are record-only fail-open; no `ValueError` gate required under N/A-fail-open-frozen-inline.
- 3: pass only if Verify exit 0, caps (10-15m, <=5 epochs, fresh [11,33,55], forbidden 6 unused, local-only, run-once) honored, evidence written only to `allow` paths.

## Coverage checklist

- [ ] Magnitude frozen run-once (fresh [11,33,55], forbidden 6 unused, <=5 epochs, 64/5/1e-2, XOR(1,3,1,2)+EQ(2,1,1), local-only)
- [ ] PRIMARY diff recorded vs THRESHOLD 0.20 BONFERRONI 2 (hold / not-hold, no gated claim)
- [ ] Fail-open recorded (no gated claim)
- [ ] Evidence written only to `allow` paths

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; within caps; outcome recorded; no file outside `files` touched; no sweeps/spend; frozen-then-once honored.
- Fail: cap breach (>5 epochs, wrong seeds, seed 6 used, >15m, repeat run), sweep/spend, file outside `files` touched, peeking before freeze, threshold/gate change, or gated advantage claim.

Authorization: user 2026-11-16 "keep on continue" narrowed to fail-open frozen-then-once confirmatory magnitude only (fresh [11,33,55], forbidden 6, held-out XOR(1,3,1,2)+EQ(2,1,1), model 64/5/1e-2, PRIMARY diff, THRESHOLD 0.20, BONFERRONI 2, caps <=5 epochs, 10-15m, local-only, run-once, no peeking before freeze).
