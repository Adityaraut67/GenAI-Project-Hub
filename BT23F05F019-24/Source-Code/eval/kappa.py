"""Cohen's kappa for inter-annotator agreement.

Usage:
    python eval/kappa.py

Reads the two independent label files (labels-ayan.csv and labels-aditya.csv),
computes per-pattern and overall Cohen's kappa, and prints a report.

This is the number that goes into the submission — run it BEFORE reconciliation,
because agreement measured after discussion is meaningless.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from common import (
    ANNOTATORS,
    DATASET,
    DatasetError,
    label_sets,
    load_labels,
    load_manifest,
    RESULTS,
)
from common import SRC_DIR  # noqa: F401 — triggers sys.path setup
from taxonomy import PATTERN_IDS


def _kappa_interpretation(k: float) -> str:
    if k < 0.0:
        return "poor (worse than chance)"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


def compute_kappa(
    a_labels: pd.DataFrame,
    b_labels: pd.DataFrame,
    screenshots: list[str],
) -> dict:
    """Compute per-pattern and overall Cohen's kappa."""
    a_sets = label_sets(a_labels, screenshots=screenshots)
    b_sets = label_sets(b_labels, screenshots=screenshots)

    all_patterns = sorted(set(PATTERN_IDS))
    per_pattern = {}

    # Build a binary matrix for overall kappa: rows = (screenshot × pattern),
    # columns = [annotator_a, annotator_b]
    all_a = []
    all_b = []

    for pat in all_patterns:
        y_a = [1 if pat in a_sets[s] else 0 for s in screenshots]
        y_b = [1 if pat in b_sets[s] else 0 for s in screenshots]
        all_a.extend(y_a)
        all_b.extend(y_b)

        # Per-pattern kappa (only meaningful if there is variance)
        if len(set(y_a)) > 1 or len(set(y_b)) > 1:
            k = cohen_kappa_score(y_a, y_b)
        else:
            # Both annotators agree on every screenshot — perfect but trivial
            k = 1.0 if y_a == y_b else 0.0
        agree = sum(1 for a, b in zip(y_a, y_b) if a == b)
        per_pattern[pat] = {
            "kappa": round(k, 4),
            "agreement_pct": round(100 * agree / len(screenshots), 1),
            "a_positive": sum(y_a),
            "b_positive": sum(y_b),
            "both_positive": sum(a and b for a, b in zip(y_a, y_b)),
        }

    overall = cohen_kappa_score(all_a, all_b)

    # Screenshot-level: did they agree on the *set* of patterns?
    exact_match = sum(
        1 for s in screenshots if a_sets[s] == b_sets[s]
    )

    return {
        "overall_kappa": round(overall, 4),
        "exact_match_pct": round(100 * exact_match / len(screenshots), 1),
        "per_pattern": per_pattern,
        "n_screenshots": len(screenshots),
    }


def main():
    print("Inter-annotator agreement (Cohen's κ)")
    print("=" * 60)

    try:
        manifest = load_manifest()
    except DatasetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    screenshots = list(manifest["screenshot"])

    labels = {}
    for name, path in ANNOTATORS.items():
        try:
            labels[name] = load_labels(path)
        except DatasetError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

    names = list(ANNOTATORS.keys())
    result = compute_kappa(labels[names[0]], labels[names[1]], screenshots)

    interp = _kappa_interpretation(result["overall_kappa"])
    print(f"\n  Overall κ = {result['overall_kappa']:.4f}  ({interp})")
    print(f"  Exact set match: {result['exact_match_pct']:.1f}% of screenshots")
    print(f"  Screenshots: {result['n_screenshots']}")
    print()

    header = f"  {'Pattern':<28} {'κ':>8} {'Agree%':>8} {'A+':>4} {'B+':>4} {'Both+':>6}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for pat, m in sorted(result["per_pattern"].items()):
        interp_short = _kappa_interpretation(m["kappa"])[:4]
        print(
            f"  {pat:<28} {m['kappa']:>8.4f} {m['agreement_pct']:>7.1f}% "
            f"{m['a_positive']:>4} {m['b_positive']:>4} {m['both_positive']:>6}"
        )
    print()

    # Identify the weakest patterns — these go in the Results discussion
    weak = [
        (pat, m["kappa"])
        for pat, m in result["per_pattern"].items()
        if m["kappa"] < 0.60 and (m["a_positive"] + m["b_positive"]) > 0
    ]
    if weak:
        print("  Patterns with κ < 0.60 (weakest agreement):")
        for pat, k in sorted(weak, key=lambda x: x[1]):
            print(f"    - {pat}: κ = {k:.4f}")
        print(
            "  These patterns are the hardest for humans to agree on and set the ceiling\n"
            "  for model performance. Discuss them in the Results section."
        )
    else:
        print("  All patterns with positive examples have κ ≥ 0.60. Strong agreement.")

    # Save
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [{"pattern": pat, **m} for pat, m in result["per_pattern"].items()]
    pd.DataFrame(rows).to_csv(RESULTS / "kappa_per_pattern.csv", index=False)

    summary = {k: v for k, v in result.items() if k != "per_pattern"}
    import json
    (RESULTS / "kappa_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"\n  Results saved to {RESULTS}/")
    print(
        "\n  ⚠  This number must be computed BEFORE reconciliation.\n"
        "     If you have already discussed disagreements, the kappa is\n"
        "     artificially inflated and should not be reported."
    )


if __name__ == "__main__":
    main()
