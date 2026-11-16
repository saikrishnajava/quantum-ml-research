#!/usr/bin/env bash
# Analysis-only paired report over an existing raw.json (default: authoritative run4).
# No runner, no training, no mutation of raw. Analyzer refuses invalid input
# via its own exit codes (0 ok, 1 data/validation failure, 2 usage error).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

INPUT="${1:-research/artifacts/equality-actual-v2/run4/raw.json}"
OUTPUT="${2:-/tmp/opencode/actual-repro-check/report-t.json}"

[ -f "$INPUT" ] || { echo "FAIL: input not found: $INPUT" >&2; exit 2; }
mkdir -p "$(dirname "$OUTPUT")"

.venv/bin/python scripts/analyze_results.py \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --method t \
  --multiplicity none

.venv/bin/python -m json.tool "$OUTPUT" > /dev/null \
  || { echo "FAIL: output is not valid JSON: $OUTPUT" >&2; exit 1; }

echo "ok input=${INPUT} output=${OUTPUT}"
