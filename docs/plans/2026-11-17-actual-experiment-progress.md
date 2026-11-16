# Actual Experiment — Progress

Branch: `research/audit-1587497` @ `a3addab`. Auth: mission Phase5 autonomous (local-only, scope-locked, tiny CPU, no secrets, no push).

## Row 1 — Locked protocol (2026-11-16)

- Wrote `research/protocols/equality-actual-v1.json` (new, frozen, spec `equality-actual-v1-R1-R6`).
- Keys: `task` (R1: `generate_equality_sequence_decision`, seq_len 4, vocab 4, n_actions 2, n_rules 1, n_train 200, n_test 50, last-position classification), `parity` (R2: same-inputs, context permitted-only, quantum-path token-local), `splits` (R3: unique-inputs, zero-overlap), `models` (R4: A ClassicalDecisionMLP/quantum_heads-0, B HybridQuantumLLM d16/L1/H2 6q-1layer, C positive tiny-MLP + negative majority/shuffle), `runner` (R5: frozen thin glue, signatures + exit-map 0/1/2, fail-closed, deterministic), `caps` (R6: tiny CPU, smoke <5m, bounded multi-seed, local-only).
- Seeds `[101,202,303]` — disjoint from priors: confirmatory-lock `[42,99,137]`, mag-fresh `[11,33,55]` (forbidden 6), other `[7,21,123]`. `[11,33,55]` deliberately NOT reused (mag consumed it).
- Artifacts `research/artifacts/equality-actual-v1/<run>/`; analysis t-test exploratory; failure fail-closed; conclusions exploratory-only, no confirmatory claim.
- Verify: `.venv/bin/python -m json.tool research/protocols/equality-actual-v1.json > /dev/null` → exit 0.
- Touched: `research/protocols/equality-actual-v1.json` (new), this progress file (new/append), evidence json (row1). Caps: well under 5m. Out-of-scope untouched: `scripts/*`, `tests/*`, training, secrets, push.

## Row 2 — Phase5 smoke: BLOCKED fail-closed at R3 (2026-11-16, tiny CPU)

- Wrapped 5-state smoke: `scripts/run_experiment.py --experiment-id equality-actual-v1 --run-id phase5-smoke-20261116 --timeout 300 --protocol-hash 6193eb42... -- scripts/run_actual_experiment.py ... --run-id phase5-smoke-20261116-inner` → outer exit **1** (`execution-failed`, child exit 2) in **1.3s** wall (time gate `<5m` met, pass gate NOT met → 202/303 expansion did not proceed as passes).
- Fail-closed cause: `invalid run: split overlap seed=101 (R3)`. Read-only overlap audit (no writes): train200/test50 draws from 4^4=256 space collide systematically — seed101: 24 overlap rows (53.3% of test), seed202: 26 (57.8%), seed303: 28 (65.1%). Root: locked generator samples 250 i.i.d. rows with replacement → R3 tolerance-0 unsatisfiable on all frozen seeds.
- Per-run acc: null (no predictions emitted); params: null (model construction never reached); positive control: **VOID** (no training; blocked at R3 — VOID not win, per fail-closed).
- Analyzer: `scripts/analyze_results.py --method t --multiplicity none` on missing runner artifacts → exit **2** (`input not found`), refused; no pairing fabricated, nothing hand-made.
- Suite: `ACTUAL_CORRECTNESS_GREEN=1 pytest tests/test_actual_experiment.py -q` → 1 failed (smoke asserts exit 0, got R3 exit 2), 2 passed — gate firing end-to-end as designed.
- Deviation (spec-gate block, escalated NOT absorbed): protocol R3 vs locked generator inconsistent. No fix here — protocol/generator/runner edits out of scope; needs planner decision (e.g. disjoint-sampling generator or revised R3). Correctness GREEN 11/11 re-verified this task (1.33s).
- Touched: 4 files under `research/artifacts/equality-actual-v1/equality-actual-v1/phase5-smoke-20261116/` (`status.json`, `config.json`, `stdout.log`, `stderr.log`) + this file + evidence json row2. Caps: local-only tiny CPU, well under 15m, no sweeps/spend/secrets/push.

## Row 3 — Phase5 actual v2: PASS 3-seed run + analyzer refusal (2026-11-17, tiny CPU)

- Wrapped 5-state run: `.venv/bin/python scripts/run_experiment.py --experiment-id equality-actual-v2 --run-id run1 --timeout 290 --output research/artifacts/equality-actual-v2 --protocol-hash b233f3d4...eccc -- .venv/bin/python scripts/run_actual_experiment.py --protocol research/protocols/equality-actual-v2.json --output research/artifacts/equality-actual-v2 --run-id run1 --timeout 280` → outer exit **0** (`success`, child exit 0) in **1.24s** wall (time gate `<5m` met; 202/303 ran as passes, run-once per frozen seed).
- Deviation (minimal, to pass fail-closed): added missing `--output research/artifacts/equality-actual-v2` to outer (task command omitted it; parser requires it, else exit 2). Inner command verbatim. Outer dir `research/artifacts/equality-actual-v2/equality-actual-v2/run1/` (4 files) + inner dir `research/artifacts/equality-actual-v2/run1/` (run.json + 3×seed dirs) — both under allowed prefix, total <100KB.
- Inner `run.json`: `status success`, `protocol equality-actual-v2`, `seeds [101,202,303]`, duration 1.07s. Per-seed acc: 101: **0.76**, 202: **0.76**, 303: **0.74** (n=50 each, majority=0). Predictions/targets equal length **50** per seed (verified). Overlap **0** rows (tripwire passed on all 3 seeds; exit 0). Params: **null** (construction-only majority baseline, no fit). Protocol-hash `b233f3d4...eccc` matches; commit `a3addab83791b9b2c39e8bb05a12e74fb1444f66`; run_ids `run1` (outer + inner, distinct dirs).
- Positive control: **VOID** (runner implements majority/negative only; no positive tiny-MLP training executed — VOID not win, per fail-closed).
- Analyzer: task-as-written (`--input .../run1/raw.json`, no `--output`) → exit **2** (usage: `--output` required). Retry on actual raw `run.json` with `--output .../run1/analysis-attempt.json --method t --multiplicity none` → exit **1** (`invalid input: missing or empty 'config_hash'`; single-arm majority output is not paired baseline/treatment — refused, nothing hand-made, no file written). No paired report fabricable under artifact policy (exploratory-only).
- Suite: `ACTUAL_CORRECTNESS_GREEN=1 pytest tests/test_actual_experiment.py -q` → **3 passed** (2.59s).
- Touched: 4 files under `research/artifacts/equality-actual-v2/equality-actual-v2/run1/` + 13 files under `research/artifacts/equality-actual-v2/run1/` (run.json + 3×seed-{101,202,303}/{predictions,targets,metrics,status}.json) + this file + evidence json row3. Caps: local-only tiny CPU, total well under 15m, no sweeps/spend/secrets/push.
