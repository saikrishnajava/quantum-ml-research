"""T3 simulator equivalence probe: fast numpy sim vs QNode (1-2 qubits, <=2 layers)."""
import numpy as np
import pennylane as qml


def _fast_state_1q(theta):
    from quantum.simulator import _ry, apply_gate

    state = np.zeros(2, dtype=complex)
    state[0] = 1.0
    return np.asarray(apply_gate(state, _ry(theta), qubit=0, n_qubits=1), dtype=complex)


def _fast_state_2q(thetas):
    # 2 layers max: layer1 RY x2, entangler CNOT(0->1), layer2 RZ x2
    from quantum.simulator import _ry, _rz, apply_cnot, apply_gate

    t0, t1, t2, t3 = (float(thetas[0]), float(thetas[1]), float(thetas[2]), float(thetas[3]))
    state = np.zeros(4, dtype=complex)
    state[0] = 1.0
    state = apply_gate(state, _ry(t0), qubit=0, n_qubits=2)
    state = apply_gate(state, _ry(t1), qubit=1, n_qubits=2)
    state = apply_cnot(state, control=0, target=1, n_qubits=2)
    state = apply_gate(state, _rz(t2), qubit=0, n_qubits=2)
    state = apply_gate(state, _rz(t3), qubit=1, n_qubits=2)
    return np.asarray(state, dtype=complex)


def _fast_expval_z0_2q(thetas):
    from quantum.simulator import pauli_z_expval

    return float(pauli_z_expval(_fast_state_2q(thetas), qubit=0, n_qubits=2))


def test_sim_equivalence_probe():
    state_atol = 1e-6
    grad_atol = 1e-5
    print(f"TOL state_atol={state_atol:g} grad_atol={grad_atol:g} qubits=[1,2] layers<=2 seeds<=3")
    # 1 qubit, 1 layer
    theta_1q = 0.5
    dev1 = qml.device("default.qubit", wires=1)

    @qml.qnode(dev1)
    def qnode_1q(theta):
        qml.RY(theta, wires=0)
        return qml.state()

    fast_1q = _fast_state_1q(theta_1q)
    ref_1q = np.asarray(qnode_1q(theta_1q), dtype=complex)
    assert np.allclose(fast_1q, ref_1q, atol=state_atol), f"1q state mismatch: {fast_1q} vs {ref_1q}"

    # 2 qubits, <=2 layers (fixed params, 2 seeds, no training)
    for thetas in (np.array([0.3, -0.7, 1.1, 0.2]), np.array([0.9, 0.4, -0.5, 1.3])):
        dev2 = qml.device("default.qubit", wires=2)

        @qml.qnode(dev2)
        def qnode_state(t):
            qml.RY(t[0], wires=0)
            qml.RY(t[1], wires=1)
            qml.CNOT(wires=[0, 1])
            qml.RZ(t[2], wires=0)
            qml.RZ(t[3], wires=1)
            return qml.state()

        @qml.qnode(dev2)
        def qnode_probs(t):
            qml.RY(t[0], wires=0)
            qml.RY(t[1], wires=1)
            qml.CNOT(wires=[0, 1])
            qml.RZ(t[2], wires=0)
            qml.RZ(t[3], wires=1)
            return qml.probs(wires=[0, 1])

        @qml.qnode(dev2, interface="autograd")
        def qnode_expval(t):
            qml.RY(t[0], wires=0)
            qml.RY(t[1], wires=1)
            qml.CNOT(wires=[0, 1])
            qml.RZ(t[2], wires=0)
            qml.RZ(t[3], wires=1)
            return qml.expval(qml.PauliZ(0))

        from quantum.simulator import probability

        fast_s = _fast_state_2q(thetas)
        ref_s = np.asarray(qnode_state(thetas), dtype=complex)
        assert np.allclose(fast_s, ref_s, atol=state_atol), f"2q state mismatch: {fast_s} vs {ref_s}"
        fast_p = np.asarray(probability(fast_s, wires=[0, 1], n_qubits=2), dtype=float)
        ref_p = np.asarray(qnode_probs(thetas), dtype=float)
        assert np.allclose(fast_p, ref_p, atol=state_atol), f"2q probs mismatch: {fast_p} vs {ref_p}"

        # analytic check: fast-sim finite-diff vs QNode qml.grad (not finite-diff both sides)
        eps = 1e-6
        tp = thetas.copy()
        tm = thetas.copy()
        tp[0] += eps
        tm[0] -= eps
        fast_grad = (_fast_expval_z0_2q(tp) - _fast_expval_z0_2q(tm)) / (2 * eps)
        import pennylane.numpy as pnp

        thetas_pnp = pnp.array(thetas, requires_grad=True)
        ref_grad = float(qml.grad(qnode_expval)(thetas_pnp)[0])
        assert np.allclose(fast_grad, ref_grad, atol=grad_atol), f"grad mismatch (fast finite-diff vs analytic qml.grad): {fast_grad} vs {ref_grad}"
    print(f"PASS sim_equivalence_probe state_atol={state_atol:g} grad_atol={grad_atol:g}")


# --- T4 AUDIT failing-first guards (RED: each fails on buggy code, fix later) ---

def test_audit_1_mask_never_to_quantum():
    """AUDIT-1: padding mask applied on classical path only, never forwarded to quantum path."""
    import numpy as np
    from hybrid.attention.quantum_attention import QuantumMultiHeadAttention
    np.random.seed(0)
    attn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=2,
                                     quantum_qubits=6, dropout=0.0, n_layers=1,
                                     max_quantum_seq=16)
    attn.eval()
    x = np.random.randn(1, 4, 8)
    mask_all = np.ones((1, 1, 4, 4), dtype=bool)
    mask_some = np.ones((1, 1, 4, 4), dtype=bool)
    mask_some[..., -2:] = False
    out_all = np.asarray(attn.forward(x, mask_all))
    out_some = np.asarray(attn.forward(x, mask_some))
    assert not np.allclose(out_all, out_some), \
        "AUDIT-1 BUG: attention_mask never reaches quantum path (outputs identical)"


def test_audit_2_objective_vs_metric_mismatch():
    """AUDIT-2: all-position loss (trainer) vs last-position acc (runner) + mask never passed."""
    from pathlib import Path
    trainer_src = Path("classical/optimizers/trainer.py").read_text()
    runner_src = Path("benchmarks/runner.py").read_text()
    trainer_last = "[:, -1" in trainer_src
    runner_last = "[:, -1" in runner_src
    assert trainer_last == runner_last, \
        f"AUDIT-2 BUG: train/eval position mismatch trainer_last={trainer_last} runner_last={runner_last}"


def test_audit_3_overlap_1000_gt_256():
    """AUDIT-3: 1000 draws from 256-space + contiguous slices leak train->test."""
    from benchmarks.tasks.benchmark_k_parity import generate_k_parity
    Xtr, _, Xte, _ = generate_k_parity(n_bits=8, k=3, n_train=800, n_test=200, seed=42)
    tr = set(map(tuple, np.asarray(Xtr).tolist()))
    te = set(map(tuple, np.asarray(Xte).tolist()))
    assert len(tr) == 800 and len(te) == 200, \
        f"AUDIT-3 BUG: duplicate rows sampled tr_unique={len(tr)} te_unique={len(te)}"
    assert tr.isdisjoint(te), "AUDIT-3 BUG: train/test row overlap (contiguous slice of one draw)"


def test_audit_4_router_misclassified():
    """AUDIT-4: MoE router/gate Linear counted as classical, skewing attribution."""
    from hybrid.interfaces.model import HybridQuantumLLM
    import numpy as np
    np.random.seed(0)
    m = HybridQuantumLLM(vocab_size=8, d_model=8, n_layers=1, n_heads=2,
                         quantum_heads_per_layer=1, d_ff=16, max_seq_length=8,
                         dropout=0.0,
                         quantum_config={"use_moe": True, "moe_qubit_configs": [6, 6],
                                         "moe_temperature": 1.0,
                                         "use_quantum_activation": False})
    names = [n for n, _ in m.named_parameters()]
    router = [n for n in names if "router" in n or "gate" in n]
    assert router, "no router/gate params found"
    bad = [n for n in router if not ("quantum" in n or n.endswith(".params"))]
    assert not bad, \
        f"AUDIT-4 BUG: router {len(bad)} params counted classical e.g. {bad[:2]}"


def test_audit_11_dense_vs_sparse():
    """AUDIT-11: dense train routing vs sparse eval routing mismatch."""
    import numpy as np
    from quantum.moe import AdaptiveQuantumHead
    np.random.seed(1)
    head = AdaptiveQuantumHead(d_model=4, head_dim=4, qubit_configs=[6, 6],
                               n_layers=1, temperature=1.0)
    q = np.random.randn(1, 2, 4)
    k = np.random.randn(1, 2, 4)
    v = np.random.randn(1, 2, 4)
    head.train(True)
    out_train, _ = head(q, k, v)
    head.eval()
    out_eval, _ = head(q, k, v)
    assert np.allclose(np.asarray(out_train), np.asarray(out_eval), atol=1e-6), \
        "AUDIT-11 BUG: dense-train vs sparse-eval MoE outputs diverge"


def test_audit_15_remainder_fallback():
    """AUDIT-15: seq remainder silently falls back to classical path."""
    import numpy as np
    from hybrid.attention.quantum_attention import QuantumMultiHeadAttention
    np.random.seed(0)
    attn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=1,
                                     quantum_qubits=6, dropout=0.0, n_layers=1,
                                     max_quantum_seq=2)
    attn.eval()
    calls = {"n": 0}
    orig = attn.quantum_circuits[0]
    orig_fwd = orig.forward
    def counting(*a, **k):
        calls["n"] += 1
        return orig_fwd(*a, **k)
    orig.forward = counting
    x = np.random.randn(1, 4, 8)
    out = np.asarray(attn.forward(x))
    assert out.shape == (1, 4, 8), f"shape {out.shape}"
    assert calls["n"] == 4, \
        f"AUDIT-15 BUG: remainder fallback to classical (circuit calls={calls['n']} expected 4)"


def test_audit_14_threshold():
    """AUDIT-14 (tighten): small-circuit grad flow must exceed 1e-3, not 1e-10.

    Tightens tests/unit/test_quantum_gradient_flow.py:30,42,54,75
    (``>1e-10`` too loose to catch vanishing flow) to ``>1e-3`` on a
    small seeded circuit (QuantumAttentionCircuit 6q/1-layer).

    AUDIT-12 (clarify, prose-vs-code, no runtime assert here):
    quantum/circuits/core.py:212-227 prose vs :289-306 actual
    (+ :331-338 per research/AUDIT.md:38) diverge; claims must cite code.

    TBD (no new mechanism established here, gaps only):
    - 5: cache key excludes params; cited quantum/optimizations.py:34-38
      is stale (file lives at hybrid/interfaces/optimizations.py:34-38);
      eval-gate/embedding/invalidate dead paths unverified -> TBD.
    - 6,7,8,9,10: no file:line in verified reports -> TBD.
    - 13: quantum/simulator/__init__.py:30-92 vs qnode :230-238,
      active path unconfirmed -> TBD (unknown).
    """
    import autograd
    import autograd.numpy as anp
    import numpy as np
    from quantum.circuits.core import QuantumAttentionCircuit
    np.random.seed(0)
    circuit = QuantumAttentionCircuit(n_qubits=6, n_layers=1)
    q = np.random.randn(4)
    k = np.random.randn(4)
    v = np.random.randn(4)

    def loss(params):
        circuit.params = params
        return anp.sum(circuit(q, k, v))

    g = np.asarray(autograd.grad(loss)(circuit.params.copy()), dtype=float)
    grad_norm = float(np.linalg.norm(g))
    print(f"AUDIT-14 grad_norm={grad_norm:g} bound=1e-3 (was 1e-10)")
    assert grad_norm > 1e-3, \
        f"AUDIT-14 BUG: vanishing gradient flow grad_norm={grad_norm:g} <= 1e-3"
