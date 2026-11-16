"""
Guards for Phase 1.1 attention remainder behaviour (Spec M2-1).

The quantum attention head truncates the sequence at ``max_quantum_seq``
(default 16); positions beyond that form a "remainder".  In the unfixed
implementation the remainder attends only within itself and never sees the
prefix, which introduces truncation bias whenever S > max_quantum_seq.

Spec M2-1 requires the remainder to attend the full prefix so no prefix
information is truncated.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hybrid.attention.quantum_attention import QuantumMultiHeadAttention


def _make_model() -> QuantumMultiHeadAttention:
    model = QuantumMultiHeadAttention(
        d_model=8,
        n_heads=1,
        quantum_heads=1,
        quantum_qubits=6,
        n_layers=1,
        max_quantum_seq=16,
        dropout=0.0,
    )
    model.eval()  # deterministic: no dropout, circuit cache enabled
    return model


def test_attention_s17():
    """S=17 (past max_quantum_seq=16) vs S=16: remainder must attend prefix."""
    rng = np.random.RandomState(1138)
    model = _make_model()

    # Two different 16-token prefixes and one shared remainder token Q.
    P1 = rng.randn(1, 16, 8).astype(np.float64)
    P2 = rng.randn(1, 16, 8).astype(np.float64)
    Q = rng.randn(1, 1, 8).astype(np.float64)

    x16 = P1                                 # (1, 16, 8) -- all quantum
    x17_a = np.concatenate([P1, Q], axis=1)  # (1, 17, 8) -- last is remainder
    x17_b = np.concatenate([P2, Q], axis=1)  # same remainder Q, different prefix

    out16 = model(x16)
    out17_a = model(x17_a)
    out17_b = model(x17_b)

    # 1. Shared quantum prefix (positions 0..15) is unaffected by sequence length.
    assert out17_a.shape == (1, 17, 8)
    assert np.allclose(out17_a[:, :16, :], out16, atol=1e-5)

    # 2. THE GUARD: the remainder position (16) must attend the full prefix,
    #    not just itself.  Same remainder token Q with two different prefixes
    #    must yield different remainder outputs (truncation bias removed).
    assert not np.allclose(out17_a[:, 16, :], out17_b[:, 16, :], atol=1e-4)


def test_stats_n_lt_2_not_computed():
    """Spec M3-1: n<2 degenerate case must not be computed; reports n + not_computed."""
    from benchmarks.analysis.statistics import paired_significance

    # Single seed: not enough to compute a paired t-test.
    res = paired_significance([0.5], [0.8])
    assert res["n"] == 1
    assert res["not_computed"] is True
    assert res["significant"] is False
    assert res["p_value"] == 1.0

    # Two seeds with variance in the diff: computable.
    res2 = paired_significance([0.5, 0.6], [0.8, 0.85])
    assert res2["n"] == 2
    assert res2["not_computed"] is False


def test_winner_tie_unless_significant():
    """Spec M3-2: winner is Tie unless significant (never Classical by default)."""
    from benchmarks.analysis.statistics import summarize_results

    results = {
        "task_a": {
            "s1": {
                "models": {
                    "classical": {"mean_test_acc": 0.80},
                    "quantum_6q": {"mean_test_acc": 0.82},
                    "moe_6_9_12": {"mean_test_acc": 0.79},
                },
                "significance": {
                    "classical_vs_quantum": {
                        "p_value": 0.50,
                        "significant": False,
                    }
                },
            }
        }
    }

    table = summarize_results(results)
    data_rows = [line for line in table.splitlines() if line.startswith("| task_a")]
    assert data_rows[0].rstrip().endswith("| Tie |")

    # Significant + quantum ahead -> Quantum.
    results["task_a"]["s1"]["significance"]["classical_vs_quantum"] = {
        "p_value": 0.01,
        "significant": True,
    }
    table_sig = summarize_results(results)
    data_rows_sig = [line for line in table_sig.splitlines() if line.startswith("| task_a")]
    assert data_rows_sig[0].rstrip().endswith("| Quantum |")


def test_parity_sign_zero_expectation():
    """Spec M4-1: sign(0) must not silently collapse parity to 0.

    np.sign(0) == 0 zeroes the product, so a zero Pauli-Z expectation yields
    (1-0)/2 = 0.5 -> int 0 regardless of the true parity (silent bug, Spec 26-36).
    Zero expectations must map to sign +1 (bit 0) so parity is computed from the
    non-zero expectations.
    """
    from quantum.circuits.core import parity_from_expectations

    z = np.array([1.0, -1.0, 0.0])  # bit pattern 0,1,(zero expectation)
    parity = int(parity_from_expectations(z))
    assert parity == 1, f"sign(0) silently collapsed parity to {parity}"
