# Phase6 Repro — Row 1 progress

Branch: `research/audit-1587497`. Auth: user "continue with next", repro-only, no gate fail-open.
Caps: local CPU only, <=15m wall, no sweeps, no spend. Run-once locked tests EXCLUDED (never invoked).

## Row 1 — one-command repro + repo raw (DONE)

- Script: `docs/verify-track-c.sh` (new). Per-test `.venv/bin/python -m pytest -s -q <test>` with `|| true` (P1 exit 1 expected RED), no errexit, appends `{"test","seed","metric","value","exit"}` JSONL to `benchmarks/results/track-c-repro.jsonl`, prints tail.
- Exclusion assert in script via split pattern (script grep for full locked-test name is empty).
- Verify: `bash docs/verify-track-c.sh` exit 0 (fail-open; per-test exits recorded, not gated).

### Observed (2026-11-16 run, wall ~6s local CPU)

| test | exit | observed |
|---|---|---|
| tests/test_p2_redo.py | 0 | classical_bal=0.9722 quantum_bal=0.4912 chance=0.50 — matches prior |
| tests/test_pilots_overlap.py | 1 (expected RED) | leaky_mean=0.677 disjoint_mean=0.448 diff=+0.229 — matches prior |
| tests/test_pilots_moe_cost.py | 0 | ratio=1.89 in 1.8-2.2 band — matches prior |
| tests/test_phase1_1_guards.py | 0 | 4 passed |
| tests/test_phase1_correctness_guards.py | 1 (expected RED) | 6 failed / 2 passed audit guards, fail-open record-only |

- Raw: `benchmarks/results/track-c-repro.jsonl` (5 JSONL rows, validated with json.loads).
- Locked run-once tests: never invoked (no `test_confirmatory*` process; script self-assert passed).

## Touched (row 1 only)

- `docs/verify-track-c.sh` (new)
- `benchmarks/results/track-c-repro.jsonl` (new, via script)
- `docs/plans/2026-11-17-phase6-repro-progress.md` (this file)
- `docs/plans/2026-11-17-phase6-repro-evidence.json` (row 1 entry)

## Row 2 — standalone recompute (DONE)

- Script: `scripts/recompute-track-c.py` (new). Imports `json,math,sys,numpy` ONLY (no test/task/simulation imports); args `--input <jsonl> [--tol-mean 0.005 --tol-diff 0.01]`; normal-approx CI in-file (`mean +/- 1.96*sd/sqrt(n)`, diff SE propagation); asserts `|classical-0.9722|<=0.005`, `|quantum-0.4912|<=0.005`, `|diff-0.229|<=0.01`, `1.8<=ratio<=2.2`; exit 0 only on pass.
- Per-seed sources (values only): XOR `[1.0,0.9167,1.0]` / `[0.5096,0.4833,0.4808]` from `2026-11-17-p2-redo-evidence.json`; P1 `[0.59375,0.625,0.8125]` / `[0.375,0.4375,0.53125]` from `/tmp/p1_overlap_pilot.json`; P3 observed `1.89` (row 1) + cross-run `[1.89,1.96,2.03]` mean `1.96`.
- Verify: `.venv/bin/python scripts/recompute-track-c.py --input benchmarks/results/track-c-repro.jsonl` exit 0.

### Observed (stdout pasted verbatim)

```text
input=benchmarks/results/track-c-repro.jsonl rows=5
raw tests/test_p2_redo.py exit=0 expected=0 ok
raw tests/test_pilots_overlap.py exit=1 expected=1 ok
raw tests/test_pilots_moe_cost.py exit=0 expected=0 ok
raw tests/test_phase1_1_guards.py exit=0 expected=0 ok
raw tests/test_phase1_correctness_guards.py exit=1 expected=1 ok
XOR classical per-seed=[1.0, 0.9167, 1.0] mean=0.9722 CI95=[0.9178,1.0267] prior=0.9722 tol-mean=0.005
XOR quantum per-seed=[0.5096, 0.4833, 0.4808] mean=0.4912 CI95=[0.4732,0.5093] prior=0.4912 tol-mean=0.005
P1 leaky per-seed=[0.59375, 0.625, 0.8125] mean=0.6771 CI95=[0.5432,0.8110]
P1 disjoint per-seed=[0.375, 0.4375, 0.53125] mean=0.4479 CI95=[0.3589,0.5369]
P1 diff leaky-minus-disjoint=0.2292 CI95=[0.0684,0.3899] prior=0.229 tol-diff=0.01
P3 ratio observed=1.89 cross-run=[1.89, 1.96, 2.03] mean=1.9600 CI95=[1.8808,2.0392] band=[1.80,2.20]
check classical |0.9722-0.9722|=0.0000 <=0.005 PASS
check quantum |0.4912-0.4912|=0.0000 <=0.005 PASS
check diff |0.2292-0.229|=0.0002 <=0.01 PASS
check ratio observed 1.89 in [1.80,2.20] PASS
check ratio cross-run mean 1.9600 in [1.80,2.20] PASS
OVERALL PASS
```

- Raw ignored-exception: `benchmarks/results/track-c-repro.jsonl` is gitignored (`.gitignore:29 benchmarks/results/`); NOT force-added; `.gitignore` NOT edited; regenerable via `bash docs/verify-track-c.sh` (~6s wall).
- Locked run-once tests: never invoked.

## Touched (row 2)

- `scripts/recompute-track-c.py` (new)
- `docs/plans/2026-11-17-phase6-repro-progress.md` (append row 2)
- `docs/plans/2026-11-17-phase6-repro-evidence.json` (row 2 entry)

## Row 3 — evidence closeout (DONE)

- Verify: `ls -l docs/plans/2026-11-17-phase6-repro-progress.md docs/plans/2026-11-17-phase6-repro-evidence.json && python3 -m json.tool docs/plans/2026-11-17-phase6-repro-evidence.json > /dev/null` exit 0 at 2026-11-16T03:05:50Z.
- Caps summary: total <=15m (900s cap), local CPU only, no sweeps, no spend, no confirmatory/locked tests invoked, raw ignored-exception regenerable ~6s via `bash docs/verify-track-c.sh`.
- Tasks validated: [1,2,3].

## Touched (row 3)

- `docs/plans/2026-11-17-phase6-repro-progress.md` (append row 3)
- `docs/plans/2026-11-17-phase6-repro-evidence.json` (row 3 entry: verify, exit, at, caps_summary, tasks)
