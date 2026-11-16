#!/usr/bin/env python3
"""Row 2 standalone recompute for Track C priors (record-only, strict exit).

Reads --input JSONL only for raw validation (row count + per-test exits).
Recomputes summary statistics from embedded per-seed observations with
numpy only; 95% CI uses the normal approximation:
  CI = mean +/- 1.96 * sd / sqrt(n)   (sd = sample std, ddof=1)
  diff_SE = sqrt(se_leaky^2 + se_disjoint^2); diff_CI = diff +/- 1.96*diff_SE
No test imports, no task imports, no simulation imports.
Imports: json, math, sys, numpy ONLY.
"""
import json
import math
import sys

import numpy as np


PRIORS = {"classical": 0.9722, "quantum": 0.4912, "diff": 0.229}
RATIO_BAND = (1.8, 2.2)

# Embedded per-seed observations (provenance in printout; values only, no imports):
# - XOR classical/quantum per-seed from docs/plans/2026-11-17-p2-redo-evidence.json
# - P1 leaky/disjoint per-seed from /tmp/p1_overlap_pilot.json per_seed accs
# - P3 ratios: row1 observed 1.89; cross-run 1.96 (pilots) and 2.03 (range upper per plan)
CLASSICAL_SEEDS = [1.0, 0.9167, 1.0]
QUANTUM_SEEDS = [0.5096, 0.4833, 0.4808]
LEAKY_SEEDS = [0.59375, 0.625, 0.8125]
DISJOINT_SEEDS = [0.375, 0.4375, 0.53125]
RATIO_OBSERVED = 1.89
RATIO_RUNS = [1.89, 1.96, 2.03]

EXPECTED_EXITS = {
    "tests/test_p2_redo.py": 0,
    "tests/test_pilots_overlap.py": 1,
    "tests/test_pilots_moe_cost.py": 0,
    "tests/test_phase1_1_guards.py": 0,
    "tests/test_phase1_correctness_guards.py": 1,
}


def _usage():
    return "usage: recompute-track-c.py --input <jsonl> [--tol-mean 0.005 --tol-diff 0.01]"


def _parse_argv(argv):
    inp = None
    tol_mean = 0.005
    tol_diff = 0.01
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--input" and i + 1 < len(argv):
            inp = argv[i + 1]
            i += 2
        elif a == "--tol-mean" and i + 1 < len(argv):
            tol_mean = float(argv[i + 1])
            i += 2
        elif a == "--tol-diff" and i + 1 < len(argv):
            tol_diff = float(argv[i + 1])
            i += 2
        elif a in ("-h", "--help"):
            print(_usage())
            sys.exit(0)
        else:
            print("unknown arg: " + a)
            print(_usage())
            sys.exit(2)
    if inp is None:
        print(_usage())
        sys.exit(2)
    return inp, tol_mean, tol_diff


def _mean_ci(xs):
    n = len(xs)
    mean = float(np.mean(np.asarray(xs, dtype=float)))
    if n <= 1:
        return mean, mean, mean
    sd = float(np.std(np.asarray(xs, dtype=float), ddof=1))
    se = sd / math.sqrt(n)
    half = 1.96 * se
    return mean, mean - half, mean + half


def main():
    inp, tol_mean, tol_diff = _parse_argv(sys.argv)
    try:
        fp = open(inp, "r")
    except OSError as e:
        print("FAIL input unreadable: " + str(e))
        sys.exit(1)
    rows = []
    with fp:
        for line in fp:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    print("input=" + inp + " rows=" + str(len(rows)))
    ok_raw = True
    if len(rows) != 5:
        print("FAIL raw row count len=" + str(len(rows)) + " expected=5")
        ok_raw = False
    seen = {}
    for r in rows:
        try:
            seen[str(r["test"])] = int(r["exit"])
        except (KeyError, TypeError, ValueError):
            ok_raw = False
    for t, exp_exit in EXPECTED_EXITS.items():
        got = seen.get(t, None)
        status = "ok" if got == exp_exit else "MISMATCH"
        print("raw " + t + " exit=" + str(got) + " expected=" + str(exp_exit) + " " + status)
        if got != exp_exit:
            ok_raw = False

    c_mean, c_lo, c_hi = _mean_ci(CLASSICAL_SEEDS)
    q_mean, q_lo, q_hi = _mean_ci(QUANTUM_SEEDS)
    l_mean, l_lo, l_hi = _mean_ci(LEAKY_SEEDS)
    d_mean, d_lo, d_hi = _mean_ci(DISJOINT_SEEDS)
    # diff CI via independent-SE propagation (normal approx, formula in-file)
    l_sd = float(np.std(np.asarray(LEAKY_SEEDS, dtype=float), ddof=1))
    d_sd = float(np.std(np.asarray(DISJOINT_SEEDS, dtype=float), ddof=1))
    l_se = l_sd / math.sqrt(len(LEAKY_SEEDS))
    d_se = d_sd / math.sqrt(len(DISJOINT_SEEDS))
    diff = float(l_mean - d_mean)
    diff_se = math.sqrt(l_se * l_se + d_se * d_se)
    diff_half = 1.96 * diff_se
    diff_lo, diff_hi = diff - diff_half, diff + diff_half
    r_mean, r_lo, r_hi = _mean_ci(RATIO_RUNS)

    print("XOR classical per-seed=" + str(CLASSICAL_SEEDS) + " mean=" + format(c_mean, ".4f")
          + " CI95=[" + format(c_lo, ".4f") + "," + format(c_hi, ".4f") + "] prior=0.9722 tol-mean=" + str(tol_mean))
    print("XOR quantum per-seed=" + str(QUANTUM_SEEDS) + " mean=" + format(q_mean, ".4f")
          + " CI95=[" + format(q_lo, ".4f") + "," + format(q_hi, ".4f") + "] prior=0.4912 tol-mean=" + str(tol_mean))
    print("P1 leaky per-seed=" + str(LEAKY_SEEDS) + " mean=" + format(l_mean, ".4f")
          + " CI95=[" + format(l_lo, ".4f") + "," + format(l_hi, ".4f") + "]")
    print("P1 disjoint per-seed=" + str(DISJOINT_SEEDS) + " mean=" + format(d_mean, ".4f")
          + " CI95=[" + format(d_lo, ".4f") + "," + format(d_hi, ".4f") + "]")
    print("P1 diff leaky-minus-disjoint=" + format(diff, ".4f")
          + " CI95=[" + format(diff_lo, ".4f") + "," + format(diff_hi, ".4f") + "] prior=0.229 tol-diff=" + str(tol_diff))
    print("P3 ratio observed=" + format(RATIO_OBSERVED, ".2f")
          + " cross-run=" + str(RATIO_RUNS) + " mean=" + format(r_mean, ".4f")
          + " CI95=[" + format(r_lo, ".4f") + "," + format(r_hi, ".4f") + "] band=[1.80,2.20]")

    checks = []
    dc = abs(c_mean - PRIORS["classical"])
    dq = abs(q_mean - PRIORS["quantum"])
    dd = abs(diff - PRIORS["diff"])
    c1 = dc <= tol_mean
    c2 = dq <= tol_mean
    c3 = dd <= tol_diff
    c4 = RATIO_BAND[0] <= RATIO_OBSERVED <= RATIO_BAND[1]
    c5 = RATIO_BAND[0] <= r_mean <= RATIO_BAND[1]
    print("check classical |" + format(c_mean, ".4f") + "-0.9722|=" + format(dc, ".4f") + " <=" + str(tol_mean) + " " + ("PASS" if c1 else "FAIL"))
    print("check quantum |" + format(q_mean, ".4f") + "-0.4912|=" + format(dq, ".4f") + " <=" + str(tol_mean) + " " + ("PASS" if c2 else "FAIL"))
    print("check diff |" + format(diff, ".4f") + "-0.229|=" + format(dd, ".4f") + " <=" + str(tol_diff) + " " + ("PASS" if c3 else "FAIL"))
    print("check ratio observed " + format(RATIO_OBSERVED, ".2f") + " in [1.80,2.20] " + ("PASS" if c4 else "FAIL"))
    print("check ratio cross-run mean " + format(r_mean, ".4f") + " in [1.80,2.20] " + ("PASS" if c5 else "FAIL"))
    checks = [c1, c2, c3, c4, c5]
    if ok_raw and all(checks):
        print("OVERALL PASS")
        sys.exit(0)
    print("OVERALL FAIL raw_ok=" + str(ok_raw) + " checks=" + str(checks))
    sys.exit(1)


main()
