# Paired Completion — Progress (Task 1 / Row 1)

Branch `research/audit-1587497` @ `a3addab`. Auth: mission Phase5 paired approved.
Protocol v2 frozen seeds [101,202,303]. Spec R1,R2,R4,R5.

## Row 1 — Shared-rng paired guard + dual-arm runner (DONE)

`scripts/run_actual_experiment.py` upgraded to dual-arm paired + C controls,
backward-compat legacy single-arm smoke path preserved:

- `config_hash = sha256(canonical-json({protocol,task,splits,models.A,B}))`
  sorted + `separators=(",",":")` → `e2a56245…c98d54` (verified independent recompute).
- Shared split: one `RandomState(seed)` stream per seed — locked rule-draw
  (p1/target/action) + `choice(256,250,replace=False)` + 200/50 partition,
  reused verbatim by both arms (paired inputs). Duplicate/overlap → `ValueError` (exit 2).
- Arm A `ClassicalDecisionMLP` inference-only; arm B `HybridQuantumLLM` tiny
  (d16/1-layer/2-head/6q-1layer) inference-only; no training on A/B.
- C-positive: tiny MLP smoke-train ≤20 epochs ≤200 samples, test acc 1.0 on all
  seeds > chance 0.5 and > majority (0.76/0.76/0.74). C-negative: majority +
  shuffle floor recorded in `metrics.json`.
- Overlap/duplicate/nonfinite → `ValueError` (exit 2). Signatures kept:
  `run(protocol)->dict`, `main(argv)->int`; exit-map 0/1/2/124 preserved.
- `run2` layout: `seed-{s}/targets.json` (shared) + `predictions-A/B.json` +
  `status-A/B.json` with `run_id` format `run2:{arm}:seed-{seed}` +
  `run.json` (`run_id=run2`, `config_hash`). Legacy `predictions/targets/
  metrics/status.json` still written (smoke compat).
- No writes outside allowlist: run2 raw verified only under `/tmp/opencode/`;
  repo `research/artifacts/.../run2/**` untouched by Task 1.

## Verify (all GREEN)

- `.venv/bin/python -m pytest tests/test_actual_experiment.py -q` →
  `2 passed, 1 skipped` (default; smoke deferred).
- `ACTUAL_CORRECTNESS_GREEN=1 ... -q` → `3 passed` (2.78s; triple-seed
  paired artifacts + fixed-seed rerun byte-identical).
- Independent `run2` run → `ok run_id=run2 seeds=[101,202,303]` (1.17s);
  per-seed paired lengths 50/50/50; determinism rerun byte-identical
  (all arm/target/metric files; `run.json` differs only in `duration_s`).
- Fail-closed: missing/malformed/nan-timeout/v1-protocol → exit 2;
  task-mismatch/nonfinite protocol → `ValueError`.

## Touched

- `scripts/run_actual_experiment.py` (edit)
- `docs/plans/2026-11-17-paired-completion-progress.md` (new, this file)
- `docs/plans/2026-11-17-paired-completion-evidence.json` (new, row 1)

No protocol/analyzer/tests/benchmarks/hybrid edits. No secrets, no push.

## Row 2 — Runner CLI run2 raw completion (DONE)

Cmd: `.venv/bin/python scripts/run_actual_experiment.py --protocol
research/protocols/equality-actual-v2.json --output
research/artifacts/equality-actual-v2 --run-id run2 --timeout 290`
→ `ok run_id=run2 seeds=[101, 202, 303] duration_s=1.18`, exit 0.

- `run.json`: `run_id=run2`, `config_hash=e2a56245…c98d54` (matches row-1
  pinned hash), `seeds=[101,202,303]`, `status=success`.
- 6 runs (2 arms × 3 seeds), run_ids unique:
  `run2:A:seed-101`, `run2:B:seed-101`, `run2:A:seed-202`,
  `run2:B:seed-202`, `run2:A:seed-303`, `run2:B:seed-303`.
- Per-seed paired lengths 50/50/50 (targets / predictions-A /
  predictions-B) on all seeds; n=50; overlap 0 (fail-closed
  duplicate/overlap guard passed — overlap would exit 2).
- Positive control > chance: 1.0 > 0.5 on all seeds (and > majority
  0.76/0.76/0.74). Metrics: seed-101 A=0.78 B=0.76; seed-202 A=0.24
  B=0.24; seed-303 A=0.60 B=0.26.
- Size: 4481 bytes (`du -sb`, <100KB). No file outside allowlist touched.

## Verify (Row 2 GREEN)

- Runner exit 0 + `ok run_id=run2 seeds=[101, 202, 303]`.
- `run.json` has `config_hash` + `run_id=run2` + 3 seeds.
- 6/6 unique run_ids; per-seed predictions/targets len 50.
- Evidence: row 2 appended to `docs/plans/2026-11-17-paired-completion-evidence.json`.

## Touched (Row 2)

- `research/artifacts/equality-actual-v2/run2/**` (new, runner-written raw only)
- `docs/plans/2026-11-17-paired-completion-progress.md` (append, this row)
- `docs/plans/2026-11-17-paired-completion-evidence.json` (row 2)

No code/protocol/test edits. No secrets, no push. Within 15m cap.

## Row 3 — Runner emits analyzer-schema raw.json; run3 + report-t (DONE)

`scripts/run_actual_experiment.py` patched (runner-only edit): after per-seed
writes, `main()` builds `raw = {protocol, config_hash, runs: 6 entries}` and
writes `raw.json` to the run dir. Runner-internal arms A/B are mapped
explicitly in code with comment: A->`baseline`, B->`treatment`
(`run_id` format `<run-id>:baseline:seed-{s}` / `<run-id>:treatment:seed-{s}`,
`seed_data` int, finite int predictions/targets lists). The old
`if run_id == "run2"` gate on dual-arm per-seed files was removed so run3+
reuse the same layout. `run()` compute untouched (same determinism);
exit-map 0/1/2/124 and overlap/duplicate/nonfinite guards unchanged.
run2 not overwritten (no `raw.json` under run2).

- Cmd: `.venv/bin/python scripts/run_actual_experiment.py --protocol
  research/protocols/equality-actual-v2.json --output
  research/artifacts/equality-actual-v2 --run-id run3 --timeout 290`
  → `ok run_id=run3 seeds=[101, 202, 303]`, exit 0, `raw.json` present.
- Analyzer: `.venv/bin/python scripts/analyze_results.py --input
  research/artifacts/equality-actual-v2/run3/raw.json --output
  research/artifacts/equality-actual-v2/run3/report-t.json --method t
  --multiplicity none` → exit 0, `n_pairs=3`.
- `_validate_run` passes 6/6 (arms `{baseline, treatment}`); run3 raw
  predictions/targets byte-match run2 per-seed A/B/targets (determinism);
  `tests/test_actual_experiment.py` default → 2 passed, 1 skipped.

## Touched (Row 3)

- `scripts/run_actual_experiment.py` (edit: unconditional dual-arm files + raw.json)
- `research/artifacts/equality-actual-v2/run3/**` (new, runner/analyzer-written only)
- `docs/plans/2026-11-17-paired-completion-progress.md` (append, this row)

No protocol/analyzer/tests edits. No secrets, no push. Within 15m cap.

## Row 3 (Task 3) — Analyzer paired report over run3; run2 preserved pre-raw (DONE)

- Input `research/artifacts/equality-actual-v2/run3/raw.json` → output
  `research/artifacts/equality-actual-v2/run3/report-t.json`
  (`--method t --multiplicity none`), analyzer exit 0.
- `n_pairs=3`, `mean_diff=-0.12`, 95% CI `[-0.5939, 0.3539]`,
  `p=0.3897` (method `t (scipy, 95%)`); multiplicity `none` →
  exploratory (`m_comparisons=1`); warning: `small-n: n_pairs=3 < 5;
  interval is wide, treat as preliminary`.
- Per-seed baseline/treatment accs: seed-101 `0.78/0.76` (diff -0.02);
  seed-202 `0.24/0.24` (diff 0.0); seed-303 `0.60/0.26` (diff -0.34).
  Run ids `run3:baseline:seed-{101,202,303}` /
  `run3:treatment:seed-{101,202,303}`; pairing `paired by seed_data
  across arms ['baseline', 'treatment']`.
- Overlap 0 (fail-closed duplicate/overlap guard passed — violation
  exits 2); positive control acc 1.0 > chance 0.5 on all seeds
  (same deterministic compute as rows 1–2).
- Deterministic: run3 raw predictions/targets byte-match run2 per-seed
  A/B/targets (see Row 3 runner section above).
- run2 preserved: no `raw.json` under
  `research/artifacts/equality-actual-v2/run2/` (pre-raw history;
  analyzer refused non-schema input — paired report rests on run3 only).
- `config_hash=e2a56245…c98d54` matches rows 1–2; protocol
  `equality-actual-v2`; accounting `total_runs=6, paired_seeds=3,
  baseline=3, treatment=3, excluded=[]`.

## Verify (Row 3 Task 3 GREEN)

- `report-t.json` parses: `n_pairs=3`, `mean_diff=-0.12`,
  `p_value≈0.3897`, CI `[-0.5939, 0.3539]`, small-n warning present,
  multiplicity none/exploratory.
- run2 dir listing: no `raw.json` (pre-raw history intact).
- Evidence: row 3 appended with `tasks==[1,2,3]`.

## Touched (Row 3 Task 3)

- `docs/plans/2026-11-17-paired-completion-progress.md` (append, this row)
- `docs/plans/2026-11-17-paired-completion-evidence.json` (row 3)

No code/artifact edits. No secrets, no push. Within 5m cap.

## MED fix — thread run_id into status files; run4 verify (DONE)

Reversible Auth Phase5 paired fix: `run(protocol)` hardcoded status
`run_ids` to `run2:A/B:seed-{s}` while `raw.json` already threaded
`{run_id}:baseline/treatment`. Runner-only edit, no protocol/analyzer change:

- `run(protocol, run_id="run2")` + `run_ids` use
  `f"{run_id}:A:seed-{s}"` / `f"{run_id}:B:seed-{s}"`;
  `main()` passes CLI `--run-id` (`artifacts = run(protocol, run_id)`).
  Default `"run2"` preserves backward-compat (`run(protocol)` callers unchanged).
- Verify run4: `.venv/bin/python scripts/run_actual_experiment.py --protocol
  research/protocols/equality-actual-v2.json --output
  research/artifacts/equality-actual-v2 --run-id run4 --timeout 290`
  → `ok run_id=run4 seeds=[101, 202, 303]`, exit 0.
  `run4/seed-*/status-{A,B}.json` → `run4:A/B:seed-{101,202,303}` (6/6);
  `run4/raw.json` → `run4:baseline/treatment:seed-{101,202,303}` (6/6).
- History preserved: run2 `status-*.json` stay `run2:A/B:*` (correct for
  run2); run3 `status-*.json` stay `run2:A/B:*` (known duplication, pre-fix
  history — paired report rests on run3 `raw.json` + `report-t.json`,
  unaffected); run2 has no `raw.json` (pre-raw). No overwrite of run2/run3.
- Tests: `tests/test_actual_experiment.py` default → 2 passed, 1 skipped.

## Touched (MED fix)

- `scripts/run_actual_experiment.py` (edit: `run(protocol, run_id)` + threaded status run_ids + `main()` passes run_id)
- `research/artifacts/equality-actual-v2/run4/**` (new, runner-written verify only)
- `docs/plans/2026-11-17-paired-completion-progress.md` (append, this row)

No protocol/analyzer/tests/benchmarks/hybrid edits. No secrets, no push. Within 10m cap.

## Row 4 — Analyzer paired report over run4; run4 authoritative (DONE)

- Input `research/artifacts/equality-actual-v2/run4/raw.json` → output
  `research/artifacts/equality-actual-v2/run4/report-t.json`
  (`--method t --multiplicity none`), analyzer exit 0.
- `n_pairs=3`, `mean_diff=-0.12`, 95% CI `[-0.5939, 0.3539]`,
  `p=0.3897` (method `t (scipy, 95%)`); multiplicity `none` →
  exploratory (`m_comparisons=1`); warning: `small-n: n_pairs=3 < 5;
  interval is wide, treat as preliminary`.
- Per-seed baseline/treatment accs: seed-101 `0.78/0.76` (diff -0.02);
  seed-202 `0.24/0.24` (diff 0.0); seed-303 `0.60/0.26` (diff -0.34).
  Run ids `run4:baseline:seed-{101,202,303}` /
  `run4:treatment:seed-{101,202,303}`; pairing `paired by seed_data
  across arms ['baseline', 'treatment']`.
- IDs correct (clean): status `run4:A/B:seed-{101,202,303}` (6/6) +
  raw `run4:baseline/treatment:seed-{101,202,303}` (6/6).
- Numbers confirm run3 (mean -0.12, p 0.39 — same deterministic
  compute). Run4 is the authoritative paired result.
- `config_hash=e2a56245…c98d54` matches rows 1–3; protocol
  `equality-actual-v2`; accounting `total_runs=6, paired_seeds=3,
  baseline=3, treatment=3, excluded=[]`.

## Verify (Row 4 GREEN)

- Analyzer exit 0 + `report-t.json` parses: `n_pairs=3`,
  `mean_diff=-0.12`, `p_value≈0.3897`, CI `[-0.5939, 0.3539]`,
  small-n warning present, multiplicity none/exploratory.
- Evidence: row 4 appended with `tasks==[1,2,3]` + run4 authoritative note.

## Touched (Row 4)

- `research/artifacts/equality-actual-v2/run4/report-t.json` (new, analyzer-written only)
- `docs/plans/2026-11-17-paired-completion-progress.md` (append, this row)
- `docs/plans/2026-11-17-paired-completion-evidence.json` (row 4)

No code/protocol/analyzer/tests edits. No secrets, no push. Within 5m cap.
