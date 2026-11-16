# Confirmatory Lock — Progress (fail-open, record-only)

- Branch: `research/audit-1587497`. Auth: user 2026-11-16 "next big win".
- Spec: N/A-fail-open-frozen-inline (no approved spec file; record-only, no gate).
- Protocol LOCKED — frozen fields not amended.
- CONFIRMATORY_RUN_ONCE (run-once marker; second invocation must refuse)

## Single run (ONE invocation, timeout 900s)

Cmd: `.venv/bin/python -m pytest tests/test_confirmatory.py -q`
Exit: 0. Tail:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/appusai/Documents/Projects/Quantum Projects/quantum-llm-agent
configfile: pyproject.toml
collected 2 items

tests/test_confirmatory.py ..                                            [100%]

============================== 2 passed in 0.78s ===============================
```

- Per-seed diffs / mean+CI: pytest `-q` captures the `CONFIRMATORY-{xor,eq}` print
  lines, so values are not visible in the tail. The tests assert every per-seed
  `balanced_acc_diff` and every CI bound is finite and passed. No numbers are
  fabricated into this record.
- Falsifier verdict / go-no-go: the frozen test emits none by design (fail-open,
  record-only, no gate). Nothing to paste; not a failure.

## Evidence tasks 1–3 (plan-table verify, actual exits)

| # | Verify | Actual |
|---|---|---|
| 1 | `.venv/bin/python -m py_compile tests/test_confirmatory.py && grep -n "F-1" tests/test_confirmatory.py` (at 2026-11-16T02:29:35Z) | py_compile exit 0; `grep -n "F-1"` exit 1 — no literal `F-1` in frozen file (uses `FRESH_SEEDS`/`FORBIDDEN_SEEDS`). Deviation recorded fail-open; no amend (LOCKED). |
| 2 | `.venv/bin/python -m pytest tests/test_confirmatory.py -q` (at ~2026-11-16T02:29Z) | exit 0, 2 passed in 0.78s. Single invocation; no re-run. |
| 3 | `ls -l` of both allow paths (post-write check) | exit 0, both exist. |

## Progress record

- Estimand: PRIMARY=`balanced_acc_diff` (classical_bal − quantum_bal per seed);
  THRESHOLD=0.20 record-only reference (fail-open, no gate); BONFERRONI=2 tasks.
- Seeds: fresh [7,21,123] only; forbidden [42,99,137] asserted disjoint (passed).
- Held-out: XOR (p1=0,p2=3,target_xor=2,action=1); EQ (p=1,target_val=3,action=2).
- Diffs: asserted finite per seed per task (passed); values captured under `-q`,
  not displayed; none invented here.
- Leakage check: `test_protocol_frozen` asserts held-out XOR pair differs from
  exploratory draws for all forbidden seeds and FRESH∩FORBIDDEN=∅ — passed.
- Scope: `files`=[tests/test_confirmatory.py]; evidence only to the two `allow`
  paths. No file outside touched.
- Exclusions: no code/test edits (no code-grounds failure occurred), no secrets,
  no push/PR, no sweeps/spend, local CPU only.
- Caps honored: 3 seeds ≤3, 5 epochs ≤5, 1 LR config, wall 0.78s < 15m, run-once.

Outcome: observed-pass, fail-open. No gated advantage claim.

## Touched

- docs/plans/2026-11-17-confirmatory-lock-progress.md (this file)
- docs/plans/2026-11-17-confirmatory-lock-evidence.json
