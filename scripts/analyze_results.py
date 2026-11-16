"""Pure analysis CLI: raw-only paired analyzer.

Reads a raw results file only, validates it fail-closed, computes paired
statistics (treatment minus baseline accuracy, paired by ``seed_data``),
writes a deterministic JSON report, and prints a human report to stdout.

Pure: ``analyze()`` performs no I/O; all file/network side effects live in
``main()``. No embedded constants steer the outcome — every number in the
report derives from the input file plus the CLI-chosen statistical method.

Exit map: 0 = ok, 1 = data/validation failure, 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from scipy import stats as _scipy_stats
except Exception:  # pragma: no cover - fallback path
    _scipy_stats = None

EXIT_OK = 0
EXIT_DATA = 1
EXIT_USAGE = 2

ARMS = ("baseline", "treatment")
METHODS = ("t", "normal")
MULTIPLICITY = ("bonferroni", "none")
NORMAL_Z = 1.96  # 95% two-sided normal quantile; statistical method constant
SMALL_N = 5


class ValidationError(Exception):
    """Fail-closed input validation error (maps to exit 1)."""


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_run(run: object, index: int) -> dict:
    if not isinstance(run, dict):
        raise ValidationError(f"runs[{index}]: must be an object")
    for field in ("run_id", "arm", "seed_data", "predictions", "targets"):
        if field not in run:
            raise ValidationError(f"runs[{index}]: missing field '{field}'")
    if not isinstance(run["run_id"], str) or not run["run_id"]:
        raise ValidationError(f"runs[{index}]: 'run_id' must be a non-empty string")
    if run["arm"] not in ARMS:
        raise ValidationError(
            f"runs[{index}]: 'arm' must be one of {list(ARMS)}, got {run['run_id']!r}"
        )
    seed = run["seed_data"]
    if not isinstance(seed, (int, str)) or isinstance(seed, bool):
        raise ValidationError(f"runs[{index}]: 'seed_data' must be an int or string")
    for field in ("predictions", "targets"):
        values = run[field]
        if not isinstance(values, list) or not values:
            raise ValidationError(f"runs[{index}]: '{field}' must be a non-empty list")
        for value in values:
            if not _is_int(value):
                raise ValidationError(
                    f"runs[{index}]: '{field}' must contain finite ints only"
                )
    if len(run["predictions"]) != len(run["targets"]):
        raise ValidationError(
            f"runs[{index}]: predictions/targets length mismatch "
            f"({len(run['predictions'])} != {len(run['targets'])})"
        )
    return run


def _validate_raw(raw: object, method: str) -> dict:
    if not isinstance(raw, dict):
        raise ValidationError("input must be a JSON object")
    if "protocol" not in raw or not isinstance(raw["protocol"], str) or not raw["protocol"]:
        raise ValidationError("missing or empty 'protocol'")
    if "config_hash" not in raw or not isinstance(raw["config_hash"], str) or not raw["config_hash"]:
        raise ValidationError("missing or empty 'config_hash'")
    if "runs" not in raw or not isinstance(raw["runs"], list) or not raw["runs"]:
        raise ValidationError("'runs' must be a non-empty list")
    if "method" in raw:
        if raw["method"] not in METHODS:
            raise ValidationError(f"input 'method' must be one of {list(METHODS)}")
        if raw["method"] != method:
            raise ValidationError(
                f"input 'method' ({raw['method']!r}) conflicts with --method ({method!r})"
            )
    runs = [_validate_run(run, i) for i, run in enumerate(raw["runs"])]
    by_arm: dict[str, dict[tuple, dict]] = {arm: {} for arm in ARMS}
    for run in runs:
        key = (type(run["seed_data"]).__name__, run["seed_data"])
        arm_runs = by_arm[run["arm"]]
        if key in arm_runs:
            raise ValidationError(
                f"duplicate seed_data {run['seed_data']!r} in arm '{run['arm']}'"
            )
        arm_runs[key] = run
    for arm in ARMS:
        if not by_arm[arm]:
            raise ValidationError(f"arm '{arm}' has no runs; paired arms required")
    base_keys = set(by_arm["baseline"])
    treat_keys = set(by_arm["treatment"])
    if base_keys != treat_keys:
        missing = sorted(repr(k[1]) for k in base_keys ^ treat_keys)
        raise ValidationError(f"unpaired seed_data sets; symmetric difference: {missing}")
    return {"protocol": raw["protocol"], "config_hash": raw["config_hash"], "by_arm": by_arm}


def _accuracy(predictions: list, targets: list) -> float:
    return sum(p == t for p, t in zip(predictions, targets)) / len(predictions)


def _ci_and_p(diffs: list[float], method: str) -> tuple:
    """Return (mean, lo, hi, p_value, method_used). lo/hi/p may be None if n < 2."""
    n = len(diffs)
    mean = sum(diffs) / n
    if n < 2:
        return mean, None, None, None, f"{method} (n=1: interval/p-value undefined)"
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    se = math.sqrt(var / n)
    if method == "t" and _scipy_stats is not None:
        crit = float(_scipy_stats.t.ppf(0.975, n - 1))
        t_stat = mean / se if se > 0 else 0.0
        p_value = float(2.0 * _scipy_stats.t.sf(abs(t_stat), n - 1)) if se > 0 else 1.0
        return mean, mean - crit * se, mean + crit * se, p_value, "t (scipy, 95%)"
    if method == "t":
        method_used = "normal (fallback: scipy unavailable, 95%)"
    else:
        method_used = "normal (1.96, 95%)"
    z = NORMAL_Z
    if se > 0:
        p_value = float(2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(mean / se) / math.sqrt(2.0)))))
    else:
        p_value = 1.0
    return mean, mean - z * se, mean + z * se, p_value, method_used


def analyze(raw: object, *, method: str, multiplicity: str) -> dict:
    """Pure analysis: validated raw input -> deterministic report dict. No I/O."""
    if method not in METHODS:
        raise ValidationError(f"method must be one of {list(METHODS)}")
    if multiplicity not in MULTIPLICITY:
        raise ValidationError(f"multiplicity must be one of {list(MULTIPLICITY)}")
    validated = _validate_raw(raw, method)
    by_arm = validated["by_arm"]
    seed_keys = sorted(by_arm["baseline"], key=lambda k: repr(k[1]))
    per_seed = []
    for key in seed_keys:
        base = by_arm["baseline"][key]
        treat = by_arm["treatment"][key]
        base_acc = _accuracy(base["predictions"], base["targets"])
        treat_acc = _accuracy(treat["predictions"], treat["targets"])
        per_seed.append(
            {
                "seed_data": key[1],
                "baseline_run_id": base["run_id"],
                "treatment_run_id": treat["run_id"],
                "baseline_acc": base_acc,
                "treatment_acc": treat_acc,
                "diff": treat_acc - base_acc,
            }
        )
    diffs = [row["diff"] for row in per_seed]
    n = len(diffs)
    mean, lo, hi, p_value, method_used = _ci_and_p(diffs, method)
    warnings = []
    if n < SMALL_N:
        warnings.append(f"small-n: n_pairs={n} < {SMALL_N}; interval is wide, treat as preliminary")
    if multiplicity == "none":
        interpretation = "exploratory (no multiplicity correction)"
    else:
        interpretation = "bonferroni, m=1 (single paired comparison; no numeric adjustment)"
    return {
        "protocol": validated["protocol"],
        "config_hash": validated["config_hash"],
        "method_requested": method,
        "method_used": method_used,
        "pairing": "paired by seed_data across arms ['baseline', 'treatment']",
        "n_pairs": n,
        "per_seed": per_seed,
        "mean_diff": mean,
        "ci_lo": lo,
        "ci_hi": hi,
        "p_value": p_value,
        "multiplicity": {
            "correction": multiplicity,
            "m_comparisons": 1,
            "interpretation": interpretation,
        },
        "warnings": warnings,
        "accounting": {
            "total_runs": sum(len(by_arm[arm]) for arm in ARMS),
            "per_arm": {arm: len(by_arm[arm]) for arm in ARMS},
            "paired_seeds": n,
            "excluded_runs": [],
        },
    }


def format_human(report: dict) -> str:
    lines = [
        "paired analysis report",
        f"protocol: {report['protocol']}",
        f"config_hash: {report['config_hash']}",
        f"method: {report['method_used']} (requested: {report['method_requested']})",
        f"pairing: {report['pairing']}",
        f"n_pairs: {report['n_pairs']}",
        f"mean_diff (treatment - baseline): {report['mean_diff']:.4f}",
    ]
    if report["ci_lo"] is None:
        lines.append("95% CI: undefined (n=1)")
    else:
        lines.append(f"95% CI: [{report['ci_lo']:.4f}, {report['ci_hi']:.4f}]")
    lines.append(
        "p_value: " + ("undefined (n=1)" if report["p_value"] is None else f"{report['p_value']:.4g}")
    )
    lines.append(f"multiplicity: {report['multiplicity']['interpretation']}")
    for warning in report["warnings"]:
        lines.append(f"warning: {warning}")
    lines.append("per-seed diffs:")
    for row in report["per_seed"]:
        lines.append(
            f"  seed_data={row['seed_data']!r} "
            f"baseline={row['baseline_acc']:.4f} treatment={row['treatment_acc']:.4f} "
            f"diff={row['diff']:+.4f}"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pure raw-only paired analyzer. Exits 0 ok, 1 data/validation "
        "failure, 2 usage error."
    )
    parser.add_argument("--input", required=True, help="path to raw results JSON")
    parser.add_argument("--output", required=True, help="path for deterministic JSON report")
    parser.add_argument("--method", required=True, choices=list(METHODS),
                        help="CI method: t (scipy) or normal (1.96)")
    parser.add_argument("--multiplicity", required=True, choices=list(MULTIPLICITY),
                        help="bonferroni or none (none labels the result exploratory)")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return EXIT_USAGE
    try:
        raw = json.loads(input_path.read_text())
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot parse input JSON: {exc}", file=sys.stderr)
        return EXIT_DATA
    try:
        report = analyze(raw, method=args.method, multiplicity=args.multiplicity)
    except ValidationError as exc:
        print(f"error: invalid input: {exc}", file=sys.stderr)
        return EXIT_DATA
    try:
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    except OSError as exc:
        print(f"error: cannot write output: {exc}", file=sys.stderr)
        return EXIT_DATA
    sys.stdout.write(format_human(report))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
