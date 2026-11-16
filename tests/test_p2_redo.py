"""P2-redo bounded checks (RED, failing-first).

Spec: docs/plans/2026-11-17-p2-redo.md rows 1-3 (TBD-exploratory,
  fail-open record-only, no gated claim).
Branch: research/audit-1587497. Auth: user "go ahead" post-Track-C,
  fail-open exploratory.
Caps (enforced fail-closed): <=3 seeds [42,99,137], <=5 epochs, tiny
  balanced 50/50 binary task, local CPU only, no sweeps, 10-15m wall.
Status: RED — written first, never executed here (write-only handoff);
  no green run yet. Implementer run cmd:
    .venv/bin/python -m py_compile tests/test_p2_redo.py && \
    .venv/bin/python -m pytest tests/test_p2_redo.py -q
Allowed writes: this file ONLY (new). Generator NOT edited: balanced
  50/50 is test-local subsampling of the XOR generator output; exact
  balance asserted in-test (fail-closed data guard).

Design (matched budget — ONLY head information differs):
  - Binary task: rule-match (label != 0) vs default (label == 0) on the
    XOR generator (benchmark_sequence_decision.py:37 rule needs p1 vs
    p2 cross-token), test-local 50/50 subsample per split (seeded).
  - Same MLP (16->64->2), same Adam(lr fixed a priori)/batch/epochs,
    same param init AND same shuffle order per seed for both arms.
  - Classical arm: ordered concat of position one-hots (16-dim) =
    cross-token head (output is a function of ALL positions).
  - Quantum arm (same-token proxy): last-position one-hot in its block,
    zeros elsewhere (16-dim, same MLP size) = same-token head.
Proxy reason: a full per-(batch,pos,step) PennyLane circuit simulation
  inside a 5-epoch gradient loop is thousands of 6-qubit statevector
  sims with autograd backward — exceeds the 10-15m local CPU cap. The
  proxy preserves the exact property under test:
  hybrid/attention/quantum_attention.py:79-86
  "circuit(q[b, s], k[b, s], v[b, s])" (same s for q/k/v — no cross-s
  mixing), so routing isolation is exact while cost stays in seconds.
Hermetic: numpy-only MLP, no network/GPU/paid APIs, no live services.
No repo file I/O (in-memory metrics only; /tmp untouched).
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


# --- P2-redo caps (fail-closed) -------------------------------------------
SEEDS = [42, 99, 137]  # <=3 seeds (plan: reuse 42,99,137)
EPOCHS = 5  # <=5 epochs, matched both arms
HIDDEN = 64  # stronger classical: wider hidden than pilot (32)
BATCH = 16
LR = 1e-2  # single config fixed a priori (1 <= 3 allowed), no tuning-to-pass
TINY = dict(seq_len=4, token_vocab=4, n_actions=4, n_rules=1,
            n_train=480, n_test=240)  # tiny sequence_decision, local only
CHANCE = 0.5  # binary balanced task chance
FALSIFIER_MARGIN = 0.10  # fixed a priori, no tuning to pass
MIN_PER_CLASS = 16  # fail-closed floor: subsample needs >=16/side
WALL_BUDGET_S = 15 * 60  # 10-15m wall cap, fail-closed on timeout
# Same-token proxy bound: tiny seq must fit max_quantum_seq=16.
assert TINY["seq_len"] <= 16, "tiny seq must fit max_quantum_seq=16 proxy"


def _balanced_binary_pair(seed: int):
    """XOR generator -> binary match-vs-default, test-local 50/50 subsample.

    Exact class balance asserted here (fail-closed): each split returns
    equal class counts, so raw accuracy == balanced accuracy by
    construction and majority-collapse is directly detectable.
    """
    Xtr, ytr, Xte, yte = generate_xor_sequence_decision(seed=seed, **TINY)
    ytr_b = (ytr[:, -1].astype(int) != 0).astype(int)
    yte_b = (yte[:, -1].astype(int) != 0).astype(int)
    rng = np.random.RandomState(5000 + seed)  # subsample stream, still seeded

    def _sub(X: np.ndarray, y: np.ndarray):
        i0 = np.where(y == 0)[0]
        i1 = np.where(y == 1)[0]
        m = min(len(i0), len(i1))
        assert m >= MIN_PER_CLASS, (
            f"cannot build 50/50 split (seed={seed}): "
            f"minority={m} < {MIN_PER_CLASS}")
        s0 = rng.choice(i0, m, replace=False)
        s1 = rng.choice(i1, m, replace=False)
        idx = np.concatenate([s0, s1])
        rng.shuffle(idx)
        Xb, yb = X[idx], y[idx]
        assert int((yb == 0).sum()) == int((yb == 1).sum()) == m, (
            f"split not 50/50 (seed={seed}): "
            f"n0={(yb == 0).sum()} n1={(yb == 1).sum()}")
        return Xb, yb

    return _sub(Xtr, ytr_b) + _sub(Xte, yte_b)


def _head_features(X: np.ndarray, mode: str) -> np.ndarray:
    """Fixed head transform (the mechanism under test); MLP trains on top."""
    oh = np.eye(TINY["token_vocab"], dtype=np.float64)[np.asarray(X, dtype=int)]
    n = oh.shape[0]
    if mode == "classical":
        return oh.reshape(n, -1)  # ordered concat: sees ALL positions
    if mode == "quantum":
        f = np.zeros((n, 16), dtype=np.float64)
        f[:, 12:16] = oh[:, -1, :]  # last-position block only (same-token)
        return f
    raise ValueError(mode)


def _train_and_eval(Ftr: np.ndarray, ytr: np.ndarray,
                    Fte: np.ndarray, yte: np.ndarray,
                    seed: int) -> dict:
    """Vanilla Adam MLP (16->64->2), plain cross-entropy, EPOCHS epochs."""
    rng_init = np.random.RandomState(1000 + seed)  # identical start both arms
    W1 = rng_init.randn(16, HIDDEN) * np.sqrt(2.0 / 16)
    b1 = np.zeros(HIDDEN)
    W2 = rng_init.randn(HIDDEN, 2) * np.sqrt(2.0 / HIDDEN)
    b2 = np.zeros(2)
    mW1, vW1 = np.zeros_like(W1), np.zeros_like(W1)
    mb1, vb1 = np.zeros_like(b1), np.zeros_like(b1)
    mW2, vW2 = np.zeros_like(W2), np.zeros_like(W2)
    mb2, vb2 = np.zeros_like(b2), np.zeros_like(b2)
    b1t, b2t, eps = 0.9, 0.999, 1e-8
    rng_shuf = np.random.RandomState(2000 + seed)  # identical order both arms
    perms = [rng_shuf.permutation(len(Ftr)) for _ in range(EPOCHS)]
    t = 0
    for perm in perms:
        for i in range(0, len(Ftr), BATCH):
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

    def _eval(F: np.ndarray, y: np.ndarray):
        pr = (np.maximum(F @ W1 + b1, 0.0) @ W2 + b2).argmax(axis=1)
        raw = float((pr == y).mean())
        recs = [float((pr[y == c] == c).mean()) for c in (0, 1)]
        return raw, float(np.mean(recs)), recs, sorted(int(v) for v in np.unique(pr))

    train_raw, _, _, _ = _eval(Ftr, ytr)
    test_raw, test_bal, test_recs, pred_classes = _eval(Fte, yte)
    return {"train_raw": train_raw, "test_raw": test_raw,
            "test_balanced": test_bal, "test_recs": test_recs,
            "pred_classes": pred_classes,
            "n_params": int(W1.size + b1.size + W2.size + b2.size)}


_P2R_CACHE: dict = {}


def _run_p2r() -> dict:
    """Matched-budget bounded run over SEEDS; cached so tests share one run."""
    if "res" in _P2R_CACHE:
        return _P2R_CACHE["res"]
    assert len(SEEDS) <= 3 and EPOCHS <= 5  # caps enforced fail-closed
    t0 = time.perf_counter()
    per_seed, c_bal, q_bal = [], [], []
    for s in SEEDS:
        s0 = time.perf_counter()
        Xtr, ytr, Xte, yte = _balanced_binary_pair(s)
        c = _train_and_eval(_head_features(Xtr, "classical"), ytr,
                            _head_features(Xte, "classical"), yte, s)
        q = _train_and_eval(_head_features(Xtr, "quantum"), ytr,
                            _head_features(Xte, "quantum"), yte, s)
        assert c["n_params"] == q["n_params"], "budget must match both arms"
        c_bal.append(c["test_balanced"])
        q_bal.append(q["test_balanced"])
        per_seed.append({"seed": s,
                         "n_train_per_class": int((ytr == 0).sum()),
                         "n_test_per_class": int((yte == 0).sum()),
                         "classical_balanced": round(c["test_balanced"], 4),
                         "classical_raw": round(c["test_raw"], 4),
                         "classical_train": round(c["train_raw"], 4),
                         "classical_pred_classes": c["pred_classes"],
                         "quantum_balanced": round(q["test_balanced"], 4),
                         "quantum_raw": round(q["test_raw"], 4),
                         "quantum_train": round(q["train_raw"], 4),
                         "quantum_pred_classes": q["pred_classes"],
                         "n_params": c["n_params"],
                         "wall_s": round(time.perf_counter() - s0, 2)})
    wall = time.perf_counter() - t0
    assert wall < WALL_BUDGET_S, f"wall cap breached {wall:.1f}s (fail-closed)"
    res = {"classical_mean_bal": float(np.mean(c_bal)),
           "quantum_mean_bal": float(np.mean(q_bal)),
           "classical_bals": c_bal, "quantum_bals": q_bal,
           "per_seed": per_seed, "wall_s": wall}
    _P2R_CACHE["res"] = res
    print(f"P2-redo classical_bal={res['classical_mean_bal']:.4f} "
          f"quantum_bal={res['quantum_mean_bal']:.4f} chance={CHANCE:.2f} "
          f"per_seed={per_seed} wall={wall:.1f}s")
    return res


def test_p2r_classical_learns_balanced():
    """Stronger classical (hidden 64, <=5 epochs, 1 fixed lr) learns 50/50 XOR."""
    res = _run_p2r()
    mean_bal = res["classical_mean_bal"]
    both = [p["classical_pred_classes"] == [0, 1] for p in res["per_seed"]]
    # ONE assertion: balanced-acc > chance AND both classes predicted
    # (no majority collapse), else HONEST FAIL (no retune-to-pass).
    assert mean_bal > CHANCE and all(both), (
        f"HONEST FAIL (no retune): classical_bal={mean_bal:.4f} not > "
        f"chance={CHANCE:.2f} with both-classes-predicted={both}; "
        f"per_seed={res['per_seed']}")


def test_p2r_quantum_matched_falsifier():
    """Same-budget same-token quantum proxy stays below classical-margin."""
    res = _run_p2r()
    c_mean, q_mean = res["classical_mean_bal"], res["quantum_mean_bal"]
    # ONE assertion (falsifier): claim "quantum < classical - margin" is
    # KILLED if quantum >= classical - margin — failure reported honestly,
    # fail-open exploratory (no gate), no retune-to-pass.
    assert q_mean < c_mean - FALSIFIER_MARGIN, (
        f"FALSIFIED (report honestly): quantum_bal={q_mean:.4f} >= "
        f"classical_bal={c_mean:.4f}-{FALSIFIER_MARGIN:.2f}; "
        f"efficiency claim killed, per_seed={res['per_seed']}")


def test_p2r_evidence_complete():
    """All primary metrics (balanced/raw per seed, both arms) are logged."""
    res = _run_p2r()
    # ONE assertion: every seed logs finite balanced+raw for both arms.
    assert all(
        all(np.isfinite(p[k]) for k in (
            "classical_balanced", "classical_raw",
            "quantum_balanced", "quantum_raw"))
        for p in res["per_seed"]
    ) and len(res["per_seed"]) == len(SEEDS), (
        f"EVIDENCE INCOMPLETE: per_seed={res['per_seed']}")


def _balanced_binary_pair_eq(seed: int):
    """Equality generator -> binary match-vs-default, test-local 50/50.

    Mirrors _balanced_binary_pair exactly; ONLY the generator differs
    (generate_equality_sequence_decision control). Same TINY/seeded
    subsample, same exact-balance fail-closed guard.
    """
    from benchmarks.tasks.benchmark_sequence_decision import (
        generate_equality_sequence_decision,
    )
    Xtr, ytr, Xte, yte = generate_equality_sequence_decision(
        seed=seed, **TINY)
    ytr_b = (ytr[:, -1].astype(int) != 0).astype(int)
    yte_b = (yte[:, -1].astype(int) != 0).astype(int)
    rng = np.random.RandomState(5000 + seed)  # same subsample stream as XOR arm

    def _sub(X: np.ndarray, y: np.ndarray):
        i0 = np.where(y == 0)[0]
        i1 = np.where(y == 1)[0]
        m = min(len(i0), len(i1))
        assert m >= MIN_PER_CLASS, (
            f"cannot build 50/50 split (eq seed={seed}): "
            f"minority={m} < {MIN_PER_CLASS}")
        s0 = rng.choice(i0, m, replace=False)
        s1 = rng.choice(i1, m, replace=False)
        idx = np.concatenate([s0, s1])
        rng.shuffle(idx)
        Xb, yb = X[idx], y[idx]
        assert int((yb == 0).sum()) == int((yb == 1).sum()) == m, (
            f"split not 50/50 (eq seed={seed}): "
            f"n0={(yb == 0).sum()} n1={(yb == 1).sum()}")
        return Xb, yb

    return _sub(Xtr, ytr_b) + _sub(Xte, yte_b)


def test_p2r_equality_control():
    """Equality control (INFORMATIONAL ONLY — does NOT gate falsifier).

    Same matched setup (heads/MLP/init/shuffle/EPOCHS/SEEDS/TINY) on
    generate_equality_sequence_decision. Reports balanced accs per seed
    and per-arm means; no performance threshold asserted (no new
    thresholds), only evidence-completeness (finite + per-seed logged).
    """
    assert len(SEEDS) <= 3 and EPOCHS <= 5  # caps enforced fail-closed
    per_seed, c_bal, q_bal = [], [], []
    for s in SEEDS:
        Xtr, ytr, Xte, yte = _balanced_binary_pair_eq(s)
        c = _train_and_eval(_head_features(Xtr, "classical"), ytr,
                            _head_features(Xte, "classical"), yte, s)
        q = _train_and_eval(_head_features(Xtr, "quantum"), ytr,
                            _head_features(Xte, "quantum"), yte, s)
        assert c["n_params"] == q["n_params"], "budget must match both arms"
        c_bal.append(c["test_balanced"])
        q_bal.append(q["test_balanced"])
        per_seed.append({"seed": s,
                         "classical_balanced": round(c["test_balanced"], 4),
                         "classical_raw": round(c["test_raw"], 4),
                         "classical_pred_classes": c["pred_classes"],
                         "quantum_balanced": round(q["test_balanced"], 4),
                         "quantum_raw": round(q["test_raw"], 4),
                         "quantum_pred_classes": q["pred_classes"]})
    print(f"EQUALITY-CONTROL classical_bal={float(np.mean(c_bal)):.4f} "
          f"quantum_bal={float(np.mean(q_bal)):.4f} chance={CHANCE:.2f} "
          f"per_seed={per_seed}")
    # Informational only: completeness, NOT a performance gate.
    assert all(
        all(np.isfinite(p[k]) for k in (
            "classical_balanced", "classical_raw",
            "quantum_balanced", "quantum_raw"))
        for p in per_seed
    ) and len(per_seed) == len(SEEDS), (
        f"EQUALITY-CONTROL INCOMPLETE: per_seed={per_seed}")
