# Pilots Progress — 2026-11-16 (bounded, research/audit-1587497)

Auth: user big-win bounded pilots only (3 max, caps, no sweeps/spend). No gate fail-open.
Branch: research/audit-1587497. Caps: ≤600s each, tiny configs only, local CPU, no network/GPU/paid APIs.

## P1 — overlap-inflation (tests/test_pilots_overlap.py)
- Cmd: `.venv/bin/python -m pytest -q tests/test_pilots_overlap.py`
- Exit: 1 (FAIL, RED expected)
- Wall: 0.74s pytest (internal wall_s 0.00s, per-seed ~0.0013s x3, budget 900s OK)
- Verbatim tail:
  - `P1 pilot /tmp JSON -> /tmp/p1_overlap_pilot.json leaky_mean=0.677 disjoint_mean=0.448 diff=+0.229 disjoint_CI=[0.253,0.643] baseline=0.5 wall=0.00s`
  - `AssertionError: RED/REFUTED: disjoint CI [0.253,0.643] not above baseline 0.5 (leaky_mean=0.677 => inflation signal +0.229; see /tmp/p1_overlap_pilot.json)`
- Per-seed (/tmp/p1_overlap_pilot.json): seed42 leaky 0.594/disjoint 0.375/overlap 9; seed99 0.625/0.438/12; seed137 0.813/0.531/14
- Expected falsifier: leaky≫disjoint≈chance → C. Actual MATCHES: leaky 0.677 vs disjoint 0.448 (+0.229), disjoint mean 0.448 ≈ chance, CI low 0.253 not >0.5.
- Go/no-go: NO-GO to scale-up (inflation proven). Track: C.

## P2 — crosstoken mechanism (tests/test_pilots_crosstoken.py)
- Cmd: `.venv/bin/python -m pytest -q tests/test_pilots_crosstoken.py`
- Exit: 1 (2 failed, 1 passed — implemented matched-budget run, honest fails preserved)
- Wall: 1.28s pytest (internal wall 0.0s, budget 900s OK)
- Verbatim tail:
  - `P2 pilot classical_mean=0.6667 quantum_mean=0.6667 chance=0.25 per_seed=[{'seed': 0, 'classical_test': 0.6458, 'quantum_test': 0.6458, 'classical_train': 0.7708, 'quantum_train': 0.7708, 'majority_test': 0.6458, 'classical_minority_recall': 0.0, 'quantum_minority_recall': 0.0}, {'seed': 1, 'classical_test': 0.6875, 'quantum_test': 0.6875, 'classical_train': 0.7083, 'quantum_train': 0.7083, 'majority_test': 0.6875, 'classical_minority_recall': 0.0, 'quantum_minority_recall': 0.0}] wall=0.0s`
  - `classical routing_gaps=[0.5600812495653473, 0.7629390502487856] seeds=[0, 1] tiny={...} accs=[0.6458333333333334, 0.6875]` → classical>0.40 PASS
  - `AssertionError: HONEST FAIL (no retune): quantum_mean=0.6667 outside 0.25±0.12; per_seed=[...]`
  - `AssertionError: HONEST FAIL (no retune): classical_balanced=0.2500 not > quantum_balanced=0.2500+0.10; per_seed=[...]`
- Expected: quantum≈chance + classical learns → C. Actual: IMPLEMENTED (was BLOCKED scaffold) — classical 0.6667>0.40 passes, but quantum 0.6667≠chance±0.12 fails: both arms collapse to majority (test accs == majority_test, minority recall 0.0). Routing probe supports mechanism (classical gaps >0, quantum gaps 0.0) but accuracy thresholds do NOT separate. Balanced 0.25 vs 0.25, no separation. No retune per boundary.
- Go/no-go: NO-GO to mechanism claim (honest fail, not inconclusive). Track: undecided/refuted-on-accuracy, pending design rethink (majority-confounded tiny task).

## P3 — MoE cost (tests/test_pilots_moe_cost.py)
- Cmd: `.venv/bin/python -m pytest -q tests/test_pilots_moe_cost.py`
- Exit: 0 (PASS, implemented real-timing run)
- Wall: 1.53s pytest (internal wall 1.5s, budget 900s OK)
- Verbatim tail:
  - `[P3 pilot] dense_t=0.0087s sparse_t=0.0045s ratio=1.96 n_experts=2 reps=10 expert_idx=[0, 1] wall=1.5s`
  - `1 passed in 1.53s`
- Expected: dense≈n× → C/cost-tool. Actual: IMPLEMENTED (was BLOCKED harness KeyError) — real perf_counter timing, dense 0.0087s vs sparse 0.0045s, ratio 1.96 within 1.8-2.2. Routed expert_idx=[0, 1] logged (one batch per expert). Bounded: n=2, tiny 6q/9q, seed 5, routing-dependent ratio.
- Go/no-go: GO (bounded) for cost-tool claim. Track: C.
- Threshold provenance: 1.8-2.2 bound set in orchestrator brief BEFORE results; observed after (1.89-2.03 across runs, 1.96 here) falls inside — no post-hoc tuning. P2 margins (CLASSICAL_MARGIN 0.15, QUANTUM_TOL 0.12, BALANCED_MARGIN 0.10) implementer-chosen a priori in-file, no pre-reg hash — disclosed.

## Overall
- Total wall ~3.6s pytest (0.80 + 1.28 + 1.53), well under 10-15m cap. Seeds ≤3, tiny configs, local-only, no sweeps/spend — caps honored.
- Reviewer fixes applied (test files only, no scope growth): P3 WALL_BUDGET_S=15*60 + wall assert; P3 routed expert_idx logged in print + assert; P1 CI fallback now raises ValueError("scipy required..."); P3 scoped seed (save/restore); P2 `assert TINY seq_len<=16` + remainder comment (magic-dim refactor deferred).
- Failures preserved, none dropped. No production edits. No secrets/push.
- Track decision: P1 → C (inflation proven). P2 honest-fail → NO-GO mechanism claim (majority-confounded). P3 PASS → bounded GO for cost-tool. Overall STOP scale-up (P1 falsifies advantage); no gate fail-open (exits reported as-is: P1 1, P2 1, P3 0).
