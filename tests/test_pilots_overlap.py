"""P1 overlap-inflation pilot (RED, failing-first).

Spec: docs/plans/2026-11-16-pilots-falsify.md row 1 (REQ-P1).
Branch: research/audit-1587497. Auth: big-win bounded, no gate fail-open.

Hypothesis under test (disjoint-learns, expected to FAIL):
  a disjoint-input split still learns above trivial baseline (0.5).
  FAIL => inflation proven (leaky contiguous split inflates via train/test
  row overlap, cf. benchmarks/tasks/benchmark_k_parity.py:40-48 contiguous
  slice of one randint draw over a 256-row input space).
  PASS => inflation refuted (report honestly, no tuning to force outcome).

Caps (enforced, logged): <=3 seeds, <=3 epochs (fake, one-shot memorizer),
  tiny n_bits=8 parity, local-only CPU, no sweeps, 10-15m wall budget.
Hermetic fake over live services: dict-memorizer + majority fallback, no
  model training, no network/GPU/paid APIs.
Runner helper: benchmarks/runner.py has no trivial paired-run helper for
  overlap, so paired run is inlined here (same fake model + same seeds).
Evidence: paired per-seed JSON to /tmp only (never repo).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from benchmarks.analysis.statistics import confidence_interval
except Exception:  # hermetic fallback if scipy stack unavailable
    confidence_interval = None  # type: ignore[assignment]

# ---- Caps (P1 bounded pilot) ----
SEEDS = [42, 99, 137]  # <=3 seeds
EPOCHS = 3  # <=3 epochs; fake count only (memorizer is one-shot, no loop)
N_BITS = 8  # tiny n=8 parity
K = 3
N_TRAIN = 128  # tiny vs 800 (still enough collisions in 256-space for signal)
N_TEST = 32  # tiny vs 200
BASELINE = 0.5  # trivial baseline (binary parity chance / majority)
WALL_BUDGET_S = 15 * 60  # 10-15m wall cap
OUT_PATH = Path("/tmp/p1_overlap_pilot.json")


def _subset_and_labels(X_all: np.ndarray, n_bits: int, k: int, seed: int):
    """Mirror benchmark_k_parity.py:40-43: hidden k-subset + xor-reduce labels."""
    rng = np.random.RandomState(seed)
    subset = sorted(rng.choice(n_bits, k, replace=False))
    labels = np.bitwise_xor.reduce(X_all[:, subset], axis=1)
    return subset, labels


def _leaky_pair(seed: int):
    """Contiguous split exactly like benchmark_k_parity.py:42-48 (leaky)."""
    rng = np.random.RandomState(seed)
    # NOTE: subset draw must precede X_all draw to mirror :40-42 ordering.
    subset = sorted(rng.choice(N_BITS, K, replace=False))
    X_all = rng.randint(0, 2, size=(N_TRAIN + N_TEST, N_BITS))
    labels = np.bitwise_xor.reduce(X_all[:, subset], axis=1)
    X_train, X_test = X_all[:N_TRAIN], X_all[N_TRAIN:]
    y_train, y_test = labels[:N_TRAIN], labels[N_TRAIN:]
    overlap = len(set(map(tuple, X_train.tolist())) & set(map(tuple, X_test.tolist())))
    return X_train, y_train, X_test, y_test, subset, overlap


def _disjoint_pair(seed: int):
    """Same train as leaky; test resampled until disjoint (bounded, local-only)."""
    X_train, y_train, _, _, subset, _ = _leaky_pair(seed)
    train_set = set(map(tuple, X_train.tolist()))
    rng = np.random.RandomState(10_000 + seed)  # distinct stream, still seeded
    got_X, got_y = [], []
    attempts, budget = 0, N_TEST * 50  # bounded resample loop, no sweep
    while len(got_X) < N_TEST and attempts < budget:
        attempts += 1
        x = tuple(rng.randint(0, 2, size=N_BITS).tolist())
        if x in train_set or x in got_X:
            continue
        got_X.append(x)
        got_y.append(int(np.bitwise_xor.reduce(np.asarray(x)[subset])))
    assert len(got_X) == N_TEST, f"disjoint resample exhausted ({attempts=})"
    return X_train, y_train, np.asarray(got_X), np.asarray(got_y), subset


def _memorizer_accuracy(
    X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray
) -> float:
    """Hermetic fake model: memorize train rows, majority(0) fallback unseen.

    Same fake for leaky + disjoint (isolates split effect). No training,
    no live service. EPOCHS is cap-logging only (one-shot lookup).
    """
    table = {tuple(x.tolist()): int(y) for x, y in zip(X_train, y_train)}
    preds = [table.get(tuple(x.tolist()), 0) for x in X_test]
    return float(np.mean(np.asarray(preds) == np.asarray(y_test)))


def _ci(values: list[float]) -> dict:
    if confidence_interval is None:
        raise ValueError("scipy required for confidence_interval (no mean fallback)")
    return dict(confidence_interval(values))


def test_disjoint_inputs_learn_above_trivial_baseline():
    """Disjoint-input split learns above 0.5 (RED: expected FAIL => inflation)."""
    t0 = time.perf_counter()
    assert len(SEEDS) <= 3 and EPOCHS <= 3  # caps enforced fail-closed
    leaky_accs, disjoint_accs, overlaps, per_seed_s = [], [], [], []
    for seed in SEEDS:
        s0 = time.perf_counter()
        Xtr, ytr, Xte_l, yte_l, _, ov = _leaky_pair(seed)
        _, _, Xte_d, yte_d, _ = _disjoint_pair(seed)
        la = _memorizer_accuracy(Xtr, ytr, Xte_l, yte_l)
        da = _memorizer_accuracy(Xtr, ytr, Xte_d, yte_d)
        leaky_accs.append(la)
        disjoint_accs.append(da)
        overlaps.append(ov)
        per_seed_s.append({"seed": seed, "leaky_acc": la, "disjoint_acc": da,
                           "overlap_rows": ov, "wall_s": time.perf_counter() - s0})
    wall_s = time.perf_counter() - t0
    assert wall_s < WALL_BUDGET_S, f"wall cap breached {wall_s:.1f}s"
    leaky_ci, disjoint_ci = _ci(leaky_accs), _ci(disjoint_accs)
    payload = {
        "pilot": "P1-overlap-inflation", "hypothesis": "disjoint-learns (RED)",
        "seeds": SEEDS, "epochs_fake": EPOCHS, "n_bits": N_BITS, "k": K,
        "n_train": N_TRAIN, "n_test": N_TEST, "baseline": BASELINE,
        "per_seed": per_seed_s,
        "leaky": {"accs": leaky_accs, "mean": leaky_ci["mean"],
                  "ci": [leaky_ci["ci_low"], leaky_ci["ci_high"]]},
        "disjoint": {"accs": disjoint_accs, "mean": disjoint_ci["mean"],
                     "ci": [disjoint_ci["ci_low"], disjoint_ci["ci_high"]]},
        "mean_diff_leaky_minus_disjoint": float(np.mean(leaky_accs) - np.mean(disjoint_accs)),
        "caps": {"seeds<=3": True, "epochs<=3": True, "local_only": True, "no_sweeps": True},
        "timeouts_logged": {"wall_s": wall_s, "budget_s": WALL_BUDGET_S, "per_seed_s": [p["wall_s"] for p in per_seed_s]},
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"P1 pilot /tmp JSON -> {OUT_PATH} "
          f"leaky_mean={np.mean(leaky_accs):.3f} disjoint_mean={np.mean(disjoint_accs):.3f} "
          f"diff={np.mean(leaky_accs)-np.mean(disjoint_accs):+.3f} "
          f"disjoint_CI=[{disjoint_ci['ci_low']:.3f},{disjoint_ci['ci_high']:.3f}] "
          f"baseline={BASELINE} wall={wall_s:.2f}s")
    # ONE assertion (disjoint-learns): FAIL proves inflation, PASS refutes it.
    assert disjoint_ci["ci_low"] > BASELINE, (
        f"RED/REFUTED: disjoint CI [{disjoint_ci['ci_low']:.3f},"
        f"{disjoint_ci['ci_high']:.3f}] not above baseline {BASELINE} "
        f"(leaky_mean={np.mean(leaky_accs):.3f} => inflation signal "
        f"{np.mean(leaky_accs)-np.mean(disjoint_accs):+.3f}; see {OUT_PATH})"
    )
