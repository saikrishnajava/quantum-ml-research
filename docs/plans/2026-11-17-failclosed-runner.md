---
spec: inline-R1-R5-failclosed-runner
status: approved
approved_by: mission-autonomous
approved_at: 2026-11-16T03:35:35Z
files:
  - scripts/run_experiment.py
  - tests/test_runner.py
allow:
  - docs/plans/2026-11-17-failclosed-runner-progress.md
  - docs/plans/2026-11-17-failclosed-runner-evidence.json
Authorization: mission Phase2 autonomous — failclosed runner only (local-only, scope-locked, no secrets, no training, no push)
---

# Plan — Failclosed Runner

Branch: `research/audit-1587497` @ `a3addab`.

Mission authorization transcribed 2026-11-16: autonomous Phase2.
Source: planner handoff `ses_e1d94b07` (draft); duplicate planner `ses_e1d93d16` ignored.
Scope-locked: writes only to `files` above; evidence only to `allow` above. No secrets, no training, no push.

## Goal

Ship a thin fail-closed experiment runner (CLI wrapper) plus 7-case test suite so any failure exits non-zero with captured output and artifacts — never silent pass, never fail-open.

```mermaid
flowchart LR
  CLI[scripts/run_experiment.py CLI wrapper] --> Run[five-state run + capture]
  Run --> Tests[tests/test_runner.py 7 cases]
  Tests --> Evidence[progress + evidence only]
```

## Arch

- CLI wrapper: `scripts/run_experiment.py` (thin glue over subprocess; parses args, enforces caps, maps five states to exits 0/0/1/124/2, captures stdout/stderr, writes artifacts).
- Test suite: `tests/test_runner.py` (7 cases: success / scientific-negative / execution-failed / timed-out / capture / regression-artifacts / caps).
- Evidence layer: progress md + evidence json only (see `allow`).

## Stack

- stdlib only for runner (`argparse`, `subprocess`, `pathlib`, `json`, `time`).
- `pytest` for `tests/test_runner.py` (`-q`).
- Local-only CPU; no GPU, no network, no paid APIs.

## Spec

- Spec: `inline-R1-R5-failclosed-runner` — explicitly no external spec file. R1–R5 below are fail-closed (any violation exits non-zero; never `0` on failure).
- R1 five-state: states are `success` / `scientific-negative` / `execution-failed` / `timed-out` / `invalid`. `execution-failed` covers child non-zero exit or spawn error; `timed-out` covers per-case timeout (`subprocess.TimeoutExpired`); `invalid` covers usage/cap refusal, malformed args, nonfinite timeout/metric, malformed metrics-file JSON, unpaired predictions/targets.
- R2 exits: exit-map `0=success`, `0=scientific-negative` (child `verdict` negative), `1=execution-failed`, `124=timed-out`, `2=invalid/usage`. All non-zero paths are fail-closed; no coercion to `0`; real child exit preserved in artifacts.
- R3 capture: per-case stdout/stderr captured with case id, state, exit code, duration; surfaced on non-zero without swallowing traceback.
- R4 regression + artifacts: deterministic rerun of recorded cases reproduces state/exit; artifacts (per-case record + summary) written only to runner out dir and transcribed to `allow` evidence; no embedded constants steering outcome.
- R5 artifacts + caps: per-case timeout enforced, total time bounded, local-only, no sweeps, no spend; evidence written only to `allow` paths; no file outside `files` touched.
- Out of scope: model/code changes beyond runner glue, secrets, training, push/PR, confirmatory re-runs.

## Constraints

- Branch `research/audit-1587497`, local-only, reversible.
- Scope locked to `files` (implementation) and `allow` (evidence); `scripts/*`, `tests/*`, `research/*` otherwise untouched; no secrets, no training.
- No push, no PR, no history rewrite, no new experiments beyond runner self-checks.
- Time cap 3m for this plan-writing step; runner self-check caps bounded per-case + total (local-only, no sweeps/spend).

## Lean

- Thin glue only: reuse `argparse` + `subprocess`; no new modules, no refactors, no perf tuning, no API changes.
- Minimum code that passes the 7 cases; no scope growth.

## Review Focus

- HIGH-1: fail-closed — every failure path exits non-zero per exit-map (0/0/1/124/2); no silent `0`, no fail-open wrapper.
- HIGH-2: exit-map + signatures honored (`main(argv)->int`, per-case record with state/exit/capture; states success/scientific-negative/execution-failed/timed-out/invalid).
- HIGH-3: scope-locked — no file outside `files` touched; evidence only to `allow`; no secrets/training/push.
- HIGH-4: caps enforced (per-case timeout, bounded total, local-only, no sweeps/spend).

## Tasks 1-3

| # | Task | Spec req | Files | Expected | Verify |
|---|---|---|---|---|---|
| 1 | Runner CLI wrapper | R1 five-state, R2 exits, R3 capture | `scripts/run_experiment.py` | thin glue, signatures + exit-map 0/0/1/124/2, capture per case | `.venv/bin/python -m py_compile scripts/run_experiment.py && grep -n "def main\|exit" scripts/run_experiment.py` |
| 2 | 7-case fail-closed suite | R1–R4 states/exits/capture/regression | `tests/test_runner.py` | 7 cases success/scientific-negative/execution-failed/timed-out/capture/regression-artifacts/caps, all fail-closed | `.venv/bin/python -m pytest tests/test_runner.py -q` |
| 3 | evidence + caps verification | R5 artifacts+caps, evidence-only | `docs/plans/2026-11-17-failclosed-runner-progress.md`, `docs/plans/2026-11-17-failclosed-runner-evidence.json` | outcome recorded, caps honored, evidence only to `allow` | `ls -l docs/plans/2026-11-17-failclosed-runner-progress.md docs/plans/2026-11-17-failclosed-runner-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-failclosed-runner-evidence.json > /dev/null` |

## Per-task notes

- 1: signatures `main(argv: list[str]) -> int`, `run_case(...) -> {id, state, exit, stdout, stderr, duration}`; exit-map `0=success, 0=scientific-negative, 1=execution-failed, 124=timed-out, 2=invalid`; `execution-failed` includes child non-zero/spawn-error path; stdlib only; Verify greps signatures + exit branches.
- 2: 7 cases — (i) success→0, (ii) scientific-negative `verdict`→0, (iii) execution-failed→1, (iv) timed-out→124, (v) stdout/stderr capture intact, (vi) regression determinism + artifacts written, (vii) caps (per-case timeout/bounded total) enforced; invalid paths assert exit 2; all non-zero paths assert exit != 0.
- 3: pass only if Verify exit 0, R1–R5 covered, caps (bounded, local-only, no sweeps/spend) honored, writes only to `allow` paths, no secrets/training/push, confirmatory locks untouched.

## Coverage checklist

- [ ] R1 five-state (success/scientific-negative/execution-failed/timed-out/invalid, child non-zero→execution-failed)
- [ ] R2 exits (0/0/1/124/2 map, no silent 0)
- [ ] R3 capture (stdout/stderr + traceback per case)
- [ ] R4 regression + artifacts (deterministic rerun, artifacts to out dir + evidence)
- [ ] R5 caps (per-case/total bounded, local-only, no sweeps/spend, evidence only to `allow`)

## Rubric

- Pass: rows 1-3 Verify cmds exit 0; R1–R5 covered; exit-map honored; no file outside `files` touched; evidence only to `allow`; within caps; no secrets/training/push; confirmatory untouched.
- Fail: fail-open (0 on failure), exit-map drift, file outside `files` touched, cap breach, sweep/spend, secret/training/push, or confirmatory re-invoked.

Authorization: mission Phase2 autonomous — failclosed runner only (local-only, scope-locked to `files`/`allow`, no secrets, no training, no push).
