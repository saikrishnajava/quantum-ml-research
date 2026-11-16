"""Paired analysis suite (RED-first).

Branch: research/audit-1587497. Spec R1,R2,R3 (inline-Phase3-pure-analysis).
Analyzer CLI contract (from scripts/analyze_results.py header):
  scripts/analyze_results.py --input PATH --output PATH
    --method t|normal --multiplicity bonferroni|none
Exits: 0 ok, 1 data/validation, 2 usage/paths.
Fixtures: tmp_path raw JSON, subprocess analyzer CLI. Hermetic, stdlib only.
Each test asserts a single (behavior, expectation) focus.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ANALYZER = Path(__file__).resolve().parents[1] / "scripts" / "analyze_results.py"
PY = sys.executable  # .venv/bin/python when run via .venv


def _make_raw(n_pairs=5, base_preds=None, base_targets=None,
              treat_preds=None, treat_targets=None):
    base_preds = [0, 0, 0, 0] if base_preds is None else list(base_preds)
    base_targets = [0, 0, 1, 1] if base_targets is None else list(base_targets)
    treat_preds = [0, 0, 1, 1] if treat_preds is None else list(treat_preds)
    treat_targets = [0, 0, 1, 1] if treat_targets is None else list(treat_targets)
    runs = []
    for i in range(n_pairs):
        runs.append({
            "run_id": f"baseline-{i}",
            "arm": "baseline",
            "seed_data": i,
            "predictions": list(base_preds),
            "targets": list(base_targets),
        })
        runs.append({
            "run_id": f"treatment-{i}",
            "arm": "treatment",
            "seed_data": i,
            "predictions": list(treat_preds),
            "targets": list(treat_targets),
        })
    return {"protocol": "test-protocol", "config_hash": "abc123", "runs": runs}


def _run_cli(workdir: Path, raw, method="normal", multiplicity="bonferroni"):
    workdir.mkdir(parents=True, exist_ok=True)
    inp = workdir / "raw.json"
    out = workdir / "report.json"
    if isinstance(raw, (dict, list)):
        inp.write_text(json.dumps(raw), encoding="utf-8")
    else:
        inp.write_text(raw, encoding="utf-8")
    cmd = [PY, str(ANALYZER), "--input", str(inp), "--output", str(out),
           "--method", method, "--multiplicity", multiplicity]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    report = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else None
    return proc.returncode, report


def test_computes_mean_diff_from_fixture_predictions_not_constants(tmp_path):
    raw_hi = _make_raw(n_pairs=5, treat_preds=[0, 0, 1, 1])
    raw_lo = _make_raw(n_pairs=5, treat_preds=[1, 1, 0, 0])
    rc_hi, rep_hi = _run_cli(tmp_path / "hi", raw_hi)
    rc_lo, rep_lo = _run_cli(tmp_path / "lo", raw_lo)
    assert (rc_hi, rc_lo, rep_hi["mean_diff"], rep_lo["mean_diff"]) == (0, 0, 0.5, -0.5)


def test_missing_predictions_schema_violation_exits_data_error(tmp_path):
    raw = _make_raw(n_pairs=5)
    del raw["runs"][0]["predictions"]
    rc, _ = _run_cli(tmp_path, raw)
    assert rc == 1


def test_unpaired_seed_set_refused_exits_data_error(tmp_path):
    raw = _make_raw(n_pairs=3)
    raw["runs"][1]["seed_data"] = 999
    rc, _ = _run_cli(tmp_path, raw)
    assert rc == 1


def test_single_arm_incomplete_comparison_refused_exits_data_error(tmp_path):
    raw = _make_raw(n_pairs=3)
    raw["runs"] = [r for r in raw["runs"] if r["arm"] == "baseline"]
    rc, _ = _run_cli(tmp_path, raw)
    assert rc == 1


def test_ci_method_name_matches_requested_normal(tmp_path):
    rc, report = _run_cli(tmp_path, _make_raw(n_pairs=5), method="normal")
    assert (rc, "normal" in report["method_used"]) == (0, True)


def test_accounting_counts_total_and_paired_runs(tmp_path):
    rc, report = _run_cli(tmp_path, _make_raw(n_pairs=5))
    assert (rc, report["accounting"]["total_runs"],
            report["accounting"]["paired_seeds"]) == (0, 10, 5)


def test_small_n_warning_with_uncertainty_when_fewer_than_five_pairs(tmp_path):
    rc, report = _run_cli(tmp_path, _make_raw(n_pairs=3))
    assert (rc, any("small-n" in w for w in report["warnings"]),
            report["ci_lo"] is not None and report["ci_hi"] is not None) == (0, True, True)


def test_multiplicity_none_labels_exploratory(tmp_path):
    rc, report = _run_cli(tmp_path, _make_raw(n_pairs=5), multiplicity="none")
    assert (rc, "exploratory" in report["multiplicity"]["interpretation"]) == (0, True)


def test_analyzer_has_no_training_imports():
    text = ANALYZER.read_text(encoding="utf-8")
    assert all(s not in text for s in ("pennylane", "torch", "benchmarks.tasks"))
