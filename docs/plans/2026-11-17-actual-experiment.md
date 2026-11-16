---
spec: equality-actual-v1-R1-R6
status: approved
approved_by: mission-autonomous
approved_at: 2026-11-16T03:46:59Z
files:
  - research/protocols/equality-actual-v1.json
  - scripts/run_actual_experiment.py
  - tests/test_actual_experiment.py
allow:
  - docs/plans/2026-11-17-actual-experiment-progress.md
  - docs/plans/2026-11-17-actual-experiment-evidence.json
Authorization: mission Phase5 autonomous — actual experiment only (local-only, scope-locked, tiny CPU, no secrets, no push)
---

# Plan — Actual Experiment

Branch: `research/audit-1587497` @ `a3addab`.

Mission authorization transcribed 2026-11-16: autonomous Phase5.
Source: planner handoff (draft); scope transcribed to `files`/`allow` above.
Scope-locked: writes only to `files` above; evidence only to `allow` above. No secrets, no push.

## Goal

Run the locked actual equality experiment end-to-end (protocol → runner → artifacts → suite → evidence) on tiny CPU with fail-closed guards, so any claim rests on runner-produced artifacts consumed by the analyzer path — no hand-made results, no unpaired comparison.

```mermaid
flowchart LR
  Proto[research/protocols/equality-actual-v1.json locked] --> Runner[scripts/run_actual_experiment.py]
  Runner --> Artifacts[raw artifacts only]
  Artifacts --> Suite[tests/test_actual_experiment.py]
  Suite --> Evidence[progress + evidence only]
```

## Arch

- Protocol layer: `research/protocols/equality-actual-v1.json` (locked spec — task, parity, splits, models, runner, caps; R1–R6; consumed verbatim by runner, never edited at runtime).
- Runner layer: `scripts/run_actual_experiment.py` (thin glue over protocol; parses protocol, runs tiny-CPU experiment, writes raw artifacts only; fail-closed exit map, no network, no mutation of protocol).
- Suite layer: `tests/test_actual_experiment.py` (protocol/runner/artifact cases; asserts parity, splits, determinism, fail-closed paths).
- Analyzer-consumed layer: runner artifacts are the only inputs the analyzer path may read (raw-only, paired); suite guards that no embedded constants or hand-made artifacts pass.
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- python 3.12 venv (`.venv/bin/python`), numpy CPU only, stdlib (`argparse`, `pathlib`, `json`) for runner/protocol.
- `pytest` for `tests/test_actual_experiment.py` (`-q`).
- Tiny CPU shapes only (tiny seq/batch/d_model, fixed seeds, N small); local-only, no GPU, no network, no paid APIs.

## Spec

- Spec: `equality-actual-v1-R1-R6` — locked in `research/protocols/equality-actual-v1.json`. R1–R6 below are fail-closed (any violation exits non-zero).
- R1 task: fixed equality task as locked in protocol (inputs, labels, metric); runner executes exactly the locked task; task mismatch → non-zero exit.
- R2 parity: capacity-matched parity only (same seeds/cases, paired comparison); unpaired comparison refused; parity keys exact.
- R3 splits: locked splits only (train/eval keys and sizes per protocol); split violation (leakage, wrong sizes, unpaired seeds) → non-zero exit.
- R4 models: locked model pair only (classical vs hybrid config per protocol, tiny CPU); model/config substitution → non-zero exit.
- R5 runner: runner consumes protocol verbatim (`main(argv)->int`, pure `run(protocol)->artifacts` with I/O only at CLI boundary); exit-map `0=ok, 1=run-failed, 2=invalid/usage` (malformed protocol, malformed splits, nonfinite values → 2); artifacts deterministic on fixed-seed rerun; stdout/stderr captured per run, surfaced on non-zero.
- R6 caps: bounded tiny-CPU run only (local-only, no sweeps, no spend, no GPU/network); cap breach refused; evidence transcribed only to `allow`.
- Out of scope: model/code changes beyond runner glue, protocol edits at runtime, sweeps, training runs beyond tiny locked run, secrets, push/PR, confirmatory re-runs.

## Constraints

- Branch `research/audit-1587497`, local-only, reversible.
- Scope locked to `files` (protocol + runner + suite) and `allow` (evidence); `research/*`, `scripts/*`, `tests/*` otherwise untouched; no secrets.
- No push, no PR, no history rewrite, no new experiments beyond the locked tiny run.
- Time cap 3m for this plan-writing step; runner execution bounded tiny CPU (no sweeps, no spend).

## Lean

- Reuse-first: reuse existing analyzer path, `argparse` + `pathlib`/`json` + `numpy`; no new modules, no refactors, no perf tuning, no API changes.
- Minimum code that passes the suite; protocol is data-only, runner is thin glue.

## Review Focus

- HIGH-1: protocol-locked — runner consumes `equality-actual-v1.json` verbatim; no embedded constants steering outcome; malformed protocol/splits/nonfinite inputs exit non-zero, never silent `0`.
- HIGH-2: parity + splits honored (R2–R3 paired only, exact pairing/split keys; unpaired/leakage refused; deterministic fixed-seed rerun reproduces artifacts).
- HIGH-3: scope-locked — no file outside `files` touched; evidence only to `allow`; no secrets/push; analyzer-consumed (no hand-made artifacts).
- HIGH-4: caps enforced (tiny CPU, bounded runtime, local-only, no sweeps/spend; signatures `main(argv)->int` + exit-map honored).

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Locked protocol | R1–R4 task/parity/splits/models, R6 caps | `research/protocols/equality-actual-v1.json` | data-only locked protocol (task, parity keys, splits, model pair, caps; no code, no constants steering) | `.venv/bin/python -m json.tool research/protocols/equality-actual-v1.json > /dev/null` |
| 2 | Runner + experiment suite | R1–R6 protocol/runner/artifacts | `scripts/run_actual_experiment.py`, `tests/test_actual_experiment.py` | thin runner glue (signatures + exit-map) + fail-closed suite (protocol/parity/splits/determinism/refusal cases) | `.venv/bin/python -m pytest tests/test_actual_experiment.py -q` |
| 3 | evidence + caps verification | R5–R6 artifacts+caps, evidence-only | `docs/plans/2026-11-17-actual-experiment-progress.md`, `docs/plans/2026-11-17-actual-experiment-evidence.json` | outcome recorded, caps honored, evidence only to `allow` | `ls -l docs/plans/2026-11-17-actual-experiment-progress.md docs/plans/2026-11-17-actual-experiment-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-actual-experiment-evidence.json > /dev/null` |

## Per-task notes

- 1: JSON keys `task`, `parity`, `splits`, `models`, `runner`, `caps` (R1–R6); Verify checks strict JSON parse via `json.tool`; any trailing-comma/duplicate-key/missing-key fails closed.
- 2: signatures `main(argv: list[str]) -> int`, pure `run(protocol: dict) -> artifacts` (no I/O inside; I/O only at CLI boundary); exit-map `0=ok, 1=run-failed, 2=invalid/usage`; cases — (i) protocol consumed verbatim, (ii) parity/splits exact keys else exit 2, (iii) artifacts deterministic + analyzer-consumable, (iv) malformed/nonfinite paths exit != 0; `-q`.
- 3: pass only if Verify exit 0, R1–R6 covered, caps (tiny CPU, local-only, no sweeps/spend) honored, writes only to `allow` paths, no secrets/push, confirmatory locks untouched.

## Coverage checklist

- [ ] R1 task (locked equality task executed verbatim)
- [ ] R2 parity (capacity-matched, paired only, unpaired refused)
- [ ] R3 splits (locked splits, no leakage, sizes/keys exact)
- [ ] R4 models (locked pair, tiny CPU, no substitution)
- [ ] R5 runner (signatures + exit-map, deterministic artifacts, analyzer-consumed)
- [ ] R6 caps (bounded tiny CPU, local-only, no sweeps/spend) + evidence only to `allow`

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; R1–R6 covered; protocol-locked + paired + deterministic honored; no file outside `files` touched; evidence only to `allow`; within caps; no secrets/push; confirmatory untouched.
- Fail: fail-open (0 on failure), embedded constants, hand-made artifacts, unpaired comparison, split leakage, file outside `files` touched, cap breach, sweep/spend, secret/push, or confirmatory re-invoked.

Authorization: mission Phase5 autonomous — actual experiment only (local-only, scope-locked to `files`/`allow`, tiny CPU, no secrets, no push).
