# EXPERIMENT_REGISTRY — Runs 1–11 + pivots (carried from handoff, read-only index)

| Run | Description (handoff label) | Status |
|-----|-----------------------------|--------|
| 1–10 | Prior benchmark/parity/scaling runs incl. Run 10 scaling results | Historical — see RESULTS_INDEX.md JSONs; do not re-characterize here |
| 11 | GPU qubit-scaling stress test; analysis refined to highlight expressivity wall (commit `1587497` message) | Historical — HEAD commit subject; details live in notebooks/JSONs, not duplicated here |
| N=3 pivot | Underpowered pivot (n=3) — insufficient for significance | Gap acknowledged; do not cite as evidence of parity or advantage |
| 5-seed parity | Planned 5-seed parity controls | **Not run** — next experimental step once env (`autograd`, `.venv`) is fixed and plan approved |

**Detail (verified 2026-11-15, no re-characterization of results):**
- Index: `RUN_LOG.md:1-326` covers Runs 1–11 (historical, read-only).
- `examples/demos/parity_results.json`: 5 seeds (42, 99, 137, 256, 314), chance-level, raw — no controls; do not cite as evidence.
- `benchmarks/results/benchmark_results.json`: raw artifact, read-only.
- `FINDINGS.md` absent — no findings doc to index.

**Harness gaps blocking next runs (verified 2026-11-15):**
- `collect` 2 ok / 9 ERR: `autograd` import at `classical/nn.py:20` fails; `autograd` absent from `requirements.txt:1-17` + `pyproject.toml:11-23`; `.venv` broken.
- No random-label / positive-control arms; wall-clock timing only (`benchmarks/runner.py:113,118,128,130`); no memory or circuit-count metrics.
- Env caps for any future run: 10–15 min/job, ≤5 epochs, ≤3 seeds, ≤8 workers, ≤3.5G GPU (12 threads i7-8700, 30Gi, P2200 5Gi, use /mnt/nvme).

**Rules:** new runs append new rows with date + command + seed + env hash. Never edit rows for Runs 1–11. Never modify historical JSONs.
