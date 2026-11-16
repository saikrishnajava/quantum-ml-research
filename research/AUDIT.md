# AUDIT — Truth Categories 1–6 + Phase 1 concerns 1–15 (Phase-1-ready)

**Date (UTC):** 2026-11-15
**Branch:** `research/audit-1587497` (local-only, base `1587497de77d33942a045b091aaded1ef45b5785`)
**Scope:** MISSION PHASE1 concerns 1–15 + truth cats 1–6. No code, no installs, no training. Docs-only, reversible.
**Scope refs:** `docs/plans/2026-11-14-phase1-1-major-fixes-progress.md:1-28` (M1–M4, m1 docs-only) + `docs/plans/2026-11-15-research-audit-progress.md:1-33` (branch ledger, 1 of 3 iters used).
**Sources (verified explorer reports, carried — re-verify file:line before code):** structTruth (commit/remote/status) + arch (code mechanisms) + harness (test/env gaps).

## Truth categories 1–6

| # | Category | Meaning | Current value (verified, re-check before code) |
|---|----------|---------|-----------------------------------------------|
| 1 | Commit | Exact HEAD hash | `1587497de77d33942a045b091aaded1ef45b5785` via `git rev-parse HEAD` |
| 2 | Remote | Fetch/push URL + name mismatch + behind-count | `git@github.com:saikrishnajava/quantum-llm-agent.git` vs working name `quantum-ml-research`; behind `origin/main` by 2 (`3e75ccc`, `c960bfb`; `c960bfb` renames to `quantum-ml-research`) |
| 3 | Status | Dirty-tree inventory | 17 M + 4 ?? = 21 entries (17 modified incl. `hybrid/attention/quantum_attention.py`, `quantum/circuits/core.py`, `quantum/moe/__init__.py`, `quantum/simulator/__init__.py`, `benchmarks/runner.py`; 4 untracked: `docs/`, `requirements.lock`, `tests/test_phase1_1_guards.py`, `tests/unit/test_surrogate.py`) |
| 4 | Plan/spec | Scope docs actually read | `docs/plans/2026-11-14-phase1-1-major-fixes-progress.md:1-28` (M1–M4 + m1, all Not started, docs-only) + parity-guards pivot spec (F1–F6 + P1–P2, smoke-only); `FINDINGS.md` absent — do not cite it |
| 5 | Test gap | Failing/missing coverage | `collect` 2 ok / 9 ERR on `autograd` import at `classical/nn.py:20`; `autograd` absent from `requirements.txt:1-17` + `pyproject.toml:11-23`; `.venv` present but broken; `tests/unit/test_surrogate.py` 1 passed / 1 failed; `RUN_LOG.md:1-326` Runs 1–11 historical; `parity_results.json` 5 seeds (42, 99, 137, 256, 314) chance-level, raw, no controls |
| 6 | Claim hygiene | No historical-result mutation | `benchmarks/results/benchmark_results.json` (raw) + `examples/demos/parity_results.json` (raw) are read-only; this workspace adds claims only in `research/CLAIMS_LEDGER.md`; no random-label / positive-control arms exist yet; wall-clock only (`benchmarks/runner.py:113,118,128,130`), no memory / circuit-count metrics |

**Prior hashes where relevant:** `1587497`, `e161aed0` (carried; context not re-resolved here).
**Tag:** `v0.1.0` lightweight (carried, untouched).

## Phase 1 concerns 1–15 — mechanism table (status + file:line + mechanism + affected conclusions + reproducer)

| # | Status | File:line | 1-line mechanism | Affected conclusions | Reproducer / test-gap pointer |
|---|--------|-----------|------------------|----------------------|-------------------------------|
| 1 | confirmed | `hybrid/attention/quantum_attention.py:71-86`, `:107-131`, `:64-68`; `quantum/moe/__init__.py:111-114` | Per-token loop re-encodes same token; padding mask applied on classical path only, never forwarded to quantum path | Any attention/MoE quality or masking claim is suspect until mask is wired through | Read `:71-86` loop + `:107-131` mask handling; no mask-forwarding test exists |
| 2 | confirmed | `classical/data.py:26-29`; `classical/trainer.py:96-100` vs `benchmarks/runner.py:157-176`; `hybrid/interfaces/model.py:143-148` + `benchmarks/runner.py:98-124` | Shift/label mismatch: all-position loss in training vs last-position accuracy in eval; mask built never passed (`model.py:143-148`, `runner.py:98-124`) | Train/eval numbers not comparable; reported accuracy does not measure trained objective | Diff `trainer.py:96-100` vs `runner.py:157-176`; grep mask plumbing `runner.py:98-124` |
| 3 | confirmed | `benchmarks/benchmark_k_parity.py:40-48`; `classical/data.py:72-74` | Parity sample overlap (1000 draws from 256 space) + contiguous slices + boolean/correlated/sequence_decision reuse same underlying bits | Parity / generalization claims confounded by leakage and correlated subtasks | Read `:40-48` sampling + `data.py:72-74`; no disjoint-split or seed-sweep test |
| 4 | confirmed | `hybrid/interfaces/model.py:199-208` + `classical/trainer.py:40-44` | Param counter mislabels MoE router/gate `Linear` as classical, skewing quantum-vs-classical attribution | Any parameter-share / efficiency claim misattributes router cost | Read `model.py:199-208` + `trainer.py:40-44`; no param-classification test |
| 5 | TBD | `quantum/optimizations.py:34-38`; `hybrid/attention/quantum_attention.py:74-88`, `:90-95`, `:110-112` | Cache key excludes params; eval-gate + embedding (`:90-95`) + `invalidate` (`:110-112`) paths are dead | Cache-correctness and eval-path claims unverified; stale-cache risk | Read `optimizations.py:34-38` + `:74-88` gate; no cache-invalidation test — re-verify before code |
| 6 | TBD | (no file:line in verified reports) | Mechanism not established in 3 reports — do not assume | No conclusion may cite concern 6 | Gap: needs fresh file:line + reproducer before Phase-1 fix |
| 7 | TBD | (no file:line in verified reports) | Mechanism not established in 3 reports — do not assume | No conclusion may cite concern 7 | Gap: needs fresh file:line + reproducer before Phase-1 fix |
| 8 | TBD | (no file:line in verified reports) | Mechanism not established in 3 reports — do not assume | No conclusion may cite concern 8 | Gap: needs fresh file:line + reproducer before Phase-1 fix |
| 9 | TBD | (no file:line in verified reports) | Mechanism not established in 3 reports — do not assume | No conclusion may cite concern 9 | Gap: needs fresh file:line + reproducer before Phase-1 fix |
| 10 | TBD | (no file:line in verified reports) | Mechanism not established in 3 reports — do not assume | No conclusion may cite concern 10 | Gap: needs fresh file:line + reproducer before Phase-1 fix |
| 11 | confirmed | `quantum/moe/__init__.py:105-121` vs `:93-103` | Dense routing in train vs sparse top-k in eval — train/eval distribution mismatch | MoE quality / routing claims compare different forward paths | Diff `:105-121` vs `:93-103`; no train-eval parity test |
| 12 | confirmed | `quantum/circuits/core.py:212-227` (prose) vs `:289-306` (actual) + `:331-338` | Prose description of entangling/amplitude path diverges from implemented circuit (`:289-306`, `:331-338`) | Expressivity / circuit-semantics claims rest on prose, not code | Read `:212-227` vs `:289-306`; no prose-vs-code test |
| 13 | unknown | `quantum/simulator/__init__.py:30-92` vs qnode `:230-238` | Unvalidated wire/noise path (`:30-92`) vs validated qnode path (`:230-238`) — which path runs is unconfirmed | Simulator fidelity claims cannot be cited either way | Read `:30-92` vs `:230-238`; needs path-resolution probe — re-verify before code |
| 14 | weak | gradient_flow tests (`>1e-10` only) + `benchmarks/runner.py:51` | Gradient test threshold too loose to detect vanishing flow; 12-qubit NaN observed at `runner.py:51` | Trainability / scaling claims weakly supported at best | Re-run gradient_flow tests + 12q NaN repro; needs tighter threshold — re-verify before code |
| 15 | confirmed | `hybrid/attention/quantum_attention.py:92-100` | Non-divisible sequence remainder silently falls back to classical path | Hybrid-vs-classical attribution silently shifts with sequence length | Read `:92-100` fallback; no remainder-path test |

**How to use this table:** each row is a fix precondition — re-verify its file:line live, then add the reproducer in `research/PLAN.md` before any code. Concerns 6–10 must not be cited until a file:line + mechanism lands here.
