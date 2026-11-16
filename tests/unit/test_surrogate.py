"""
Surrogate + ablation unit tests (NumPy only, no new dependencies).

Covers RIGOR-2 Phase 1 T5:
  * Random Fourier Features approximate an RBF kernel (surrogate check).
  * Removing entanglement from the feature map degrades parity decoding
    (no-entanglement ablation: collective rotations only, no SigmaZZ/CNOT).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np

try:
    from classical.nn import Parameter
    from quantum.circuits.core import (
        QuantumFeatureMapCircuit,
        parity_from_expectations,
    )
    _CORE_OK = True
except Exception:  # pragma: no cover - RED phase: core hook/flag not yet implemented
    _CORE_OK = False


# -----------------------------------------------------------------------
# Surrogate: RFF approximates RBF kernel
# -----------------------------------------------------------------------

def _rff_features(X, D, gamma, seed=0):
    """Random Fourier features for the RBF kernel k(x,y)=exp(-gamma||x-y||^2)."""
    rng = np.random.RandomState(seed)
    d = X.shape[1]
    W = rng.normal(0.0, np.sqrt(2.0 * gamma), size=(D, d))
    b = rng.uniform(0.0, 2.0 * np.pi, size=D)
    return np.sqrt(2.0 / D) * np.cos(X @ W.T + b)


def test_rff_matches_rbf_kernel():
    rng = np.random.RandomState(3)
    X = rng.randn(24, 6)
    Y = rng.randn(24, 6)
    gamma = 0.5
    D = 4096
    phi_X = _rff_features(X, D, gamma)
    phi_Y = _rff_features(Y, D, gamma)
    rff_kernel = phi_X @ phi_Y.T
    dd = np.linalg.norm(X[:, None, :] - Y[None, :, :], axis=2) ** 2
    rbf_kernel = np.exp(-gamma * dd)
    assert np.allclose(rff_kernel, rbf_kernel, atol=0.12)


# -----------------------------------------------------------------------
# Ablation: no-entanglement degrades parity decoding
# -----------------------------------------------------------------------

def _linear_parity_accuracy(feats, y):
    """Deterministic ridge-readout parity accuracy (closed form, no training)."""
    n_states = feats.shape[0]
    A = np.concatenate([feats, np.ones((n_states, 1))], axis=1)
    w = np.linalg.solve(A.T @ A + 1e-9 * np.eye(A.shape[1]), A.T @ y)
    return float(np.mean((A @ w >= 0.5).astype(int) == y))


def test_no_entanglement_degrades_parity():
    if not _CORE_OK:
        raise AssertionError(
            "core.py is missing the no_entanglement flag / parity_from_expectations hook"
        )
    from classical.nn import Parameter
    from quantum.circuits.core import (
        QuantumFeatureMapCircuit,
        parity_from_expectations,
    )

    n = 4
    n_states = 2 ** n
    X = np.eye(n_states)  # computational-basis inputs |0>..|15>
    bits = (np.arange(n_states)[:, None] >> np.arange(n)) & 1
    y = np.bitwise_xor.reduce(bits, axis=1).astype(int)

    rng = np.random.RandomState(4)
    rot = rng.randn(2)            # shared collective rotations (one layer)
    zz = rng.randn(n * (n - 1) // 2)

    ent = QuantumFeatureMapCircuit(n, n_layers=1)
    ent.params = Parameter(np.concatenate([rot, zz]))
    noent = QuantumFeatureMapCircuit(n, n_layers=1, no_entanglement=True)
    noent.params = Parameter(rot)

    fe_ent = np.asarray(ent(X))
    fe_noent = np.asarray(noent(X))

    # 1. The no-entanglement flag drops every SigmaZZ parameter (collective
    #    rotations only) -> fewer params than the entangled circuit.
    assert noent.params.shape[0] == 2
    assert ent.params.shape[0] == 2 + n * (n - 1) // 2

    # 2. The parity hook exists and returns one parity bit per input sample.
    ph = parity_from_expectations(fe_ent)
    assert ph.shape == (n_states,)
    assert set(np.unique(ph).tolist()) <= {0, 1}

    # 3. Without entanglement the circuit is a product of identical single-qubit
    #    rotations, so feature i depends on bit i only.  |0000> (idx 0) and
    #    |0001> (idx 1) differ only in bit 3, hence features 0..2 are identical.
    assert np.allclose(fe_noent[0, :3], fe_noent[1, :3], atol=1e-6)

    # 4. Parity degradation: no-entanglement features are per-bit isolated, so no
    #    linear readout can perfectly recover 4-bit parity (XOR is not linear).
    assert _linear_parity_accuracy(fe_noent, y) < 1.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
