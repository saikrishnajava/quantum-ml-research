# Progress — Failclosed Runner (row1: Runner CLI wrapper)

Branch: `research/audit-1587497` @ `a3addab`. Task1 row1 only (R1 five-state, R2 exits, R4 artifacts-capture). Tests suite (row2) out of scope for this task.

## Done
- Created `scripts/run_experiment.py` (stdlib only: argparse, subprocess, json, hashlib, platform, sys, os, time, math).
- CLI: `--experiment-id --run-id --timeout --output --protocol-hash [--metrics-file] -- <cmd...>`; `subprocess.run(check=False)`.
- Five states/exits: success 0, scientific-negative 0 (child `verdict` field), execution-failed 1, timed-out 124, invalid 2. Real child exit preserved in artifacts.
- Child-output contract documented in file header: stdout JSON unless `--metrics-file` given; non-JSON stdout + exit 0 accepted as success/metrics-null; metrics-file must be valid JSON; nonfinite metrics or unpaired predictions/targets → invalid(2). No embedded constants.
- Artifacts: `<output>/<exp>/<run>/{status.json, stdout.log, stderr.log, config.json}`; config.json has 12 fields (protocol_hash, commit, env, hardware, config, params, seeds, budget, curves, predictions_targets_ref, overlap, status), unknowns null, commit via best-effort `git rev-parse HEAD`.

## Verify (all exit 0)
- `.venv/bin/python -m py_compile scripts/run_experiment.py && .venv/bin/python scripts/run_experiment.py --help && ! grep -q "|| true" scripts/run_experiment.py` → exit 0.
- Smoke `/tmp/arts/smoke/smk1` (verdict success) → runner exit 0, `status.json` status `success`.
- Extra (fail-closed): scientific-negative → 0; child exit 3 → 1; sleep>timeout → 124; `--timeout nan` → 2.

## Touched
- `scripts/run_experiment.py` (new)
- `docs/plans/2026-11-17-failclosed-runner-progress.md` (new, this file)
- `docs/plans/2026-11-17-failclosed-runner-evidence.json` (new, row1)

## Critic drift fix (2026-11-16, plan/impl exit-map + LOW hygiene, no behavior change)

- Critic: impl `scripts/run_experiment.py` already correct per mission 5-state (success 0 / scientific-negative 0 / execution-failed 1 / timed-out 124 / invalid 2); plan doc still said PASS/FAIL/ERROR/TIMEOUT/BLOCKED 0/1/2/3/4. Fixed plan R1/R2 + Arch/Tasks/per-task-notes/coverage to success-map.
- LOW hygiene (no exit-map change): (1) deleted unused `_is_finite_number`, (2) kept full-payload `_check_metrics_finite(payload)` only (removed metrics-subset pre-check), (3) set `cmd`/`timeout` inside `run_case` record init.
- Verify: `.venv/bin/python -m py_compile scripts/run_experiment.py && .venv/bin/python scripts/run_experiment.py --help && ! grep -q "|| true" scripts/run_experiment.py` → exit 0 (see below).

## Row2 verify — 7-case fail-closed suite (2026-11-16T03:37:57Z)

- Cmd (verbatim): `.venv/bin/python -m pytest tests/test_runner.py -q` → exit 0.
- Tail: `tests/test_runner.py .......  [100%]` / `7 passed in 0.94s`.
- Plan row2 Expected: 7 cases pass/fail-closed/error/timeout/capture/regression-artifacts/caps, all fail-closed — met (no code edits, verify-only).
- Touched (this task): `docs/plans/2026-11-17-failclosed-runner-progress.md` (append row2), `docs/plans/2026-11-17-failclosed-runner-evidence.json` (row2).

## Row3 verify — Phase2 closeout after hygiene fix (2026-11-16T03:39:11Z)

- Cmd (verbatim): `ls -l docs/plans/2026-11-17-failclosed-runner-progress.md docs/plans/2026-11-17-failclosed-runner-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-failclosed-runner-evidence.json > /dev/null && git branch --show-current && git rev-parse HEAD | grep -q a3addab` → exit 0.
- Hygiene no-break re-run: `.venv/bin/python -m pytest tests/test_runner.py -q` → exit 0, `7 passed in 0.94s`.
- at: 2026-11-16T03:39:11Z; caps: local-only, <5m, no sweeps/spend, no GPU/network/paid APIs.
- Scope: no push/training/secrets; branch `research/audit-1587497` @ `a3addab`; locked confirmatory untouched; `scripts/run_experiment.py` + `tests/test_runner.py` untouched this task.
- Touched (this task): `docs/plans/2026-11-17-failclosed-runner-progress.md` (append row3), `docs/plans/2026-11-17-failclosed-runner-evidence.json` (row3 + tasks).
- Tasks: [1, 2, 3] complete; R1–R5 covered; exit-map 0/0/1/124/2 honored.
