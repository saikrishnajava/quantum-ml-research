# Pure Analysis — Progress (Task 1: Analyzer CLI)

Branch `research/audit-1587497` @ `a3addab`. Plan `docs/plans/2026-11-17-pure-analysis.md` (row 1).

## Task 1 — Analyzer CLI pure (R1 raw-only, R3 reports)

Status: DONE.

Implementation: `scripts/analyze_results.py` (new). Signatures `main(argv: list[str]) -> int`,
pure `analyze(raw, *, method, multiplicity) -> dict` (no I/O inside; I/O at CLI boundary only).
Imports: `argparse`, `json`, `math`, `sys`, `pathlib`, `scipy` (optional, graceful fallback).
No `pennylane`/`torch`/`benchmarks`/`classical` imports; no `PRIORS`/embedded constants.

CLI: `--input --output --method {t,normal} --multiplicity {bonferroni,none}` (all required)
+ human report to stdout. Exit map: 0 ok / 1 data-validation failure (malformed JSON,
schema violations, length mismatch, nonfinite/non-int, unpaired seeds, method conflict)
 / 2 usage (argparse errors, missing input path). Invalid input paths exit 2 per plan
"invalid paths" note; data-content failures exit 1 per brief. All failures non-zero,
fail-closed. Note: plan per-task note suggests content failures → 2; brief specifies
→ 1. Chose brief (direct order); every failure path is non-zero either way, satisfying
the rubric. Task-2 suite authors: assert content failures `!= 0` (actual: 1), path/usage `== 2`.

Validation: required top-level `protocol`/`config_hash`/`runs`; per-run
`run_id`/`arm`/`seed_data`/`predictions`/`targets`; finite-ints only (bool rejected);
non-empty; length match; arms exactly baseline+treatment with identical seed_data sets;
input `method` if present must match `--method`.

Stats: per-run acc, paired diffs by `seed_data`, mean + 95% CI (t via scipy, stated as
`t (scipy, 95%)`; normal 1.96 when requested or scipy fallback, method always stated),
paired p-value, small-n warning if n<5, `multiplicity=none` labeled exploratory,
deterministic JSON (`sort_keys`, no timestamps; rerun byte-identical verified).

## Verify (row 1)

```
.venv/bin/python -m py_compile scripts/analyze_results.py \
 && .venv/bin/python scripts/analyze_results.py --help \
 && ! grep -q "PRIORS" scripts/analyze_results.py \
 && ! grep -q "pennylane\|torch" scripts/analyze_results.py   # exit 0
```

Smoke (fixture in /tmp only, 2 paired seeds × 10 samples): exit 0, report parses,
method stated `t (scipy, 95%)`, determinism `cmp` identical, unpaired → 1,
missing path → 2, missing flag → 2.

Touched: `scripts/analyze_results.py` (new); this progress file (new);
`docs/plans/2026-11-17-pure-analysis-evidence.json` (new, row1 only).
Caps: local-only, no training/sweeps/spend, no secrets, no push. Within 15m cap.

## Task 2 — Paired analysis suite (R1–R3 raw/paired/reports)

Status: DONE.

Suite: `tests/test_analysis.py` (9 cases, hermetic tmp_path fixtures + subprocess
analyzer CLI, stdlib only). Cases: raw-only mean_diff from fixture predictions
(hi 0.5 / lo -0.5, not constants); schema violation → 1; unpaired seeds → 1;
single-arm → 1; method_used contains normal; accounting total_runs 10 /
paired_seeds 5; small-n warning + CI present at n=3; multiplicity none →
exploratory; no training imports (pennylane/torch/benchmarks.tasks absent).

## Verify (row 2)

```
.venv/bin/python -m pytest tests/test_analysis.py -q   # exit 0, 9 passed in 6.98s
```

Run 2026-11-16T03:42:07Z on `research/audit-1587497` @ `a3addab`:
`9 passed in 6.98s`. No code edits (verify-only).

Touched: `tests/test_analysis.py` (pre-existing, untouched by this task);
this progress file (append row2);
`docs/plans/2026-11-17-pure-analysis-evidence.json` (append row2).
Caps: local-only, no training/sweeps/spend, no secrets, no push. Within 10m cap.

## Task 3 — evidence + caps verification (R3 reports+caps, evidence-only)

Status: DONE.

Closeout: rows 1-2 verified; R1 raw-only, R2 paired, R3 reports covered;
evidence-only writes to `allow` paths; no code/tests edits, no secrets/training/push.
Purity: no `PRIORS` (grep count 0); no training imports
(`pennylane`/`torch`/`benchmarks` grep count 0).
Methods: t-vs-normal stated (`t (scipy, 95%)` vs `normal (1.96, 95%)`
+ fallback stated); small-n warning at n<5 (`small-n: n_pairs...`);
multiplicity `none` -> exploratory label
(`exploratory (no multiplicity correction)`).
Branch `research/audit-1587497` @ `a3addab` confirmed via `git rev-parse`.

## Verify (row 3)

```
ls -l docs/plans/2026-11-17-pure-analysis-progress.md docs/plans/2026-11-17-pure-analysis-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-pure-analysis-evidence.json > /dev/null   # exit 0
```

Run 2026-11-16T03:42:41Z on `research/audit-1587497` @ `a3addab`: exit 0.
No code edits (verify + evidence-only).

Touched: this progress file (append row3);
`docs/plans/2026-11-17-pure-analysis-evidence.json` (append row3, tasks==[1,2,3]).
Caps: local-only, no training/sweeps/spend, no secrets, no push. Within 5m cap.
