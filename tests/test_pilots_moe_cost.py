"""
P3 MoE-cost pilot (REQ-P3, pilots plan row 3).
Caps: 10-15m, tiny model, local only. No secrets, no push.

Reads (verbatim basis):
- quantum/moe/__init__.py:93-103 (sparse eval: single-expert per batch)
  vs :105-121 (dense train: soft routing, run all experts, weighted sum).
- benchmarks/runner.py timing helper: time.perf_counter() around
  train loop (t_start) / epoch (epoch_t0 / epoch_time / total_time_s).

Behavior: dense-train (all-experts) wall-clock ~= n_experts x
single-expert (sparse eval) wall-clock, measured with real
perf_counter timing over reps (no call-count wrapper).
TDD GREEN: strict ~=n x bound (1.8-2.2 for n=2); failure message
reports opposite (verbatim times/ratio) for implementer.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

WALL_BUDGET_S = 15 * 60  # 10-15m wall cap (mirror P1/P2)


def _make_tiny_head():
    # Tiny, local only; [6, 9] avoids 12q NaN (benchmarks/runner.py:51-58).
    # Fixed seed: deterministic router init -> deterministic sparse routing
    # (ratio is routing-dependent since experts differ in cost: 6q vs 9q).
    # Scoped seed (LOW): save/restore global RNG around init.
    _state = np.random.get_state()
    np.random.seed(5)
    try:
        from quantum.moe import AdaptiveQuantumHead

        head = AdaptiveQuantumHead(
            d_model=8, head_dim=8, qubit_configs=[6, 9], n_layers=1
        )
    finally:
        np.random.set_state(_state)
    assert head.n_experts == 2
    return head


def test_dense_train_cost_scales_with_n_experts():
    """Dense-train all-experts wall-clock ~= n_experts x single-expert."""
    t_wall0 = time.perf_counter()
    head = _make_tiny_head()
    n_experts = head.n_experts  # 2 -> expect ratio ~= 2.0
    rng = np.random.RandomState(0)
    q = rng.randn(2, 2, 8).astype(np.float64)  # batch=2, seq=2, tiny
    k = rng.randn(2, 2, 8).astype(np.float64)
    v = rng.randn(2, 2, 8).astype(np.float64)

    # Warmup, real minimal calls (timing mirrors benchmarks/runner.py).
    head.train()
    head(q, k, v)
    head.eval()
    head(q, k, v)

    reps = 10
    head.train()  # dense: moe/__init__.py:105-121, all experts
    t0 = time.perf_counter()
    for _ in range(reps):
        head(q, k, v)
    dense_t = (time.perf_counter() - t0) / reps

    head.eval()  # sparse: moe/__init__.py:93-103, single expert
    t0 = time.perf_counter()
    for _ in range(reps):
        head(q, k, v)
    sparse_t = (time.perf_counter() - t0) / reps

    ratio = dense_t / max(sparse_t, 1e-12)
    # Routed expert per batch in sparse-eval mode (moe/__init__.py:93-103:
    # expert_idx = argmax gate_probs[b]); recomputed via router (no prod change).
    head.eval()
    _logits = head.router(q)
    _probs = head.router.softmax(_logits)
    expert_idx = [int(i) for i in np.argmax(np.asarray(_probs), axis=1)]
    wall_s = time.perf_counter() - t_wall0
    assert wall_s < WALL_BUDGET_S, f"wall cap breached {wall_s:.1f}s"
    print(
        f"\n[P3 pilot] dense_t={dense_t:.4f}s sparse_t={sparse_t:.4f}s "
        f"ratio={ratio:.2f} n_experts={n_experts} reps={reps} "
        f"expert_idx={expert_idx} wall={wall_s:.1f}s"
    )
    # One assertion focus: dense ~= n x single. Opposite reported above.
    assert 1.8 <= ratio <= 2.2, (
        f"OPPOSITE: dense_t={dense_t:.4f}s sparse_t={sparse_t:.4f}s "
        f"ratio={ratio:.2f} != ~{n_experts}x reps={reps} "
        f"expert_idx={expert_idx}"
    )
