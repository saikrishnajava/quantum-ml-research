# Confirmatory Magnitude — Progress (run-once record)

CONFIRMATORY_MAG_RUN_ONCE

- Branch: `research/audit-1587497`. Protocol LOCKED (no frozen-field amends).
- Auth: user "keep on continue" (2026-11-16), fail-open frozen-then-once only.
- Spec: N/A-fail-open-frozen-inline (plan `docs/plans/2026-11-17-confirmatory-mag.md`). Record-only, no gated advantage claim.
- Run: SINGLE invocation `.venv/bin/python -m pytest tests/test_confirmatory_mag.py -q -s` → exit 0, 2 passed, 0.76s. No repeat run (marker above; test refuses second invocation).

## Estimand

- PRIMARY `balanced_acc_diff` = classical_bal − quantum_bal per seed; mean + CI recorded vs THRESHOLD 0.20, BONFERRONI 2 tasks (XOR held-out + equality held-out). Fail-open record-only, no gate.

## Frozen caps (all honored)

- Seeds: fresh [11, 33, 55] ONLY; forbidden seed 6 never used.
- Held-out: XOR(p1=1, p2=3, target_xor=1, action=2) + EQ(p=2, target_val=1, action=1).
- Model: 64 hidden / 5 epochs max / lr 1e-2, 1 LR config (no sweep). Local CPU only. Wall 0.1s ≪ 900s budget.

## Observed diffs (record-only, no gate)

- XOR: seed 11 → 0.4297 (1.0 vs 0.5703); seed 33 → 0.5203 (1.0 vs 0.4797); seed 55 → 0.5000 (1.0 vs 0.5000). mean_diff=0.4833 CI=[0.3652, 0.6014].
- EQ: seed 11 → 0.5424 (1.0 vs 0.4576); seed 33 → 0.5385 (1.0 vs 0.4615); seed 55 → 0.5085 (1.0 vs 0.4915). mean_diff=0.5298 CI=[0.4837, 0.5758].
- Both task CIs lie above THRESHOLD 0.20 — recorded as observation only; no advantage claim gated or made.

## Leakage

- Held-out XOR pair (1,3) distinct from prior locks (0,3), (1,2) and from fresh-seed exploratory draws — verified passing in `test_protocol_frozen_mag`.
- Forbidden seed 6 absent from run (asserted in-run).

## Scope / exclusions

- Scope: `tests/test_confirmatory_mag.py` untouched by this run (no code/test edits made).
- Writes in this step ONLY: this progress file + `docs/plans/2026-11-17-confirmatory-mag-evidence.json`.
- Exclusions honored: no secrets touched, no push/PR, no sweep, no spend, no GPU.

## Falsifier

- Had any per-seed diff been non-finite, CI non-finite, wall ≥ 900s, or seed/epoch/model mismatch, the run would have failed and been logged BLOCKED — outcome recorded fail-open either way. Actual: all finite, within caps, 2 passed.

## Doc-text correction 2026-11-17 (RED, pre-results, no rerun)

- Plan doc-text fixed per critic: XOR (1,2,1,2)→(1,3,1,2) + correction note; Task-1 Verify grep F-1→FRESH_SEEDS|FORBIDDEN_SEEDS|HELD_OUT; Task-2 `-s` reworded to pytest -s + numbers in tail. No rerun (run-once consumed), no numbers changed.
