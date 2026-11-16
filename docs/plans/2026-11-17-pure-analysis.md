---
spec: inline-Phase3-pure-analysis
status: approved
approved_by: mission-autonomous
approved_at: 2026-11-16T03:39:07Z
files:
  - scripts/analyze_results.py
  - tests/test_analysis.py
allow:
  - docs/plans/2026-11-17-pure-analysis-progress.md
  - docs/plans/2026-11-17-pure-analysis-evidence.json
Authorization: mission Phase3 autonomous — pure analysis only (local-only, scope-locked, no secrets, no training, no push)
---

# Plan — Pure Analysis

Branch: `research/audit-1587497` @ `a3addab`.

Mission authorization transcribed 2026-11-16: autonomous Phase3.
Source: planner handoff (draft); scope transcribed to `files`/`allow` below.
Scope-locked: writes only to `files` above; evidence only to `allow` above. No secrets, no training, no push.

## Goal

Ship a thin pure analysis layer (raw-only analyzer CLI + paired test suite) so claims rest on raw result files with paired statistics and written reports — no embedded constants, no fail-open pass, no unpaired comparison.

```mermaid
flowchart LR
  Raw[raw results only] --> Analyzer[scripts/analyze_results.py pure analyzer]
  Analyzer --> Suite[tests/test_analysis.py paired suite]
  Suite --> Evidence[progress + evidence only]
```

## Arch

- Analyzer: `scripts/analyze_results.py` (thin glue over raw result files; parses args, reads raw-only inputs, computes paired stats, writes reports; pure — no network, no mutation of inputs).
- Test suite: `tests/test_analysis.py` (paired cases: raw-only / paired stats / reports).
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- stdlib + `numpy`/`scipy` for analyzer (`argparse`, `pathlib`, `json`; paired stats via `numpy`/`scipy` only).
- `pytest` for `tests/test_analysis.py` (`-q`).
- Local-only CPU; no GPU, no network, no paid APIs.

## Spec

- Spec: `inline-Phase3-pure-analysis` — explicitly no external spec file. R1–R3 below are fail-closed (any violation exits non-zero).
- R1 raw-only: analyzer reads raw result files only; no embedded constants steering outcome; inputs validated (malformed JSON / unpaired predictions-targets / nonfinite values → non-zero exit, usage exit 2).
- R2 paired: comparisons are paired only (same seeds/cases); unpaired comparison refused; paired stats (difference, CI/p-value via numpy/scipy) reported with exact pairing keys.
- R3 reports: per-analysis report + summary artifacts written only to analyzer out dir and transcribed to `allow` evidence; deterministic rerun reproduces report bytes; stdout/stderr captured per run, surfaced on non-zero.
- Out of scope: model/code changes beyond analyzer glue, secrets, training, push/PR, confirmatory re-runs.

## Constraints

- Branch `research/audit-1587497`, local-only, reversible.
- Scope locked to `files` (implementation) and `allow` (evidence); `scripts/*`, `tests/*`, `research/*` otherwise untouched; no secrets, no training.
- No push, no PR, no history rewrite, no new experiments beyond analyzer self-checks.
- Time cap 3m for this plan-writing step; analyzer self-check caps bounded (local-only, no sweeps/spend).

## Lean

- Thin glue only: reuse `argparse` + `pathlib`/`json` + `numpy`/`scipy`; no new modules, no refactors, no perf tuning, no API changes.
- Minimum code that passes the suite; no scope growth.

## Review Focus

- HIGH-1: raw-only — reads raw result files only; no embedded constants; malformed/unpaired/nonfinite inputs exit non-zero, never silent `0`.
- HIGH-2: paired + signatures honored (`main(argv)->int`, pure analyze functions; paired stats with exact pairing keys; no unpaired comparison).
- HIGH-3: scope-locked — no file outside `files` touched; evidence only to `allow`; no secrets/training/push.
- HIGH-4: caps enforced (bounded runtime, local-only, no sweeps/spend; deterministic report rerun).

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Analyzer CLI pure | R1 raw-only, R3 reports | `scripts/analyze_results.py` | thin glue, signatures + exit-map, raw-only reads, paired reports | `.venv/bin/python -m py_compile scripts/analyze_results.py && .venv/bin/python scripts/analyze_results.py --help` |
| 2 | Paired analysis suite | R1–R3 raw/paired/reports | `tests/test_analysis.py` | cases raw-only/paired-stats/reports, all fail-closed | `.venv/bin/python -m pytest tests/test_analysis.py -q` |
| 3 | evidence + caps verification | R3 reports+caps, evidence-only | `docs/plans/2026-11-17-pure-analysis-progress.md`, `docs/plans/2026-11-17-pure-analysis-evidence.json` | outcome recorded, caps honored, evidence only to `allow` | `ls -l docs/plans/2026-11-17-pure-analysis-progress.md docs/plans/2026-11-17-pure-analysis-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-pure-analysis-evidence.json > /dev/null` |

## Per-task notes

- 1: signatures `main(argv: list[str]) -> int`, pure `analyze(raw) -> report` (no I/O inside; I/O only at CLI boundary); exit-map `0=ok, 1=analysis-failed, 2=invalid/usage` (malformed args, malformed JSON, unpaired predictions/targets, nonfinite values → 2); stdlib + numpy/scipy only; Verify checks compile + `--help` signatures.
- 2: cases — (i) raw-only (embedded-constant/refusal path), (ii) paired stats correctness (pairing keys exact, unpaired refused), (iii) reports determinism + artifacts written; invalid paths assert exit 2; all failure paths assert exit != 0.
- 3: pass only if Verify exit 0, R1–R3 covered, caps (bounded, local-only, no sweeps/spend) honored, writes only to `allow` paths, no secrets/training/push, confirmatory locks untouched.

## Coverage checklist

- [ ] R1 raw-only (raw result files only, no embedded constants, malformed/unpaired/nonfinite → non-zero)
- [ ] R2 paired (same-seed/same-case pairing keys, unpaired refused, numpy/scipy paired stats)
- [ ] R3 reports (per-analysis report + summary to out dir + evidence, deterministic rerun, capture on non-zero)

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; R1–R3 covered; raw-only + paired honored; no file outside `files` touched; evidence only to `allow`; within caps; no secrets/training/push; confirmatory untouched.
- Fail: fail-open (0 on failure), embedded constants, unpaired comparison, file outside `files` touched, cap breach, sweep/spend, secret/training/push, or confirmatory re-invoked.

Authorization: mission Phase3 autonomous — pure analysis only (local-only, scope-locked to `files`/`allow`, no secrets, no training, no push).
