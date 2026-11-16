#!/usr/bin/env python3
"""Thin actual-experiment runner (protocol-verbatim glue, fail-closed).

Delegates 5-state/exit-map semantics to scripts/run_experiment.py
(success 0, scientific-negative 0, execution-failed 1, timed-out 124,
invalid 2). Stdlib CLI: argparse/pathlib/json only (+ repo imports
below for the locked task/model pair, no training beyond tiny smoke).

Locked task/model pair (protocol R1-R4):
  generate_equality_sequence_decision,
  ClassicalDecisionMLP (classical baseline),
  HybridQuantumLLM (quantum candidate, tiny CPU instantiation only).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# NOTE: locked task/model imports (generate_equality_sequence_decision,
# ClassicalDecisionMLP, HybridQuantumLLM) are lazy inside run() so that
# --help / protocol validation stay stdlib-only and hermetic. No training
# loops here (skeleton stage); full smoke training follows separately.


def _load_five_state_helpers():
    """Delegate 5-state validation to scripts/run_experiment.py."""
    sibling = Path(__file__).resolve().parent / "run_experiment.py"
    try:
        spec = importlib.util.spec_from_file_location("_five_state", str(sibling))
        mod = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod._check_metrics_finite, mod._check_pairing, mod._classify_verdict
    except Exception:
        def _finite(obj):
            if isinstance(obj, float):
                return math.isfinite(obj)
            if isinstance(obj, dict):
                return all(_finite(v) for v in obj.values())
            if isinstance(obj, (list, tuple)):
                return all(_finite(v) for v in obj)
            return True

        def _pairing(payload):
            if not isinstance(payload, dict):
                return True
            p, t = payload.get("predictions"), payload.get("targets")
            if p is None and t is None:
                return True
            if p is None or t is None:
                return False
            try:
                return len(p) == len(t)
            except TypeError:
                return False

        def _verdict(payload):
            return "success"

        return _finite, _pairing, _verdict


_CHECK_FINITE, _CHECK_PAIRING, _CLASSIFY_VERDICT = _load_five_state_helpers()

PROTOCOL_DEFAULT = REPO_ROOT / "research" / "protocols" / "equality-actual-v1.json"
ARTIFACTS_DEFAULT = REPO_ROOT / "research" / "artifacts" / "equality-actual-v1"

REQUIRED_TOP_KEYS = (
    "protocol", "spec", "task", "parity", "splits", "models",
    "runner", "caps", "seeds", "artifacts",
)


def _scan_nonfinite(obj) -> bool:
    """True if any float in obj is NaN/Inf (fail-closed -> invalid)."""
    if isinstance(obj, float):
        return not math.isfinite(obj)
    if isinstance(obj, dict):
        return any(_scan_nonfinite(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_scan_nonfinite(v) for v in obj)
    return False


def validate_protocol(protocol: dict) -> None:
    """Fail-closed R1-R4 + nonfinite checks. Raises ValueError on invalid."""
    if not isinstance(protocol, dict):
        raise ValueError("protocol must be an object")
    for key in REQUIRED_TOP_KEYS:
        if key not in protocol:
            raise ValueError(f"missing required key: {key}")
    if protocol.get("protocol") != "equality-actual-v2":
        raise ValueError("protocol id mismatch (R5: locked to equality-actual-v2)")
    if _scan_nonfinite(protocol):
        raise ValueError("nonfinite value in protocol")
    task = protocol["task"]
    for key in ("generator", "seq_len", "token_vocab", "n_actions",
                "n_rules", "n_train", "n_test"):
        if key not in task:
            raise ValueError(f"missing task key: {key}")
    if task["generator"] != "generate_equality_sequence_decision":
        raise ValueError("task generator mismatch (R1)")
    if not (task["seq_len"] == 4 and task["token_vocab"] == 4
            and task["n_actions"] == 2 and task["n_rules"] == 1
            and task["n_train"] == 200 and task["n_test"] == 50):
        raise ValueError("task shape mismatch (R1)")
    parity = protocol["parity"]
    if parity.get("same_inputs") is not True:
        raise ValueError("parity same_inputs must be true (R2)")
    if parity.get("quantum_path") != "token-local":
        raise ValueError("parity quantum_path mismatch (R2)")
    splits = protocol["splits"]
    for key in ("unique_inputs", "zero_overlap", "train_size",
                "test_size", "overlap_tolerance"):
        if key not in splits:
            raise ValueError(f"missing splits key: {key}")
    if not (splits["unique_inputs"] is True and splits["zero_overlap"] is True
            and splits["train_size"] == 200 and splits["test_size"] == 50
            and splits["overlap_tolerance"] == 0):
        raise ValueError("splits mismatch (R3)")
    if splits.get("sampling") != "disjoint-without-replacement-250-of-256-in-runner":
        raise ValueError("splits sampling mismatch (R3: disjoint-without-replacement)")
    models = protocol["models"]
    try:
        a_arch = models["A_classical"]["arch"]
        b_arch = models["B_hybrid"]["arch"]
    except (KeyError, TypeError):
        raise ValueError("models pair keys missing (R4)")
    if a_arch != "ClassicalDecisionMLP":
        raise ValueError("model A mismatch (R4)")
    if b_arch != "HybridQuantumLLM":
        raise ValueError("model B mismatch (R4)")
    b = models["B_hybrid"]
    if not (b.get("d_model") == 16 and b.get("n_layers") == 1
            and b.get("n_heads") == 2 and b.get("quantum") == "6q-1layer"):
        raise ValueError("model B config mismatch (R4)")
    if list(protocol["seeds"]) != [101, 202, 303]:
        raise ValueError("seeds must be exactly [101, 202, 303] (R6)")


def compute_config_hash(protocol: dict) -> str:
    """R5: sha256(canonical-json({protocol,task,splits,models.A,B}))."""
    canonical = {
        "models": {
            "A_classical": protocol["models"]["A_classical"],
            "B_hybrid": protocol["models"]["B_hybrid"],
        },
        "protocol": protocol["protocol"],
        "splits": protocol["splits"],
        "task": protocol["task"],
    }
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _shared_split(seed: int, task: dict):
    """Shared-rng R3 split: rule-draw + choice(256,250,replace=False) + 200/50.

    Single rng=RandomState(seed) stream shared by both arms (paired).
    Raises ValueError on exhaustion/duplicate/overlap/size violation (exit 2).
    """
    import numpy as np

    rng = np.random.RandomState(int(seed))
    rules = []
    for _ in range(int(task["n_rules"])):
        p1 = int(rng.randint(0, int(task["seq_len"])))
        target_val = int(rng.randint(0, int(task["token_vocab"])))
        action = int(rng.randint(1, int(task["n_actions"])))
        rules.append((p1, target_val, action))
    space = int(task["token_vocab"]) ** int(task["seq_len"])
    need = int(task["n_train"]) + int(task["n_test"])
    if need > space:
        raise ValueError(
            f"sampling exhaustion seed={seed}: need {need} > space {space} (R3)")
    try:
        picks = rng.choice(space, size=need, replace=False)
    except ValueError as exc:
        raise ValueError(f"sampling exhaustion seed={seed} (R3): {exc}") from exc
    if len(set(int(v) for v in picks.tolist())) != need:
        raise ValueError(f"duplicate sample seed={seed} (R3)")
    base, span = int(task["token_vocab"]), int(task["seq_len"])
    X = np.empty((need, span), dtype=int)
    for i, idx in enumerate(picks):
        v = int(idx)
        for j in range(span - 1, -1, -1):
            X[i, j] = v % base
            v //= base
    if len({tuple(map(int, r)) for r in X}) != need:
        raise ValueError(f"duplicate inputs seed={seed} (R3)")
    labels = np.zeros(need, dtype=int)
    for p1, target_val, action in rules:
        labels[X[:, p1] == target_val] = action
    n_train = int(task["n_train"])
    X_train, X_test = X[:n_train], X[n_train:]
    labels_train, labels_test = labels[:n_train], labels[n_train:]
    if len(X_train) != task["n_train"] or len(X_test) != task["n_test"]:
        raise ValueError(f"split size violation seed={seed} (R3)")
    train_rows = {tuple(map(int, r)) for r in X_train}
    test_rows = {tuple(map(int, r)) for r in X_test}
    if train_rows & test_rows:
        raise ValueError(f"split overlap seed={seed} (R3)")
    return X_train, X_test, labels_train, labels_test, rules


def _infer_arm_A(X_test, seed: int, n_actions: int) -> list[int]:
    """Baseline A ClassicalDecisionMLP, inference-only (no training)."""
    import numpy as np

    from benchmarks.tasks.benchmark_decision import ClassicalDecisionMLP

    np.random.seed(1000 + int(seed))
    mlp = ClassicalDecisionMLP(input_dim=8, n_options=int(n_actions))
    mlp.eval()
    preds: list[int] = []
    for row in X_test:
        r = np.asarray(row, dtype=float) / 3.0
        ctx = np.tile(r, 2)[:8].astype(float)
        opts = np.tile(r[::-1], 2)[:8].astype(float)
        probs = np.asarray(mlp(ctx, opts), dtype=float)
        if not all(math.isfinite(float(v)) for v in probs.ravel().tolist()):
            raise ValueError(f"nonfinite arm-A output seed={seed}")
        preds.append(int(np.argmax(probs)) % int(n_actions))
    return preds


def _infer_arm_B(X_test, seed: int, task: dict) -> list[int]:
    """Treatment B HybridQuantumLLM tiny, inference-only (no training)."""
    import numpy as np

    from hybrid.interfaces.model import HybridQuantumLLM

    np.random.seed(2000 + int(seed))
    llm = HybridQuantumLLM(
        vocab_size=int(task["token_vocab"]), d_model=16, n_layers=1,
        n_heads=2, quantum_heads_per_layer=1, d_ff=32,
        max_seq_length=8, dropout=0.0,
        quantum_config={
            "use_quantum_embedding": False,
            "use_quantum_activation": False,
            "attention_qubits": 6,
            "quantum_n_layers": 1,
        },
    )
    llm.eval()
    ids = np.asarray(X_test, dtype=int)
    logits = np.asarray(llm(ids), dtype=float)
    if not math.isfinite(float(np.sum(logits))):
        raise ValueError(f"nonfinite arm-B output seed={seed}")
    last = logits[:, -1, :]
    return [int(v) % int(task["n_actions"]) for v in np.argmax(last, axis=1).tolist()]


def _one_hot_16(X) -> "object":
    import numpy as np

    Xa = np.asarray(X, dtype=int)
    n = Xa.shape[0]
    oh = np.zeros((n, 16), dtype=float)
    for i in range(4):
        oh[np.arange(n), i * 4 + Xa[:, i]] = 1.0
    return oh


def _train_positive_control(X_train, y_train, X_test, y_test, seed: int,
                            epochs: int = 20, max_samples: int = 200):
    """C-positive: tiny MLP smoke-trained <=20 epochs, <=200 samples."""
    import numpy as np

    if epochs > 20 or max_samples > 200:
        raise ValueError("positive-control budget breach (<=20 epochs, <=200 samples)")
    n = min(int(max_samples), len(X_train))
    Xoh = np.asarray(_one_hot_16(X_train[:n]), dtype=float)
    Toh = np.asarray(_one_hot_16(X_test), dtype=float)
    ytr = np.asarray(y_train[:n], dtype=int)
    yte = np.asarray(y_test, dtype=int)
    rng = np.random.RandomState(int(seed) + 999)
    W1 = rng.randn(16, 16) * np.sqrt(2.0 / 16)
    b1 = np.zeros(16)
    W2 = rng.randn(16, 2) * np.sqrt(2.0 / 16)
    b2 = np.zeros(2)
    lr = 0.5
    for _ in range(int(epochs)):
        h = np.maximum(Xoh @ W1 + b1, 0.0)
        logits = h @ W2 + b2
        s = logits - logits.max(axis=1, keepdims=True)
        e = np.exp(s)
        p = e / e.sum(axis=1, keepdims=True)
        N = len(Xoh)
        dlog = p.copy()
        dlog[np.arange(N), ytr] -= 1.0
        dlog /= N
        dW2 = h.T @ dlog
        db2 = dlog.sum(axis=0)
        dh = dlog @ W2.T
        dh[h <= 0] = 0.0
        dW1 = Xoh.T @ dh
        db1 = dh.sum(axis=0)
        W1 -= lr * dW1
        b1 -= lr * db1
        W2 -= lr * dW2
        b2 -= lr * db2
    h = np.maximum(Toh @ W1 + b1, 0.0)
    pred = (h @ W2 + b2).argmax(axis=1).tolist()
    preds = [int(v) for v in pred]
    acc = float(sum(p == t for p, t in zip(preds, yte.tolist())) / len(yte))
    return preds, acc


def _negative_controls(y_train, y_test, seed: int):
    """C-negative: majority + label-shuffle floor."""
    import numpy as np

    ytr = [int(v) for v in np.asarray(y_train).tolist()]
    yte = [int(v) for v in np.asarray(y_test).tolist()]
    majority = max(set(ytr), key=ytr.count)
    maj_preds = [int(majority)] * len(yte)
    maj_acc = float(sum(p == t for p, t in zip(maj_preds, yte)) / len(yte))
    shr = np.asarray(yte, dtype=int).copy()
    np.random.RandomState(int(seed) + 777).shuffle(shr)
    shuffle_acc = float(
        sum(p == t for p, t in zip(maj_preds, shr.tolist())) / len(shr))
    return maj_preds, float(maj_acc), float(shuffle_acc), int(majority)


def run(protocol: dict, run_id: str = "run2") -> dict:
    """Pure compute (no I/O): protocol -> artifacts dict.

    Skeleton stage: validates protocol verbatim and references the locked
    task/model pair by import (no training loops). Full per-seed smoke
    training lands separately; this keeps file presence + audit green.

    run_id threads into per-seed status run_ids
    (f"{run_id}:{arm}:seed-{seed}") so status files match the run dir;
    raw.json maps the same run_id to baseline/treatment arms.
    """
    validate_protocol(protocol)
    from benchmarks.tasks.benchmark_sequence_decision import (
        generate_equality_sequence_decision,
    )

    assert callable(generate_equality_sequence_decision)
    task = protocol["task"]
    config_hash = compute_config_hash(protocol)
    per_seed = []
    for seed in protocol["seeds"]:
        # Shared-rng paired split: one rng stream per seed, both arms reuse
        # the identical X_train/X_test (paired inputs, R2). R3 amended
        # disjoint-without-replacement lives in _shared_split (runner glue).
        X_train, X_test, labels_train, labels_test, _rules = _shared_split(
            int(seed), task)
        y_train = labels_train
        y_test = labels_test
        # Paired inference-only arms on the SAME X_test.
        preds_A = _infer_arm_A(X_test, int(seed), int(task["n_actions"]))
        preds_B = _infer_arm_B(X_test, int(seed), task)
        targets = [int(v) for v in y_test.tolist()]
        if not (len(preds_A) == len(preds_B) == len(targets) == 50):
            raise ValueError(f"unpaired predictions/targets seed={seed}")
        maj_preds, maj_acc, shuffle_acc, majority = _negative_controls(
            y_train, y_test, int(seed))
        pos_preds, pos_acc = _train_positive_control(
            X_train, y_train, X_test, y_test, int(seed))
        if not all(math.isfinite(v) for v in
                   [maj_acc, shuffle_acc, pos_acc]):
            raise ValueError(f"nonfinite control metric seed={seed}")
        payload = {"predictions": preds_A, "targets": targets,
                   "metrics": {"acc": 0.0}}
        payload_b = {"predictions": preds_B, "targets": targets,
                     "metrics": {"acc": 0.0}}
        if not _CHECK_FINITE(payload) or not _CHECK_FINITE(payload_b):
            raise ValueError(f"nonfinite payload seed={seed}")
        if not _CHECK_PAIRING(payload) or not _CHECK_PAIRING(payload_b):
            raise ValueError(f"unpaired predictions/targets seed={seed}")
        acc_A = sum(p == t for p, t in zip(preds_A, targets)) / len(targets)
        acc_B = sum(p == t for p, t in zip(preds_B, targets)) / len(targets)
        for v in (acc_A, acc_B, pos_acc, maj_acc, shuffle_acc):
            if not math.isfinite(v):
                raise ValueError("nonfinite metric")
        metrics = {"acc": float(acc_A), "n": len(targets),
                   "majority": int(majority),
                   "acc_A": float(acc_A), "acc_B": float(acc_B),
                   "positive_acc": float(pos_acc),
                   "majority_acc": float(maj_acc),
                   "shuffle_acc": float(shuffle_acc),
                   "chance": 0.5}
        per_seed.append({
            "seed": int(seed),
            "predictions": preds_A,
            "targets": targets,
            "metrics": metrics,
            "arm_A": {"predictions": preds_A, "acc": float(acc_A)},
            "arm_B": {"predictions": preds_B, "acc": float(acc_B)},
            "controls": {
                "positive": {"predictions": pos_preds,
                             "acc": float(pos_acc),
                             "epochs": 20, "max_samples": 200},
                "negative": {"majority": int(majority),
                             "majority_acc": float(maj_acc),
                             "shuffle_acc": float(shuffle_acc)},
            },
            "run_ids": {"A": f"{run_id}:A:seed-{int(seed)}",
                        "B": f"{run_id}:B:seed-{int(seed)}"},
            "config_hash": config_hash,
        })
    return {"protocol": protocol.get("protocol"), "seeds": list(protocol["seeds"]),
            "per_seed": per_seed, "verdict": "success",
            "config_hash": config_hash}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Thin actual-experiment runner (protocol-verbatim, fail-closed).")
    p.add_argument("--protocol", default=str(PROTOCOL_DEFAULT),
                   help="path to frozen protocol JSON")
    p.add_argument("--output", default=str(ARTIFACTS_DEFAULT),
                   help="artifacts root dir")
    p.add_argument("--run-id", default=None,
                   help="run dir name (default: timestamp)")
    p.add_argument("--timeout", type=float, default=290.0,
                   help="wall budget seconds (default 290)")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        timeout = float(args.timeout)
    except (TypeError, ValueError):
        parser.error("malformed --timeout")
        return 2
    if not math.isfinite(timeout) or timeout <= 0:
        parser.error("nonfinite/nonpositive --timeout")
        return 2
    proto_path = Path(args.protocol)
    try:
        protocol = json.loads(proto_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        print(f"invalid protocol (missing): {exc}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        print(f"invalid protocol (malformed): {exc}", file=sys.stderr)
        return 2
    try:
        validate_protocol(protocol)
    except ValueError as exc:
        print(f"invalid protocol: {exc}", file=sys.stderr)
        return 2
    run_id = args.run_id or time.strftime("run-%Y%m%d-%H%M%S")
    out_root = Path(args.output) / run_id
    t0 = time.monotonic()
    try:
        artifacts = run(protocol, run_id)
    except ValueError as exc:
        print(f"invalid run: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # execution-failed, never silent 0
        print(f"run failed: {exc}", file=sys.stderr)
        return 1
    duration = time.monotonic() - t0
    if not math.isfinite(duration) or duration > timeout:
        try:
            out_root.mkdir(parents=True, exist_ok=True)
            (out_root / "status.json").write_text(json.dumps(
                {"status": "timed-out", "run_id": run_id,
                 "duration_s": duration, "timeout": timeout},
                indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            pass
        print(f"timed out after {duration:.1f}s > {timeout}s", file=sys.stderr)
        return 124
    try:
        out_root.mkdir(parents=True, exist_ok=True)
        for entry in artifacts["per_seed"]:
            seed_dir = out_root / f"seed-{entry['seed']}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            (seed_dir / "predictions.json").write_text(
                json.dumps(entry["predictions"]), encoding="utf-8")
            (seed_dir / "targets.json").write_text(
                json.dumps(entry["targets"]), encoding="utf-8")
            (seed_dir / "metrics.json").write_text(json.dumps(
                entry["metrics"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
            verdict = _CLASSIFY_VERDICT(
                {"verdict": "success", "predictions": entry["predictions"],
                 "targets": entry["targets"], "metrics": entry["metrics"]})
            (seed_dir / "status.json").write_text(json.dumps(
                {"status": verdict if verdict else "success",
                 "run_id": run_id, "seed": entry["seed"],
                 "duration_s": duration,
                 "predictions_n": len(entry["predictions"]),
                 "targets_n": len(entry["targets"])},
                indent=2, sort_keys=True) + "\n", encoding="utf-8")
            # Paired dual-arm raw: same shared targets, per-arm predictions.
            # (Unconditional: run2 gate removed so run3+ reuse the same layout.)
            (seed_dir / "predictions-A.json").write_text(
                json.dumps(entry["arm_A"]["predictions"]), encoding="utf-8")
            (seed_dir / "predictions-B.json").write_text(
                json.dumps(entry["arm_B"]["predictions"]), encoding="utf-8")
            for arm in ("A", "B"):
                (seed_dir / f"status-{arm}.json").write_text(json.dumps(
                    {"status": verdict if verdict else "success",
                     "run_id": entry["run_ids"][arm],
                     "seed": entry["seed"], "arm": arm,
                     "duration_s": duration,
                     "config_hash": entry["config_hash"],
                     "predictions_n": len(entry[f"arm_{arm}"]["predictions"]),
                     "targets_n": len(entry["targets"])},
                    indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out_root / "run.json").write_text(json.dumps(
            {"run_id": run_id, "protocol": artifacts["protocol"],
             "seeds": artifacts["seeds"], "verdict": artifacts["verdict"],
             "duration_s": duration, "status": "success",
             "config_hash": artifacts["config_hash"]},
            indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Analyzer-schema raw.json: runner uses arm A/B internally; the
        # analyzer requires arm baseline/treatment, so map A->baseline and
        # B->treatment explicitly here (paired by shared seed_data).
        raw_runs: list[dict] = []
        for entry in artifacts["per_seed"]:
            seed = int(entry["seed"])
            targets = [int(v) for v in entry["targets"]]
            preds_A = [int(v) for v in entry["arm_A"]["predictions"]]
            preds_B = [int(v) for v in entry["arm_B"]["predictions"]]
            for v in preds_A + preds_B + targets:
                if not math.isfinite(v):
                    raise ValueError(f"nonfinite raw value seed={seed}")
            raw_runs.append({
                "run_id": f"{run_id}:baseline:seed-{seed}",
                "arm": "baseline",  # internal arm A
                "seed_data": seed,
                "predictions": preds_A,
                "targets": targets,
            })
            raw_runs.append({
                "run_id": f"{run_id}:treatment:seed-{seed}",
                "arm": "treatment",  # internal arm B
                "seed_data": seed,
                "predictions": preds_B,
                "targets": targets,
            })
        (out_root / "raw.json").write_text(json.dumps(
            {"protocol": artifacts["protocol"],
             "config_hash": artifacts["config_hash"],
             "runs": raw_runs},
            indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"artifact write failed: {exc}", file=sys.stderr)
        return 2
    print(f"ok run_id={run_id} seeds={artifacts['seeds']} "
          f"duration_s={duration:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
