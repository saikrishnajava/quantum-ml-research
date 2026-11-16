# STATE — Persistent Research Workspace

**Date (UTC):** 2026-11-15
**Commit:** `1587497de77d33942a045b091aaded1ef45b5785`
**Remote:** `git@github.com:saikrishnajava/quantum-llm-agent.git`
  - Name mismatch vs working-tree project name `quantum-ml-research` (origin/main renames to `quantum-ml-research` in `c960bfb`).
**Branch:** `research/audit-1587497` (local-only, base `1587497de77d33942a045b091aaded1ef45b5785`)
**Status:** `git status --porcelain` = **21 entries: 17 M + 4 ??**
  - 17 modified: README.md, benchmarks/analysis/statistics.py, benchmarks/runner.py, examples/demos/experiment_parity.py, examples/demos/parity_results.json, hybrid/attention/quantum_attention.py, hybrid/interfaces/model.py, notebooks/quantum_gpu_scaling.ipynb, notebooks/quantum_llm_colab.ipynb, pyproject.toml, quantum/backends/manager.py, quantum/circuits/core.py, quantum/moe/__init__.py, quantum/simulator/__init__.py, requirements.txt, setup.sh, setup_gpu.sh
  - 4 untracked paths: docs/, requirements.lock, tests/test_phase1_1_guards.py, tests/unit/test_surrogate.py
**Behind:** 2 commits behind `origin/main` (`3e75ccc`, `c960bfb` ahead of HEAD).
**Tag:** `v0.1.0` (lightweight).

## What was verified (3 audits + branch + enrichment + 2 critics, carried from handoff)
1. Commit/remote/status audit (this file's header — live-verified 2026-11-15).
2. Plan/spec audit: `docs/plans/2026-11-14-phase1-1-major-fixes-progress.md:1-28` + `docs/specs/2026-11-15-parity-guards-pivot.md` (F1–F6 + P1–P2, smoke-only).
3. Test/gap audit: `tests/unit/test_surrogate.py` (1 passed, 1 failed) + `pip show autograd` (not found).
4. Branch audit: `research/audit-1587497` HEAD `1587497de77d33942a045b091aaded1ef45b5785` verified (no push, no rebase, no history rewrite).
5. Docs enrichment audit: `research/AUDIT.md` cats 1–6 + 15-row mechanism table, `research/PLAN.md`, `research/CLAIMS_LEDGER.md`, `research/EXPERIMENT_REGISTRY.md` Runs 1–11.
6. Critics: 2 critics clean/pass (wording fixes applied this iter; no code).
- Note: `e161aed0` (cited `research/AUDIT.md:20`) is unsourced-carried — source pending, do NOT treat as verified; do not invent source.

## Hypothesis
**TBD** — not yet established. No claim of advantage / parity / expressivity wall is endorsed here; see FINAL_ASSESSMENT.md.

## Completed
- Workspace scaffold (this `research/` dir, docs-only, reversible).
- Base-state capture (commit, remote, dirty-tree count, behind-count, tag).
- Live test probe: `python3 -m pytest tests/unit/test_surrogate.py -q` → 1 passed, 1 failed (`test_no_entanglement_degrades_parity` asserts missing `no_entanglement` flag / `parity_from_expectations` hook).
- Dependency probe: `pip show autograd` → `Package(s) not found: autograd`.
- Artifact location: `benchmarks/results/benchmark_results.json`, `examples/demos/parity_results.json`.
- Docs-only enrichment 2026-11-15: updated working-tree research/AUDIT.md (no git history rewrite) (cats 1–6 + 15-row mechanism table), `research/PLAN.md` (mechanism + reproducer/test-gap + fix precondition), appended structTruth/arch/harness rows to `research/CLAIMS_LEDGER.md`, added Runs 1–11 detail + harness gaps to `research/EXPERIMENT_REGISTRY.md`. No training, no installs, no background jobs.

## Running
- Nothing running (docs-only handoff complete; no background jobs, no training, no installs).

## Artifact locations (read-only, DO NOT modify)
- `benchmarks/results/benchmark_results.json`
- `examples/demos/parity_results.json`

## Budget
- 2 of 3 used going into this task, 1 remaining; this task consumes last → 3/3 used, budget exhausted. Docs-only unless a new approved plan authorizes code.

## Exact next commands (for fresh agent, in order)
- Await human approval for Phase1 fix plan; no code until approved.
```
git branch --show-current; git rev-parse HEAD; ls research/
```
Then (budget exhausted 3/3; re-verify TBD/unknown/weak + concerns 6–10 file:lines live before any code plan):
```
python3 -m pytest tests/unit/test_surrogate.py -q
pip show autograd
```
Then:
```
git status --porcelain; git rev-parse HEAD
```

## Blockers
1. `autograd` missing in system pip (confirmed `Package(s) not found: autograd`).
2. `.venv` present (`.venv/bin/python3.12`) but dependency state unchecked / reported broken in handoff — do not assume it works; verify before use, do not reinstall without approval.
3. No controls established for parity claims (see EXPERIMENT_REGISTRY.md N=3 pivot + 5-seed parity gap).
4. 1 failing surrogate (`test_no_entanglement_degrades_parity`); concerns 6–10 need file:line, 13 unknown, 14 weak — re-verify live before any code plan.

## Recovery
```
git status --porcelain; git rev-parse HEAD
```
Expected HEAD: `1587497de77d33942a045b091aaded1ef45b5785`. If mismatch, stop and re-audit before writing anything.

## Current (SESSION handoff 2026-11-16, fail-open — no gate active)
- Authorization: user go-ahead 2026-11-16.
- Branch: `research/audit-1587497` @ `1587497` (verified live: `git branch --show-current; git rev-parse --short HEAD` → `research/audit-1587497` / `1587497`; full HEAD `1587497de77d33942a045b091aaded1ef45b5785`).
- Phase1b: CLOSED 2026-11-16 — 6/6 exit 0 (guards pre-existing zero-line, smoke 4 passed).
- Limitations: F1 wording, p=0.535 pointer, LOWs (carried, see ledger).
- Artifacts: evidence JSON (6 ints), progress file, guard files (read-only pointers; do not modify history).
- Budget: Phase1c planning — 1 running.
- Blockers: none (gate clear, tools unblocked).

## Next
- Approve Phase1c → execute → critic → close.
- Recovery: `git status --porcelain; git rev-parse HEAD; ls research/` (expected short `1587497`).

## Current (2026-11-16, Track C banked — no gate fail-open)
- Current: Track C informative negative BANKED (`research/FINAL_ASSESSMENT.md`).
- Headline: "Parity gains vanish under disjoint splits; MoE dense-train costs ~2× — no advantage demonstrated."
- Proven: P1 overlap +0.229 (disjoint-at-chance), P3 dense ~2× (1.89–2.03); P2 honest-fail (balanced 0.25).
- Auth: user big-win bounded; no gate fail-open carried.
- Caps noted: local-only, no spend, tiny configs, seeds ≤3, no sweeps, 600s timeout each.
- Touched (this task): `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

## Current (2026-11-16, FINAL_ASSESSMENT v2 — decisive P2-redo + equality)
- Current: Track C decisive informative negative BANKED (`research/FINAL_ASSESSMENT.md` v2).
- XOR redo (matched ~1218 params): classical_bal 0.9722 ([1,0.9167,1]) vs quantum 0.4912 ([0.51,0.48,0.48]) vs chance 0.50.
- Equality confirmatory: classical 1.0 vs quantum 0.5206.
- Carried: P1 +0.229 inflation; P3 1.96× cost; guards 6/6 + Phase1c 4/4; critics clean/pass.
- P2-pilot confound superseded by redo; F1 wording fixed; LOWs deferred with reasons.
- Headline: "Same-token quantum head fails cross-token routing that matched classical learns (0.97 vs 0.49); parity gains are overlap inflation; dense-train ~2×."
- Auth: user go-ahead; fail-open (no gate active). Branch `research/audit-1587497` local-only.
- Touched (this task): `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

## Next (confirmatory lock or stop)
- Confirmatory lock (needs fresh gate): fresh seeds + held-out task, then close — or STOP (current v2 stands as banked negative).
- No scale-up, no code until explicit approval; no fail-open for new code.
- Repro (4 cmds): `pytest -q tests/test_pilots_overlap.py`, `tests/test_pilots_moe_cost.py`, `tests/test_pilots_crosstoken.py`, `tests/test_phase1_1_guards.py` under `.venv/bin/python`.

## Current (2026-11-16, FINAL_ASSESSMENT v3 — confirmatory binary PASS)
- Current: confirmatory LOCKED→executed ONCE — fresh seeds 7/21/123, held-out XOR(0,3,2,1)+EQ(1,3,2), fixed model, run-once marker, exit 0 2 passed 0.78s.
- Verdict: binary PASS (pre-registered falsifier thresholds met on fresh data — direction replicated).
- Capture flaw disclosed: `-q` hid per-seed print lines, finiteness asserted not values — NO confirmatory effect-size/CI claim; exploratory priors stand (0.97/0.49, +0.229, 1.96× with own CIs).
- Leakage check passed; no amendments post-view. Contribution: Track C (independently replicated binary) + B-lite. Headline unchanged in magnitude, upgraded in independence.
- Auth: user go-ahead; fail-open. Branch `research/audit-1587497` local-only.
- Touched (this task): `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

## Next (post-v3: stop or re-lock with -s)
- Do NOT re-run confirmatory (run-once: second invocation must refuse). Freeze verify only: `git branch --show-current; git rev-parse --short HEAD; git status --porcelain; ls research/`.
- If magnitude needed: new-seed re-lock with `-s` capture (fresh gate required), or STOP (v3 stands).

## Current (2026-11-16, FINAL_ASSESSMENT v4 — confirmatory-mag quantitative PASS)
- Current: confirmatory-mag LOCKED→executed ONCE — fresh seeds [11,33,55], held-out XOR(1,3)+EQ(2,1,1), fixed model, run-once marker, `-s` capture.
- XOR diffs 0.4297/0.5203/0.5000 mean 0.4833 CI [0.3652,0.6014]; EQ diffs 0.5424/0.5385/0.5085 mean 0.5298 CI [0.4837,0.5758]; both CIs >0.20; params matched; wall 0.1s/900.
- Contribution: Track C quantitative (2 tasks, Bonferroni-noted) + B-lite; NO advantage.
- Headline: "Fresh-seed held-out replication: quantum gaps persist (XOR +0.48 [0.37,0.60], EQ +0.53 [0.48,0.58]) — no advantage demonstrated."
- Limits: MLP proxy, tiny, task-specific.
- Auth: keep-on-continue; fail-open. Branch `research/audit-1587497` local-only.
- Touched (this task): `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

## Next (post-v4: write-up or stop)
- Do NOT re-run confirmatory tests (run-once). Freeze verify only: `git branch --show-current; git rev-parse --short HEAD; git status --porcelain; ls research/`.
- Repro (4 cmds incl. mag `-s`, mag run-once — do not re-invoke): `pytest -q tests/test_pilots_overlap.py`, `tests/test_pilots_moe_cost.py`, `tests/test_pilots_crosstoken.py` under `.venv/bin/python`, plus `pytest tests/test_confirmatory_mag.py -s` (locked single invocation record only).

## Current (2026-11-16, FINAL_ASSESSMENT v5 — Phase 6 repro 3/3, STOP-or-writeup)
- Current: Phase 6 repro 3/3 — verify 5 tests ~6s (`bash docs/verify-track-c.sh` exit 0), recompute OVERALL PASS, evidence 3/3; critics clean/PASS.
- Raw `benchmarks/results/track-c-repro.jsonl` ignored-exception (gitignored, regenerable ~6s, no force-add).
- Confirmatory locks untouched (run-once preserved).
- Contribution stands: Track C quantitative + B-lite; headline unchanged.
- Repro: `bash docs/verify-track-c.sh` + `.venv/bin/python scripts/recompute-track-c.py --input benchmarks/results/track-c-repro.jsonl`.
- Limits as before + raw-ephemeral.
- Auth: keep-on-continue; fail-open. Branch `research/audit-1587497` local-only.
- Touched (this task): `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

## Next (post-v5: stop-or-writeup)
- Next: write-up or stop (no further experiments without fresh approval).
