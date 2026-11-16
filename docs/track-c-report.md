# Track C Report — Negative Result: Same-Token Quantum Head Associated with Chance-Level Routing Under Tested Conditions; No Advantage Observed

**Status:** Track C banked informative negative. No quantum advantage observed.
**Auth:** user "go ahead" (write-up).
**Branch:** `research/audit-1587497`.
**Gate:** no gate active; no gate fail-open. Record-only from assessed evidence.
**Sources (read-only):** `research/FINAL_ASSESSMENT.md` v5; `docs/plans/2026-11-17-confirmatory-mag-progress.md`; `docs/plans/2026-11-17-p2-redo-progress.md`; `docs/plans/2026-11-16-pilots-progress.md`.

## Abstract

Headline (exploratory): "Same-token quantum head fails cross-token routing that matched classical learns (0.97 vs 0.49); parity gains are overlap inflation; dense-train ~2x." Headline (confirmatory-mag): "Fresh-seed held-out replication: quantum gaps persist (XOR +0.48 [0.37,0.60], EQ +0.53 [0.48,0.58]) — no advantage demonstrated." This report records paired pilots under tested conditions. No quantum advantage was observed or claimed under tested conditions.

## Methods

- Same-token loop under test: `hybrid/attention/quantum_attention.py:79-86` — `circuit(q[b, s], k[b, s], v[b, s])` uses the same `s` for q/k/v with no cross-`s` mixing. Proxy isolation of this property (test-file description; MLP proxy, no circuit): `tests/test_p2_redo.py:101-110` (`_head_features`), where the classical arm sees all positions (ordered concat) and the quantum arm sees the last-position block only with zeros elsewhere; described also in `tests/test_pilots_crosstoken.py:15-22`.
- Splits: P1 leaky vs disjoint parity split comparison, recorded as overlap-inflation pilot.
- Matched budgets: classical vs quantum heads compared at matched params ~1218 (per `research/FINAL_ASSESSMENT.md:15,27` + `docs/plans/2026-11-17-p2-redo-progress.md:27`), tiny configs (seeds ≤ 3 per task, epochs ≤ 5 per `tests/test_p2_redo.py:55,182` + `docs/plans/2026-11-17-p2-redo-progress.md:6,71`), identical init and shuffle order per seed in the redo (per `tests/test_p2_redo.py:118,128`).
- MoE cost: dense-train vs single-expert (sparse) timing comparison at n_experts=2 (per `tests/test_pilots_moe_cost.py:46,54` + `docs/plans/2026-11-16-pilots-progress.md:34`), associated routing `expert_idx=[0, 1]`.
- Language: associations only, under tested conditions; no causal claim beyond the recorded numbers.

## Results

- P1 overlap-inflation: leaky 0.677 vs disjoint 0.448, diff +0.229; disjoint CI [0.253, 0.643] (per `docs/plans/2026-11-16-pilots-progress.md:11-12`), straddles chance (v5 wording per `research/FINAL_ASSESSMENT.md:29`).
- P2-redo XOR (matched ~1218 params): classical_bal 0.9722 vs quantum_bal 0.4912 vs chance 0.50.
- Equality control (matched setup): classical_bal 1.0 vs quantum_bal 0.5206, near chance.
- P3 MoE cost: dense/sparse ratio observed 1.89–2.03 across runs (1.96 in the bounded run), within the pre-set 1.8–2.2 band.
- Confirmatory-mag held-out replication: XOR diff +0.48, CI [0.37, 0.60]; EQ diff +0.53, CI [0.48, 0.58]; both CIs above the 0.20 threshold as recorded observations.

## Limitations

- MLP proxy, no circuit: all accuracy numbers are associated with a small classical MLP proxy of the same-token restriction, not with a quantum circuit or hardware run; no hardware claim is associated with these numbers under tested conditions.
- Tiny sampling: each task used at most 3 seeds with few epochs, so sampling noise is only partially mapped and task-local CIs are narrow in scope; no broader statistical generalization is recorded.
- Task-specific: observations are associated only with the tested XOR routing, equality routing, parity leaky/disjoint, and 2-expert MoE timing tasks; no scaling, transfer, or other-task claim is recorded.
- venv-only environment: runs were local CPU in `.venv` with small configs; environment dependence outside that setup was not assessed.
- Raw-ephemeral and regenerable: the raw `benchmarks/results/track-c-repro.jsonl` rows are gitignored and regenerable in seconds via the verify script; they are not banked as persisted artifacts.
- Run-once confirmatory locks: the confirmatory and confirmatory-mag tests are locked run-once invocations with markers that must refuse a second invocation; they were not re-run during repro closeout and must not be re-run to verify.
- Additional bounds: the MoE ratio is routing-dependent; the P2 pilot (superseded, majority-confounded, balanced 0.25 with no separation) is not used as evidence beyond its honest-fail record; the historical p=0.535 pointer and any hardware or scaling speculation are out of scope with no new claim depending on them.

## Repro

Safe re-runnable pilots and guards (do NOT re-run confirmatory tests):

```bash
bash docs/verify-track-c.sh
.venv/bin/python scripts/recompute-track-c.py --input benchmarks/results/track-c-repro.jsonl
.venv/bin/python -m pytest -q tests/test_pilots_overlap.py
.venv/bin/python -m pytest -q tests/test_pilots_moe_cost.py
.venv/bin/python -m pytest -q tests/test_pilots_crosstoken.py
.venv/bin/python -m pytest -q tests/test_phase1_1_guards.py
```

Do-NOT-rerun note: do NOT re-run `tests/test_confirmatory_routing.py` or `tests/test_confirmatory_mag.py` to verify; both are run-once locked and a second invocation must refuse via the run-once marker. The recorded confirmatory outcomes are read from the banked progress files only.

## Touched

- `docs/track-c-report.md` (new; this file only).
