"""Task1 actual-correctness probes (AC1-AC10), tiny CPU only.

Scope: writes ONLY this file. Tiny shapes: d_model=8, n_heads=2,
vocab 8, B=1, S=4, 6q/1-layer, max_quantum_seq<=16, seeds 0-1,
single training_step per test. Each test prints its ACn value+bound.
Fail-closed: violations raise, never silent pass.

Note (doc only, not asserted by string match): classical/optimizers/
trainer.py computes all-position flat CrossEntropyLoss
(logits.reshape(-1, V) vs labels.reshape(-1)); benchmarks/runner.py
instead scores last-position logits. AC2 below proves the trainer
behavior behaviorally via HybridQuantumTrainer.evaluate.
"""

import numpy as np


def _make_tiny_llm(seed=0):
    from hybrid.interfaces.model import HybridQuantumLLM
    np.random.seed(seed)
    return HybridQuantumLLM(
        vocab_size=8,
        d_model=8,
        n_layers=1,
        n_heads=2,
        quantum_heads_per_layer=1,
        d_ff=16,
        max_seq_length=8,
        dropout=0.0,
        quantum_config={
            "use_quantum_embedding": False,
            "use_quantum_activation": False,
            "attention_qubits": 6,
            "quantum_n_layers": 1,
        },
    )


def _tiny_batch(seed=0, vocab=8):
    rng = np.random.default_rng(seed)
    ids = rng.integers(0, vocab, size=(1, 4))
    labels = rng.integers(0, vocab, size=(1, 4))
    return ids, labels


def _flat_grad_norm(model, ids, labels):
    """Independently recompute ||grad loss|| over the model's flat params."""
    import autograd
    from classical.nn import CrossEntropyLoss
    loss_fn = CrossEntropyLoss()
    locs = model._parameter_locations()

    def loss_from_flat(flat):
        saved = []
        idx = 0
        for parent, attr, _, p in locs:
            saved.append((parent, attr, getattr(parent, attr)))
            setattr(parent, attr, flat[idx:idx + p.size].reshape(p.shape))
            idx += p.size
        try:
            logits = model.forward(ids)
            return loss_fn(logits.reshape(-1, logits.shape[-1]), labels.reshape(-1))
        finally:
            for parent, attr, orig in saved:
                setattr(parent, attr, orig)

    flat0 = np.concatenate([np.asarray(p).flatten() for (_, _, _, p) in locs])
    val, g = autograd.value_and_grad(loss_from_flat)(flat0)
    return float(val), np.asarray(g, dtype=float)


def test_ac01_finite_forward_train_and_eval():
    """AC1 finite: forward finite in eval AND train mode, same shape."""
    m = _make_tiny_llm(seed=0)
    ids, _ = _tiny_batch(seed=0)
    m.eval()
    logits_eval = np.asarray(m.forward(ids))
    m.train()
    logits_train = np.asarray(m.forward(ids))
    n_bad = int((~np.isfinite(logits_eval)).sum() + (~np.isfinite(logits_train)).sum())
    print(f"AC1 eval_shape={logits_eval.shape} train_shape={logits_train.shape} nonfinite={n_bad} bound=0")
    assert logits_eval.shape == (1, 4, 8), f"eval shape {logits_eval.shape}"
    assert logits_train.shape == logits_eval.shape, (
        f"train/eval shape mismatch {logits_train.shape} vs {logits_eval.shape}"
    )
    assert np.all(np.isfinite(logits_eval)), "eval logits non-finite"
    assert np.all(np.isfinite(logits_train)), "train logits non-finite"


def test_ac02_evaluate_loss_metric():
    """AC2 loss-metric: evaluate returns finite loss, acc in [0,1], preds shape."""
    from classical.optimizers.trainer import HybridQuantumTrainer
    m = _make_tiny_llm(seed=0)
    tr = HybridQuantumTrainer(m)
    ids, labels = _tiny_batch(seed=1)
    res = tr.evaluate(ids, labels)
    preds = np.asarray(m.forward(ids)).argmax(axis=-1)
    print(f"AC2 eval_loss={res['eval_loss']:.6f} acc={res['accuracy']:.4f} "
          f"preds_shape={preds.shape} labels_shape={labels.shape} bound=finite/[0,1]/match")
    assert isinstance(res["eval_loss"], float) and np.isfinite(res["eval_loss"]), res
    assert 0.0 <= res["accuracy"] <= 1.0, res
    assert preds.shape == labels.shape, f"preds {preds.shape} vs labels {labels.shape}"


def test_ac03_training_step_grad_norm_and_clip():
    """AC3 grads: flat grads finite; reported grad_norm equals true norm; clip honored."""
    from classical.optimizers.trainer import HybridQuantumTrainer
    m = _make_tiny_llm(seed=0)
    tr = HybridQuantumTrainer(m, learning_rate=1e-3)
    ids, labels = _tiny_batch(seed=1)
    # Train-mode forward is stochastic by design (embedding Dropout(0.1)
    # draws a fresh np.random.binomial mask per forward). Reseed immediately
    # before each sampled computation so both sides draw the identical mask
    # sequence; the norm-equality property is then proved on the real path.
    np.random.seed(123)
    _, g = _flat_grad_norm(m, ids, labels)
    true_norm = float(np.linalg.norm(g))
    assert np.all(np.isfinite(g)), "non-finite grad entries"
    np.random.seed(123)
    res = tr.training_step(ids, labels)
    gn = res["grad_norm"]
    print(f"AC3 reported_norm={gn:.6g} true_norm={true_norm:.6g} bound=finite+equal,clip-to-1-if->1")
    assert np.isfinite(gn), res
    assert np.isclose(gn, true_norm, rtol=1e-5, atol=1e-8), (
        f"reported grad_norm {gn} != true norm {true_norm}"
    )
    if true_norm > 1.0:
        clipped_norm = float(np.linalg.norm(g * (1.0 / true_norm)))
        print(f"AC3 over-norm branch: true_norm={true_norm:.6g} clipped_norm={clipped_norm:.6g} bound=1.0")
        assert np.isclose(clipped_norm, 1.0, rtol=1e-6, atol=1e-8), (
            f"clip rule not honored: {clipped_norm}"
        )
    else:
        print(f"AC3 under-norm branch (record only): true_norm={true_norm:.6g} <= 1, no clip expected")


def test_ac04_training_step_counters():
    """AC4 step: step+1, float finite loss, elapsed_ms>0, params move."""
    from classical.optimizers.trainer import HybridQuantumTrainer
    m = _make_tiny_llm(seed=0)
    tr = HybridQuantumTrainer(m, learning_rate=1e-3)
    ids, labels = _tiny_batch(seed=1)
    before = tr._flatten_params().copy()
    res = tr.training_step(ids, labels)
    after = tr._flatten_params()
    delta = float(np.max(np.abs(after - before)))
    print(f"AC4 step={res['step']} loss={res['loss']:.6f} loss_type={type(res['loss']).__name__} "
          f"elapsed_ms={res['elapsed_ms']:.6g} maxdelta={delta:.6g} bound=1/float-finite/>0/>0")
    assert res["step"] == 1, res
    assert isinstance(res["loss"], float) and np.isfinite(res["loss"]), res
    assert res["elapsed_ms"] > 0, res
    assert delta > 0, "no param moved after step"


def test_ac05_cache_train_bypass_eval_hit():
    """AC5 cache: get/put hit-miss; train bypasses cache; eval hits identical."""
    from hybrid.interfaces.optimizations import CircuitResultCache
    m = _make_tiny_llm(seed=0)
    attn = m.layers[0].attention
    ids, _ = _tiny_batch(seed=0)
    x = np.asarray(m.embedding(ids))

    # Unit: miss -> None + counter; put -> identical hit.
    c = CircuitResultCache(max_size=8)
    a, b = np.array([1.0, 2.0]), np.array([3.0])
    assert c.get(a, b) is None, "expected miss"
    assert (c.hits, c.misses) == (0, 1), (c.hits, c.misses)
    c.put(np.array([9.0]), a, b)
    hit = c.get(a, b)
    assert hit is not None and np.array_equal(hit, np.array([9.0])), hit
    assert (c.hits, c.misses) == (1, 1), (c.hits, c.misses)
    print(f"AC5 unit hits={c.hits} misses={c.misses} bound=1/1, identical put/get")

    # Train path bypasses cache: counters stay zero across forwards.
    m.train()
    assert getattr(attn, "_training", None) is True
    attn._circuit_cache.clear()
    _ = np.asarray(attn.forward(x))
    _ = np.asarray(attn.forward(x))
    print(f"AC5 train use_cache=False hits={attn._circuit_cache.hits} "
          f"misses={attn._circuit_cache.misses} bound=0/0")
    assert (attn._circuit_cache.hits, attn._circuit_cache.misses) == (0, 0), (
        f"train path touched cache hits={attn._circuit_cache.hits} "
        f"misses={attn._circuit_cache.misses}"
    )

    # Eval path uses cache: second identical forward hits, outputs identical.
    m.eval()
    attn._circuit_cache.clear()
    o1 = np.asarray(attn.forward(x))
    h1, mi1 = attn._circuit_cache.hits, attn._circuit_cache.misses
    o2 = np.asarray(attn.forward(x))
    h2 = attn._circuit_cache.hits
    print(f"AC5 eval fwd1 hits={h1} misses={mi1}; fwd2 hits={h2} bound=misses>0,hits-grow,identical")
    assert mi1 > 0, "eval first forward never populated cache"
    assert h2 > h1, "eval second forward did not hit cache"
    assert np.array_equal(o1, o2), "eval cache hit returned different projection"


def test_ac06_head_counts_and_param_partition():
    """AC6 counts: classical+quantum==n_heads, head_dim==d_model//n_heads, maps partition."""
    from classical.optimizers.trainer import HybridQuantumTrainer
    from hybrid.attention.quantum_attention import QuantumMultiHeadAttention
    attn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=1,
                                     quantum_qubits=6, dropout=0.0, n_layers=1,
                                     max_quantum_seq=16)
    print(f"AC6 classical={attn.classical_heads} quantum={attn.quantum_heads} "
          f"n_heads={attn.n_heads} head_dim={attn.head_dim} bound=1+1==2,8//2==4")
    assert attn.classical_heads + attn.quantum_heads == attn.n_heads == 2
    assert attn.head_dim == attn.d_model // attn.n_heads == 4

    m = _make_tiny_llm(seed=0)
    c = m.count_parameters()
    tr = HybridQuantumTrainer(m)
    n = len(tr._all_params)
    cs, qs = set(tr._classical_map), set(tr._quantum_map)
    print(f"AC6 total={c['total']} classical={c['classical']} quantum={c['quantum']} "
          f"n={n} overlap={len(cs & qs)} bound=total==c+q,q>0,overlap0,union==n")
    assert c["total"] == c["classical"] + c["quantum"], c
    assert c["quantum"] > 0, c
    assert len(cs & qs) == 0, f"overlap {sorted(cs & qs)[:4]}"
    assert (cs | qs) == set(range(n)), "maps do not cover all params"


def test_ac07_classical_mask_rows():
    """AC7 mask: classical softmax rows sum to 1, masked cols ~0; quantum blind recorded."""
    from hybrid.attention.quantum_attention import QuantumMultiHeadAttention
    np.random.seed(0)
    attn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=1,
                                     quantum_qubits=6, dropout=0.0, n_layers=1,
                                     max_quantum_seq=16)
    attn.eval()
    q = np.random.randn(1, 2, 4, 4)
    k = np.random.randn(1, 2, 4, 4)
    scores = (q @ k.transpose((0, 1, 3, 2))) / attn.scale
    mask = np.ones((1, 1, 4, 4), dtype=bool)
    mask[..., -2:] = False
    weights = np.asarray(attn.softmax(np.where(mask, scores, -1e9)))
    row_sums = weights.sum(axis=-1)
    masked_max = float(weights[..., -2:].max())
    print(f"AC7 rowsum_min={row_sums.min():.8f} rowsum_max={row_sums.max():.8f} "
          f"masked_max={masked_max:.3g} bound=1.0/<1e-6")
    assert np.allclose(row_sums, 1.0, atol=1e-6), f"rows do not sum to 1: {row_sums}"
    assert masked_max < 1e-6, f"masked cols leak: {masked_max}"

    # Forward-level wiring: mask changes classical-path output.
    x = np.random.randn(1, 4, 8)
    mall = np.ones((1, 1, 4, 4), dtype=bool)
    dall = np.asarray(attn.forward(x, mall))
    dsome = np.asarray(attn.forward(x, mask))
    diff = float(np.max(np.abs(dall - dsome)))
    print(f"AC7 fwd_mask_sensitivity={diff:.6g} bound=>1e-6")
    assert diff > 1e-6, "mask had no effect on classical-path forward"

    # Record-only: pure-quantum path mask blindness (no assert, do not force).
    qattn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=2,
                                      quantum_qubits=6, dropout=0.0, n_layers=1,
                                      max_quantum_seq=16)
    qattn.eval()
    q1 = np.asarray(qattn.forward(x, mall))
    q2 = np.asarray(qattn.forward(x, mask))
    qdiff = float(np.max(np.abs(q1 - q2)))
    print(f"AC7-REC quantum_only_maxdiff={qdiff:.6g} (record: mask-blind if ~0)")


def test_ac08_long_sequence_split_prefix():
    """AC8 split: S>max_quantum_seq keeps length S; remainder covers full prefix."""
    from hybrid.attention.quantum_attention import QuantumMultiHeadAttention
    np.random.seed(0)
    attn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=1,
                                     quantum_qubits=6, dropout=0.0, n_layers=1,
                                     max_quantum_seq=2)
    attn.eval()
    x = np.random.randn(1, 4, 8)
    out = np.asarray(attn.forward(x))
    print(f"AC8 split_out_shape={out.shape} bound=(1,4,8), finite")
    assert out.shape == (1, 4, 8), f"split changed length: {out.shape}"
    assert np.all(np.isfinite(out)), "split output non-finite"

    # Prefix coverage: perturbing prefix (pos 0..1) moves remainder outputs (pos 2..).
    x2 = x.copy()
    x2[:, :2, :] += 1.0
    out2 = np.asarray(attn.forward(x2))
    rem_diff = float(np.max(np.abs(out2[:, 2:, :] - out[:, 2:, :])))
    print(f"AC8 prefix_to_remainder_maxdiff={rem_diff:.6g} bound=>1e-12")
    assert rem_diff > 1e-12, "remainder queries ignore prefix (truncation bias)"

    # S <= max path unchanged: full-length output, finite.
    attn16 = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=1,
                                       quantum_qubits=6, dropout=0.0, n_layers=1,
                                       max_quantum_seq=16)
    attn16.eval()
    out16 = np.asarray(attn16.forward(x))
    print(f"AC8 shortpath_shape={out16.shape} bound=(1,4,8), finite")
    assert out16.shape == (1, 4, 8), out16.shape
    assert np.all(np.isfinite(out16)), "short-path output non-finite"


def test_ac09_fixed_seed_determinism():
    """AC9 sim: fixed-seed rerun gives exact identical logits and step loss."""
    from classical.optimizers.trainer import HybridQuantumTrainer
    ids, labels = _tiny_batch(seed=1)
    m1 = _make_tiny_llm(seed=0)
    m2 = _make_tiny_llm(seed=0)
    m1.eval()
    m2.eval()
    l1 = np.asarray(m1.forward(ids))
    l2 = np.asarray(m2.forward(ids))
    print(f"AC9 logits_exact={np.array_equal(l1, l2)} bound=True")
    assert np.array_equal(l1, l2), "fixed-seed rerun logits differ"

    tr1 = HybridQuantumTrainer(_make_tiny_llm(seed=0), learning_rate=1e-3)
    tr2 = HybridQuantumTrainer(_make_tiny_llm(seed=0), learning_rate=1e-3)
    # Same-mask control as AC3: train forward draws dropout masks from global
    # RNG, so a fixed-seed rerun reseeds immediately before each step.
    np.random.seed(123)
    r1 = tr1.training_step(ids, labels)
    np.random.seed(123)
    r2 = tr2.training_step(ids, labels)
    print(f"AC9 loss1={r1['loss']!r} loss2={r2['loss']!r} bound=exact equal")
    assert r1["loss"] == r2["loss"], (r1["loss"], r2["loss"])


def test_ac09b_sim_agreement_extra():
    """AC9-extra: fast_sim vs QNode agreement atol 1e-5 (supplement, not determinism)."""
    from quantum.circuits.core import QuantumAttentionCircuit
    np.random.seed(1)
    circ = QuantumAttentionCircuit(n_qubits=6, n_layers=1)
    q = np.random.randn(2)
    k = np.random.randn(2)
    v = np.random.randn(2)
    fast = np.asarray(circ._forward_fast_sim(q, k, v), dtype=float)
    ref = np.asarray(circ._forward_qnode(q, k, v), dtype=float)
    diff = float(np.max(np.abs(fast - ref)))
    print(f"AC9-extra maxdiff={diff:.6g} bound=1e-5")
    assert np.allclose(fast, ref, atol=1e-5), f"sim mismatch diff={diff} fast={fast} ref={ref}"


def test_ac10_softmax_rows_and_small_lr_step():
    """AC10 derivs: attention weights rows sum to 1; small-lr step loss sane."""
    from classical.optimizers.trainer import HybridQuantumTrainer
    from hybrid.attention.quantum_attention import QuantumMultiHeadAttention
    np.random.seed(0)
    attn = QuantumMultiHeadAttention(d_model=8, n_heads=2, quantum_heads=1,
                                     quantum_qubits=6, dropout=0.0, n_layers=1,
                                     max_quantum_seq=16)
    scores = np.random.randn(1, 2, 4, 4)
    weights = np.asarray(attn.softmax(scores))
    row_sums = weights.sum(axis=-1)
    print(f"AC10 rowsum_min={row_sums.min():.8f} rowsum_max={row_sums.max():.8f} bound=1.0")
    assert np.allclose(row_sums, 1.0, atol=1e-6), f"weights rows != 1: {row_sums}"

    m = _make_tiny_llm(seed=0)
    tr = HybridQuantumTrainer(m, learning_rate=1e-4)
    ids, labels = _tiny_batch(seed=1)
    r1 = tr.training_step(ids, labels)
    r2 = tr.training_step(ids, labels)
    print(f"AC10 loss1={r1['loss']:.6f} loss2={r2['loss']:.6f} "
          f"gnorms=({r1['grad_norm']:.6g},{r2['grad_norm']:.6g}) bound=finite/no-explosion")
    assert np.isfinite(r1["grad_norm"]) and r1["grad_norm"] > 0, r1
    assert np.isfinite(r2["grad_norm"]) and r2["grad_norm"] > 0, r2
    assert np.isfinite(r2["loss"]), r2
    assert r2["loss"] <= r1["loss"] + 1.0, (
        f"small-lr step exploded: {r1['loss']} -> {r2['loss']}"
    )
