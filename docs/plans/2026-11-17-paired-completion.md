---
spec: equality-actual-v2-R1-R6-R3-amended
status: approved
approved_by: mission-autonomous
approved_at: 2026-11-16T04:05:00Z
files:
  - scripts/run_actual_experiment.py
  - research/artifacts/equality-actual-v2/run2/**
allow:
  - docs/plans/2026-11-17-paired-completion-progress.md
  - docs/plans/2026-11-17-paired-completion-evidence.json
Authorization: mission Phase5 autonomous — paired completion only (local-only, scope-locked, tiny CPU, no secrets, no training beyond tiny smoke, no push)
---

# Plan — Paired Completion

Branch: `research/audit-1587497` @ `a3addab`.

Mission authorization transcribed 2026-11-16: autonomous Phase5 paired completion.
Source: planner handoff (draft); scope transcribed to `files`/`allow` above.
Scope-locked: writes only to `files` above (runner glue + `run2/**` raw only); evidence only to `allow` above. No secrets, no push.

## Goal

Complete the paired `run2` for locked protocol `equality-actual-v2` end-to-end (protocol → runner → raw → analyzer → report) on tiny CPU with fail-closed guards, so any claim rests on runner-produced `run2` raw artifacts consumed paired-only by the analyzer — no hand-made results, no unpaired comparison.

```mermaid
flowchart LR
  Proto[protocol v2 locked] --> Runner[scripts/run_actual_experiment.py]
  Runner --> Raw[research/artifacts/equality-actual-v2/run2 raw only]
  Raw --> Analyzer[analyzer CLI paired-only]
  Analyzer --> Report[progress + evidence only]
```

## Arch

- Touched: `scripts/run_actual_experiment.py` (thin glue only; protocol-verbatim run, shared-rng paired seeds, tiny-smoke training only; `main(argv)->int`, pure `run(protocol)->artifacts`).
- Produced: `research/artifacts/equality-actual-v2/run2/**` (raw only: per-seed `predictions.json`/`targets.json`/`metrics.json`/`status.json` + `run.json` with `config_hash`/`run_id`; no hand-made files).
- Consumed: locked protocol `research/protocols/equality-actual-v2.json` read-only verbatim (R1–R6, R3 amended disjoint-without-replacement); existing suite/analyzer scripts read-only (never edited here).
- Interfaces: runner `main(argv: list[str]) -> int`, `run(protocol: dict) -> artifacts` (I/O only at CLI boundary); exit-map `0=ok, 1=run-failed, 2=invalid/usage`; analyzer CLI consumes `run2/**` raw-only paired, writes report transcribed to `allow`.
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- python 3.12 venv (`.venv/bin/python`), numpy CPU only, stdlib (`argparse`, `pathlib`, `json`) for runner/protocol.
- `scipy` + `numpy` for analyzer paired stats only (paired t, CI/p via scipy; no training libs).
- `pytest` for guard suite (`-q`, read-only here).
- Tiny CPU shapes only (per protocol v2: seq_len 4, vocab 4, n_train 200 / n_test 50, frozen seeds 101/202/303); local-only, no GPU, no network, no paid APIs.

## Spec

- Spec: `equality-actual-v2-R1-R6-R3-amended` — locked in `research/protocols/equality-actual-v2.json` (frozen 2026-11-16, R3 amended 2026-11-17). R1–R6 below are fail-closed (any violation exits non-zero).
- R1 task: fixed equality task as locked (`generate_equality_sequence_decision`, seq_len 4, vocab 4, n_train 200, n_test 50, last-position classification); runner executes exactly the locked task; task mismatch → non-zero exit.
- R2 parity: capacity-matched parity only (same inputs per seed, permitted-only context, token-local quantum path); paired comparison only; unpaired comparison refused; parity keys exact.
- R3 splits: locked splits only (unique_inputs, zero_overlap tolerance-0, train 200 / test 50, disjoint-without-replacement 250-of-256 in runner glue); split violation (leakage, wrong sizes, overlap) → non-zero exit.
- R4 models: locked model pair only (A classical `ClassicalDecisionMLP` tiny, B hybrid `HybridQuantumLLM` d16/1-layer/2-head/6q-1layer, C controls positive/negative); substitution → non-zero exit.
- R5 runner: runner consumes protocol verbatim (`main(argv)->int`, pure `run(protocol)->artifacts`); exit-map `0=ok, 1=run-failed, 2=invalid/usage` (malformed protocol/splits, nonfinite values → 2); artifacts deterministic on fixed-seed rerun; `config_hash` + `run_id` recorded per run; stdout/stderr captured per run, surfaced on non-zero.
- R6 caps: bounded tiny-CPU run only (`run2` run-once per frozen seed, smoke budget <5m, local-only, no sweeps, no spend, no GPU/network); cap breach refused; evidence transcribed only to `allow`.
- Out of scope: model/code changes beyond runner glue, protocol edits at runtime, sweeps, training beyond tiny locked smoke, secrets, push/PR, confirmatory re-runs.

## Constraints

- Branch `research/audit-1587497` @ `a3addab`, local-only, reversible.
- Scope locked to `files` (runner glue + `run2/**` raw) and `allow` (evidence); `research/protocols/*`, `tests/*`, `scripts/analyze_results.py` consumed read-only, never edited; `research/*`, `scripts/*` otherwise untouched; no secrets.
- No push, no PR, no history rewrite, no new experiments beyond the locked `run2` tiny run + analyzer read-only report.
- Time cap 3m for this plan-writing step; `run2` execution bounded tiny CPU (smoke <5m, run-once per seed, no sweeps/spend).

## Lean

- Glue-only: reuse `argparse` + `pathlib`/`json` + `numpy`, existing analyzer path; no new modules, no refactors, no perf tuning, no API changes.
- Minimum code that completes `run2` raw + paired report; no scope growth.

## Review Focus

- HIGH-1: protocol-locked + paired-only — runner consumes v2 verbatim (`config_hash` pinned); shared-rng paired seeds (same inputs per seed); unpaired/hand-made/embedded-constant artifacts refused with non-zero exit, never silent `0`.
- HIGH-2: runner signatures + exit-map honored (`main(argv)->int`, pure `run`; `0/1/2` map; `run_id=run2` recorded; deterministic fixed-seed rerun reproduces `run2` bytes; capture on non-zero; tiny-smoke training only).
- HIGH-3: scope-locked — no file outside `files` touched; evidence only to `allow`; local-only, no sweeps/spend, no secrets/training-beyond-smoke/push; confirmatory untouched.

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Shared-rng paired guard (pytest, read-only) | R1–R4 task/parity/splits/models | `scripts/run_actual_experiment.py`, `research/artifacts/equality-actual-v2/run2/**` | guard holds: locked task/parity/split/model keys, shared-rng paired inputs, no unpaired pass | `.venv/bin/python -m pytest tests/test_actual_experiment.py -q` |
| 2 | Runner CLI run2 raw completion | R5 runner, R6 caps | `scripts/run_actual_experiment.py`, `research/artifacts/equality-actual-v2/run2/**` | thin glue run_id=run2, config_hash pinned, raw-only run2 artifacts, deterministic rerun | `.venv/bin/python -m py_compile scripts/run_actual_experiment.py && .venv/bin/python scripts/run_actual_experiment.py --help` |
| 3 | Analyzer CLI paired report over run2 | R2 paired, R5 analyzer-consumed | `research/artifacts/equality-actual-v2/run2/**`, `docs/plans/2026-11-17-paired-completion-progress.md`, `docs/plans/2026-11-17-paired-completion-evidence.json` | analyzer reads run2 raw-only paired, report transcribed to allow, no hand-made results | `.venv/bin/python scripts/analyze_results.py --help` |

## Per-task notes

- 1: `config_hash` pinned to frozen v2 (R3-amended); `run_id=run2`; shared rng per seed across A/B (same inputs, exact pairing keys); training is tiny smoke only on locked pair (no full training, no tuning); pytest is read-only guard here (no writes outside `files`); invalid/unpaired/nonfinite paths assert exit != 0.
- 2: signatures `main(argv: list[str]) -> int`, pure `run(protocol: dict) -> artifacts` (no I/O inside; I/O only at CLI boundary); exit-map `0=ok, 1=run-failed, 2=invalid/usage`; `run_id=run2` exact, `config_hash` recorded in `run.json`; shared-rng seeds 101/202/303 run-once; deterministic rerun reproduces `run2` bytes; Verify checks compile + `--help` signatures.
- 3: analyzer consumes `run2/**` raw only (predictions/targets paired per seed; unpaired refused); paired stats via scipy/numpy with exact pairing keys; report (per-seed + summary) transcribed only to `allow` progress/evidence; no training, no mutation of `run2` raw; Verify checks analyzer CLI `--help` (paired-only path).

## Coverage checklist

- [ ] R1 task (locked equality task executed verbatim, config_hash pinned)
- [ ] R2 parity (same inputs/shared-rng, paired only, unpaired refused)
- [ ] R3 splits (disjoint-without-replacement, 200/50, zero-overlap tolerance-0)
- [ ] R4 models (locked A/B/C pair, tiny CPU, no substitution; training = tiny smoke only)
- [ ] R5 runner (signatures + exit-map, run_id=run2, deterministic raw, analyzer-consumed)
- [ ] R6 caps (bounded tiny CPU <5m, local-only, no sweeps/spend) + evidence only to `allow`

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; R1–R6 covered; protocol-locked + shared-rng paired + deterministic honored; `run_id=run2` + `config_hash` recorded; no file outside `files` touched; evidence only to `allow`; within caps; no secrets/training-beyond-smoke/push; confirmatory untouched.
- Fail: fail-open (0 on failure), embedded constants, hand-made artifacts, unpaired comparison, split leakage, config_hash/run_id drift, file outside `files` touched, cap breach, sweep/spend, secret/training-beyond-smoke/push, or confirmatory re-invoked.

Authorization: mission Phase5 autonomous — paired completion only (local-only, scope-locked to `files`/`allow`, tiny CPU, no secrets, no training beyond tiny smoke, no push).
