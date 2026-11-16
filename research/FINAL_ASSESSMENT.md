# FINAL_ASSESSMENT v2 — Track C decisive (banked 2026-11-16)

**Status:** TRACK C BANKED — decisive informative negative. NO quantum advantage shown.
**Auth:** user go-ahead; fail-open (no gate active).
**Branch:** `research/audit-1587497` (local-only).

## Headline
"Same-token quantum head fails cross-token routing that matched classical learns (0.97 vs 0.49); parity gains are overlap inflation; dense-train ~2×."

## 1. Built
- Guards: Phase1b 6/6 exit 0 + Phase1c 4/4 (pre-existing zero-line; smoke passed).
- Pilots: P1 proven, P3 proven, P2-redo decisive + equality confirmatory.
  - P1 overlap-inflation: RED-expected (exit 1), then implemented with paired evidence.
  - P2-pilot (superseded): honest-fail, majority-confounded (balanced 0.25, no separation) — confound fixed by redo.
  - P2-redo XOR (decisive): matched-param (~1218 params) classical_bal 0.9722 vs quantum 0.4912 vs chance 0.50.
  - Equality (confirmatory): classical 1.0 vs quantum 0.5206.
  - P3 MoE-cost: PASS (ratio 1.96 in 1.8–2.2, expert_idx=[0,1]).
- Critics: clean/pass.
- Harness: collect 62/0, `.venv` (`autograd` present), simulator probe.

## 2. Tested
- Leaky vs disjoint parity (P1 overlap-inflation).
- Cross-token routing, matched params: XOR redo (classical_bal vs quantum) + equality task (classical vs quantum).
- Dense vs sparse MoE timing (P3 cost, dense-train vs single-expert).

## 3. Establishes (3 quantitative bricks + code fact)
- Brick 1 — XOR redo (matched ~1218 params): classical_bal 0.9722 (per-seed [1, 0.9167, 1]) vs quantum 0.4912 (per-seed [0.51, 0.48, 0.48]) vs chance 0.50. Gap ≈0.48, quantum at chance.
- Brick 2 — Equality (confirmatory): classical 1.0 vs quantum 0.5206 (≈chance). Same direction as XOR redo.
- Brick 3 — P1 + P3: overlap inflation +0.229 (0.677 leaky vs 0.448 disjoint; disjoint CI straddles chance) + dense-train 1.96× cost (in pre-set 1.8–2.2 band; observed 1.89–2.03).
- Code fact: same-token loop + routing-gap isolation (architectural fact, not accuracy win).
- NO quantum advantage shown or claimed.

## 4. Failed / deferred (honest)
- P2-pilot confound → FIXED by redo: pilot balanced 0.25 (majority-confounded, no separation) superseded by matched-param XOR redo + equality confirmatory (above).
- F1 wording: FIXED in Phase1c (no history rewrite).
- LOWs DEFERRED with reasons: p=0.535 pointer (historical-only pointer, no new claim depends on it); scale/sweeps (capped local-only, seeds ≤3, no sweeps by auth); hardware/scaling speculation (out of scope — no evidence here).
- Demonstrated (routing gap, inflation, cost, code fact) vs hypotheses (learnable-comparator routing accuracy beyond these tasks — NOT demonstrated).

## 5. Contribution
- Track C informative negative: original narrow mechanism study — same-token quantum head vs cross-token routing under matched params, with paired quantitative bricks.
- Reusable tools: guards (6/6 + 4/4) + pilots (P1/P2-redo/P3 + equality) as rerunnable tests.
- NO advantage: not a parity/advantage/expressivity claim; parity gains explained as overlap inflation.

## 6. Headline / narrowest claim
"Same-token quantum head fails cross-token routing that matched classical learns (0.97 vs 0.49); parity gains are overlap inflation; dense-train ~2×."
- Narrowest: on the tested XOR/equality routing tasks at ~1218 matched params, the quantum head stays at chance (0.49/0.52) while the matched classical learns (0.97/1.0). No broader claim.

## 7. Repro (4 cmds)
```
.venv/bin/python -m pytest -q tests/test_pilots_overlap.py
.venv/bin/python -m pytest -q tests/test_pilots_moe_cost.py
.venv/bin/python -m pytest -q tests/test_pilots_crosstoken.py
.venv/bin/python -m pytest -q tests/test_phase1_1_guards.py
```
- Artifacts: `docs/plans/2026-11-16-pilots-*` (progress + evidence.json + falsify) + `research/` (this file, RESULTS_INDEX, STATE).
- Caps: local-only, no spend, tiny configs, seeds ≤3, no sweeps, timeout 600s each, WALL_BUDGET_S=15*60 with wall assert (P1/P2/P3).

## 8. Limitations
- Tiny MLP proxy, no circuit — no hardware claim.
- ≤3 seeds/epochs — sampling noise not fully mapped.
- Routing-dependent ratio (P3 1.8–2.2 band; routed expert_idx per batch asserted).
- Task-specific (XOR/equality routing + parity/MoE pilots) — no scaling claim.
- Speculation flagged: hardware advantage, scaling — NOT evidenced here.

**Plan refs:** `docs/plans/2026-11-16-pilots-progress.md` + `docs/plans/2026-11-16-pilots-evidence.json` + `docs/plans/2026-11-16-pilots-falsify.md`.
**Prior refs:** `docs/plans/2026-11-14-phase1-1-major-fixes-progress.md:1-28` + `docs/plans/2026-11-15-research-audit-progress.md:1-33` + `research/AUDIT.md:1-43`.
**Touched (this task):** `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

---
# FINAL_ASSESSMENT v3 — Confirmatory binary PASS (banked 2026-11-16, v2 intact above)

**Status:** CONFIRMATORY PASS (binary only) — direction independently replicated on fresh data. NO magnitude claim.
**Auth:** user go-ahead; fail-open (no gate active).
**Branch:** `research/audit-1587497` (local-only).

## Protocol (LOCKED → executed ONCE)
- Locked then executed exactly ONCE: fresh seeds 7/21/123, held-out tasks XOR(0,3,2,1) + EQ(1,3,2), fixed model.
- Run-once marker present; single invocation only.
- Result: exit 0, 2 passed, 0.78s.

## Binary verdict: PASS
- Pre-registered falsifier thresholds met on fresh held-out data — direction replicated (classical learns routing, quantum head at chance).
- Binary claim only; no new effect-size or CI asserted from confirmatory run.

## Capture flaw (disclosed)
- `-q` flag hid per-seed print lines in confirmatory run output; only finiteness asserted, not values.
- Consequence: NO confirmatory effect-size/CI claim permitted from this run.
- Exploratory numbers stand as priors with their own CIs only: 0.97/0.49 (XOR redo), +0.229 inflation (P1), 1.96× cost (P3).
- Leakage check: passed. No amendments made post-view of confirmatory output.

## Contribution
- Track C informative negative — now independently replicated (binary).
- Plus B-lite (reusable locked confirmatory protocol + run-once guard as rerunnable pattern).
- Headline unchanged in magnitude, upgraded in independence: "Same-token quantum head fails cross-token routing that matched classical learns (0.97 vs 0.49); parity gains are overlap inflation; dense-train ~2×." Magnitudes are exploratory priors (v2), binary direction confirmed here (v3).

## Repro (freeze verify + single run — DO NOT RE-RUN)
- Freeze verify (safe, read-only):
```
git branch --show-current; git rev-parse --short HEAD
git status --porcelain; ls research/
```
- Single confirmatory run (RUN-ONCE — NOTE: do NOT re-run; second invocation must refuse via run-once marker):
```
.venv/bin/python -m pytest tests/test_confirmatory_routing.py -q
```
- Expected v3 record: exit 0, 2 passed, 0.78s on the locked invocation only. Do not invoke again to "verify."

## Limitations
- Tiny MLP proxy, no circuit — no hardware claim.
- Confirmatory run asserts finiteness/direction only (no per-seed values captured due to `-q`).
- Seeds 7/21/123 + held-out XOR(0,3,2,1)/EQ(1,3,2) only — no broader generalization.
- Task-specific (XOR/equality routing) — no scaling claim.

## Next
- Either STOP (v3 stands as replicated binary negative) or new-seed re-lock with `-s` capture if a confirmatory magnitude/CI is needed (requires fresh gate, fresh seeds, no reuse).
- No scale-up, no code until explicit approval.

**Touched (v3 task):** `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

---
# FINAL_ASSESSMENT v4 — Confirmatory-magnitude quantitative replication (banked 2026-11-16, v1–v3 intact above)

**Status:** CONFIRMATORY-MAG PASS (quantitative) — fresh-seed held-out replication with captured effect sizes + CIs. NO quantum advantage demonstrated.
**Auth:** keep-on-continue; fail-open (no gate active).
**Branch:** `research/audit-1587497` (local-only).

## Headline
"Fresh-seed held-out replication: quantum gaps persist (XOR +0.48 [0.37,0.60], EQ +0.53 [0.48,0.58]) — no advantage demonstrated."

## Protocol (LOCKED → executed ONCE)
- confirmatory-mag executed exactly ONCE: fresh seeds [11,33,55], held-out XOR(1,3)+EQ(2,1,1), fixed model, run-once marker, `-s` capture.
- Params matched (classical vs quantum head); wall 0.1s/900 (well under budget).
- Run-once: do NOT re-run confirmatory tests (second invocation must refuse via run-once marker).

## Quantitative result
- XOR diffs (classical − quantum): 0.4297 / 0.5203 / 0.5000; mean 0.4833, CI [0.3652,0.6014].
- EQ diffs (classical − quantum): 0.5424 / 0.5385 / 0.5085; mean 0.5298, CI [0.4837,0.5758].
- Both CIs > 0.20 (lower bounds 0.3652 and 0.4837 clear the 0.20 bar with margin).
- Direction consistent with v2 exploratory priors (0.97/0.49) and v3 binary replication — now quantified on fresh held-out data.

## Contribution
- Track C quantitative: 2-task confirmatory-magnitude replication (XOR + EQ), Bonferroni-noted (2 tasks).
- Plus B-lite (reusable locked confirmatory-mag protocol with `-s` capture + run-once guard as rerunnable pattern).
- NO advantage: gaps favor matched classical on routing tasks; not a parity/advantage/expressivity claim.

## Repro (4 cmds incl. mag -s — do NOT re-run confirmatory tests, run-once)
```
.venv/bin/python -m pytest -q tests/test_pilots_overlap.py
.venv/bin/python -m pytest -q tests/test_pilots_moe_cost.py
.venv/bin/python -m pytest -q tests/test_pilots_crosstoken.py
.venv/bin/python -m pytest tests/test_confirmatory_mag.py -s
```
- First 3 cmds are safe re-runnable pilots. 4th cmd is the RUN-ONCE confirmatory-mag invocation (record above) — do NOT invoke again to "verify."
- Freeze verify (safe, read-only): `git branch --show-current; git rev-parse --short HEAD; git status --porcelain; ls research/`.

## Limitations
- Tiny MLP proxy, no circuit — no hardware claim.
- Tiny (3 seeds/task) — sampling noise only partially mapped; CIs are task-local.
- Task-specific (held-out XOR(1,3) + EQ(2,1,1) routing) — no scaling claim.

## Next
- Write-up or stop. No scale-up, no code until explicit approval.

**Touched (v4 task):** `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

---
# FINAL_ASSESSMENT v5 — Phase 6 repro closeout (banked 2026-11-16, v1–v4 intact above)

**Status:** PHASE 6 REPRO 3/3 — exploratory priors re-observed; confirmatory locks untouched. NO quantum advantage demonstrated.
**Auth:** keep-on-continue; fail-open (no gate active).
**Branch:** `research/audit-1587497` (local-only).

## Phase 6 3/3
- Row 1 verify: `bash docs/verify-track-c.sh` exit 0 (fail-open), 5 tests ~6s wall — `test_p2_redo.py` exit 0 (0.9722/0.4912 matches prior), `test_pilots_overlap.py` exit 1 expected RED (+0.229 matches prior), `test_pilots_moe_cost.py` exit 0 (1.89 in band), `test_phase1_1_guards.py` exit 0 (4 passed), `test_phase1_correctness_guards.py` exit 1 record-only (6 failed/2 passed).
- Row 2 recompute: `.venv/bin/python scripts/recompute-track-c.py --input benchmarks/results/track-c-repro.jsonl` exit 0, OVERALL PASS (classical/quantum/diff/ratio checks all PASS).
- Row 3 evidence: `ls -l` + `json.tool` exit 0; tasks validated [1,2,3].
- Critics: clean/PASS.

## Raw ignored-exception
- Raw `benchmarks/results/track-c-repro.jsonl` (5 JSONL rows) is gitignored (`.gitignore:29 benchmarks/results/`); NOT force-added; `.gitignore` NOT edited; regenerable ~6s via `bash docs/verify-track-c.sh`.

## Confirmatory locks untouched
- Run-once confirmatory tests never invoked in Phase 6 (script self-assert excludes locked names; run-once markers preserved — second invocation must still refuse).

## Contribution (stands)
- Track C quantitative + B-lite (as v4). No new claim in v5; repro only.

## Headline (unchanged)
"Fresh-seed held-out replication: quantum gaps persist (XOR +0.48 [0.37,0.60], EQ +0.53 [0.48,0.58]) — no advantage demonstrated."

## Repro (one-command + recompute)
```
bash docs/verify-track-c.sh
.venv/bin/python scripts/recompute-track-c.py --input benchmarks/results/track-c-repro.jsonl
```

## Limitations
- As v4 (MLP proxy, tiny, task-specific) + raw-ephemeral (ignored, regenerable).

## Next
- Next: write-up or stop. No further experiments without fresh approval.

**Touched (v5 task):** `research/FINAL_ASSESSMENT.md`, `research/RESULTS_INDEX.md`, `research/STATE.md` only.

---
## Superseding assessment 2026-11-17 (research/audit-1587497 @ a3addab) — authoritative, priors preserved below

**Date:** 2026-11-17 UTC. **Scope:** docs-audit only; priors v1–v5 preserved above without edit. No new experiments, no confirmatory re-runs, no code changes. See pointer: `research/EVIDENCE_REPAIR.md`.

**A. Actual-circuit measurements:** none yet from confirmatory_mag (numpy MLP only); quantum head same-token per `hybrid/attention/quantum_attention.py:79-86`, fallback classical per `hybrid/attention/quantum_attention.py:92-100`. No hardware run; no circuit gap measured.

**B. Classical proxy experiments:** full-information MLP (ordered-concat) vs last-token-only MLP (zeros+last-block) per `tests/test_confirmatory_mag.py:134-142,146-152`; numbers +0.48/+0.53 are proxy gaps, not circuit gaps. Associations-only; no hardware claim.

**C. Synthetic memorization controls:** dict memorizer `tests/test_pilots_overlap.py:89-99` shows split-design vulnerability (+0.229); memorizer result demonstrates inflation mechanics only, no causation for original models — no causation claimed.

**D. Structural code observations:** same-token loop, mask-blind quantum path, threshold record-only (`:68,:250`), Bonferroni constant (`:69,:255`), wrapper fail-open (`:5`). Record-only observations; no behavior beyond code fact asserted.

**E. Historical unverified reports:** prior quantitative headlines are proxy-scoped, associations-only, no hardware/novelty/publication claim. Restated: no novelty claimed, no publication claim made. No quantum advantage claimed or shown.

**Pointer:** full repair plan and checklist in `research/EVIDENCE_REPAIR.md`.

---
## Superseding assessment 2026-11-16 actual-model — authoritative, priors v1–v5 preserved above

**Date:** 2026-11-16 UTC. **Branch:** `research/audit-1587497` @ `a3addab` (`a3addab83791b9b2c39e8bb05a12e74fb1444f66`), local-only.
**Scope:** actual-model smoke only; priors preserved above without edit. Auth: mission Phase7 autonomous. No new proxy claims; no push.

**Headline:** "Actual-model equality-task smoke (n=3, exploratory): no difference demonstrated (mean -0.12 [-0.59,0.35] p 0.39); positive control learns (1.0), negative at floor; no advantage claimed or shown."

**A. Actual-circuit measurements (run4, equality-actual-v2):** n_pairs=3, mean_diff -0.12, CI [-0.5939,0.3539] ([-0.5939432689913657,0.3539432689913657]), p 0.3897 (0.3897428467412706), method t/exploratory small-n (scipy, 95%, multiplicity none/m=1); per-seed 101 0.78/0.76 -0.02, 202 0.24/0.24 0.0, 303 0.60/0.26 -0.34; overlap 0; positive 1.0 (positive_acc=1.0 all seeds); deterministic (predictions/targets bytes match on repro); config e2a5 (`e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54`); actual QuantumAttentionCircuit 6q/1-layer executed (forward+grads+step proven 11/11).

**B. Classical proxy experiments:** prior full-information vs last-token-only MLP gaps +0.48/+0.53 are proxy-only, not circuit gaps (per EVIDENCE_REPAIR). Associations-only; no hardware claim; full-information and last-token-only labels refer to MLP proxy conditions only.

**C. Synthetic memorizer:** dict memorizer +0.229 shows split vulnerability (split-design inflation mechanics only); memorizer result demonstrates inflation mechanics only, no causation for original models — no causation claimed.

**D. Structural:** same-token head `hybrid/attention/quantum_attention.py:79-86`, classical fallback `hybrid/attention/quantum_attention.py:92-100`, token-local stated; threshold/Bonferroni record-only; wrapper fail-open replaced by fail-closed runner (`docs/verify-actual.sh` `set -euo pipefail`).

**E. Historical unverified:** prior quantitative headlines proxy-scoped only, associations-only. Restated: no novelty, no publication claim made — no publication claim; no quantum advantage claimed or shown — no quantum advantage claimed.

**Limits:** n=3 exploratory, tiny CPU, single task, MLP proxy history separate, venv-only.

**Pointers:** `research/EVIDENCE_REPAIR.md` + `research/protocols/equality-actual-v2.json` + `research/artifacts/equality-actual-v2/run4/raw.json` + `research/artifacts/equality-actual-v2/run4/report-t.json` + `docs/verify-actual.sh` + `docs/analyze-only.sh`.

**Touched (this task):** `research/FINAL_ASSESSMENT.md` only (append).

---
## Correction note 2026-11-17 (critic fixes — append-only; no numbers change)

Refs the two superseding sections above; priors v1–v5 intact, no values altered, no re-runs performed.

**1. Exact repro cmds + expected outputs (actual-model superseding 2026-11-16 section).**
Safe re-runnable (fail-closed `set -euo pipefail`):
```
bash docs/verify-actual.sh
bash docs/analyze-only.sh research/artifacts/equality-actual-v2/run4/raw.json /tmp/opencode/actual-repro-check/report-t.json && .venv/bin/python -m json.tool /tmp/opencode/actual-repro-check/report-t.json
```
Expected outputs: `bash docs/verify-actual.sh` → exit 0, `ok run_id=run-repro-<stamp>`, report match `n_pairs=3 mean_diff=-0.12 overlap=0 positive_acc=1.0`; analyze-only → exit 0, report byte-identical to `run4/report-t.json` (1483B). Read-only freeze verify: `git branch --show-current; git rev-parse --short HEAD; git status --porcelain; ls research/`.
Old confirmatory locks stay locked — do NOT re-run `tests/test_confirmatory_routing.py` (v3) or `tests/test_confirmatory_mag.py` (v4); second invocation must refuse via run-once marker. Phase 6 / actual-model repro never invoked them.

**2. Chronological inversion annotated.**
The "Superseding assessment 2026-11-17" (docs-audit) section is banked above the "Superseding assessment 2026-11-16 actual-model" section: order is banking order, not authoring-date order — the 11-17 audit note was appended first, the 11-16-dated actual-model note second. No timeline claim affected; numbers unchanged.

**3. Low fixes.**
Touched-scope alignment: per-section "Touched" lines are historical records of their own tasks and stand; authoritative touched for this correction task: `research/FINAL_ASSESSMENT.md` (this appended note only) + `docs/plans/2026-11-17-actual-repro-progress.md` (pointer note). Single-sentence novelty/advantage statement: no novelty is claimed, no publication claim is made, and no quantum advantage is claimed or shown. Per-seed split (values duplicated from the superseding 2026-11-16 section above, not new measurements):

| seed | classical | quantum | diff |
| 101 | 0.78 | 0.76 | -0.02 |
| 202 | 0.24 | 0.24 | 0.0 |
| 303 | 0.60 | 0.26 | -0.34 |

Mean diff -0.12, CI [-0.5939,0.3539], p 0.3897 — unchanged.

**Touched (this task):** `research/FINAL_ASSESSMENT.md`, `docs/plans/2026-11-17-actual-repro-progress.md` only (append).
