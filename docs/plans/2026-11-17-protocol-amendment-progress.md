# Protocol Amendment — Progress

Branch: `research/audit-1587497` @ `a3addab`. Plan: `docs/plans/2026-11-17-protocol-amendment.md` row 1.

## Row 1 — Locked V2 protocol (2026-11-17)

- Wrote `research/protocols/equality-actual-v2.json` (new): v1 keys copied verbatim
  (`task` seq4/vocab4/200/50, `parity` same_inputs/token-local, `models` A/B/C+negative,
  `runner`, `caps` tiny-CPU, `seeds` [101,202,303], `analysis` t/exploratory,
  `failure_policy`, `permitted_conclusions` all IDENTICAL per key-diff).
- Amended only `splits`: added `sampling: disjoint-without-replacement-250-of-256-in-runner`
  (sizes 200/50, unique_inputs/zero_overlap/tolerance-0 retained).
- Provenance: `amends: equality-actual-v1`, `amend_reason` (R3 unsatisfiable under
  with-replacement sampling), `amended_at: 2026-11-17`, `branch: research/audit-1587497`.
- Identity: `protocol: equality-actual-v2`, `spec: equality-actual-v2-R1-R6-R3-amended`,
  `artifacts: research/artifacts/equality-actual-v2/<run>/` (v2 run must not overwrite v1 artifacts).
- Verify: `json.tool` parse OK. Key-diff script: all copied keys IDENTICAL, splits +1 key only.
- DEVIATION (pre-existing, not caused by this task): v1-clean check
  `test -z "$(git status --porcelain research/protocols/equality-actual-v1.json)"` exits 1 —
  v1 is untracked (`?? research/protocols/equality-actual-v1.json`; `git ls-files
  research/protocols/` empty at HEAD `a3addab`). V1 bytes untouched (read-only); no
  add/commit performed (out of scope, no push). Task 2/3 owners: treat v1-frozen as
  content-frozen (byte-identical), not index-clean, until v1 is committed by an authorized step.
- Touched (this task): `research/protocols/equality-actual-v2.json`,
  `docs/plans/2026-11-17-protocol-amendment-progress.md`,
  `docs/plans/2026-11-17-protocol-amendment-evidence.json`. V1 unmodified.

## Row 2 — Runner disjoint-sampling (2026-11-17)

- Edited `scripts/run_actual_experiment.py` ONLY (`run()` sampling + two
  `validate_protocol` guards; generator/benchmarks untouched).
- `run()`: mirrors locked generator rule-draw preamble exactly
  (`RandomState(seed)`: p1/target/action per rule), seed-derived
  `choice-without-replacement` of 250 unique rows from the 256-row space,
  locked equality-rule application, partition-then-split 200/50. Overlap
  tripwire retained (`train&test -> ValueError`, exit 2, never repaired);
  exhaustion (`need > space` or choice failure) -> `ValueError` exit 2.
- `validate_protocol`: requires `protocol == equality-actual-v2` (R5) and
  `splits.sampling == disjoint-without-replacement-250-of-256-in-runner`
  (R3); malformed -> exit 2. V1 now fail-closed exit 2 (id guard; previously
  overlap exit 2 — same code, no silent pass).
- RED (pre-fix): v2 smoke -> `invalid run: split overlap seed=101 (R3)`, exit 2.
- GREEN: `.venv/bin/python scripts/run_actual_experiment.py --protocol
  research/protocols/equality-actual-v2.json --output /tmp/opencode/amend-smoke
  --run-id smoke --timeout 290` -> `ok run_id=smoke seeds=[101, 202, 303]`, exit 0.
  Exit 0 with retained tripwire PROVES zero overlap on all frozen seeds
  (any leakage exits 2). Per-seed: 50 preds / 50 targets (acc .76/.76/.74).
  Rerun (`smoke2`) exit 0, per-seed predictions/targets/metrics byte-identical
  (determinism). Tampered sampling -> exit 2; v1 -> exit 2.
- Generator untouched: `git diff --stat -- benchmarks/tasks/benchmark_sequence_decision.py`
  empty (exit 0) before and after.
- Touched (this task): `scripts/run_actual_experiment.py`,
  `docs/plans/2026-11-17-protocol-amendment-progress.md`,
  `docs/plans/2026-11-17-protocol-amendment-evidence.json`. No v1/v2 JSON edits,
  no generator edits, no secrets, no push.

## Row 3 — Suite retarget to v2 (2026-11-17)

- Edited `tests/test_actual_experiment.py` ONLY (protocol path/assertions to v2;
  no runner/protocol JSON edits, no secrets, no push).
- `PROTOCOL` retargeted `equality-actual-v1.json` -> `equality-actual-v2.json`;
  added `V1_PROTOCOL` read-only reference for frozen check.
- Strengthened (no weakening): protocol/spec id, parity same_inputs/token-local,
  splits 200/50 unique/zero/tolerance-0 + sampling disjoint string, task shape,
  seeds [101,202,303], v1 `protocol == equality-actual-v1` (content-frozen);
  smoke asserts `run.json` seeds/protocol, per-seed 50 preds/50 targets,
  `metrics.n == 50`, finite acc in [0,1], plus fixed-seed rerun (`smoke2`)
  byte-identical predictions/targets/metrics (determinism); exit 0 with retained
  runner tripwire proves zero-overlap by construction (any leakage exits 2).
- Fail-closed kept: missing/bad-json/nan-timeout nonzero; added v1-consumed
  refusal (`--protocol v1` -> exit 2).
- RED (pre-fix): `ACTUAL_CORRECTNESS_GREEN=1 pytest -q` -> 1 failed
  (`invalid protocol: protocol id mismatch (R5: locked to equality-actual-v2)`,
  exit 2 vs 0).
- GREEN: `ACTUAL_CORRECTNESS_GREEN=1 .venv/bin/python -m pytest
  tests/test_actual_experiment.py -q` -> `3 passed in 2.63s`, exit 0.
  Ungated `pytest -q` -> `2 passed, 1 skipped`, exit 0. Runner direct
  `ok run_id=smoke seeds=[101, 202, 303]` per-seed 50/50 acc .76/.76/.74.
- Caps: tiny CPU (~2.6s <5m), local-only, no sweeps/spend/network, no secrets/push.
- Touched (this task): `tests/test_actual_experiment.py`,
  `docs/plans/2026-11-17-protocol-amendment-progress.md`,
  `docs/plans/2026-11-17-protocol-amendment-evidence.json`. No v1/v2 JSON edits,
  no runner/generator edits, no secrets, no push.
