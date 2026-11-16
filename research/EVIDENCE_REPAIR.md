# EVIDENCE_REPAIR — Track C parity-guard bank

Branch: research/audit-1587497
Commit: a3addab
Date (UTC): 2026-11-16
Spec: docs/specs/2026-11-15-parity-guards-pivot.md + mission Phase1 delta
Plan: docs/plans/2026-11-17-evidence-repair.md (approved, rows 1-3)
Scope: evidence bank only. No novelty claims. No publication claims. No code fixes. No training.

## Categories legend (A–E)

- A — Proxy / construct: what the harness actually measures vs what the claim names.
- B — Causation / attribution: whether the design supports a causal reading.
- C — Recomputation / provenance: whether an independent rerun is possible from banked artifacts.
- D — Runner integrity: fail-open vs fail-closed verification mechanics.
- E — Statistics / multiplicity and scope wording; repro workflow mechanics.

## Row 1 — Mag proxy is classical, full-information vs last-token-only (A)

- Status: Verified
- File + function: tests/test_confirmatory_mag.py — module-level harness (numpy-only import at :45; classical fixtures at :134–152; train/eval parity at :228–232)
- Minimal evidence:
  - tests/test_confirmatory_mag.py:45 numpy-only (no PennyLane import)
  - tests/test_confirmatory_mag.py:134-138 classical ordered-concat 16-dim full-information
  - tests/test_confirmatory_mag.py:139-142 zeros+last-block last-token-only
  - tests/test_confirmatory_mag.py:146-152 MLP 16->64->2
  - tests/test_confirmatory_mag.py:228-232 same train/eval
- Affected claims: any reading of mag results as circuit/quantum evidence; "quantum vs classical" labels on these two arms.
- Required correction: relabel arms as full-information vs last-token-only, never "quantum"; describe MLP as classical control.
- blocks-new-experiments? Yes (proxy cannot support circuit claim — new circuit experiments need a real circuit arm before any quantum claim).

## Row 2 — Pilots overlap is dict memorizer, no causation (B)

- Status: Verified
- File + function: tests/test_pilots_overlap.py — overlap/split-design probe (:15–16 no training; :89–99 dict memorizer)
- Minimal evidence:
  - tests/test_pilots_overlap.py:15-16 no training
  - tests/test_pilots_overlap.py:89-99 dict memorizer
  - imports json/sys/time/pathlib/numpy+statistics only (no model training stack)
- Affected claims: any causal claim that overlap explains original-model behavior.
- Required correction: no causation for original models; retain only as split-design lesson (overlap inflates naive reruns).
- blocks-new-experiments? Yes for causation, No for split-design lesson (lesson arm may proceed; causal arm blocked).

## Row 3 — recompute-track-c.py cannot support independent analysis (C)

- Status: Verified
- File + function: scripts/recompute-track-c.py — JSONL recompute entrypoint (:19 PRIORS; :26–31 embedded seeds; :93–115 JSONL len+exit only; :12–16 imports json/math/sys/numpy)
- Minimal evidence:
  - scripts/recompute-track-c.py:19 PRIORS
  - scripts/recompute-track-c.py:26-31 embedded seeds
  - scripts/recompute-track-c.py:93-115 JSONL len+exit only
  - scripts/recompute-track-c.py:12-16 imports json/math/sys/numpy
- Affected claims: "independently recomputed / verified" from JSONL length + exit code alone.
- Required correction: needs raw predictions (per-example predictions + seeds + config) banked before any independent-analysis claim.
- blocks-new-experiments? Yes for independent analysis (blocked until raw-prediction artifacts exist).

## Row 4 — verify-track-c.sh is fail-open (D)

- Status: Verified (fail-open)
- File + function: docs/verify-track-c.sh — verification runner (:5 no errexit; :22–33 `|| true`; :23 PIPESTATUS; :9–11 split-pattern exclusion; no set -e)
- Minimal evidence:
  - docs/verify-track-c.sh:5 no errexit (no set -e / set -euo pipefail)
  - docs/verify-track-c.sh:22-33 || true
  - docs/verify-track-c.sh:23 PIPESTATUS
  - docs/verify-track-c.sh:9-11 split-pattern exclusion
- Affected claims: "verification passed" from this runner.
- Required correction: fail-closed runner (set -euo pipefail or explicit non-zero propagation; remove `|| true` swallows; surface PIPESTATUS failures as hard errors).
- blocks-new-experiments? Yes (fail-open runner cannot gate new experiments).

## Row 5 — Thresholds and Bonferroni are record/log-only (E)

- Status: Verified
- File + function: tests/test_confirmatory_mag.py — threshold/multiplicity handling (:68 THRESHOLD record-only; :250 print-only; :293–309 finite+wall asserts only; :69 BONFERRONI log-only; :255 log-only) + statistics.py:13 no Bonferroni arg
- Minimal evidence:
  - tests/test_confirmatory_mag.py:68 THRESHOLD record-only
  - tests/test_confirmatory_mag.py:250 print-only
  - tests/test_confirmatory_mag.py:293-309 finite+wall asserts only
  - tests/test_confirmatory_mag.py:69 BONFERRONI log-only
  - tests/test_confirmatory_mag.py:255 log-only
  - statistics.py:13 no Bonferroni arg
- Affected claims: any "confirmatory (threshold-gated / multiplicity-corrected)" reading.
- Required correction: implement threshold gating + Bonferroni (or equivalent) correction, or explicitly mark analyses exploratory.
- blocks-new-experiments? Yes for confirmatory claim (exploratory work may proceed labeled as such).

## Row 6 — Attention proxy is token-local; cross-token path is classical fallback (A)

- Status: Verified (nuance)
- File + function: hybrid/attention/quantum_attention.py (:79–86 same-s loop; :92–100 classical fallback cross-token; no circuit(s,t) s!=t) + test_p2_redo.py (:31–33, :101–110 proxy isolation exact)
- Minimal evidence:
  - hybrid/attention/quantum_attention.py:79-86 same-s loop
  - hybrid/attention/quantum_attention.py:92-100 classical fallback cross-token
  - no circuit(s,t) s!=t
  - test_p2_redo.py:31-33 proxy isolation exact
  - test_p2_redo.py:101-110 proxy isolation exact
- Affected claims: any cross-token / entangling-attention reading of this proxy.
- Required correction: must state token-local in every description; cross-token behavior is classical fallback, not a circuit.
- blocks-new-experiments? Yes — must state token-local (new cross-token claims blocked until a true s!=t circuit path exists).

## Row 7 — Scoped-correctly disclaimers present; concern NOT UPHELD (E)

- Status: NOT UPHELD (scoped-correctly)
- File + function: research/FINAL_ASSESSMENT.md (:59, :156–159 disclaimers) + docs/track-c-report.md (:19, :31 disclaimers)
- Minimal evidence:
  - research/FINAL_ASSESSMENT.md:59 disclaimer present
  - research/FINAL_ASSESSMENT.md:156-159 disclaimer present
  - docs/track-c-report.md:19 disclaimer present
  - docs/track-c-report.md:31 disclaimer present
  - Note quantitative wording bounded (no open-ended novelty/publication language at cited lines)
- Affected claims: none — existing scope wording is adequate at these lines.
- Required correction: keep disclaimers; do not widen wording in future edits.
- blocks-new-experiments? No, but keep disclaimers (no block; preservation obligation only).

## Row 8 — Marker-consumed repro workflow blocks reruns (C/E)

- Status: Verified (mechanics confirmed)
- File + function: tests/test_confirmatory.py (:79, :220–223 markers) + tests/test_confirmatory_mag.py (:74, :215–217 markers consumed + exclusion) + exclusion recorded research/FINAL_ASSESSMENT.md:182-183, docs/track-c-report.md:36,52
- Minimal evidence:
  - tests/test_confirmatory.py:79 marker
  - tests/test_confirmatory.py:220-223 markers consumed + exclusion
  - tests/test_confirmatory_mag.py:74 marker
  - tests/test_confirmatory_mag.py:215-217 markers consumed + exclusion
  - research/FINAL_ASSESSMENT.md:182-183 exclusion
  - docs/track-c-report.md:36 exclusion
  - docs/track-c-report.md:52 exclusion
- Affected claims: "reran verification" when reruns hit consumed markers / exclusions instead of fresh execution.
- Required correction: allow reruns to new run dirs; preserve markers as history (append-only), never as a gate that converts a rerun into a skip.
- blocks-new-experiments? Yes for repro workflow (new runs blocked until reruns write to fresh dirs without marker-gated skips).
