"""Confirmatory magnitude lock (RED, failing-first, write-only).

Spec: docs/plans/2026-11-17-confirmatory-mag.md rows 1-3
  (N/A-fail-open-frozen-inline, record-only, no gated advantage claim).
Branch: research/audit-1587497. Auth: user "keep on continue",
  frozen-then-once, no peeking before freeze.
Caps: FRESH seeds [11,33,55] ONLY (forbidden 6 never used), <=5 epochs,
  1 LR config, 900s wall, local CPU only, run-once (marker
  CONFIRMATORY_MAG_RUN_ONCE in mag progress file; second invocation
  refuses).
Status: RED — written first, never executed here (write-only handoff).
  Implementer run cmd:
    .venv/bin/python -m pytest tests/test_confirmatory_mag.py -q -s
Allowed writes: this file ONLY (new). Mechanism copied from
  tests/test_confirmatory.py (MLP/_heldout/_ci pattern) — no import of
  prior lock to preserve independence.
No repo file I/O (in-memory metrics only; evidence files are implementer
  step to allow paths only).

Freeze (locked before any run — do not edit after first green):
  FRESH_SEEDS=[11,33,55], FORBIDDEN_SEEDS=[6],
  HELD_OUT_XOR=(p1=1,p2=3,target_xor=1,action=2),
  HELD_OUT_EQ=(p=2,target_val=1,action=1),
  MODEL hidden=64/epochs=5/lr=1e-2 x1 config, PRIMARY=balanced_acc_diff
  (classical_bal - quantum_bal), THRESHOLD=0.20, BONFERRONI=2 tasks
  (XOR held-out + equality held-out), WALL=900s, STOPPING=run-once.
Design (matched budget — ONLY head information differs, mirrors
  tests/test_confirmatory.py mechanism):
  - Binary task: rule-match (label != 0) vs default (label == 0) on
    test-local held-out rules (XOR needs p1 vs p2 cross-token; equality
    needs single-position match), test-local 50/50 subsample per split.
  - Same MLP (16->64->2), same Adam(lr fixed a priori)/batch/epochs,
    same param init AND same shuffle order per seed for both arms.
  - Classical arm: ordered concat of position one-hots (16-dim).
  - Quantum arm (same-token proxy): last-position one-hot in its block,
    zeros elsewhere (16-dim, same MLP size).
Hermetic: numpy-only MLP, no network/GPU/paid APIs, no live services.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

try:
    from benchmarks.analysis.statistics import confidence_interval
except Exception:  # hermetic fallback: t approx for n=3
    confidence_interval = None  # type: ignore[assignment]


# --- Confirmatory-magnitude freeze (DO NOT EDIT after first green) ---------
FRESH_SEEDS = [11, 33, 55]  # ONLY these; forbidden 6 never used
FORBIDDEN_SEEDS = [6]  # exploratory reuse — banned here
HELD_OUT_XOR_P1, HELD_OUT_XOR_P2 = 1, 3
HELD_OUT_XOR_TARGET, HELD_OUT_XOR_ACTION = 1, 2
HELD_OUT_EQ_P, HELD_OUT_EQ_TARGET, HELD_OUT_EQ_ACTION = 2, 1, 1
HIDDEN = 64  # matched MLP width
EPOCHS = 5  # <=5 epochs, matched both arms/tasks
LR = 1e-2  # single LR config fixed a priori (1 config, no tuning)
LR_CONFIGS = 1  # no sweep
BATCH = 16
TINY = dict(seq_len=4, token_vocab=4, n_actions=4, n_rules=1,
            n_train=480, n_test=240)  # tiny, local only
CHANCE = 0.5  # binary balanced task chance
PRIMARY = "balanced_acc_diff"  # classical_bal - quantum_bal per seed
THRESHOLD = 0.20  # record-only reference (fail-open, no gate)
BONFERRONI = 2  # two held-out tasks: XOR + equality
WALL_BUDGET_S = 900  # 900s wall cap, fail-open record (asserted, no gate)
MIN_PER_CLASS = 16  # floor for 50/50 subsample
PROGRESS_PATH = Path(
    "docs/plans/2026-11-17-confirmatory-mag-progress.md")
RUN_ONCE_MARKER = "CONFIRMATORY_MAG_RUN_ONCE"
assert TINY["seq_len"] <= 16, "tiny seq must fit max_quantum_seq=16 proxy"


def _exploratory_xor_pair(seed: int):
    """Replicate exploratory RNG rule draw (benchmark_sequence_decision:40-48)."""
    rng = np.random.RandomState(seed)
    p1, p2 = sorted(rng.choice(TINY["seq_len"], 2, replace=False).tolist())
    return (int(p1), int(p2))


def _ci(values: list[float]) -> dict:
    if confidence_interval is not None:
        return dict(confidence_interval(values))
    v = np.asarray(values, dtype=float)  # hermetic t-approx fallback (n=3)
    m, sd = float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
    margin = 4.303 * sd / np.sqrt(len(v)) if len(v) > 1 else 0.0
    return {"mean": m, "ci_low": m - margin, "ci_high": m + margin,
            "std": sd, "n": len(v)}


def _heldout_pair(seed: int, task: str):
    """Test-local held-out data: fixed literal rule, RNG-drawn X per seed."""
    rng = np.random.RandomState(seed)
    n_total = TINY["n_train"] + TINY["n_test"]
    X = rng.randint(0, TINY["token_vocab"], (n_total, TINY["seq_len"]))
    labels = np.zeros(n_total, dtype=int)
    if task == "xor":
        mask = (X[:, HELD_OUT_XOR_P1] ^ X[:, HELD_OUT_XOR_P2]
                ) == HELD_OUT_XOR_TARGET
        labels[mask] = HELD_OUT_XOR_ACTION
    elif task == "eq":
        mask = X[:, HELD_OUT_EQ_P] == HELD_OUT_EQ_TARGET
        labels[mask] = HELD_OUT_EQ_ACTION
    else:
        raise ValueError(task)
    n_tr = TINY["n_train"]
    Xtr, Xte = X[:n_tr], X[n_tr:]
    ytr = (labels[:n_tr] != 0).astype(int)
    yte = (labels[n_tr:] != 0).astype(int)
    sub_rng = np.random.RandomState(5000 + seed)

    def _sub(Xs: np.ndarray, ys: np.ndarray):
        i0 = np.where(ys == 0)[0]
        i1 = np.where(ys == 1)[0]
        m = min(len(i0), len(i1))
        assert m >= MIN_PER_CLASS, (
            f"cannot build 50/50 ({task} seed={seed}): minority={m}")
        s0 = sub_rng.choice(i0, m, replace=False)
        s1 = sub_rng.choice(i1, m, replace=False)
        idx = np.concatenate([s0, s1])
        sub_rng.shuffle(idx)
        Xb, yb = Xs[idx], ys[idx]
        assert int((yb == 0).sum()) == int((yb == 1).sum()) == m, (
            f"split not 50/50 ({task} seed={seed})")
        return Xb, yb

    return _sub(Xtr, ytr) + _sub(Xte, yte)


def _head_features(X: np.ndarray, mode: str) -> np.ndarray:
    oh = np.eye(TINY["token_vocab"], dtype=np.float64)[np.asarray(X, dtype=int)]
    n = oh.shape[0]
    if mode == "classical":
        return oh.reshape(n, -1)
    if mode == "quantum":
        f = np.zeros((n, 16), dtype=np.float64)
        f[:, 12:16] = oh[:, -1, :]
        return f
    raise ValueError(mode)


def _train_and_eval(Ftr: np.ndarray, ytr: np.ndarray,
                    Fte: np.ndarray, yte: np.ndarray,
                    seed: int) -> dict:
    rng_init = np.random.RandomState(1000 + seed)
    W1 = rng_init.randn(16, HIDDEN) * np.sqrt(2.0 / 16)
    b1 = np.zeros(HIDDEN)
    W2 = rng_init.randn(HIDDEN, 2) * np.sqrt(2.0 / HIDDEN)
    b2 = np.zeros(2)
    mW1, vW1 = np.zeros_like(W1), np.zeros_like(W1)
    mb1, vb1 = np.zeros_like(b1), np.zeros_like(b1)
    mW2, vW2 = np.zeros_like(W2), np.zeros_like(W2)
    mb2, vb2 = np.zeros_like(b2), np.zeros_like(b2)
    b1t, b2t, eps = 0.9, 0.999, 1e-8
    rng_shuf = np.random.RandomState(2000 + seed)
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
            dh = (dp @ W2.T)
            dh[h <= 0.0] = 0.0
            dW1 = xb.T @ dh
            db1 = dh.sum(axis=0)
            for P, dP, m, v in ((W1, dW1, mW1, vW1), (W2, dW2, mW2, vW2)):
                m[:] = b1t * m + (1 - b1t) * dP
                v[:] = b2t * v + (1 - b2t) * dP ** 2
                P -= LR * (m / (1 - b1t ** t)) / (
                    np.sqrt(v / (1 - b2t ** t)) + eps)
            mb1[:] = b1t * mb1 + (1 - b1t) * db1
            vb1[:] = b2t * vb1 + (1 - b2t) * db1 ** 2
            b1 -= LR * (mb1 / (1 - b1t ** t)) / (
                np.sqrt(vb1 / (1 - b2t ** t)) + eps)
            mb2[:] = b1t * mb2 + (1 - b1t) * db2
            vb2[:] = b2t * vb2 + (1 - b2t) * db2 ** 2
            b2 -= LR * (mb2 / (1 - b1t ** t)) / (
                np.sqrt(vb2 / (1 - b2t ** t)) + eps)

    def _eval(F: np.ndarray, y: np.ndarray):
        pr = (np.maximum(F @ W1 + b1, 0.0) @ W2 + b2).argmax(axis=1)
        raw = float((pr == y).mean())
        recs = [float((pr[y == c] == c).mean()) for c in (0, 1)]
        return raw, float(np.mean(recs))

    train_raw, _ = _eval(Ftr, ytr)
    test_raw, test_bal = _eval(Fte, yte)
    return {"train_raw": train_raw, "test_raw": test_raw,
            "test_balanced": test_bal,
            "n_params": int(W1.size + b1.size + W2.size + b2.size)}


_CONF_MAG_CACHE: dict = {}


def _run_confirmatory_mag() -> dict:
    """Frozen single-run magnitude workload over FRESH_SEEDS; cached one run."""
    if "res" in _CONF_MAG_CACHE:
        return _CONF_MAG_CACHE["res"]
    if PROGRESS_PATH.exists() and RUN_ONCE_MARKER in PROGRESS_PATH.read_text():
        raise AssertionError(
            f"STOPPING run-once: {RUN_ONCE_MARKER} found in {PROGRESS_PATH}; "
            "second invocation refuses (no repeat run)")
    assert len(FRESH_SEEDS) == 3 and EPOCHS <= 5 and LR_CONFIGS == 1
    assert not set(FRESH_SEEDS) & set(FORBIDDEN_SEEDS)
    t0 = time.perf_counter()
    tasks: dict = {}
    for task in ("xor", "eq"):
        per_seed, diffs, c_bal, q_bal = [], [], [], []
        for s in FRESH_SEEDS:
            s0 = time.perf_counter()
            Xtr, ytr, Xte, yte = _heldout_pair(s, task)
            c = _train_and_eval(_head_features(Xtr, "classical"), ytr,
                                _head_features(Xte, "classical"), yte, s)
            q = _train_and_eval(_head_features(Xtr, "quantum"), ytr,
                                _head_features(Xte, "quantum"), yte, s)
            assert c["n_params"] == q["n_params"], "budget must match both arms"
            diff = float(c["test_balanced"] - q["test_balanced"])
            diffs.append(diff)
            c_bal.append(float(c["test_balanced"]))
            q_bal.append(float(q["test_balanced"]))
            per_seed.append({"seed": s,
                             "balanced_acc_diff": round(diff, 4),
                             "classical_balanced": round(c["test_balanced"], 4),
                             "quantum_balanced": round(q["test_balanced"], 4),
                             "wall_s": round(time.perf_counter() - s0, 2)})
        ci = _ci(diffs)
        tasks[task] = {"per_seed": per_seed, "diffs": diffs,
                       "mean_diff": float(np.mean(diffs)), "ci": ci,
                       "classical_mean": float(np.mean(c_bal)),
                       "quantum_mean": float(np.mean(q_bal))}
        print(f"CONFIRMATORY-MAG-{task} diffs={per_seed} "
              f"mean_diff={np.mean(diffs):.4f} "
              f"CI=[{ci['ci_low']:.4f},{ci['ci_high']:.4f}] "
              f"threshold={THRESHOLD} (record-only, no gate)")
    wall = time.perf_counter() - t0
    res = {"tasks": tasks, "wall_s": wall}
    _CONF_MAG_CACHE["res"] = res
    print(f"CONFIRMATORY-MAG wall={wall:.1f}s budget={WALL_BUDGET_S}s "
          f"primary={PRIMARY} bonferroni={BONFERRONI} timeouts_logged=True")
    return res


def test_protocol_frozen_mag():
    """Frozen magnitude protocol constants are locked and held-out is distinct."""
    # Protocol correction (pre-results, freeze RED): held-out must be unseen
    # WITHIN this run (fresh seeds [11,33,55] draws {(2,3),(1,2),(0,3)}) +
    # distinct from prior locks (0,3),(1,2) (protocol independence).
    # Historical draws from other seeds never mix into this run — excluding
    # them over-constrains to impossibility (9 seeds cover all 6 pairs).
    # This narrows the check to what leakage requires, not a weakening.
    # ONE assertion: every frozen literal matches AND held-out pair differs
    # from prior locks and fresh-seed draws (leakage-relevant set only).
    assert (
        FRESH_SEEDS == [11, 33, 55]
        and FORBIDDEN_SEEDS == [6]
        and not set(FRESH_SEEDS) & set(FORBIDDEN_SEEDS)
        and (HELD_OUT_XOR_P1, HELD_OUT_XOR_P2,
             HELD_OUT_XOR_TARGET, HELD_OUT_XOR_ACTION) == (1, 3, 1, 2)
        and (HELD_OUT_EQ_P, HELD_OUT_EQ_TARGET,
             HELD_OUT_EQ_ACTION) == (2, 1, 1)
        and HIDDEN == 64 and EPOCHS == 5 and LR == 1e-2 and LR_CONFIGS == 1
        and PRIMARY == "balanced_acc_diff" and THRESHOLD == 0.20
        and BONFERRONI == 2 and WALL_BUDGET_S == 900
        and RUN_ONCE_MARKER == "CONFIRMATORY_MAG_RUN_ONCE"
        and (HELD_OUT_XOR_P1, HELD_OUT_XOR_P2) not in [(0, 3), (1, 2)]
        and all((HELD_OUT_XOR_P1, HELD_OUT_XOR_P2)
                != _exploratory_xor_pair(s)
                for s in FRESH_SEEDS)
    ), (
        f"FROZEN-MAG MISMATCH: fresh={FRESH_SEEDS} forbidden={FORBIDDEN_SEEDS} "
        f"xor={(HELD_OUT_XOR_P1, HELD_OUT_XOR_P2)} "
        f"prior_locks=[(0, 3), (1, 2)] "
        f"exploratory="
        f"{[(s, _exploratory_xor_pair(s)) for s in FRESH_SEEDS]}")


def test_confirmatory_single_run_mag():
    """Frozen magnitude single-run completes once within caps, outcome recorded."""
    res = _run_confirmatory_mag()
    # ONE assertion: once-only fresh-seed run within caps with per-seed
    # diffs finite and matched params (record-only fail-open, no gate).
    assert (
        len(res["tasks"]["xor"]["per_seed"]) == len(FRESH_SEEDS) == 3
        and len(res["tasks"]["eq"]["per_seed"]) == len(FRESH_SEEDS) == 3
        and all(np.isfinite(p["balanced_acc_diff"])
                for t in ("xor", "eq")
                for p in res["tasks"][t]["per_seed"])
        and all(np.isfinite(res["tasks"][t]["ci"]["ci_low"])
                and np.isfinite(res["tasks"][t]["ci"]["ci_high"])
                for t in ("xor", "eq"))
        and res["wall_s"] < WALL_BUDGET_S
        and EPOCHS <= 5 and LR_CONFIGS == 1
    ), f"MAG EVIDENCE INCOMPLETE or CAP BREACH: {res}"
