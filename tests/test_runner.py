"""Fail-closed runner 7-case fail-when-should proof (RED-first).

Branch: research/audit-1587497. Spec R1,R2,R3 (inline failclosed-runner).
Runner CLI contract (from scripts/run_experiment.py header):
  scripts/run_experiment.py --experiment-id ID --run-id RID --timeout SEC
    --output DIR --protocol-hash HASH [--metrics-file PATH] -- <cmd...>

Five states -> exits: success 0, scientific-negative 0,
execution-failed 1, timed-out 124, invalid 2.
Fixtures: .venv/bin/python -c inline child (via sys.executable under .venv),
tmp_path outdir, subprocess.run runner CLI. Hermetic, stdlib only.
Each test asserts single (rc, status) pair (tuple assert).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_experiment.py"
PY = sys.executable  # .venv/bin/python when run via .venv


def _run_runner(tmp_path: Path, exp: str, run: str, child_code: str,
                timeout: float = 10.0, metrics_file: str | None = None):
    outdir = str(tmp_path)
    cmd = [
        PY, str(RUNNER),
        "--experiment-id", exp,
        "--run-id", run,
        "--timeout", str(timeout),
        "--output", outdir,
        "--protocol-hash", "testhash123",
    ]
    if metrics_file is not None:
        cmd += ["--metrics-file", metrics_file]
    cmd += ["--", PY, "-c", child_code]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    status_path = tmp_path / exp / run / "status.json"
    status_doc = json.loads(status_path.read_text(encoding="utf-8"))
    return proc.returncode, status_doc


def test_success_verdict_success_returns_zero_and_status_success(tmp_path):
    rc, doc = _run_runner(
        tmp_path, "exp1", "success",
        "print('{\"metrics\": {\"acc\": 0.9}, \"verdict\": \"success\"}')",
    )
    assert (rc, doc["status"]) == (0, "success")


def test_scientific_negative_verdict_negative_returns_zero_and_status_scientific_negative(tmp_path):
    rc, doc = _run_runner(
        tmp_path, "exp2", "negative",
        "print('{\"metrics\": {\"acc\": 0.1}, \"verdict\": \"negative\"}')",
    )
    assert (rc, doc["status"]) == (0, "scientific-negative")


def test_execution_failed_child_exit_3_preserves_exit_and_status(tmp_path):
    rc, doc = _run_runner(
        tmp_path, "exp3", "execfail",
        "import sys; sys.exit(3)",
    )
    assert (rc, doc["status"], doc["child_exit"]) == (1, "execution-failed", 3)


def test_timed_out_sleep_beyond_timeout_returns_124(tmp_path):
    rc, doc = _run_runner(
        tmp_path, "exp4", "timeout",
        "import time; time.sleep(5)",
        timeout=0.5,
    )
    assert (rc, doc["status"]) == (124, "timed-out")


def test_missing_output_without_json_is_invalid(tmp_path):
    missing = str(tmp_path / "missing.json")  # never created
    rc, doc = _run_runner(
        tmp_path, "exp5", "missing",
        "print('{\"verdict\": \"success\"}')",
        metrics_file=missing,
    )
    assert (rc, doc["status"]) == (2, "invalid")


def test_malformed_not_json_is_invalid(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not-json{{{", encoding="utf-8")
    rc, doc = _run_runner(
        tmp_path, "exp6", "malformed",
        "print('ok')",
        metrics_file=str(bad),
    )
    assert (rc, doc["status"]) == (2, "invalid")


def test_nonfinite_and_incomplete_paired_is_invalid(tmp_path):
    rc, doc = _run_runner(
        tmp_path, "exp7", "nonfinite-paired",
        "print('{\"metrics\": {\"score\": NaN}, "
        "\"predictions\": [1, 2], \"targets\": [1]}')",
    )
    assert (rc, doc["status"]) == (2, "invalid")
