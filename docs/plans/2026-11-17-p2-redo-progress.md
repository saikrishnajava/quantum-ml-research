# P2-redo progress — bounded + record (GREEN)

Branch: `research/audit-1587497`.
Auth: user "go ahead" post-Track-C, fail-open exploratory.
Spec: TBD-exploratory (no approved spec, fail-open record-only, no gated claim).
Caps: <=3 seeds [42,99,137], <=5 epochs, 10-15m, local CPU only, no sweeps/spend.
Status: **GREEN** — 4 passed, fail-open record-only, no gated claim.
Provenance: `HIDDEN = 64` set in the write step BEFORE any GREEN run —
  cite write handoff `tests/test_p2_redo.py:56` (`HIDDEN = 64 # stronger
  classical: wider hidden than pilot (32)`), header states "RED — written
  first, never executed here (write-only handoff); no green run yet".
  Sampler 2x per-class oversample only (480 train / 240 test);
  thresholds (`CHANCE`/`FALSIFIER_MARGIN`) and seeds unchanged, no tuning.

## Design

- Task layer: `benchmarks/tasks/benchmark_sequence_decision.py` (`generate_xor_sequence_decision` + `generate_equality_sequence_decision` control).
- Check layer: `tests/test_p2_redo.py` bounded assertions only (no sweeps): classical-learns-balanced, quantum-matched falsifier, evidence-complete.
- Sampler: 2x per-class oversample → 480 train / 240 test (balanced 50/50 per seed); `MIN_PER_CLASS` guard unchanged.
- Thresholds unchanged; no tuning, no sweeps, no spend.

## Numbers per seed (balanced accuracy)

- classical_bal mean **0.9722** ([1.0, 0.9167, 1.0]) for seeds [42, 99, 137].
- quantum_bal mean **0.4912** ([0.5096, 0.4833, 0.4808]) for seeds [42, 99, 137].
- Chance band: **0.50**; quantum sits at chance, classical learns.
- n_params: **1218 matched** (classical == quantum, no efficiency edge to record).
- Raw per seed (== balanced by 50/50 construction): classical_raw
  [1.0, 0.9167, 1.0], quantum_raw [0.5096, 0.4833, 0.4808];
  pred_classes [0, 1] both arms all seeds (no majority collapse).
  Full per-seed raw/pred_classes persisted in
  `docs/plans/2026-11-17-p2-redo-evidence.json` (`per_seed`,
  `classical_raw`/`quantum_raw`, `equality_control`).

## Equality control (informational — does NOT gate falsifier)

- Same matched setup (heads/MLP/init/shuffle/EPOCHS/SEEDS/TINY) on
  `generate_equality_sequence_decision`; tiny, <=3 seeds, <=5 epochs.
- classical_bal mean **1.0000** ([1.0, 1.0, 1.0]); quantum_bal mean
  **0.5206** ([0.4627, 0.549, 0.55]); raw == balanced per seed;
  pred_classes [0, 1] both arms all seeds.
- No new thresholds asserted; completeness-only (finite + logged).
  Falsifier verdict above unchanged (XOR arms only).

## Falsifier verdict: PASS

- Expected: `quantum_bal < classical_bal - 0.10`.
- Actual: 0.4912 < 0.9722 − 0.10 (= 0.8722) → **PASS** (margin ≈ 0.48).

## Go / no-go

- **GO (Track C mechanism proven, record-only)**: on XOR-vs-equality control, classical reaches ~0.97 balanced with 1218 params while param-matched quantum stays at chance (~0.49); no efficiency/advantage claim beyond this recorded outcome.

## Verification (GREEN)

Cmd: `.venv/bin/python -m py_compile tests/test_p2_redo.py && .venv/bin/python -m pytest tests/test_p2_redo.py -q` (timeout 900)
- `py_compile` exit: 0 (at 2026-11-16T02:21:00Z)
- `pytest` exit: **0** (at 2026-11-16T02:22:53Z, wall ~1.23s)
- Tail: `4 passed in 1.23s` (incl. `test_p2r_equality_control`, informational)

Prior RED (2026-11-16T02:19:50Z, seed=99 `minority=15 < 16` guard) superseded by GREEN after sampler fix in `tests/test_p2_redo.py` (out of this record-only scope; logged here only).

## Evidence tasks 1-3

| # | Verify cmd (per plan rows) | Actual exit | At (UTC) |
|---|---|---|---|
| 1 | `.venv/bin/python -m py_compile benchmarks/tasks/benchmark_sequence_decision.py && grep -n "generate_xor_sequence_decision" benchmarks/tasks/benchmark_sequence_decision.py` | 0 (`24:def generate_xor_sequence_decision(`, `148:data_generator=generate_xor_sequence_decision,`) | 2026-11-16T02:21:00Z |
| 2 | `.venv/bin/python -m py_compile tests/test_p2_redo.py && .venv/bin/python -m pytest tests/test_p2_redo.py -q` | 0 (4 passed in 1.23s, incl. equality-control) | 2026-11-16T02:22:53Z |
| 3 | `ls -l docs/plans/2026-11-17-p2-redo-progress.md docs/plans/2026-11-17-p2-redo-evidence.json` | 0 (post-write) | 2026-11-16T02:21:00Z |

Caps honored: 3 seeds [42,99,137], 5 epochs (constants), wall ~1.14s < 15m, local CPU only, no sweeps/spend. No file outside `files` touched by this step; no generator/test edits here (record-only).

## Touched

- docs/plans/2026-11-17-p2-redo-progress.md (updated: GREEN section)
- docs/plans/2026-11-17-p2-redo-evidence.json (updated: GREEN tasks 1-3)
