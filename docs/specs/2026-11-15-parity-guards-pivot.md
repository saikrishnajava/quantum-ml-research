# Parity Guards Pivot — Spec 2026-11-15

Status: draft (smoke-only acceptance). IDs: F1-F6 (config-load guards) + P1-P2 (parity guards).
All failures must raise `ValueError` (fail-closed), never silent coercion or `AssertionError` under `-O`.

## F1 — Missing `backends` key defaults to `{}`
YAML without a `backends` key defaults `raw.get("backends") is None` → `{}`, then fails closed at the `active_backend` check (`manager.py:152-157`) — never clean end-to-end.
- `quantum/backends/manager.py:116-119`

## F2 — `backends` not a mapping → `ValueError`
`backends` present but not a dict (e.g. a list or scalar) → `ValueError`, never AttributeError.
- `quantum/backends/manager.py:119-123`

## F3 — Malformed per-backend config → `ValueError`
Missing `device` key (`KeyError`) or non-subscriptable/non-mapping cfg (`TypeError`) caught per-backend and re-raised as `ValueError` naming the backend.
- `quantum/backends/manager.py:125-150`

## F4 — `max_qubits` must be a real int → `ValueError`
`max_qubits` that is not an `int` (including `bool`, which is an `int` subclass) → `ValueError`.
- `quantum/backends/manager.py:134-137`

## F5 — `resource_limits` not a mapping → `ValueError`
`resource_limits` present but not a dict → `ValueError` (same guard shape as F2).
- `quantum/backends/manager.py:159-166` (`limits` block below `_active_backend`)

## F6 — YAML file handling
- Open with `encoding="utf-8"` — `quantum/backends/manager.py:102`
- Empty YAML (`safe_load` → `None`) → `ValueError` naming the file — `quantum/backends/manager.py:105-109`
- Top-level non-mapping → `ValueError` — `quantum/backends/manager.py:110-114`

## P1 — `paired_significance` length mismatch → `ValueError` (assert-safe)
`len(baseline) != len(treatment)` raises `ValueError`, not `assert`, so it cannot be stripped by `-O`.
- `benchmarks/analysis/statistics.py:41-43`

## P2 — `_json_default` bool before int
`bool`/`np.bool_` handled before `np.integer` so booleans serialize as `bool` (not silently as `int` via the `int` subclass path).
- `benchmarks/runner.py:312-315`

## Acceptance (smoke only)
1. `py_compile` passes for all three edited files.
2. `grep` confirms: `ValueError` raised in F1-F6 sites, `isinstance` int/bool guards present, `encoding="utf-8"` on `open`, `assert` removed from `statistics.py:41`, `bool` branch first in `_json_default`.
3. `pytest tests/test_phase1_1_guards.py -q` passes (p=0.535 tie preserved; guards unaffected).
4. JSON round-trip: `json.dumps(obj, default=_json_default)` with a `np.bool_`/`bool` yields a JSON boolean (`true`/`false`), not `1`/`0`.

Touched files:
- `quantum/backends/manager.py`
- `benchmarks/analysis/statistics.py`
- `benchmarks/runner.py`
- `docs/specs/2026-11-15-parity-guards-pivot.md` (this file)

Out of scope: no new deps, no other files, no plan doc mutation.
