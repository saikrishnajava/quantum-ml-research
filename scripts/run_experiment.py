#!/usr/bin/env python3
"""Fail-closed experiment runner (thin CLI wrapper over subprocess).

Child-output contract (chosen for row1, documented here):
- Default: child STDOUT is parsed as JSON if possible. Expected shape:
  {"metrics": {...}, "verdict": "success" | "scientific-negative", ...}
  Optional paired fields: "predictions" + "targets" (must pair by length).
- Override: if --metrics-file PATH is given and the file exists, that file
  is read as JSON instead of stdout (stdout still captured to logs).
- Non-JSON stdout with child exit 0 is accepted as success with
  metrics=null (raw text preserved in stdout.log); --metrics-file content,
  when used, MUST be valid JSON or the run is invalid(2).
- No constants are embedded here (no PRIORS, no thresholds, no seeds);
  unknown config/params/seeds/budget fields are recorded as null, never faked.

Five states -> exits:
  success (child exit 0, verdict success/absent)      -> exit 0
  scientific-negative (child exit 0, verdict negative) -> exit 0
  execution-failed (child exit != 0 or spawn error)     -> exit 1
  timed-out (subprocess.TimeoutExpired)                 -> exit 124
  invalid (missing/malformed args, nonfinite timeout or
           metric, malformed metrics-file JSON,
           incomplete predictions/targets pairing)      -> exit 2
Real child exit is preserved in artifacts; no suppression.
Stdlib only: argparse, subprocess, json, hashlib, platform, sys, os, time, math.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time


NEGATIVE_VERDICTS = ("scientific-negative", "negative", "null-result")


def _best_effort_commit():
    try:
        p = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        out = (p.stdout or "").strip()
        return out if p.returncode == 0 and out else None
    except Exception:
        return None


def _check_metrics_finite(obj):
    """Recursively reject NaN/Infinity in decoded JSON metrics."""
    if isinstance(obj, float):
        return math.isfinite(obj)
    if isinstance(obj, dict):
        return all(_check_metrics_finite(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return all(_check_metrics_finite(v) for v in obj)
    return True


def _check_pairing(payload):
    """Incomplete-paired check: predictions/targets must pair by length."""
    if not isinstance(payload, dict):
        return True
    preds = payload.get("predictions")
    targs = payload.get("targets")
    if preds is None and targs is None:
        return True
    if preds is None or targs is None:
        return False
    try:
        return len(preds) == len(targs)
    except TypeError:
        return False


def _parse_payload(stdout_text, metrics_file):
    """Return (payload_or_None, invalid_reason_or_None)."""
    if metrics_file:
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except (json.JSONDecodeError, ValueError, OSError) as exc:
                return None, "malformed metrics-file: %s" % exc
            return payload, None
        return None, "missing metrics-file: %s" % metrics_file
    text = (stdout_text or "").strip()
    if not text:
        return None, None
    try:
        return json.loads(text), None
    except (json.JSONDecodeError, ValueError):
        return None, None


def _classify_verdict(payload):
    if isinstance(payload, dict):
        v = payload.get("verdict")
        if isinstance(v, str) and v.strip().lower() in NEGATIVE_VERDICTS:
            return "scientific-negative"
    return "success"


def build_parser():
    p = argparse.ArgumentParser(description="Fail-closed experiment runner.")
    p.add_argument("--experiment-id", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--timeout", required=True, type=float)
    p.add_argument("--output", required=True)
    p.add_argument("--protocol-hash", required=True)
    p.add_argument("--metrics-file", required=False, default=None)
    p.add_argument("command", nargs=argparse.REMAINDER)
    return p


def run_case(experiment_id, run_id, cmd, timeout, output, protocol_hash,
             metrics_file=None):
    """Run one case; return record dict with state/exit/capture."""
    record = {
        "id": "%s/%s" % (experiment_id, run_id),
        "state": "invalid",
        "exit": 2,
        "stdout": "",
        "stderr": "",
        "duration": 0.0,
        "cmd": cmd,
        "timeout": timeout,
    }
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        dur = time.monotonic() - start
        out = exc.stdout
        err = exc.stderr
        record.update(
            state="timed-out",
            exit=124,
            stdout=out if isinstance(out, str) else "",
            stderr=(err if isinstance(err, str) else "")
            or ("timed out after %s s" % timeout),
            duration=dur,
        )
        return record
    except (OSError, ValueError) as exc:
        dur = time.monotonic() - start
        record.update(
            state="execution-failed", exit=1,
            stderr="spawn failed: %s" % exc, duration=dur,
        )
        return record
    dur = time.monotonic() - start
    record.update(
        stdout=proc.stdout or "", stderr=proc.stderr or "", duration=dur,
    )
    if proc.returncode != 0:
        record.update(state="execution-failed", exit=1)
        record["child_exit"] = proc.returncode
        return record
    record["child_exit"] = 0
    # Child exit 0: validate payload contract (fail-closed on invalid).
    payload, reason = _parse_payload(record["stdout"], metrics_file)
    if reason is not None:
        record.update(state="invalid", exit=2)
        record["error"] = reason
        return record
    if isinstance(payload, dict):
        if not _check_metrics_finite(payload):
            record.update(state="invalid", exit=2)
            record["error"] = "nonfinite value in payload"
            return record
        if not _check_pairing(payload):
            record.update(state="invalid", exit=2)
            record["error"] = "incomplete predictions/targets pairing"
            return record
        record["verdict"] = _classify_verdict(payload)
        record["payload"] = payload
    else:
        record["verdict"] = "success"
        record["payload"] = None
    record.update(state=record["verdict"], exit=0)
    return record


def _write_artifacts(record, args, commit):
    outdir = os.path.join(args.output, args.experiment_id, args.run_id)
    os.makedirs(outdir, exist_ok=True)
    stdout_text = record.get("stdout", "") or ""
    stderr_text = record.get("stderr", "") or ""
    with open(os.path.join(outdir, "stdout.log"), "w", encoding="utf-8") as fh:
        fh.write(stdout_text)
    with open(os.path.join(outdir, "stderr.log"), "w", encoding="utf-8") as fh:
        fh.write(stderr_text)
    payload = record.get("payload")
    if not isinstance(payload, dict):
        payload = None
    metrics = None
    curves = None
    pred_targ_ref = None
    if payload is not None:
        metrics = payload.get("metrics")
        curves = payload.get("curves")
        if "predictions" in payload or "targets" in payload:
            try:
                pred_targ_ref = {
                    "predictions_n": len(payload.get("predictions") or []),
                    "targets_n": len(payload.get("targets") or []),
                }
            except TypeError:
                pred_targ_ref = {"predictions_n": None, "targets_n": None}
    status_doc = {
        "experiment_id": args.experiment_id,
        "run_id": args.run_id,
        "status": record.get("state"),
        "exit_code": record.get("exit"),
        "child_exit": record.get("child_exit"),
        "verdict": record.get("verdict"),
        "cmd": record.get("cmd"),
        "timeout": record.get("timeout"),
        "duration_s": record.get("duration"),
        "protocol_hash": args.protocol_hash,
        "commit": commit,
        "stdout_sha256": hashlib.sha256(
            stdout_text.encode("utf-8")).hexdigest(),
        "metrics": metrics,
    }
    if "error" in record:
        status_doc["error"] = record["error"]
    with open(os.path.join(outdir, "status.json"), "w",
              encoding="utf-8") as fh:
        json.dump(status_doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    config_doc = {
        "protocol_hash": args.protocol_hash,
        "commit": commit,
        "env": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "hardware": {
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "config": None,
        "params": None,
        "seeds": None,
        "budget": None,
        "curves": curves,
        "predictions_targets_ref": pred_targ_ref,
        "overlap": None,
        "status": record.get("state"),
    }
    with open(os.path.join(outdir, "config.json"), "w",
              encoding="utf-8") as fh:
        json.dump(config_doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return outdir


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    # Fail-closed validation -> invalid(2). argparse errors already exit 2.
    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        parser.error("missing command after '--'")
    if not args.experiment_id or not args.experiment_id.strip():
        parser.error("missing --experiment-id")
    if not args.run_id or not args.run_id.strip():
        parser.error("missing --run-id")
    try:
        timeout = float(args.timeout)
    except (TypeError, ValueError):
        parser.error("malformed --timeout")
    if not math.isfinite(timeout) or timeout <= 0:
        parser.error("nonfinite/nonpositive --timeout")
    if not args.output or not str(args.output).strip():
        parser.error("missing --output")
    if not args.protocol_hash or not str(args.protocol_hash).strip():
        parser.error("missing --protocol-hash")
    record = run_case(
        args.experiment_id, args.run_id, cmd, timeout,
        str(args.output), str(args.protocol_hash), args.metrics_file,
    )
    record["cmd"] = cmd
    record["timeout"] = timeout
    commit = _best_effort_commit()
    try:
        _write_artifacts(record, args, commit)
    except OSError as exc:
        print("artifact write failed: %s" % exc, file=sys.stderr)
        return 2
    return int(record.get("exit", 2))


if __name__ == "__main__":
    sys.exit(main())
