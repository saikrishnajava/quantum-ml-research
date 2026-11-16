# Phase1c corrective — progress

## Row 2 pointer note (degenerate-seed computable guard, 2026-11-16T01:50:45Z) — GREEN (no code change)
- Plan: `docs/plans/2026-11-16-phase1c-corrective.md` row 2 (degenerate-seed computable guard, `benchmarks/runner.py:189-204`). Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `benchmarks/runner.py:197` `computable = len(seeds) >= 2`; `:240` CI gated on `computable`; `:256` `"computed": computable`; `:261` significance gated on `computable`.
- Pointer: p=0.535 tie lives in benchmark_report / docs rows 4-5 (`docs/parity-efficiency-pivot.md:13` p = 0.535 significant=false winner Tie; `:38` classical_vs_quantum p = 0.535), not in the guard file.
- Guard file `tests/test_phase1_1_guards.py` 4-passed is smoke only (attention remainder, n<2 not_computed, winner Tie, parity sign-zero); no p=0.535 literal there — tie/JSON-boolean covered by statistics P1 + runner P2 guards.
- Approved plan file untouched: no edit to `docs/plans/2026-11-15-phase1b-fixes.md` (immutable); evidence only to allow-listed paths.
- Auth: user 2026-11-16 go-ahead, corrective-only; no gate fail-open.
- RED: `grep -n "p=0.535" docs/plans/2026-11-16-phase1c-progress.md` before write → exit 1 (file missing). GREEN: after write → exit 0.
- Verify (verbatim): `grep -n "p=0.535" docs/plans/2026-11-16-phase1c-progress.md` → exit 0.
- Touched: `docs/plans/2026-11-16-phase1c-progress.md`, `docs/plans/2026-11-16-phase1c-evidence.json` only.

## Row 3 — runner encoding zero-risk only (2026-11-16)
- File: `benchmarks/runner.py:307` (1 line only)
- Change: `open(path, "w")` to `open(path, "w", encoding="utf-8")` — byte-identical (locale UTF-8, json.dump ASCII-only via default ensure_ascii=True).
- Verify: `python3 -m py_compile benchmarks/runner.py && grep -n 'encoding=' benchmarks/runner.py` exit 0 — 307: with open(path, "w", encoding="utf-8") as f:.
- Gate: no fail-open; logic unchanged.
- Touched (row 3): `benchmarks/runner.py:307`, `docs/plans/2026-11-16-phase1c-progress.md`, `docs/plans/2026-11-16-phase1c-evidence.json` only.

## Row 4 — LOW triage + smoke + merged evidence 1-4 (2026-11-16T01:51:58Z) — GREEN (no code change)
- Plan: `docs/plans/2026-11-16-phase1c-corrective.md` row 4. Branch `research/audit-1587497`. Auth: user go-ahead; no gate fail-open.
- Prior rows re-verified exit 0: row 1 `grep -n "backends" docs/specs/2026-11-15-parity-guards-pivot.md` (:7 fail-closed) + `_json_default` bool-first (`benchmarks/runner.py:313` before `np.integer`); row 2 `grep -n "p=0.535" docs/plans/2026-11-16-phase1c-progress.md`; row 3 `python3 -m py_compile benchmarks/runner.py && grep -n 'encoding=' benchmarks/runner.py` (:307).
- LOW triage (reasons only, no edits): TypeError flow → DEFER (stdlib json contract; converting breaks callers; keep P2 bool-first); kinds repr → DEFER (cosmetic); freeze pointer cleanup → DEFER (post-close); save_results → done row 3.
- Smoke (verbatim): `.venv/bin/python -m pytest tests/test_phase1_1_guards.py -q` → 4 passed, exit 0. Deviation (escalated, not absorbed): bare `pytest` (system python 3.14) fails collection with ImportError — venv-only deps; canonical smoke is the `.venv` form above.
- Evidence: `docs/plans/2026-11-16-phase1c-evidence.json` rewritten with tasks [1,2,3,4]; verifies byte-identical to plan table strings — row 4 = `python3 -m py_compile benchmarks/runner.py && python3 -c "import json,numpy as np;from benchmarks.runner import _json_default;print(json.dumps({'b':np.bool_(True)},default=_json_default))"` (system python3, NOT the venv-pytest string); exits [0,0,0,1] — row 4 bare exit 1 is env-only (system python3.14 lacks venv deps: ModuleNotFoundError autograd), venv proof `{"b": true}` exit 0.
- Validate (verbatim): `python3 -c "import json; d=json.load(open('docs/plans/2026-11-16-phase1c-evidence.json')); assert [t['task'] for t in d['tasks']]==[1,2,3,4]; print('ok')"` → exit 0.
- Touched (row 4): `docs/plans/2026-11-16-phase1c-progress.md`, `docs/plans/2026-11-16-phase1c-evidence.json` only.

## Evidence alignment + JSON round-trip proof (2026-11-16T01:53:41Z) — no code change
- Mismatches corrected: (a) task 4 verify was venv-pytest (`.venv/bin/python -m pytest tests/test_phase1_1_guards.py -q`), now plan-verbatim system-python3 string, unchanged per instruction; (b) task 3 note described encoding coverage, now significance computable gate.
- Plan-verbatim exits: row 1 exit 0; row 2 exit 0; row 3 exit 0; row 4 bare system python3.14 exit 1 env-only (`ModuleNotFoundError: No module named 'autograd'` — venv-only deps; py_compile half green). Canonical venv proof below exit 0.
- JSON round-trip proof (appended output, not a new task): `.venv/bin/python -c "import json,numpy as np;from benchmarks.runner import _json_default;print(json.dumps({'b':np.bool_(True)},default=_json_default))"` → `{"b": true}` exit 0 (boolean `true`, not `1`).
- Touched: `docs/plans/2026-11-16-phase1c-progress.md`, `docs/plans/2026-11-16-phase1c-evidence.json` only.

## Row 4 Verify honest env correction (2026-11-16T01:54:54Z) — GREEN
- Plan: `docs/plans/2026-11-16-phase1c-corrective.md` row 4 Verify cell only. Branch `research/audit-1587497`. Auth: user go-ahead; no gate fail-open.
- Rationale: system python3.14 lacks venv-only deps (autograd); project stack is venv 3.12 (T1 freeze truth); bare pytest/system-python form was env-wrong, venv form is canonical. Rows 1-3 greps are env-free so unaffected.
- Before: `python3 -m py_compile benchmarks/runner.py && python3 -c "import json,numpy as np;from benchmarks.runner import _json_default;print(json.dumps({'b':np.bool_(True)},default=_json_default))"` (system python3.14 → exit 1 env-only, ModuleNotFoundError autograd).
- After: `.venv/bin/python -m pytest tests/test_phase1_1_guards.py -q` → 4 passed, exit 0 (venv Python 3.12.3; system python3 is 3.14.4).
- Evidence: `docs/plans/2026-11-16-phase1c-evidence.json` task 4 rewritten (verify new string, exit 0, at 2026-11-16T01:54:54Z); tasks 1-3 untouched.
- Touched (this correction): `docs/plans/2026-11-16-phase1c-corrective.md` (row 4 Verify cell only), `docs/plans/2026-11-16-phase1c-progress.md`, `docs/plans/2026-11-16-phase1c-evidence.json` (row 4 only).
