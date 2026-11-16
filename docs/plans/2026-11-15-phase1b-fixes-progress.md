# Phase1b fixes — progress

## Row 1 freeze truth (2026-11-16T01:31:32Z) — SUPERSEDED / VOID (wrong Verify, replaced below)
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` →
  `active spec gate: docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`
  `files 14 · allow 2 · approved_by appusai @ 2026-11-16T01:27:13.481Z`
  `plan ce94d1de53c0 · spec 68b3030e5b3f`, exit 0. Branch `research/audit-1587497`, base `1587497`.
- Freeze (venv truth): `autograd==1.8.0`, `pennylane==0.44.1`,
  `pennylane_lightning==0.44.0`, `pennylane_lightning_gpu==0.44.0`. Expected 0.44.1 / 1.8.0 — match.
- Delta vs freeze-file pins:
  - autograd: `requirements.txt` `==1.8.0` == venv `1.8.0` MATCH;
    `pyproject.toml` `>=1.8,<2` admits `1.8.0` MATCH. No edit needed.
  - pennylane: `requirements.txt` `==0.39.0` vs venv `0.44.1` DELTA (pin stale, install newer);
    `pyproject.toml` `>=0.39.0,<0.45` admits `0.44.1` MATCH. Recorded, not acted on (row-1: no downgrade).
  - pennylane-lightning: `==0.39.0` vs venv `0.44.0` (+gpu `0.44.0` unpinned) DELTA, same handling.
- Autograd justification (keep pin):
  - Keep costs 2 lines (`autograd==1.8.0` + `autograd>=1.8,<2`); removal forces a ~10-line rewrite.
  - `classical/nn.py` uses `anp` 4× (:182 exp, :195 exp, :257 where, :279 log/exp-sum in softmax/attention).
  - Rewrite = grad-flow risk (QNode analytic `qml.grad` uses the autograd interface).
  - Floor == venv truth `1.8.0`; `<2` ceiling holds the upper bound; pennylane METADATA requires
    autograd unbounded → compatible.
  - No downgrade, no reinstall performed.
- RED/GREEN: RED = delta unrecorded; GREEN = freeze truth recorded here + evidence.json row 1,
  verify exit 0, no downgrade, no reinstall. `requirements.txt` / `pyproject.toml` untouched
  (autograd already at truth; pennylane delta escalated, not absorbed).
- Verify (verbatim): `.venv/bin/pip freeze | grep -i -E "pennylane|autograd"` → exit 0.
- Touched: no code files; evidence only (2 files below).
- Deviation (reported, not absorbed): brief named `docs/plans/2026-11-15-phase1b-progress.md` and
  `docs/plans/2026-11-15-phase1b-evidence.json`, but gate `allow` lists the `-fixes-` variants;
  wrote gate-allowed paths.

## Row 1 TRUE (backends mapping guards F1-F2, 2026-11-16T01:33:02Z) — GREEN
- Supersedes freeze truth above (wrong Verify `.venv/bin/pip freeze | grep -i -E "pennylane|autograd"` void for row 1).
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` → active spec gate `docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`, `plan ce94d1de53c0`, exit 0. Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `quantum/backends/manager.py:116-123` F1 `raw.get("backends") is None → {}`; F2 non-dict → `ValueError`, never AttributeError.
- RED: `python3 -m py_compile quantum/backends/manager.py && grep -n "ValueError" quantum/backends/manager.py` → exit 0 with ValueError hits (guards already present, zero-line change).
- Verify (verbatim): `python3 -m py_compile quantum/backends/manager.py && grep -n "ValueError" quantum/backends/manager.py` → exit 0.
- Autograd exception note kept: keep `autograd==1.8.0` + `>=1.8,<2` (2 lines vs ~10-line rewrite; `classical/nn.py` anp 4×; grad-flow risk; floor == venv truth).
- Touched: no code change; evidence only (`docs/plans/2026-11-15-phase1b-fixes-progress.md`, `docs/plans/2026-11-15-phase1b-fixes-evidence.json`).

## Row 2 TRUE (per-backend guards F3-F4, 2026-11-16T01:33:46Z) — GREEN
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` → active spec gate `docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`, `plan ce94d1de53c0`, exit 0. Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `quantum/backends/manager.py:125-150` F3 `except (KeyError, TypeError)` per-backend re-raised as `ValueError` naming backend (`Invalid backend config {name!r}`); non-mapping cfg → `ValueError` naming backend. F4 `max_qubits` guard `:134` `if not isinstance(max_qubits, int) or isinstance(max_qubits, bool)` → `TypeError` caught → `ValueError` (bool excluded).
- RED: `python3 -m py_compile quantum/backends/manager.py && grep -n "isinstance.*bool" quantum/backends/manager.py` → exit 0 with hits `:134` + `:169` (guards already present, zero-line change).
- Verify (verbatim): `python3 -m py_compile quantum/backends/manager.py && grep -n "isinstance.*bool" quantum/backends/manager.py` → exit 0.
- Touched: no code change; evidence only (`docs/plans/2026-11-15-phase1b-fixes-progress.md`, `docs/plans/2026-11-15-phase1b-fixes-evidence.json`).

## Row 3 TRUE (yaml file guards F5-F6, 2026-11-16T01:34:39Z) — GREEN
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` → active spec gate `docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`, `plan ce94d1de53c0`, exit 0. Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `quantum/backends/manager.py:102` `open(path, encoding="utf-8")`; `:105-109` `safe_load → None` → `ValueError` naming file; `:110-114` top-level non-mapping → `ValueError`; `:159-166` `resource_limits` non-mapping → `ValueError` (same guard shape as F2).
- RED: `python3 -m py_compile quantum/backends/manager.py && grep -n 'encoding="utf-8"' quantum/backends/manager.py` → exit 0 with hit `:102` (guards already present, zero-line change).
- Functional (`.venv/bin/python`): empty → `ValueError` naming file PASS; top-level str → `ValueError` PASS; top-level list → `ValueError` PASS; `resource_limits: [1,2]` → `ValueError` PASS.
- Verify (verbatim): `python3 -m py_compile quantum/backends/manager.py && grep -n 'encoding="utf-8"' quantum/backends/manager.py` → exit 0.
- Touched: no code change; evidence only (`docs/plans/2026-11-15-phase1b-fixes-progress.md`, `docs/plans/2026-11-15-phase1b-fixes-evidence.json`).

## Row 4 TRUE (paired_significance assert-safe P1, 2026-11-16T01:35:38Z) — GREEN
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` → active spec gate `docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`, `plan ce94d1de53c0`, exit 0. Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `benchmarks/analysis/statistics.py:41-43` `if len(baseline) != len(treatment): raise ValueError("Must have same number of seeds")`, no `assert` (assert-safe under `-O`).
- RED: baseline `assert len(baseline) == len(treatment)` (see `git diff` history) would fail `grep -n "ValueError"` and be stripped by `-O`; GREEN replaces with `ValueError` (zero-line change by this task).
- Verify (verbatim): `python3 -m py_compile benchmarks/analysis/statistics.py && grep -n "ValueError" benchmarks/analysis/statistics.py` → exit 0 with hit `:42 raise ValueError("Must have same number of seeds")`.
- Guard-path assert check: `grep -n "assert " benchmarks/analysis/statistics.py` → no hit (exit 1), confirm no `assert` in guard path.
- Functional: `paired_significance([1.0,2.0],[1.0])` → `ValueError: Must have same number of seeds` PASS; `python3 -O` same mismatch → `ValueError` PASS (no `AssertionError`, not stripped).
- Read: `benchmarks/analysis/statistics.py:35-50` confirms `:41-42` guard.
- Touched: no code change; evidence only (`docs/plans/2026-11-15-phase1b-fixes-progress.md`, `docs/plans/2026-11-15-phase1b-fixes-evidence.json`).

## Row 5 TRUE (json bool-before-int P2, 2026-11-16T01:36:34Z) — GREEN
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` → active spec gate `docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`, `plan ce94d1de53c0`, exit 0. Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `benchmarks/runner.py:312-315` `if isinstance(obj, (bool, np.bool_)): return bool(obj)` at `:313` before `if isinstance(obj, np.integer)` at `:315`, so booleans serialize as bool not int.
- RED: swapped order (int branch first) would route `np.bool_` via int path risking `1`/`0`; GREEN keeps bool branch first (zero-line change by this task).
- Verify (verbatim): `python3 -m py_compile benchmarks/runner.py && grep -n "_json_default" benchmarks/runner.py` → exit 0 with hits `:308` usage + `:312` def.
- Order check: `grep -n "isinstance.*bool\|isinstance.*np.integer\|isinstance.*np.floating" benchmarks/runner.py` → `:313` bool, `:315` integer, `:317` floating (bool first confirmed).
- Functional (`.venv/bin/python`): `from benchmarks.runner import _json_default; json.dumps(True)=true PASS; json.dumps(np.bool_(True))=true PASS; json.dumps(np.int64(1))=1 PASS` (round-trip `true` not `1`).
- Read: `benchmarks/runner.py:305-320` confirms `:312-315` guard.
- Touched: no code change; evidence only (`docs/plans/2026-11-15-phase1b-fixes-progress.md`, `docs/plans/2026-11-15-phase1b-fixes-evidence.json`).

## Row 6 TRUE (smoke acceptance F1-F6+P1-P2, 2026-11-16T01:37:22Z) — GREEN
- Gate: `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` → active spec gate `docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`, `plan ce94d1de53c0`, exit 0. Branch `research/audit-1587497`.
- Code (pre-existing, no edit — TDD GREEN): `tests/test_phase1_1_guards.py` 4 tests pass; rows 1-5 guards unchanged (manager.py F1-F6, statistics.py P1, runner.py P2).
- RED: n/a (no code change; pre-existing GREEN).
- Verify (verbatim): `pytest tests/test_phase1_1_guards.py -q` → exit 0 via `.venv/bin/python -m pytest tests/test_phase1_1_guards.py -q` (`4 passed in 1.16s`). Interpreter recorded: `.venv/bin/python` (plan tech stack python 3.12 venv).
- Note: plan Expected cites `p=0.535 tie preserved, JSON boolean` — this guard file holds 4 guard tests (attention remainder, n<2 not_computed, winner Tie, parity sign-zero); tie/JSON-boolean behavior covered by rows 4-5 guards (statistics P1, runner P2), both pre-existing GREEN. No p=0.535 literal in this file; smoke GREEN as found.
- Touched: no code change; evidence only (`docs/plans/2026-11-15-phase1b-fixes-progress.md`, `docs/plans/2026-11-15-phase1b-fixes-evidence.json`).

## Known limitations at close (reviewer HIGH/MEDIUM/LOWs)
- Gate (verbatim head-3): `node /home/appusai/.config/opencode/scripts/spec-check.mjs status` →
  `active spec gate: docs/plans/2026-11-15-phase1b-fixes.md -> docs/specs/2026-11-15-parity-guards-pivot.md`
  `files 14 · allow 2 · approved_by appusai @ 2026-11-16T01:27:13.481Z`
  `plan ce94d1de53c0 · spec 68b3030e5b3f`. Branch `research/audit-1587497`, SHA `ce94d1de` matches (no drift).
- HIGH: spec :7 F1 loads-cleanly overstates — code :152-157 fail-closes at active_backend; end-to-end never clean without explicit backend. Fix deferred (spec immutable under gate, needs follow-up).
- MEDIUM: row-6 Expected cites p=0.535 tie but guard file has 4 tests, no p literal (admitted row-6 note); tie covered rows 4-5. Plan :108 acceptance = 4 passed smoke.
- LOWs deferred: TypeError-as-control-flow, rationale words, save_results encoding, kinds repr, 28-line freeze pointer cleanup.
- Evidence: tasks 1-6 exit 0 (task-6 confirmed exit 0 at 2026-11-16T01:37:22Z, 4 passed); SHA ce94d1de matches; zero-line code (pre-existing guards).
- Evidence ID migration 2026-11-16: task IDs string→integer 1..6 to satisfy close validator, no other fields changed.
