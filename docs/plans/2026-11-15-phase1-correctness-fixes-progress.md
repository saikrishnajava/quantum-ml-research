# Phase 1 correctness fixes — progress

## T1 autograd spike (2026-11-15T20:59:29Z) — DONE
- Option: add-pin (2 lines) over remove-dep. anp used 4x in classical/nn.py
  (softmax/attention/where/log-sum-exp); rewrite = grad-flow risk.
- `pyproject.toml`: `autograd>=1.8,<2`. `requirements.txt`: `autograd==1.8.0`.
  Floor == installed venv truth 1.8.0; pennylane METADATA requires
  autograd unbounded → compatible.
- Surprise (escalated, not absorbed): `.venv/bin/python` symlink resolves to
  system python3.14 (no deps); venv pkgs are python3.12. Verified with
  `/usr/bin/python3.12` + `PYTHONPATH=.venv/.../site-packages`. Symlink left
  untouched (out of scope).
- Verify: collect-only 62 collected, 0 errors, exit 0. `pip check` exit 0.

## T2 venv repair (2026-11-15T21:05Z) — DONE
- Diagnose: `.venv/bin/python3` symlinked to `/usr/bin/python3` (=3.14 after
  system upgrade); venv payload is python3.12 (`pyvenv.cfg` version 3.12.3,
  executable `/usr/bin/python3.12`). `pip` module missing under 3.14.
- Fix (minimal, local-only, no sudo/recreate/reinstall): repointed
  `.venv/bin/python3 -> /usr/bin/python3.12`. Chain
  `python -> python3 -> /usr/bin/python3.12` now yields 3.12.3 with venv
  site-packages on `sys.path`.
- Verify: `.venv/bin/python -m pip check` exit 0 (no broken requirements);
  pennylane 0.44.1 / autograd 1.8.0 / anp import ok exit 0;
  `test_surrogate.py` 2 passed exit 0.

## T3 sim equivalence probe (2026-11-15T21:15Z) — DONE
- Probe-only, no training: 1q (1 layer RY) + 2q (<=2 layers RY/CNOT/RZ),
  2 fixed param sets (<=3 seeds), fast numpy sim vs QNode state/probs.
- Finite-diff grad of <Z0> w.r.t. t[0], central eps=1e-6, both backends.
- Verify: `test_sim_equivalence_probe` 1 passed exit 0;
  TOL state_atol=1e-06 grad_atol=1e-05 stated in output.

## T4 audit failing-first guards 1,2,3,4,11,15 (RED, no fix) — DONE
- Gate: branch `research/audit-1587497`, HEAD `1587497`, plan approved, spec F1-F6+P1-P2 present.
- RED pre: `-k "test_audit_1 or ..._15"` 0 selected / 1 deselected, exit 0 (no guards yet).
- Appended 6 tests to `tests/test_phase1_correctness_guards.py` (no code-under-test touched):
  1 mask never to quantum (all-quantum heads, mask change -> no output change);
  2 objective vs metric (`[:, -1` in trainer vs runner mismatch);
  3 overlap 1000 draws / 256 space (tr_unique=244 te_unique=148);
  4 router misclassified (router/gate names lack quantum/.params);
  11 dense-train vs sparse-eval MoE diverge; 15 remainder fallback (calls=2 expected 4).
- RED post: `-k audit` 6 failed / 1 deselected; full file 6 failed / 1 passed (sim probe green).
- No fix, no push, no secrets; scope kept to test + progress + evidence.

## T5 tighten-14 / clarify-12 / TBD 5,6-10,13 (2026-11-15) — DONE (test+docs only)
- Gate: branch `research/audit-1587497`, HEAD `1587497`, plan `approved`, spec F1-F6+P1-P2 present; gate-status cmd exit 0.
- Appended `test_audit_14_threshold` to `tests/test_phase1_correctness_guards.py` (no code-under-test touched):
  seeded QuantumAttentionCircuit 6q/1-layer, autograd grad_norm bound `>1e-3` (was `>1e-10` per tests/unit/test_quantum_gradient_flow.py:30,42,54,75).
  Docstring clarifies AUDIT-12 prose-vs-code (`quantum/circuits/core.py:212-227` vs `:289-306` + `:331-338` per research/AUDIT.md:38, claims cite code)
  and marks TBD with file:line gaps: 5 stale `quantum/optimizations.py:34-38` (real `hybrid/interfaces/optimizations.py:34-38`, no invalidation test);
  6,7,8,9,10 no file:line; 13 `quantum/simulator/__init__.py:30-92` vs qnode `:230-238` path unconfirmed.
- Verify: `-k test_audit_14_threshold` 1 passed / 7 deselected (pass-with-tight-bound, documented, not RED);
  full file `-q` 6 failed / 2 passed (prior 6 RED unchanged; sim probe + audit-14 green).
- research/AUDIT.md NOT edited (not authorized); note kept here. No fix, no push, no secrets.

## T6 validate evidence JSON (2026-11-15T22:15:00Z) — DONE (validate + record, escalated deviation)
- Gate: branch `research/audit-1587497`, HEAD `1587497`, plan sha256 `9866b5a9d5a7...` matches `.sdlc/spec-gate.json`, exit 0.
- Verify (verbatim brief cmd): `python3 -c "import json; d=json.load(open('docs/plans/2026-11-15-phase1-correctness-fixes-evidence.json')); assert len(d['tasks'])==6"` → `KeyError: 'tasks'`, exit 1 (RED).
- At time of check file used `evidence` key with 5 entries (T1–T5); T6 entry appended here makes 6 under `evidence`.
- Deviation escalated (not absorbed): brief expects `d['tasks']`; file schema is `d['evidence']`. No rename applied — rewriting T1–T5 schema would be scope growth. Orchestrator to resolve (fix validation cmd vs migrate key).
- `sha256sum docs/plans/2026-11-15-phase1-correctness-fixes.md` exit 0; `cat .sdlc/spec-gate.json | head -20` exit 0. No code, no push, no secrets.

## T6 fixup align evidence JSON to tasks schema (2026-11-15) — DONE
- Gate: branch `research/audit-1587497`, HEAD `1587497`, plan sha256 `9866b5a9d5a7...` matches `.sdlc/spec-gate.json`, exit 0.
- RED pre: verbatim `assert len(d['tasks'])==6` → `KeyError: 'tasks'`, exit 1 (file used `evidence` key).
- Fix: migrated `evidence` array → `tasks` (verbatim entries preserved T1–T6); kept `plan`, `plan_sha256` from `.sdlc/spec-gate.json`. No note edits.
- GREEN post: verbatim `assert len(d['tasks'])==6` → `ok`, exit 0. Keys `plan, plan_sha256, tasks`; 6 rows T1–T6 each with task/verify/exit/at. No code, no push, no secrets.

## Close attempt RED-only (2026-11-15) — BLOCKED, gate remains active
- `spec-check.mjs status` exit 0: active gate plan 9866b5a9d5a7 spec 68b3030e5b3f, files 6 allow 2.
- `spec-check.mjs close --help` exit 0 pasted; `spec-check.mjs close` → `[spec-check] missing-task-table: plan has no task table with #, Task, and Verify columns` exit 1.
- Honest outcome RED-only: 6 failed proving bugs, 2 passed (sim probe + audit-14); F1-F6+P1-P2 unmet; reviewer HIGHs open. No green wash; no evidence fabricated.
- Deviation: close blocked by plan schema (no task table), not by evidence. No plan edit (gate-locked, out of scope). Gate left active for orchestrator; Phase1b planning unblocked only via orchestrator decision.

## Deadlock 2026-11-15T (gate-table + double-gate + RED)
- Gate: branch `research/audit-1587497`, HEAD `1587497`, plan sha `9866b5a9` approved; spec docs/specs/2026-11-15-parity-guards-pivot.md; gate active.
- Close needs `#|Task|Verify` + numeric rows (spec-check.mjs:286,298,314) but plan :92 is `| ID | File | Change | Verify |` + T1-T6 rows → `missing-task-table` exit 1.
- Approve blocked double-gate (second gate requires first closed); plan-edit by tool blocked (gate-locked, out of scope).
- Human close needs all exit 0 (:744) but T4 RED by design (6 failed guards, honest failing-first); human stated cant do terminal/file edit.
- No bypass attempted: no plan table edit, no .sdlc touch, no close/approve CLI run, no push, no secrets. Gate left active for orchestrator.

## T3-followup strengthen probe + clarify prose (2026-11-16T01:08:37Z) — DONE (test+docstring only)
- Gate: branch `research/audit-1587497`, HEAD `1587497`, plan sha `9866b5a9` approved; spec F1-F3; `cat .sdlc/spec-gate.json | head -5` exit 0.
- Probe: `test_sim_equivalence_probe` now fast-sim finite-diff (central eps=1e-6) vs QNode `qml.grad` analytic (interface=autograd, 1-2q <=2 layers, atol 1e-5, 2 fixed param sets); `-k test_sim_equivalence_probe` 1 passed exit 0.
- Prose: `quantum/circuits/core.py:212-227` docstring clarified to match `:289-306` (amplitude-embed + V-local RY/RZ+IsingZZ, basis-only XOR note); no math change; `py_compile` OK exit 0.
- Full: `pytest tests/test_phase1_correctness_guards.py -q` 6 failed / 2 passed exit 1 (RED expected: audits 1,2,3,4,11,15; GREEN sim probe + audit-14).
- No push, no secrets, no plan/.sdlc touch.
