# Actual Repro — Progress (rows 1-2)

Branch: `research/audit-1587497` @ `a3addab83791b9b2c39e8bb05a12e74fb1444f66`.
Auth: mission Phase6 autonomous (local-only, scope-locked, tiny CPU, no secrets, no push).
Protocol: `equality-actual-v2` frozen true, `config_hash=e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54`, seeds [101,202,303].

## Row 1 — Gate + runner repro raw (R1–R6)
- File: `docs/verify-actual.sh` (new, chmod +x, `set -euo pipefail`).
- Preflight: branch exact, HEAD prefix `a3addab`, `.venv` python + scipy, protocol frozen true + config_hash recompute pinned, overlap_tolerance 0.
- Runner: NEW `--run-id run-repro-<stamp>` (never run2/3/4), `--timeout 290`, output under `/tmp/opencode/actual-repro-check/<run-id>/` (authoritative `run4` untouched).
- Analyzer: `--method t --multiplicity none`.
- Gate: `n_pairs=3`, `mean_diff=-0.12` (|tol| 1e-9), CI `[-0.5939432689913657,0.3539432689913657]` (abs 1e-6), `p=0.3897428467412706` (rel 1e-6), `config_hash` exact, `method_used=t (scipy, 95%)`, `multiplicity=none/m=1`, `small-n` warning, per-seed acc exact vs run4, same-inputs paired `n=50`, `positive_acc=1.0` all seeds, predictions/targets bytes match run4 (run_id prefix differs only).
- Verify: `bash docs/verify-actual.sh` → exit 0.
- Observed: `ok run_id=run-repro-20261115-221815`, `report match n_pairs=3 mean_diff=-0.12 ... overlap=0 positive_acc=1.0`.

## Row 2 — Analysis-only paired report (R2, R5 analyzer)
- File: `docs/analyze-only.sh` (new, chmod +x, `set -euo pipefail`).
- Behavior: analyzer only over existing raw (no runner); defaults `research/artifacts/equality-actual-v2/run4/raw.json` → `/tmp/opencode/actual-repro-check/report-t.json`; `--method t --multiplicity none`; invalid refused via analyzer exit codes; output validated with `json.tool`.
- Verify: `bash docs/analyze-only.sh research/artifacts/equality-actual-v2/run4/raw.json /tmp/opencode/actual-repro-check/report-t.json && .venv/bin/python -m json.tool /tmp/opencode/actual-repro-check/report-t.json` → exit 0, report identical to `run4/report-t.json`.

## Caps / scope
- Local-only, tiny CPU (runner ~1.1s), no sweeps/spend/GPU/network, no secrets, no push.
- Touched (allowed only): `docs/verify-actual.sh`, `docs/analyze-only.sh`, this progress file, `docs/plans/2026-11-17-actual-repro-evidence.json`.
- Untouched: `research/protocols/*`, `scripts/*`, `research/artifacts/*`, `tests/*`.

## Row 3 — Evidence + caps verification (R5–R6 closeout)
- Verify: `ls -l docs/plans/2026-11-17-actual-repro-progress.md docs/plans/2026-11-17-actual-repro-evidence.json && .venv/bin/python -m json.tool docs/plans/2026-11-17-actual-repro-evidence.json > /dev/null` → exit 0 at `2026-11-16T04:19:08Z`.
- Re-verify GREEN: `bash docs/verify-actual.sh` → exit 0, `run_id=run-repro-20261115-221856`, `duration_s=1.12`, real 2.192s; `bash docs/analyze-only.sh research/artifacts/equality-actual-v2/run4/raw.json /tmp/opencode/actual-repro-check/report-t.json && .venv/bin/python -m json.tool /tmp/opencode/actual-repro-check/report-t.json` → exit 0 + exit 0, real 0.768s.
- Determinism: analyze-only `report-t.json` byte-identical to `run4/report-t.json` (`diff -q` BYTE_IDENTICAL, 1483B); repro predictions/targets bytes match run4 (gate ok, run_id prefix + duration_s differ only); tolerances: `mean_diff` diff 0.0 (|tol| 1e-9), `p_value` rel 0.0 (rel 1e-6), CI diff 0.0/0.0 (abs 1e-6), `config_hash` exact `e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54`.
- n stays 3: `n_pairs` repro=3 auth=3.
- No markers: `grep -rn '<<<<<<<\|=======\|>>>>>>>\|TODO\|FIXME\|XXX'` clean over progress/evidence/gate/analysis-only.
- Caps 5m: runner 1.12s, verify 2.192s + analyze 0.768s <5m, tiny CPU, local-only, no sweeps/spend/GPU/network, no secrets, no push.
- Tasks: [1,2,3].
- Touched (row3 only): this progress file, `docs/plans/2026-11-17-actual-repro-evidence.json`.

## Row 4 — Handoff pointer (2026-11-16 actual-model closeout)
- Superseding assessment: `research/FINAL_ASSESSMENT.md` (Superseding actual-model 2026-11-16, run4 n=3 mean -0.12 p 0.39, no advantage claimed or shown).
- Resumable state: `research/STATE.md` (2026-11-16 actual-model smoke closeout, branch `research/audit-1587497` @ `a3addab`, pointers to EVIDENCE_REPAIR + equality-actual-v2 protocol + run4 raw/report + verify/analyze scripts; next = stop).
- Touched (row4 only): this progress file (append).

## Row 5 — Critic-fix pointer (2026-11-17 correction note, no numbers change)
- Correction note: `research/FINAL_ASSESSMENT.md` (Correction note 2026-11-17: exact repro cmds `bash docs/verify-actual.sh` exit 0 + analyze-only byte-identical, old confirmatory locks do NOT re-run, chronological-inversion annotation, per-seed table; no values altered).
- Touched (row5 only): `research/FINAL_ASSESSMENT.md`, this progress file (append).

## Row 6 — Handoff (2026-11-16 actual-model milestone met, stop)
- Task/phase: mission 2026-11-16 actual-model milestone; Auth mission Phase7 autonomous.
- Verified: 8 verdicts; runner 7/7; analyzer 9/9; correctness 11/11; protocol v2 frozen (config_hash `e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54`, seeds [101,202,303]); run4 authoritative (n=3 mean -0.12 p 0.39, overlap 0, positive 1.0); repro byte-identical.
- Resumable state: `research/STATE.md` (final handoff entry, branch `research/audit-1587497` @ `a3addab`, milestone met).
- Next: stop — milestone met, user push only. Deadline none (local). Limits tiny CPU, no spend. In-flight none. Deviations: run3 ID duplication fixed in run4; v1 untracked content-frozen. Allowed: review files. Forbidden: push, re-run confirmatory, sweeps.
- Touched (row6 only): this progress file (append).

## Row 7 — Skeptical 12/12 pointer (no new science, full verification ses_e1d68abe)
- Branch `research/audit-1587497` @ `a3addab`; Auth Phase7 autonomous; source explorer `ses_e1d68abe` full verification (12 YES, no new science, pointer to progress).
- 1 circuits 11/11: YES — `docs/plans/2026-11-17-actual-correctness-progress.md:46` 11 passed GREEN.
- 2 same inputs shared rng: YES — `scripts/run_actual_experiment.py:170` single rng=RandomState(seed) shared by both arms.
- 3 positive 1.0: YES — `scripts/run_actual_experiment.py:276` C-positive tiny MLP + `research/artifacts/equality-actual-v2/run4/seed-101/metrics.json:9` positive_acc 1.0.
- 4 negative majority/shuffle: YES — `scripts/run_actual_experiment.py:321` C-negative majority + label-shuffle floor.
- 5 grads AC3/AC4: YES — `tests/test_actual_correctness.py:105` AC3 grad-norm+clip + `tests/test_actual_correctness.py:137` AC4 step/loss/params-move.
- 6 splits overlap 0: YES — `research/protocols/equality-actual-v2.json:28` splits zero_overlap true tolerance 0 + `scripts/run_actual_experiment.py:213` split overlap guard.
- 7 derivable raw->report: YES — `scripts/analyze_results.py:144` pure validated raw -> deterministic report.
- 8 failed visible excluded_runs: YES — `research/artifacts/equality-actual-v2/run4/report-t.json:3` excluded_runs [] + `scripts/analyze_results.py:201` excluded_runs [].
- 9 fail-closed 5-state: YES — `scripts/run_actual_experiment.py:4` 5-state/exit-map + `research/protocols/equality-actual-v2.json:98` failure_policy fail-closed non-zero.
- 10 fair paired: YES — `scripts/analyze_results.py:184` paired by seed_data + `research/protocols/equality-actual-v2.json:92` paired_only true unpaired_refused.
- 11 reproducible byte-identical: YES — `scripts/analyze_results.py:267` sort_keys deterministic + this file Row3 `docs/plans/2026-11-17-actual-repro-progress.md:29` diff BYTE_IDENTICAL 1483B.
- 12 in-scope exploratory: YES — `research/protocols/equality-actual-v2.json:99` permitted_conclusions exploratory only.
- Touched (row7 only): this progress file (append).
