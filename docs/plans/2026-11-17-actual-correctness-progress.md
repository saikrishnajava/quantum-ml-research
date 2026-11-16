# Actual Correctness — Progress

Branch: `research/audit-1587497` @ `a3addab`. Auth: Phase4. Plan: `docs/plans/2026-11-17-actual-correctness.md`.

## Row 1 — Task1 verify (2026-11-16, tiny CPU)

- Verify: `.venv/bin/python -m pytest tests/test_actual_correctness.py -q` → exit 0, **10 passed** (1.19s), GREEN.
- No code fixes (Task2 scope). Gate: NoFix record-only.
- Per-AC observed values (`-q -s`):

| AC | Result | Observed |
|----|--------|----------|
| AC1 finite | PASS | shape=(1,4,8) nonfinite=0 |
| AC2 loss-metric code facts | PASS | trainer_allpos_flat=True runner_lastpos=True |
| AC3 grads | PASS | loss=2.285593 cnorm=1.49834 qnorm=0.0532068 |
| AC4 step | PASS | step=1 loss=2.285593 maxdelta=0.00101 |
| AC5 no-stale-cache | PASS | eval_redo_maxdiff=0 param_mutate_maxdiff=2.35922e-16 (borderline: >0 but eps-level — flagged for Task2 review, NOT fixed here) |
| AC6 counts | PASS | total=775 classical=760 quantum=15 |
| AC7 mask | PASS | classical_path_maxdiff=0.146141; REC quantum_only_maxdiff=0 (mask-blind, record-only) |
| AC8 maps | PASS | n=25 classical=22 quantum=3 overlap=0 |
| AC9 sim agreement | PASS | maxdiff=1.31044e-10 (bound 1e-5) |
| AC10 derivs | PASS | grad_norm=1.47684 |
| AC-EV | PASS | recorded here + evidence json only |

- Caps: tiny CPU local-only, no sweeps/spend, no secrets/push. Time <10m.

## Row 2 — Task2 Gate + guards (2026-11-16, tiny CPU)

- Verify: `.venv/bin/python -m pytest tests/test_actual_correctness.py tests/test_phase1_correctness_guards.py -q` → exit 1, **6 failed, 12 passed** in 1.36s.
- Actual-only: `.venv/bin/python -m pytest tests/test_actual_correctness.py -q` → exit 0, **10 passed** in 1.19s, GREEN.
- Gate: **NoFix** — GREEN means touch nothing; **zero code change** (no edits to `hybrid/`, `classical/`, `tests/` this task; `git diff --stat -- hybrid classical tests` empty).
- Guards observed record-only (do NOT fix): passed 2 (`test_sim_equivalence_probe`, `test_audit_14_threshold`); failed 6 as expected (`test_audit_1`, `test_audit_2`, `test_audit_3`, `test_audit_4`, `test_audit_11`, `test_audit_15` — matches prior 6 failed/2 passed).
- Caps: tiny CPU local-only, no sweeps/spend, no secrets/push. Time <10m.

## Row 3 — Task3 evidence + caps verification / closeout (2026-11-16, tiny CPU)

- Verify: `ls -l docs/plans/2026-11-17-actual-correctness-progress.md docs/plans/2026-11-17-actual-correctness-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-actual-correctness-evidence.json > /dev/null` → exit 0, at 2026-11-16T03:45:58Z, branch `research/audit-1587497` @ `a3addab`, auth Phase4.
- Actual-only: `.venv/bin/python -m pytest tests/test_actual_correctness.py -q` → exit 0, **10/10 passed** in 1.15s, GREEN. Gate: **NoFix**, zero code change (`git diff --stat -- hybrid classical tests` empty, no edits to `hybrid/`/`classical/`/`tests/`).
- Guards record-only (do NOT fix): combined `.venv/bin/python -m pytest tests/test_actual_correctness.py tests/test_phase1_correctness_guards.py -q` → exit 1, **6 failed, 12 passed** in 1.35s; guards passed 2 (`test_sim_equivalence_probe`, `test_audit_14_threshold`) / failed 6 (`test_audit_1`, `test_audit_2`, `test_audit_3`, `test_audit_4`, `test_audit_11`, `test_audit_15`).
- Caps: tiny CPU local-only, no sweeps/spend, no secrets/push. Time <5m.
- Tasks: [1, 2, 3] complete. Touched: `docs/plans/2026-11-17-actual-correctness-progress.md`, `docs/plans/2026-11-17-actual-correctness-evidence.json` only.

## Row 4 — Fix iteration verify (2026-11-16, tiny CPU)

- Fix observed (verify-only, no edits here): dropout reseed control in AC3/AC9 (`np.random.seed(123)` before each sampled train-forward so embedding Dropout(0.1) masks match); norm-equality + determinism proved on the real path.
- Verify: `.venv/bin/python -m pytest tests/test_actual_correctness.py -q` → exit 0, **11 passed** in 1.33s, GREEN (was 10/10; now 11/11 with AC9b sim-agreement extra).
- Behavioral now: cache AC5 (train bypass 0/0, eval hit identical), split AC8 (S>max length==S, prefix→remainder), determinism AC9 (exact logits + step loss), weights AC7/AC10 (rows sum to 1, masked≈0).
- Guards record-only (do NOT fix): `.venv/bin/python -m pytest tests/test_actual_correctness.py tests/test_phase1_correctness_guards.py -q` → exit 1, **6 failed, 13 passed** in 1.51s; failed 6 (`test_audit_1`, `test_audit_2`, `test_audit_3`, `test_audit_4`, `test_audit_11`, `test_audit_15`); passed 11 actual + 2 guards (`test_sim_equivalence_probe`, `test_audit_14_threshold`).
- Zero code change this task (`git diff --stat -- hybrid classical tests` empty). Touched: `docs/plans/2026-11-17-actual-correctness-progress.md`, `docs/plans/2026-11-17-actual-correctness-evidence.json` only.
- Caps: tiny CPU local-only, no sweeps/spend, no secrets/push. Time <10m.
