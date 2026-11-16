# PLAN — Phase 1, 15 concerns (Phase-1-ready: mechanism + reproducer/test-gap + fix precondition, no code yet)

Branch: research/audit-1587497 / base 1587497

**Scope refs:** `docs/plans/2026-11-14-phase1-1-major-fixes-progress.md:1-28` (M1–M4, m1 docs-only) + `docs/plans/2026-11-15-research-audit-progress.md:1-33` (branch ledger).
**Mechanism source:** `research/AUDIT.md` Phase-1 table (structTruth + arch + harness reports). Re-verify file:line live before any code.
**Rule:** no code edits under this task. Each row's fix precondition must be satisfied first.

| # | Status | Mechanism (file:line) | Reproducer / test gap | Fix precondition (no code yet) |
|---|--------|----------------------|----------------------|-------------------------------|
| 1 | confirmed | Same-token loop + mask never to quantum: `hybrid/attention/quantum_attention.py:71-86`, `:107-131`, `:64-68`; `quantum/moe/__init__.py:111-114` | No mask-forwarding test; read loop + mask handling | Confirm live which forward path drops mask; write failing mask test first |
| 2 | confirmed | All-pos loss vs last-pos acc + mask never passed: `classical/data.py:26-29`, `classical/trainer.py:96-100` vs `benchmarks/runner.py:157-176`, `hybrid/interfaces/model.py:143-148` + `runner.py:98-124` | No train/eval label-alignment test; grep mask plumbing | Agree single label convention (all-pos vs last-pos) + mask wiring; failing alignment test first |
| 3 | confirmed | Overlap + contiguous + correlated tasks: `benchmarks/benchmark_k_parity.py:40-48`, `classical/data.py:72-74` | No disjoint-split / seed-sweep test | Define disjoint sampling + seed protocol; failing leakage test first |
| 4 | confirmed | Router gate misclassified: `hybrid/interfaces/model.py:199-208` + `classical/trainer.py:40-44` | No param-classification test | Agree router-attribution rule; failing counting test first |
| 5 | TBD | Cache key excludes params + dead eval paths: `quantum/optimizations.py:34-38`, `quantum_attention.py:74-88`, `:90-95`, `:110-112` | No cache-invalidation test | Re-verify dead-path reachability live; failing cache test first |
| 6 | TBD | TBD — no file:line in verified reports | Missing reproducer | Land file:line + mechanism in AUDIT.md before any fix |
| 7 | TBD | TBD — no file:line in verified reports | Missing reproducer | Land file:line + mechanism in AUDIT.md before any fix |
| 8 | TBD | TBD — no file:line in verified reports | Missing reproducer | Land file:line + mechanism in AUDIT.md before any fix |
| 9 | TBD | TBD — no file:line in verified reports | Missing reproducer | Land file:line + mechanism in AUDIT.md before any fix |
| 10 | TBD | TBD — no file:line in verified reports | Missing reproducer | Land file:line + mechanism in AUDIT.md before any fix |
| 11 | confirmed | Dense-train vs sparse-eval MoE: `quantum/moe/__init__.py:105-121` vs `:93-103` | No train-eval routing parity test | Agree single routing mode for comparison; failing parity test first |
| 12 | confirmed | Prose vs actual circuit: `quantum/circuits/core.py:212-227` vs `:289-306` + `:331-338` | No prose-vs-code test | Correct prose or code (decision logged); failing circuit-semantics test first |
| 13 | unknown | Unvalidated vs qnode path: `quantum/simulator/__init__.py:30-92` vs `:230-238` | Needs path-resolution probe | Resolve which path runs live; failing path test first |
| 14 | weak | Loose gradient threshold + 12q NaN: gradient_flow tests `>1e-10`, `benchmarks/runner.py:51` | Needs tighter threshold + NaN repro | Re-run gradient + 12q probe; agree threshold before fix |
| 15 | confirmed | Remainder classical fallback: `hybrid/attention/quantum_attention.py:92-100` | No remainder-path test | Decide explicit fallback policy; failing remainder test first |

**Next:** fresh agent re-verifies concerns 5, 13, 14 (TBD/unknown/weak) plus 6–10 (missing) live before any code; budget 2 of 3 used going in, 1 remaining — this task consumes last (3/3 exhausted after; see `research/STATE.md` Budget).
