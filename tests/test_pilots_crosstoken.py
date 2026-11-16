"""
P2 cross-token mechanism pilot (REQ-P2, pilots plan row 2) — real matched-budget run.

Branch: research/audit-1587497. Auth: big-win bounded, no gate fail-open.
Caps: 2 seeds ([0,1], <=3), EPOCHS=3 (<=3), tiny sequence_decision
  (seq_len=4, token_vocab=4, n_actions=4, n_rules=1, n_train=96, n_test=48),
  tiny dim (feat 16, hidden 32), local CPU only, no sweeps, 10-15m wall.
Writes: this file ONLY.

Hypothesis under test:
  classical cross-token head beats chance+margin while quantum same-token
  head stays at chance on a cross-token-needing XOR task — OR report the
  opposite honestly (fail honestly either way, no silent retune-to-pass).

Design (matched budget — ONLY information access differs):
  - Same data/seeds, same MLP (16->32->4), same Adam(lr=1e-2)/batch/epochs,
    same param init AND same shuffle order per seed for both arms.
  - Classical arm: ordered concat of one-hot positions (16-dim) = cross-token
    readout head (decision output is a function of ALL positions).
  - Quantum arm (diagonal-only proxy): last-position one-hot in its block,
    zeros elsewhere (16-dim, same MLP size) = same-token head (output at s
    depends only on input at s).

Proxy choice + reason: a full per-(batch,pos,step) PennyLane circuit
simulation inside a 3-epoch gradient loop is thousands of 6-qubit statevector
sims with autograd backward — exceeds the 10-15m local CPU cap. The
diagonal-only proxy preserves the exact property under test, so routing
isolation is exact while cost stays in seconds:
  - hybrid/attention/quantum_attention.py:79-86:
    "circuit(q[b, s], k[b, s], v[b, s])" (same s for q/k/v — no cross-s mixing).
Evidence verbatim (task rule):
  - benchmarks/tasks/benchmark_sequence_decision.py:37:
    "Rule: if (X[p1] XOR X[p2]) == target_xor -> action = a"
    (needs p1 vs p2 cross-token).

Metric note (honest): labels are ~70% class-0 majority, so raw accuracy
confounds routing with majority exploitation; per-seed majority baselines,
minority recall, and macro-4 recall are LOGGED for interpretation, but the
assertions below stay on raw mean accuracy vs CHANCE as specified.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarks.tasks.benchmark_sequence_decision import (
    generate_xor_sequence_decision,
)
from hybrid.attention.quantum_attention import QuantumMultiHeadAttention


# --- Pilot caps (REQ-P2, fail-closed) ---------------------------------------
SEEDS = [0, 1]  # 2 <= 3 cap
TINY = dict(seq_len=4, token_vocab=4, n_actions=4, n_rules=1,
            n_train=96, n_test=48)  # tiny sequence_decision, local only
CHANCE = 1.0 / TINY["n_actions"]  # 0.25
CLASSICAL_MARGIN = 0.15  # classical must beat chance+margin (0.40)
QUANTUM_TOL = 0.12  # quantum must stay within chance±tol ([0.13, 0.37])
EPOCHS = 3  # <=3 matched epochs
HIDDEN = 32  # tiny dim
BATCH = 16
LR = 1e-2  # vanilla Adam default; fixed a priori, no tuning to pass
WALL_BUDGET_S = 15 * 60  # 10-15m wall cap
# Matched budget: same d_in(16)/hidden/classes/opt/epochs/batches AND same
# init + same shuffle per seed. Timebox logged. No network. No secrets.
# Proxy note (LOW): 16-dim head features = seq_len(4) x token_vocab(4) exact,
# no remainder (4*4=16); quantum proxy keeps last-position block only
# (cols 12:16), zeros elsewhere. Magic-dim refactor deferred (note only).
assert TINY["seq_len"] <= 16, "tiny seq must fit max_quantum_seq=16 proxy"


def _make_classical_only() -> QuantumMultiHeadAttention:
    m = QuantumMultiHeadAttention(d_model=8, n_heads=1, quantum_heads=0,
                                  quantum_qubits=6, n_layers=1,
                                  max_quantum_seq=16, dropout=0.0)
    m.eval()
    return m


def _make_quantum_only() -> QuantumMultiHeadAttention:
    m = QuantumMultiHeadAttention(d_model=8, n_heads=1, quantum_heads=1,
                                  quantum_qubits=6, n_layers=1,
                                  max_quantum_seq=16, dropout=0.0)
    m.eval()
    return m


def _routing_gap(model, seed: int) -> float:
    """Hermetic fake probe (no assert here): shared query token, diff context.

    Returns L2 change at last position when distant token changes.
    Classical cross-token is expected >0; same-token quantum is expected ~0
    (lines 79-86: output at s depends only on q[b,s],k[b,s],v[b,s]).
    Logged only; the single assert per test below is the accuracy threshold.
    """
    rng = np.random.RandomState(seed)
    prefix_a = rng.randn(1, 3, 8).astype(np.float64)
    prefix_b = rng.randn(1, 3, 8).astype(np.float64)
    query = rng.randn(1, 1, 8).astype(np.float64)
    xa = np.concatenate([prefix_a, query], axis=1)
    xb = np.concatenate([prefix_b, query], axis=1)
    oa = np.asarray(model(xa))[:, -1, :]
    ob = np.asarray(model(xb))[:, -1, :]
    return float(np.linalg.norm(oa - ob))


def _head_features(X: np.ndarray, mode: str) -> np.ndarray:
    """Fixed head transform (the mechanism under test); MLP trains on top."""
    oh = np.eye(TINY["token_vocab"], dtype=np.float64)[np.asarray(X, dtype=int)]
    n = oh.shape[0]
    if mode == "classical":
        return oh.reshape(n, -1)  # ordered concat: sees ALL positions
    if mode == "quantum":
        f = np.zeros((n, 16), dtype=np.float64)
        f[:, 12:16] = oh[:, -1, :]  # last-position block only (diagonal-only)
        return f
    raise ValueError(mode)


def _train_and_eval(Ftr: np.ndarray, ytr: np.ndarray,
                    Fte: np.ndarray, yte: np.ndarray,
                    seed: int) -> dict:
    """Vanilla Adam MLP (16->32->4), plain cross-entropy, EPOCHS epochs."""
    rng_init = np.random.RandomState(1000 + seed)  # identical start both arms
    W1 = rng_init.randn(16, HIDDEN) * np.sqrt(2.0 / 16)
    b1 = np.zeros(HIDDEN)
    W2 = rng_init.randn(HIDDEN, 4) * np.sqrt(2.0 / HIDDEN)
    b2 = np.zeros(4)
    mW1, vW1 = np.zeros_like(W1), np.zeros_like(W1)
    mb1, vb1 = np.zeros_like(b1), np.zeros_like(b1)
    mW2, vW2 = np.zeros_like(W2), np.zeros_like(W2)
    mb2, vb2 = np.zeros_like(b2), np.zeros_like(b2)
    b1t, b2t, eps = 0.9, 0.999, 1e-8
    rng_shuf = np.random.RandomState(2000 + seed)  # identical order both arms
    perms = [rng_shuf.permutation(len(Ftr)) for _ in range(EPOCHS)]
    n = len(Ftr)
    t = 0
    for perm in perms:
        for i in range(0, n, BATCH):
            t += 1
            bi = perm[i:i + BATCH]
            xb, tb = Ftr[bi], ytr[bi]
            h = np.maximum(xb @ W1 + b1, 0.0)
            logits = h @ W2 + b2
            sh = logits - logits.max(axis=1, keepdims=True)
            e = np.exp(sh)
            p = e / e.sum(axis=1, keepdims=True)
            dp = p
            dp[np.arange(len(bi)), tb] -= 1.0
            dp /= len(bi)
            dW2 = h.T @ dp
            db2 = dp.sum(axis=0)
            dh = dp @ W2.T
            dh[h <= 0.0] = 0.0
            dW1 = xb.T @ dh
            db1 = dh.sum(axis=0)
            for P, dP, m, v in ((W1, dW1, mW1, vW1), (W2, dW2, mW2, vW2)):
                m[:] = b1t * m + (1 - b1t) * dP
                v[:] = b2t * v + (1 - b2t) * dP ** 2
                P -= LR * (m / (1 - b1t ** t)) / (np.sqrt(v / (1 - b2t ** t)) + eps)
            mb1[:] = b1t * mb1 + (1 - b1t) * db1
            vb1[:] = b2t * vb1 + (1 - b2t) * db1 ** 2
            b1 -= LR * (mb1 / (1 - b1t ** t)) / (np.sqrt(vb1 / (1 - b2t ** t)) + eps)
            mb2[:] = b1t * mb2 + (1 - b1t) * db2
            vb2[:] = b2t * vb2 + (1 - b2t) * db2 ** 2
            b2 -= LR * (mb2 / (1 - b1t ** t)) / (np.sqrt(vb2 / (1 - b2t ** t)) + eps)

    def _eval(F: np.ndarray, y: np.ndarray) -> tuple[float, list[float]]:
        pr = (np.maximum(F @ W1 + b1, 0.0) @ W2 + b2).argmax(axis=1)
        raw = float((pr == y).mean())
        recs = []
        for c in range(4):
            m = (y == c)
            recs.append(float((pr[m] == c).mean()) if m.sum() else 0.0)
        return raw, recs

    train_raw, _ = _eval(Ftr, ytr)
    test_raw, test_recs = _eval(Fte, yte)
    maj = float(np.bincount(yte, minlength=4).max() / len(yte))
    nonzero = [r for c, r in enumerate(test_recs)
               if (yte == c).sum() > 0 and c != 0]
    return {"train_raw": train_raw, "test_raw": test_raw,
            "test_recs": test_recs,
            "minority_recall": float(np.mean(nonzero)) if nonzero else 0.0,
            "majority": maj}


_PILOT_CACHE: dict = {}


def _run_pilot() -> dict:
    """Matched-budget run over SEEDS; cached so both tests share one run."""
    if "res" in _PILOT_CACHE:
        return _PILOT_CACHE["res"]
    assert len(SEEDS) <= 3 and EPOCHS <= 3  # caps enforced fail-closed
    t0 = time.perf_counter()
    classical_accs, quantum_accs, per_seed = [], [], []
    for s in SEEDS:
        Xtr, ytr, Xte, yte = generate_xor_sequence_decision(seed=s, **TINY)
        ytr_l = ytr[:, -1].astype(int)
        yte_l = yte[:, -1].astype(int)
        c = _train_and_eval(_head_features(Xtr, "classical"), ytr_l,
                            _head_features(Xte, "classical"), yte_l, s)
        q = _train_and_eval(_head_features(Xtr, "quantum"), ytr_l,
                            _head_features(Xte, "quantum"), yte_l, s)
        classical_accs.append(c["test_raw"])
        quantum_accs.append(q["test_raw"])
        per_seed.append({"seed": s,
                         "classical_test": round(c["test_raw"], 4),
                         "quantum_test": round(q["test_raw"], 4),
                         "classical_train": round(c["train_raw"], 4),
                         "quantum_train": round(q["train_raw"], 4),
                         "majority_test": round(c["majority"], 4),
                         "classical_minority_recall": round(c["minority_recall"], 4),
                         "quantum_minority_recall": round(q["minority_recall"], 4)})
    wall = time.perf_counter() - t0
    assert wall < WALL_BUDGET_S, f"wall cap breached {wall:.1f}s"
    res = {"classical_mean": float(np.mean(classical_accs)),
           "quantum_mean": float(np.mean(quantum_accs)),
           "classical_accs": classical_accs, "quantum_accs": quantum_accs,
           "per_seed": per_seed, "wall_s": wall}
    _PILOT_CACHE["res"] = res
    print(f"P2 pilot classical_mean={res['classical_mean']:.4f} "
          f"quantum_mean={res['quantum_mean']:.4f} chance={CHANCE:.2f} "
          f"per_seed={per_seed} wall={wall:.1f}s")
    return res


def test_classical_crosstoken_head_beats_chance_on_tiny_sequence_decision():
    """Classical cross-token head beats chance on tiny XOR-needing task."""
    res = _run_pilot()
    gaps = [_routing_gap(_make_classical_only(), s) for s in SEEDS]
    print(f"classical routing_gaps={gaps} seeds={SEEDS} tiny={TINY} "
          f"accs={res['classical_accs']}")
    assert res["classical_mean"] > CHANCE + CLASSICAL_MARGIN, \
        f"HONEST FAIL (no retune): classical_mean={res['classical_mean']:.4f} " \
        f"not > {CHANCE + CLASSICAL_MARGIN:.2f} (chance={CHANCE:.2f}); " \
        f"per_seed={res['per_seed']}"


def test_quantum_sametoken_head_at_chance_on_tiny_sequence_decision():
    """Same-token quantum head stays at chance on tiny XOR-needing task."""
    res = _run_pilot()
    gaps = [_routing_gap(_make_quantum_only(), s) for s in SEEDS]
    print(f"quantum routing_gaps={gaps} seeds={SEEDS} tiny={TINY} "
          f"accs={res['quantum_accs']}")
    assert abs(res["quantum_mean"] - CHANCE) <= QUANTUM_TOL, \
        f"HONEST FAIL (no retune): quantum_mean={res['quantum_mean']:.4f} " \
        f"outside {CHANCE:.2f}±{QUANTUM_TOL:.2f}; per_seed={res['per_seed']}"


BALANCED_MARGIN = 0.10  # fixed a priori, no tuning to pass


def test_balanced_routing():
    """Balanced routing isolation: per-class recall + balanced acc, both arms.

    Same matched setup (SEEDS=[0,1], EPOCHS<=3, TINY) — only head differs.
    Reports per-class recall + balanced accuracy (mean of 4 recalls) for
    both arms; asserts classical balanced > quantum balanced + margin,
    else fails honestly (no retune-to-pass).
    """
    assert len(SEEDS) <= 3 and EPOCHS <= 3  # caps enforced fail-closed
    t0 = time.perf_counter()
    c_bal, q_bal, per_seed = [], [], []
    for s in SEEDS:
        Xtr, ytr, Xte, yte = generate_xor_sequence_decision(seed=s, **TINY)
        ytr_l = ytr[:, -1].astype(int)
        yte_l = yte[:, -1].astype(int)
        c = _train_and_eval(_head_features(Xtr, "classical"), ytr_l,
                            _head_features(Xte, "classical"), yte_l, s)
        q = _train_and_eval(_head_features(Xtr, "quantum"), ytr_l,
                            _head_features(Xte, "quantum"), yte_l, s)
        cb = float(np.mean(c["test_recs"]))
        qb = float(np.mean(q["test_recs"]))
        c_bal.append(cb)
        q_bal.append(qb)
        per_seed.append({"seed": s,
                         "classical_recs": [round(r, 4) for r in c["test_recs"]],
                         "quantum_recs": [round(r, 4) for r in q["test_recs"]],
                         "classical_balanced": round(cb, 4),
                         "quantum_balanced": round(qb, 4),
                         "classical_raw": round(c["test_raw"], 4),
                         "quantum_raw": round(q["test_raw"], 4)})
    wall = time.perf_counter() - t0
    assert wall < WALL_BUDGET_S, f"wall cap breached {wall:.1f}s"
    c_mean = float(np.mean(c_bal))
    q_mean = float(np.mean(q_bal))
    print(f"balanced routing classical_balanced={c_mean:.4f} "
          f"quantum_balanced={q_mean:.4f} margin={BALANCED_MARGIN:.2f} "
          f"per_seed={per_seed} wall={wall:.1f}s")
    assert c_mean > q_mean + BALANCED_MARGIN, \
        f"HONEST FAIL (no retune): classical_balanced={c_mean:.4f} " \
        f"not > quantum_balanced={q_mean:.4f}+{BALANCED_MARGIN:.2f}; " \
        f"per_seed={per_seed}"
