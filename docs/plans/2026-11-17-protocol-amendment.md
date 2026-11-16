---
spec: equality-actual-v2-R1-R6-R3-amended
status: approved
approved_by: mission-autonomous
approved_at: 2026-11-16T03:55:35Z
files:
  - research/protocols/equality-actual-v2.json
  - scripts/run_actual_experiment.py
  - tests/test_actual_experiment.py
allow:
  - docs/plans/2026-11-17-protocol-amendment-progress.md
  - docs/plans/2026-11-17-protocol-amendment-evidence.json
Authorization: mission Phase5 autonomous — protocol amendment only (reversible disjoint-sampling fix, v1 frozen, local-only, scope-locked, tiny CPU, no secrets, no push)
---

# Plan — Protocol Amendment (V1 → V2 disjoint-sampling fix)

Branch: `research/audit-1587497` @ `a3addab`.

Mission authorization transcribed 2026-11-16: autonomous Phase5.
Source: planner handoff (draft); scope transcribed to `files`/`allow` above.
Scope-locked: writes only to `files` above; evidence only to `allow` above. No secrets, no push.

Context: Phase5 smoke BLOCKED fail-closed at R3 — locked generator draws 250 i.i.d. rows with replacement from 4^4=256 input space, so R3 zero-overlap tolerance-0 is unsatisfiable on all frozen seeds (101: 24 rows / 53.3%, 202: 26 / 57.8%, 303: 28 / 65.1%). Spec-gate block escalated, not absorbed. V1 stays frozen; this amendment adds V2 with an implementation-only R3 fix (disjoint sampling in runner glue).

## Goal

Ship locked V2 protocol (R1–R6 carried, R3 implementation amended to disjoint sampling) plus retargeted runner/suite, so the tiny-CPU run proceeds end-to-end (protocol → runner → artifacts → suite → evidence) with zero-overlap satisfiable — no hand-made results, no unpaired comparison.

```mermaid
flowchart LR
  V1[research/protocols/equality-actual-v1.json frozen] --> V2[research/protocols/equality-actual-v2.json locked]
  V2 --> Runner[scripts/run_actual_experiment.py disjoint-sampling]
  Runner --> Artifacts[raw artifacts only]
  Artifacts --> Suite[tests/test_actual_experiment.py retargeted]
  Suite --> Evidence[progress + evidence only]
```

## Arch

- Protocol layer: `research/protocols/equality-actual-v2.json` (new locked spec — copies V1 keys verbatim except R3 implementation note + disjoint-sampling directive; consumed verbatim by runner, never edited at runtime). V1 untouched/frozen.
- Runner layer: `scripts/run_actual_experiment.py` (thin glue; keeps `main(argv)->int` + pure `run(protocol)->artifacts` with I/O only at CLI boundary; adds dedup/disjoint-sampling loop so 200/50 splits are zero-overlap by construction; fail-closed exit map, no network, no mutation of protocol).
- Suite layer: `tests/test_actual_experiment.py` (retargeted to V2; asserts parity, disjoint splits, determinism, fail-closed paths).
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- python 3.12 venv (`.venv/bin/python`), numpy CPU only, stdlib (`argparse`, `pathlib`, `json`) for runner/protocol.
- `pytest` for `tests/test_actual_experiment.py` (`-q`).
- Tiny CPU shapes only (tiny seq/batch/d_model, fixed seeds `[101,202,303]`, N small); local-only, no GPU, no network, no paid APIs.

## Spec

- Spec: `equality-actual-v2-R1-R6-R3-amended` — R1–R6 carried from V1; only R3 implementation amended (intent unchanged: unique-inputs, zero-overlap, tolerance-0). All fail-closed (any violation exits non-zero).
- R1 task: unchanged from V1 (fixed equality task as locked; generator name, seq_len 4, vocab 4, n_actions 2, n_rules 1, n_train 200, n_test 50); task mismatch → non-zero exit.
- R2 parity: unchanged (capacity-matched parity only, same seeds/cases, paired comparison; unpaired refused; parity keys exact).
- R3 splits (AMENDED implementation only): locked sizes 200/50 + unique-inputs/zero-overlap/tolerance-0 retained; sampling implementation changes from with-replacement i.i.d. to disjoint without-replacement (dedup loop partitions 250 unique rows from 256-space, then 200/50 split); split violation (leakage, wrong sizes, unpaired seeds) → non-zero exit.
- R4 models: unchanged (locked pair classical vs hybrid tiny CPU; substitution → non-zero exit).
- R5 runner: unchanged signatures/exit-map (`main(argv)->int`, pure `run(protocol)->artifacts`, I/O only at CLI boundary; `0=ok, 1=run-failed, 2=invalid/usage`); artifacts deterministic on fixed-seed rerun; stdout/stderr captured per run, surfaced on non-zero. Runner consumes V2 verbatim.
- R6 caps: unchanged (bounded tiny-CPU run only, local-only, no sweeps, no spend, no GPU/network; cap breach refused; evidence only to `allow`).
- Out of scope: v1 edits, generator-function edits, model/code changes beyond runner glue, sweeps, training beyond tiny locked run, secrets, push/PR, confirmatory re-runs.

## Constraints

- Branch `research/audit-1587497`, local-only, reversible (V2 additive; V1 + generator untouched).
- Scope locked to `files` (V2 protocol + runner + suite) and `allow` (evidence); v1 protocol frozen (read-only reference); generator function untouched (fix lives in runner glue only); `research/*`, `scripts/*`, `tests/*` otherwise untouched; no secrets.
- No push, no PR, no history rewrite, no new experiments beyond the locked tiny run.
- Time cap 3m for this plan-writing step; runner execution bounded tiny CPU (no sweeps, no spend).

## Lean

- Reuse-first: reuse existing analyzer path, `argparse` + `pathlib`/`json` + `numpy`; no new modules, no refactors, no perf tuning, no API changes.
- Minimum code that passes the suite; V2 protocol is data-only (copied keys), runner change is a thin-glue dedup loop only.

## Review Focus

- HIGH-1: protocol-locked — runner consumes `equality-actual-v2.json` verbatim; V1 byte-identical (frozen); no embedded constants steering outcome; malformed protocol/splits/nonfinite inputs exit non-zero, never silent `0`.
- HIGH-2: parity + splits honored (R2–R3 paired only, exact pairing/split keys; disjoint sampling proves zero-overlap on all 3 frozen seeds; unpaired/leakage refused; deterministic fixed-seed rerun reproduces artifacts).
- HIGH-3: scope-locked — no file outside `files` touched; V1 + generator untouched; evidence only to `allow`; no secrets/push; analyzer-consumed (no hand-made artifacts).
- HIGH-4: caps enforced (tiny CPU, bounded runtime, local-only, no sweeps/spend; signatures `main(argv)->int` + exit-map honored).

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Locked V2 protocol | R1–R4 task/parity/splits/models, R6 caps (R3 amended) | `research/protocols/equality-actual-v2.json` | data-only locked V2 (copied task/parity/models/caps keys, amended R3 disjoint-sampling note; no code, no constants steering; V1 frozen) | `.venv/bin/python -m json.tool research/protocols/equality-actual-v2.json > /dev/null && git status --short research/protocols/equality-actual-v1.json | grep -c "^"` |
| 2 | Runner disjoint-sampling + suite retarget | R1–R6 protocol/runner/artifacts | `scripts/run_actual_experiment.py`, `tests/test_actual_experiment.py` | thin-glue dedup loop (disjoint 200/50 by construction, signatures + exit-map kept) + retargeted fail-closed suite (V2 verbatim, parity/disjoint/determinism/refusal cases) | `.venv/bin/python scripts/run_actual_experiment.py --help && ACTUAL_CORRECTNESS_GREEN=1 .venv/bin/python -m pytest tests/test_actual_experiment.py -q` |
| 3 | Evidence + caps verification | R5–R6 artifacts+caps, evidence-only | `docs/plans/2026-11-17-protocol-amendment-progress.md`, `docs/plans/2026-11-17-protocol-amendment-evidence.json` | outcome recorded, caps honored, evidence only to `allow` | `.venv/bin/python -m pytest tests/test_actual_experiment.py -q` |

## Per-task notes

- 1: copy keys `task`, `parity`, `models`, `runner`, `caps`, `seeds` verbatim from V1; only `splits` gains disjoint-sampling implementation note (sizes 200/50, tolerance-0 unchanged); Verify checks strict JSON parse via `json.tool` plus V1 untouched (`git status` clean on v1 path).
- 2: dedup loop in runner glue only (sample-without-replacement / partition-then-split; generator function untouched); retarget suite `PROTOCOL` constant to V2 (keep V1-frozen assertion); signatures `main(argv: list[str]) -> int`, pure `run(protocol: dict) -> artifacts` (no I/O inside; I/O only at CLI boundary); exit-map `0=ok, 1=run-failed, 2=invalid/usage`; cases — (i) V2 consumed verbatim, (ii) parity/splits exact keys else exit 2, (iii) zero-overlap on 101/202/303 + deterministic + analyzer-consumable, (iv) malformed/nonfinite paths exit != 0; CLI `--help` + `-q`.
- 3: pass only if Verify exit 0, R1–R6 covered, caps (tiny CPU, local-only, no sweeps/spend) honored, writes only to `allow` paths, no secrets/push, confirmatory locks untouched, V1 still frozen.

## Coverage checklist

- [ ] R1 task (locked equality task executed verbatim, copied V1→V2)
- [ ] R2 parity (capacity-matched, paired only, unpaired refused)
- [ ] R3 splits amended (disjoint sampling, locked 200/50, no leakage, sizes/keys exact, satisfiable on all frozen seeds)
- [ ] R4 models (locked pair, tiny CPU, no substitution)
- [ ] R5 runner (signatures + exit-map, deterministic artifacts, analyzer-consumed, V2 verbatim)
- [ ] R6 caps (bounded tiny CPU, local-only, no sweeps/spend) + evidence only to `allow` + V1 frozen

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; R1–R6 covered; protocol-locked (V2) + paired + disjoint + deterministic honored; V1 + generator untouched; no file outside `files` touched; evidence only to `allow`; within caps; no secrets/push; confirmatory untouched.
- Fail: fail-open (0 on failure), embedded constants, hand-made artifacts, unpaired comparison, split leakage/overlap, V1 or generator edited, file outside `files` touched, cap breach, sweep/spend, secret/push, or confirmatory re-invoked.

Authorization: mission Phase5 autonomous — protocol amendment only (reversible disjoint-sampling fix, v1 frozen, local-only, scope-locked to `files`/`allow`, tiny CPU, no secrets, no push).
