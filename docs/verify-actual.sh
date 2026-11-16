#!/usr/bin/env bash
# Gate + runner repro for locked protocol equality-actual-v2 (run4 authoritative).
# Scope-locked: writes only under /tmp/opencode/actual-repro-check; never touches
# research/artifacts, scripts, protocols, or tests. Fail-closed: any R1-R6
# violation exits non-zero, never silent 0.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

EXPECTED_BRANCH="research/audit-1587497"
EXPECTED_HEAD_PREFIX="a3addab"
EXPECTED_HEAD_FULL="a3addab83791b9b2c39e8bb05a12e74fb1444f66"
EXPECTED_CONFIG_HASH="e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54"
PROTOCOL="research/protocols/equality-actual-v2.json"
AUTH_RAW="research/artifacts/equality-actual-v2/run4/raw.json"
AUTH_REPORT="research/artifacts/equality-actual-v2/run4/report-t.json"
OUT_BASE="/tmp/opencode/actual-repro-check"

fail() { echo "FAIL: $*" >&2; exit 2; }
info() { echo "$*"; }

# --- prereq gates (any violation exits non-zero) ---
BRANCH="$(git branch --show-current 2>/dev/null || true)"
[ "$BRANCH" = "$EXPECTED_BRANCH" ] || fail "branch mismatch: got '${BRANCH}' want '${EXPECTED_BRANCH}'"
HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
case "$HEAD" in
  "$EXPECTED_HEAD_PREFIX"*) ;;
  *) fail "HEAD mismatch: got '${HEAD}' want prefix '${EXPECTED_HEAD_PREFIX}' (${EXPECTED_HEAD_FULL})" ;;
esac
[ -x ".venv/bin/python" ] || fail ".venv/bin/python missing or not executable"
.venv/bin/python -c "import scipy, numpy" 2>/dev/null || fail "scipy/numpy import failed under .venv/bin/python"
[ -f "$PROTOCOL" ] || fail "protocol missing: $PROTOCOL"
[ -f "$AUTH_RAW" ] || fail "authoritative raw missing: $AUTH_RAW"
[ -f "$AUTH_REPORT" ] || fail "authoritative report missing: $AUTH_REPORT"

# protocol frozen + verbatim checks (R1-R6 locked fields) + config_hash recompute
.venv/bin/python - "$PROTOCOL" "$EXPECTED_CONFIG_HASH" <<'PY'
import hashlib, json, sys
proto_path, expected = sys.argv[1], sys.argv[2]
p = json.loads(open(proto_path, encoding="utf-8").read())
if p.get("protocol") != "equality-actual-v2":
    print("FAIL: protocol id mismatch", file=sys.stderr); sys.exit(2)
if p.get("frozen") is not True:
    print("FAIL: protocol frozen must be true", file=sys.stderr); sys.exit(2)
canonical = {
    "models": {"A_classical": p["models"]["A_classical"], "B_hybrid": p["models"]["B_hybrid"]},
    "protocol": p["protocol"],
    "splits": p["splits"],
    "task": p["task"],
}
blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
got = hashlib.sha256(blob.encode("utf-8")).hexdigest()
if got != expected:
    print(f"FAIL: config_hash mismatch got {got} want {expected}", file=sys.stderr); sys.exit(2)
if list(p.get("seeds", [])) != [101, 202, 303]:
    print("FAIL: seeds must be exactly [101,202,303]", file=sys.stderr); sys.exit(2)
if p.get("splits", {}).get("overlap_tolerance") != 0:
    print("FAIL: overlap_tolerance must be 0", file=sys.stderr); sys.exit(2)
PY

STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_ID="run-repro-${STAMP}"
case "$RUN_ID" in
  run2|run3|run4|run2:*|run3:*|run4:*) fail "refusing reserved run_id: $RUN_ID" ;;
esac
mkdir -p "$OUT_BASE"
RUN_DIR="${OUT_BASE}/${RUN_ID}"

info "preflight ok branch=${BRANCH} head=${HEAD} config_hash=${EXPECTED_CONFIG_HASH}"

# --- runner (NEW run-id, never run2/3/4; timeout 290) ---
.venv/bin/python scripts/run_actual_experiment.py \
  --protocol "$PROTOCOL" \
  --output "$OUT_BASE" \
  --run-id "$RUN_ID" \
  --timeout 290
[ -f "${RUN_DIR}/raw.json" ] || fail "runner did not produce ${RUN_DIR}/raw.json"

# --- analyzer (paired-only; --method t --multiplicity none) ---
.venv/bin/python scripts/analyze_results.py \
  --input "${RUN_DIR}/raw.json" \
  --output "${RUN_DIR}/report-t.json" \
  --method t \
  --multiplicity none
[ -f "${RUN_DIR}/report-t.json" ] || fail "analyzer did not produce ${RUN_DIR}/report-t.json"

# --- gate asserts: repro vs authoritative run4 within tolerances; exit non-zero on drift ---
REPRO_RAW="${RUN_DIR}/raw.json" REPRO_REPORT="${RUN_DIR}/report-t.json" RUN_DIR_ENV="${RUN_DIR}" .venv/bin/python - "$AUTH_REPORT" "$AUTH_RAW" <<'PY'
import json, math, os, sys, glob
auth_report_path, auth_raw_path = sys.argv[1], sys.argv[2]
repro_report_path = os.environ["REPRO_REPORT"]
repro_raw_path = os.environ["REPRO_RAW"]
run_dir = os.environ["RUN_DIR_ENV"]
expected_hash = "e2a56245deea3ff12a3c15e46efa745c227788df5610cf89d15e1222c3e98d54"

auth = json.loads(open(auth_report_path, encoding="utf-8").read())
rep = json.loads(open(repro_report_path, encoding="utf-8").read())
auth_raw = json.loads(open(auth_raw_path, encoding="utf-8").read())
repro_raw = json.loads(open(repro_raw_path, encoding="utf-8").read())

def bad(msg):
    print(f"FAIL: {msg}", file=sys.stderr); sys.exit(1)

# structure
if rep.get("n_pairs") != 3: bad(f"n_pairs={rep.get('n_pairs')} want 3")
if rep.get("config_hash") != expected_hash: bad("repro config_hash mismatch pinned")
if auth.get("config_hash") != expected_hash: bad("authoritative config_hash drift from pinned")
if repro_raw.get("config_hash") != expected_hash: bad("repro raw config_hash mismatch")
if rep.get("method_requested") != "t": bad("method_requested must be t")
if rep.get("method_used") != "t (scipy, 95%)": bad(f"method_used={rep.get('method_used')!r}")
mult = rep.get("multiplicity", {})
if mult.get("correction") != "none" or mult.get("m_comparisons") != 1:
    bad(f"multiplicity mismatch: {mult}")
if not any("small-n: n_pairs=3 < 5" in w for w in rep.get("warnings", [])):
    bad(f"small-n warning missing: {rep.get('warnings')}")
acct = rep.get("accounting", {})
if acct.get("total_runs") != 6 or acct.get("paired_seeds") != 3:
    bad(f"accounting mismatch: {acct}")

# repro target (authoritative numbers) + drift vs authoritative file
exp_mean, exp_lo, exp_hi, exp_p = -0.12, -0.5939432689913657, 0.3539432689913657, 0.3897428467412706
if abs(rep["mean_diff"] - exp_mean) > 1e-9: bad(f"mean_diff {rep['mean_diff']} vs target {exp_mean}")
if abs(rep["mean_diff"] - auth["mean_diff"]) > 1e-9: bad("mean_diff drift vs authoritative run4")
for k in ("ci_lo", "ci_hi"):
    if abs(rep[k] - auth[k]) > 1e-6: bad(f"{k} drift vs authoritative: {rep[k]} vs {auth[k]}")
    exp = exp_lo if k == "ci_lo" else exp_hi
    if abs(rep[k] - exp) > 1e-6: bad(f"{k} {rep[k]} vs target {exp}")
if auth["p_value"] == 0:
    bad("authoritative p_value is 0")
rel = abs(rep["p_value"] - auth["p_value"]) / abs(auth["p_value"])
if rel > 1e-6: bad(f"p_value rel drift {rel}: {rep['p_value']} vs {auth['p_value']}")
rel_exp = abs(rep["p_value"] - exp_p) / abs(exp_p)
if rel_exp > 1e-6: bad(f"p_value vs target rel {rel_exp}")

# per-seed acc exact vs authoritative
a_by = {r["seed_data"]: r for r in auth["per_seed"]}
r_by = {r["seed_data"]: r for r in rep["per_seed"]}
if set(a_by) != {101, 202, 303} or set(r_by) != {101, 202, 303}:
    bad(f"seed set mismatch auth={sorted(a_by)} repro={sorted(r_by)}")
for s in (101, 202, 303):
    for k in ("baseline_acc", "treatment_acc"):
        if abs(r_by[s][k] - a_by[s][k]) > 1e-12:
            bad(f"seed {s} {k} drift: {r_by[s][k]} vs auth {a_by[s][k]}")

# overlap 0: paired same-inputs (baseline targets == treatment targets, n=50 each)
by_arm = {}
for r in repro_raw["runs"]:
    by_arm.setdefault((r["arm"], r["seed_data"]), r)
for s in (101, 202, 303):
    b, t = by_arm.get(("baseline", s)), by_arm.get(("treatment", s))
    if b is None or t is None: bad(f"missing paired runs seed {s}")
    if b["targets"] != t["targets"]: bad(f"unpaired targets seed {s} (same_inputs violated)")
    if not (len(b["predictions"]) == len(b["targets"]) == 50): bad(f"seed {s} baseline n != 50")
    if not (len(t["predictions"]) == len(t["targets"]) == 50): bad(f"seed {s} treatment n != 50")
# run_ids use the NEW repro run-id, never run2/3/4
for r in repro_raw["runs"]:
    rid = r["run_id"]
    if rid.startswith("run2:") or rid.startswith("run3:") or rid.startswith("run4:"):
        bad(f"repro run_id collides with reserved: {rid}")

# positive control 1.0 (all seeds)
for s in (101, 202, 303):
    m = json.loads(open(f"{run_dir}/seed-{s}/metrics.json", encoding="utf-8").read())
    if abs(float(m.get("positive_acc", -1)) - 1.0) > 1e-12:
        bad(f"seed {s} positive_acc={m.get('positive_acc')} want 1.0")

# determinism: predictions/targets bytes match authoritative (run_id prefix may differ)
def norm_runs(raw):
    out = {}
    for r in raw["runs"]:
        out[(r["arm"], r["seed_data"])] = (tuple(r["predictions"]), tuple(r["targets"]))
    return out
if norm_runs(repro_raw) != norm_runs(auth_raw):
    bad("repro predictions/targets differ from authoritative fixed-seed rerun")
PY

info "ok run_id=${RUN_ID}"
info "report match n_pairs=3 mean_diff=-0.12 CI=[-0.5939432689913657,0.3539432689913657] p=0.3897428467412706 overlap=0 positive_acc=1.0"
info "raw: ${RUN_DIR}/raw.json"
info "report: ${RUN_DIR}/report-t.json"
