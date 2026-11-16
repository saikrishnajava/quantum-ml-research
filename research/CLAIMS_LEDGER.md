# CLAIMS_LEDGER — claim | source | date (append-only, no edits to history)

| Claim | Source | Date |
|-------|--------|------|
| HEAD is `1587497de77d33942a045b091aaded1ef45b5785` | `git rev-parse HEAD` (live 2026-11-15) | 2026-11-15 |
| Remote is `git@github.com:saikrishnajava/quantum-llm-agent.git`, mismatched vs `quantum-ml-research` name; behind origin/main by 2 | `git remote -v` + `git rev-list --count HEAD..origin/main` (live 2026-11-15) | 2026-11-15 |
| Tree has 21 entries (17 M + 4 ??) | `git status --porcelain` (live 2026-11-15) | 2026-11-15 |
| `tests/unit/test_surrogate.py`: 1 passed, 1 failed (missing `no_entanglement` flag / `parity_from_expectations` hook) | `python3 -m pytest tests/unit/test_surrogate.py -q` (live 2026-11-15) | 2026-11-15 |
| `autograd` not installed in system pip | `pip show autograd` (live 2026-11-15) | 2026-11-15 |
| Parity-guard spec is smoke-only (F1–F6 config guards + P1–P2 parity guards, fail-closed `ValueError`) | `docs/specs/2026-11-15-parity-guards-pivot.md` (read 2026-11-15) | 2026-11-15 |
| Phase 1.1 plan is docs-only (M1–M4, m1 all Not started) | `docs/plans/2026-11-14-phase1-1-major-fixes-progress.md:1-28` (read 2026-11-15) | 2026-11-15 |
| Behind origin/main by 2: `3e75ccc`, `c960bfb` ahead of HEAD; `c960bfb` renames to `quantum-ml-research` | structTruth report (verified 2026-11-15) | 2026-11-15 |
| `FINDINGS.md` absent — must not be cited | structTruth report (verified 2026-11-15) | 2026-11-15 |
| `RUN_LOG.md:1-326` covers Runs 1–11 (historical) | structTruth report (verified 2026-11-15) | 2026-11-15 |
| `parity_results.json`: 5 seeds (42, 99, 137, 256, 314), chance-level, raw | structTruth report (verified 2026-11-15) | 2026-11-15 |
| Concerns 1–4, 11, 12, 15 confirmed with file:line mechanisms (arch-affected: attention mask, train/eval labels, parity leakage, router counting, MoE routing, circuit prose, remainder fallback) | arch report: `hybrid/attention/quantum_attention.py:71-86,:107-131,:64-68,:92-100`; `classical/data.py:26-29,:72-74`; `classical/trainer.py:96-100,:40-44`; `benchmarks/runner.py:98-124,:157-176`; `benchmarks/benchmark_k_parity.py:40-48`; `hybrid/interfaces/model.py:143-148,:199-208`; `quantum/moe/__init__.py:93-121`; `quantum/circuits/core.py:212-227,:289-306,:331-338` (verified 2026-11-15) | 2026-11-15 |
| Concern 5 TBD (cache key + dead eval paths); concern 13 unknown (simulator path); concern 14 weak (gradient threshold + 12q NaN); concerns 6–10 TBD (no mechanism) | arch report: `quantum/optimizations.py:34-38`; `quantum_attention.py:74-88,:90-95,:110-112`; `quantum/simulator/__init__.py:30-92` vs qnode `:230-238`; gradient_flow `>1e-10` + `benchmarks/runner.py:51` (verified 2026-11-15) | 2026-11-15 |
| Harness: `collect` 2 ok / 9 ERR on `autograd` at `classical/nn.py:20`; `autograd` absent from `requirements.txt:1-17` + `pyproject.toml:11-23`; `.venv` broken; artifacts raw; no random-label/positive controls; wall-clock only (`runner.py:113,118,128,130`), no memory/circuit counts | harness report (verified 2026-11-15) | 2026-11-15 |
| Env caps: 12 threads i7-8700, 30Gi (26 avail), P2200 5Gi, /home 94G free use /mnt/nvme; job caps ≤5 epochs ≤3 seeds ≤8 workers ≤3.5G GPU, 10–15m/job | env report (verified 2026-11-15) | 2026-11-15 |

## Harness gaps (structural truth, from handoff — re-verify before use)
- No control arms recorded for parity claims.
- N=3 pivot underpowered; 5-seed parity not yet run (see EXPERIMENT_REGISTRY.md).
- `.venv` dependency state unchecked; system-pip `autograd` gap blocks any gradient-dependent repro.
- Historical JSONs (`benchmark_results.json`, `parity_results.json`) must not be edited to close gaps — new runs get new registry entries.
