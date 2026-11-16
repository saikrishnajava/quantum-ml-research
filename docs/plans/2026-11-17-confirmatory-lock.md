---
spec: N/A-fail-open-frozen-inline
status: approved
approved_by: user
approved_at: 2026-11-16T02:27:28Z
files:
  - tests/test_confirmatory.py
allow:
  - docs/plans/2026-11-17-confirmatory-lock-progress.md
  - docs/plans/2026-11-17-confirmatory-lock-evidence.json
Authorization: user "next big win", frozen-then-once, no peeking before freeze
---

# Plan — Confirmatory Lock

Branch: `research/audit-1587497`.

User approval transcribed 2026-11-16: "next big win".
No gate fail-open. Confirmatory frozen-then-once only; no peeking before freeze.

## Goal

Run one frozen confirmatory check via `tests/test_confirmatory.py` to record whether the frozen F-1/F-2/F-3 claims hold under caps. No advantage claim; record outcome only.

```mermaid
flowchart LR
  Spec[Spec frozen inline F-1/F-2/F-3] --> Run[Confirmatory run-once <=5 epochs <=3 seeds]
  Run --> Test[tests/test_confirmatory.py checks]
  Test --> Evidence[progress + evidence only]
```

## Arch

- Single-file: `tests/test_confirmatory.py` (frozen checks only, no sweeps).
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- python 3.12 venv (`.venv/bin/python`)
- pytest
- numpy / PennyLane CPU only (local-only)

## Spec

- Spec: N/A-fail-open-frozen-inline — explicitly no approved spec file. Frozen inline claims below are record-only, fail-open (no gate).
- F-1 (frozen): confirmatory run completes within caps (<=5 epochs, <=3 seeds, 10-15m, local-only, run-once).
- F-2 (frozen): outcome recorded as observed (hold / not-hold) with no gated advantage claim.
- F-3 (frozen): evidence written only to `allow` paths; no file outside `files` touched.
- No fail-closed gate is wired; outcomes are recorded, not gated.
- Out of scope: code changes beyond frozen confirmatory run, secrets, push/PR.

## Constraints

- Time cap 10-15m total; reversible.
- <=5 epochs per run; <=3 seeds per run (reuse 42,99,137); run-once.
- Local-only CPU; no GPU, no paid APIs, no sweeps, no spend.
- Frozen-then-once; no peeking before freeze.
- Scope locked to `files` list above; evidence only to `allow` list above.

## Lean

- Minimum single-file rerun that answers confirmatory check; no refactors, no new modules.
- Reuse existing frozen checks and configs; no perf tuning, no API changes.

## Review Focus

- HIGH-1: No approved spec file — must stay N/A fail-open frozen-inline, no gated claim.
- HIGH-2: Caps enforced (<=3 seeds, <=5 epochs, 10-15m, local-only, run-once).
- HIGH-3: No file outside `files` touched; evidence only to `allow`.
- HIGH-4: Frozen-then-once honored; no peeking before freeze.

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Confirmatory frozen run-once | F-1 frozen, caps-only | `tests/test_confirmatory.py` | <=5 epochs <=3 seeds (42,99,137) local run-once, outcome observed | `.venv/bin/python -m py_compile tests/test_confirmatory.py && grep -n "F-1" tests/test_confirmatory.py` |
| 2 | Confirmatory frozen checks | F-2 frozen, record-only | `tests/test_confirmatory.py` | frozen assertions, fail-open record, no gate | `.venv/bin/python -m pytest tests/test_confirmatory.py -q` |
| 3 | evidence + caps verification | F-3 frozen, evidence-only | `docs/plans/2026-11-17-confirmatory-lock-progress.md`, `docs/plans/2026-11-17-confirmatory-lock-evidence.json` | outcome recorded, caps honored, no sweep/spend | `ls -l docs/plans/2026-11-17-confirmatory-lock-progress.md docs/plans/2026-11-17-confirmatory-lock-evidence.json` |

## Per-task notes

- 1: constants 42,99,137 only; <=5 epochs; run-once; if frozen outcome does not hold, record only, no gate.
- 2: checks are record-only fail-open; no `ValueError` gate required under N/A-fail-open-frozen-inline.
- 3: pass only if Verify exit 0, caps (10-15m, <=5 epochs, <=3 seeds, local-only, run-once) honored, evidence written only to `allow` paths.

## Coverage checklist

- [ ] Confirmatory frozen run-once (<=5 epochs, <=3 seeds 42,99,137, local-only)
- [ ] Outcome recorded (hold / not-hold per F-1/F-2/F-3, no gated claim)
- [ ] Fail-open recorded (no gated claim)
- [ ] Evidence written only to `allow` paths

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; within caps; outcome recorded; no file outside `files` touched; no sweeps/spend; frozen-then-once honored.
- Fail: cap breach (>5 epochs, >3 seeds, >15m, repeat run), sweep/spend, file outside `files` touched, peeking before freeze, or gated advantage claim.

Authorization: user 2026-11-16 "next big win" narrowed to fail-open frozen-then-once confirmatory only (caps <=3 seeds, <=5 epochs, 10-15m, local-only, run-once, no peeking before freeze).
