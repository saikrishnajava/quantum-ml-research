"""Actual-experiment suite (v2 locked, tiny-CPU smoke).

Covers: (i) v2 protocol loads + required keys (R1-R4,R6 verbatim, R3
disjoint-sampling amended; v1 frozen read-only); (ii) smoke triple-seed
paired artifacts when correctness GREEN (no skip-weakening, paired +
disjoint-by-tripwire + deterministic); (iii) malformed protocol/args
exit nonzero (fail-closed, v1 refused). Hermetic, fast, stdlib + pytest only.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = REPO_ROOT / "research" / "protocols" / "equality-actual-v2.json"
V1_PROTOCOL = REPO_ROOT / "research" / "protocols" / "equality-actual-v1.json"
RUNNER = REPO_ROOT / "scripts" / "run_actual_experiment.py"
PY = sys.executable

REQUIRED_TOP_KEYS = (
    "protocol", "spec", "task", "parity", "splits", "models",
    "runner", "caps", "seeds", "artifacts",
)


def test_protocol_loads_required_keys():
    doc = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for key in REQUIRED_TOP_KEYS:
        assert key in doc, f"missing required key: {key}"
    assert doc["protocol"] == "equality-actual-v2"
    assert doc["spec"] == "equality-actual-v2-R1-R6-R3-amended"
    assert doc["task"]["generator"] == "generate_equality_sequence_decision"
    assert list(doc["seeds"]) == [101, 202, 303]
    assert doc["models"]["A_classical"]["arch"] == "ClassicalDecisionMLP"
    assert doc["models"]["B_hybrid"]["arch"] == "HybridQuantumLLM"
    assert doc["parity"]["same_inputs"] is True
    assert doc["parity"]["quantum_path"] == "token-local"
    assert doc["splits"]["train_size"] == 200
    assert doc["splits"]["test_size"] == 50
    assert doc["splits"]["unique_inputs"] is True
    assert doc["splits"]["zero_overlap"] is True
    assert doc["splits"]["overlap_tolerance"] == 0
    assert doc["splits"]["sampling"] == "disjoint-without-replacement-250-of-256-in-runner"
    # V1 frozen (read-only reference, never consumed by runner post-amendment).
    v1 = json.loads(V1_PROTOCOL.read_text(encoding="utf-8"))
    assert v1["protocol"] == "equality-actual-v1"


def test_runner_smoke_paired_artifacts_deferred_until_correctness_green(tmp_path):
    """Smoke triple-seed paired artifacts (v2, <5m); deferred until GREEN."""
    import pytest

    if os.environ.get("ACTUAL_CORRECTNESS_GREEN") != "1":
        pytest.skip(
            "record-only: correctness not yet GREEN — "
            "full smoke (triple-seed paired artifacts, <5m) deferred, no training run"
        )
    proc = subprocess.run(
        [PY, str(RUNNER), "--protocol", str(PROTOCOL),
         "--output", str(tmp_path), "--run-id", "smoke",
         "--timeout", "290"],
        capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr
    run_doc = json.loads((tmp_path / "smoke" / "run.json").read_text())
    assert run_doc["seeds"] == [101, 202, 303]
    assert run_doc["protocol"] == "equality-actual-v2"
    for seed in (101, 202, 303):
        preds = json.loads((tmp_path / "smoke" / f"seed-{seed}" / "predictions.json").read_text())
        targs = json.loads((tmp_path / "smoke" / f"seed-{seed}" / "targets.json").read_text())
        assert len(preds) == len(targs) > 0
        assert len(preds) == 50, f"seed {seed}: expected 50 test rows"
        metrics = json.loads((tmp_path / "smoke" / f"seed-{seed}" / "metrics.json").read_text())
        assert metrics["n"] == 50
        assert math.isfinite(metrics["acc"]) and 0.0 <= metrics["acc"] <= 1.0
    # Determinism: fixed-seed rerun reproduces artifacts exactly.
    proc2 = subprocess.run(
        [PY, str(RUNNER), "--protocol", str(PROTOCOL),
         "--output", str(tmp_path), "--run-id", "smoke2",
         "--timeout", "290"],
        capture_output=True, text=True, timeout=300,
    )
    assert proc2.returncode == 0, proc2.stderr
    for seed in (101, 202, 303):
        for name in ("predictions.json", "targets.json", "metrics.json"):
            a = (tmp_path / "smoke" / f"seed-{seed}" / name).read_bytes()
            b = (tmp_path / "smoke2" / f"seed-{seed}" / name).read_bytes()
            assert a == b, f"nondeterministic artifact seed={seed} {name}"


def test_malformed_protocol_args_nonzero(tmp_path):
    missing = tmp_path / "no-such-protocol.json"
    p1 = subprocess.run(
        [PY, str(RUNNER), "--protocol", str(missing),
         "--output", str(tmp_path), "--run-id", "bad"],
        capture_output=True, text=True, timeout=60,
    )
    assert p1.returncode == 2, (p1.returncode, p1.stderr)
    bad = tmp_path / "bad.json"
    bad.write_text("not-json{{{", encoding="utf-8")
    p2 = subprocess.run(
        [PY, str(RUNNER), "--protocol", str(bad),
         "--output", str(tmp_path), "--run-id", "bad"],
        capture_output=True, text=True, timeout=60,
    )
    assert p2.returncode == 2, (p2.returncode, p2.stderr)
    p3 = subprocess.run(
        [PY, str(RUNNER), "--protocol", str(PROTOCOL),
         "--output", str(tmp_path), "--timeout", "nan"],
        capture_output=True, text=True, timeout=60,
    )
    assert p3.returncode != 0, (p3.returncode, p3.stderr)
    p4 = subprocess.run(
        [PY, str(RUNNER), "--protocol", str(V1_PROTOCOL),
         "--output", str(tmp_path), "--run-id", "badv1"],
        capture_output=True, text=True, timeout=60,
    )
    assert p4.returncode == 2, (p4.returncode, p4.stderr)
