---
spec: equality-actual-v2-R1-R6-R3-amended
status: approved
approved_by: mission-autonomous
approved_at: 2026-11-16T04:16:25Z
files:
  - docs/verify-actual.sh
  - docs/analyze-only.sh
allow:
  - docs/plans/2026-11-17-actual-repro-progress.md
  - docs/plans/2026-11-17-actual-repro-evidence.json
Authorization: mission Phase6 autonomous — actual repro only (local-only, scope-locked, tiny CPU, no secrets, no push)
---

# Plan — Actual Repro

Branch: `research/audit-1587497` @ `a3addab`.

Mission authorization transcribed 2026-11-16: autonomous Phase6.
Source: planner handoff (draft); scope transcribed to `files`/`allow` above.
Scope-locked: writes only to `files` above; evidence only to `allow` above. No secrets, no push.

## Goal

Reproduce authoritative `run4` for locked protocol `equality-actual-v2` end-to-end (preflight → runner → analyzer → gate) on tiny CPU with fail-closed guards, so any claim rests on runner-produced raw + analyzer paired report — no hand-made results, no unpaired comparison.

```mermaid
flowchart LR
  Pre[preflight protocol+run4 gate] --> Run[runner repro run4 raw]
  Run --> Ana[analyzer paired-only]
  Ana --> Gate[gate verdict + evidence]
```

## Arch

- Gate layer: `docs/verify-actual.sh` (preflight + fail-closed gate; protocol frozen check, `config_hash` pinned, overlap 0, run-once per seed).
- Runner layer: `scripts/run_actual_experiment.py` consumed read-only verbatim via gate (thin glue, `main(argv)->int`, pure `run(protocol)->artifacts`; exit-map `0/1/2`; deterministic fixed-seed rerun).
- Analyzer layer: `scripts/analyze_results.py` consumed read-only paired-only (scipy/numpy paired t, exact pairing keys; unpaired refused).
- Analysis-only layer: `docs/analyze-only.sh` (analyzer CLI over `run4/raw.json` only; no training, no mutation of raw).
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- python 3.12 venv (`.venv/bin/python`), numpy CPU only, stdlib (`argparse`, `pathlib`, `json`) for runner/protocol; `scipy` + `numpy` for analyzer paired stats only.
- `bash` for `docs/verify-actual.sh` / `docs/analyze-only.sh`.
- `pytest` for guard suite (`-q`, read-only here).
- Tiny CPU shapes only (per protocol v2: seq_len 4, vocab 4, n_train 200 / n_test 50, frozen seeds 101/202/303); local-only, no GPU, no network, no paid APIs.

## Spec

- Spec: `equality-actual-v2-R1-R6-R3-amended` — locked in `research/protocols/equality-actual-v2.json` (frozen 2026-11-16, R3 amended 2026-11-17). R1–R6 below are fail-closed (any violation exits non-zero).
- R1 task: fixed equality task as locked (`generate_equality_sequence_decision`, seq_len 4, vocab 4, n_train 200, n_test 50, last-position classification); runner executes exactly the locked task; task mismatch → non-zero exit.
- R2 parity: capacity-matched parity only (same inputs per seed, permitted-only context, token-local quantum path); paired comparison only; unpaired comparison refused; parity keys exact.
- R3 splits: locked splits only (unique_inputs, zero_overlap tolerance-0, train 200 / test 50, disjoint-without-replacement 250-of-256 in runner glue); split violation (leakage, wrong sizes, overlap) → non-zero exit.
- R4 models: locked model pair only (A classical `ClassicalDecisionMLP` tiny, B hybrid `HybridQuantumLLM` d16/1-layer/2-head/6q-1layer, C controls positive/negative); substitution → non-zero exit.
- R5 runner: runner consumes protocol verbatim (`main(argv: list[str]) -> int`, pure `run(protocol: dict) -> artifacts`); exit-map `0=ok, 1=run-failed, 2=invalid/usage` (malformed protocol/splits, nonfinite values → 2); artifacts deterministic on fixed-seed rerun; `config_hash` + `run_id` recorded per run; stdout/stderr captured per run, surfaced on non-zero.
- R6 caps: bounded tiny-CPU repro only (`run4` run-once per frozen seed, smoke budget <5m, local-only, no sweeps, no spend, no GPU/network); cap breach refused; evidence transcribed only to `allow`.
- Authoritative `run4` numbers (must-reproduce, tolerances in per-task notes): `config_hash=e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54`, seeds `[101,202,303]`, `run_id=run4`, `run_ids` `run4:baseline/treatment:seed-{101,202,303}` + status `run4:A/B:seed-{101,202,303}` (6/6), per-seed `101: 0.78/0.76 diff -0.02`, `202: 0.24/0.24 diff 0.0`, `303: 0.60/0.26 diff -0.34`, `mean_diff=-0.12`, `p=0.3897428467412706`, `CI=[-0.5939432689913657, 0.3539432689913657]`, `method=t (scipy, 95%)`, `n_pairs=3`, `multiplicity=none (exploratory, m_comparisons=1)`, `positive_acc=1.0`, `overlap=0`, warning `small-n: n_pairs=3 < 5`.
- Out of scope: model/code changes beyond gate/analysis-only glue, protocol edits at runtime, sweeps, training beyond tiny locked repro, secrets, push/PR, confirmatory re-runs.

## Constraints

- Branch `research/audit-1587497` @ `a3addab`, local-only, reversible.
- Scope locked to `files` (gate + analysis-only) and `allow` (evidence); `research/protocols/*`, `scripts/*`, `research/artifacts/*` consumed read-only, never edited; `research/*`, `scripts/*`, `tests/*` otherwise untouched; no secrets.
- No push, no PR, no history rewrite, no new experiments beyond the locked `run4` tiny repro + analyzer read-only report.
- Time cap 3m for this plan-writing step; repro execution bounded tiny CPU (smoke <5m, run-once per seed, no sweeps/spend).

## Lean

- Reuse-first: reuse existing runner + analyzer path, `argparse` + `pathlib`/`json` + `numpy`/`scipy`; no new modules, no refactors, no perf tuning, no API changes.
- Minimum code that reproduces `run4` raw + paired report; no scope growth.

## Review Focus

- HIGH-1: gate locked + paired-only — protocol v2 consumed verbatim (`config_hash` pinned); shared-rng paired seeds (same inputs per seed); overlap 0 tolerance-0; unpaired/hand-made/embedded-constant artifacts refused with non-zero exit, never silent `0`.
- HIGH-2: runner + analyzer signatures honored (`main(argv)->int`, pure `run`/`analyze`; exit-map `0/1/2`; `run_id=run4` recorded; deterministic fixed-seed rerun reproduces `run4` bytes; capture on non-zero; analyzer paired-only with exact pairing keys).
- HIGH-3: scope-locked — no file outside `files` touched; evidence only to `allow`; local-only, no sweeps/spend, no secrets/training-beyond-repro/push; confirmatory untouched.

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Gate + runner repro raw | R1–R6 task/parity/splits/models/runner/caps | `docs/verify-actual.sh` | preflight gate (frozen v2, config_hash pinned, overlap 0) + runner repro `run_id=run4` raw-only, deterministic rerun | `bash docs/verify-actual.sh` |
| 2 | Analysis-only paired report | R2 paired, R5 analyzer-consumed | `docs/analyze-only.sh` | analyzer reads `run4/raw.json` raw-only paired, report matches authoritative numbers within tolerances, no hand-made results | `bash docs/analyze-only.sh && .venv/bin/python -m json.tool research/artifacts/equality-actual-v2/run4/report-t.json > /dev/null` |
| 3 | evidence + caps verification | R5–R6 artifacts+caps, evidence-only | `docs/plans/2026-11-17-actual-repro-progress.md`, `docs/plans/2026-11-17-actual-repro-evidence.json` | outcome recorded, caps honored, evidence only to `allow` | `ls -l docs/plans/2026-11-17-actual-repro-progress.md docs/plans/2026-11-17-actual-repro-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-actual-repro-evidence.json > /dev/null` |

## Per-task notes

- 1: gate — preflight checks frozen `equality-actual-v2.json` (`config_hash=e2a5…9854` recomputed canonical-json, `run_id=run4` exact); runner `main(argv: list[str]) -> int`, pure `run(protocol: dict) -> artifacts` (I/O only at CLI boundary); exit-map `0=ok, 1=run-failed, 2=invalid/usage`; shared-rng seeds 101/202/303 run-once; overlap 0 tolerance-0 else exit 2; deterministic rerun reproduces raw bytes (`run.json` differs only `duration_s`); Verify `bash docs/verify-actual.sh` must exit 0.
- 2: analyzer — consumes `run4/raw.json` only (baseline/treatment paired by `seed_data`, run_ids `run4:baseline/treatment:seed-{101,202,303}` 6/6); paired t via scipy/numpy with exact pairing keys; unpaired refused; report `run4/report-t.json` transcribed to `allow`; tolerances: per-seed acc exact, `mean_diff` |repro+0.12|<=1e-9, `p_value` rel-tol 1e-6, CI bounds abs-tol 1e-6, `config_hash` exact, `overlap==0`; Verify `bash docs/analyze-only.sh` + `json.tool report-t.json` must exit 0.
- 3: pass only if Verify exit 0, R1–R6 covered, authoritative `run4` numbers reproduced within tolerances, caps (tiny CPU <5m, local-only, no sweeps/spend) honored, writes only to `allow` paths, no secrets/push, confirmatory locks untouched.

## Coverage checklist

- [ ] R1 task (locked equality task executed verbatim, config_hash pinned)
- [ ] R2 parity (same inputs/shared-rng, paired only, unpaired refused)
- [ ] R3 splits (disjoint-without-replacement, 200/50, zero-overlap tolerance-0, overlap 0)
- [ ] R4 models (locked A/B/C pair, tiny CPU, no substitution; repro = tiny run only)
- [ ] R5 runner + analyzer (signatures + exit-map, run_id=run4, deterministic raw, analyzer-consumed paired report within tolerances)
- [ ] R6 caps (bounded tiny CPU <5m, local-only, no sweeps/spend) + evidence only to `allow`
- [ ] Authoritative run4 numbers reproduced (mean -0.12, p 0.3897, CI [-0.5939,0.3539], per-seed 0.78/0.76, 0.24/0.24, 0.60/0.26)

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; R1–R6 covered; protocol-locked + shared-rng paired + deterministic honored; `run_id=run4` + `config_hash` recorded; authoritative numbers within tolerances; no file outside `files` touched; evidence only to `allow`; within caps; no secrets/training-beyond-repro/push; confirmatory untouched.
- Fail: fail-open (0 on failure), embedded constants, hand-made artifacts, unpaired comparison, split leakage, config_hash/run_id drift, tolerance breach, file outside `files` touched, cap breach, sweep/spend, secret/training-beyond-repro/push, or confirmatory re-invoked.

Authorization: mission Phase6 autonomous — actual repro only (local-only, scope-locked to `files`/`allow`, tiny CPU, no secrets, no push).
