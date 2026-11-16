#!/usr/bin/env bash
# Row 1 one-command repro (Track C bounded pilots, fail-open, no gate).
# Auth: user continue-with-next. Caps: local CPU only, <=15m wall.
# Run-once locked tests are EXCLUDED (asserted below via split pattern).
# No errexit (fail-open): every per-test pytest carries || true (P1 exit 1 expected RED).
RAW="benchmarks/results/track-c-repro.jsonl"
mkdir -p "$(dirname "$RAW")"
: > "$RAW"
A="confirm"
B="atory"
PAT="${A}${B}"
if printf '%s\n' tests/test_p2_redo.py tests/test_pilots_overlap.py tests/test_pilots_moe_cost.py tests/test_phase1_1_guards.py tests/test_phase1_correctness_guards.py | grep -q "$PAT"; then
  echo "FAIL: excluded test referenced in test list"
  exit 1
fi
if grep -q "$PAT" "$0"; then
  echo "FAIL: excluded test referenced in script"
  exit 1
fi
run_one() {
  t="$1"
  .venv/bin/python -m pytest -s -q "$t" 2>&1 | tail -n 20 || true
  code="${PIPESTATUS[0]}"
  printf '{"test":"%s","seed":"all","metric":"exit_code","value":%d,"exit":%d}\n' "$t" "$code" "$code" >> "$RAW" || true
  echo "--- $t exit=$code ---" || true
}
run_one "tests/test_p2_redo.py" || true
run_one "tests/test_pilots_overlap.py" || true
run_one "tests/test_pilots_moe_cost.py" || true
run_one "tests/test_phase1_1_guards.py" || true
run_one "tests/test_phase1_correctness_guards.py" || true
echo "--- RAW tail ($RAW) ---" || true
tail -n 20 "$RAW" || true
