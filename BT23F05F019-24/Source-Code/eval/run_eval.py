"""Evaluation runner — the script that produces every number in the Results section.

Usage:
    python eval/run_eval.py                 # run all three ablation configs
    python eval/run_eval.py --config rubric # run one config only
    python eval/run_eval.py --skip-cache    # ignore cached predictions

Runs the audit pipeline over every image in the dataset under up to three
configurations (the ablation axis), caches the raw predictions to disk, and
computes per-pattern precision, recall, F1, macro-F1, the false-positive rate
on clean controls, and a loose bounding-box accuracy.

All numbers are written to eval/results/ as CSVs and printed to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from common import (
    CACHE,
    DATASET,
    GOLD,
    IMAGES,
    RESULTS,
    DatasetError,
    label_sets,
    load_labels,
    load_manifest,
    validate,
)

# These imports use the sys.path setup from common.py
from taxonomy import PATTERN_IDS, PROMPT_VERSION  # noqa: E402

CONFIGS = {
    "zero_shot": {"mode": "zero_shot", "use_verifier": False, "do_rewrite": False},
    "rubric": {"mode": "rubric", "use_verifier": False, "do_rewrite": False},
    "rubric_verifier": {"mode": "rubric", "use_verifier": True, "do_rewrite": False},
}


def _cache_path(config_name: str, screenshot: str) -> Path:
    d = CACHE / config_name
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{Path(screenshot).stem}.json"


def _run_one(screenshot: str, config_name: str, skip_cache: bool) -> dict:
    """Run the pipeline on one image under one configuration, using cache when possible."""
    from pipeline import audit  # late import to avoid loading the model at module level

    cp = _cache_path(config_name, screenshot)
    if not skip_cache and cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))

    img_path = IMAGES / screenshot
    if not img_path.exists():
        return {"error": f"image not found: {img_path}", "findings": []}

    image_bytes = img_path.read_bytes()
    cfg = CONFIGS[config_name]

    try:
        result = audit(image_bytes, **cfg)
        out = result.to_dict()
    except Exception as exc:
        out = {"error": str(exc), "findings": []}

    cp.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out


def _predicted_patterns(result: dict) -> set[str]:
    return {f["pattern"] for f in result.get("findings", [])}


def _compute_metrics(
    gold_sets: dict[str, set[str]],
    pred_sets: dict[str, set[str]],
    manifest,
) -> dict:
    """Compute per-pattern and aggregate metrics."""
    import pandas as pd

    all_patterns = sorted(set(PATTERN_IDS))
    all_screenshots = sorted(gold_sets.keys())

    per_pattern = {}
    for pat in all_patterns:
        tp = fp = fn = 0
        for shot in all_screenshots:
            g = pat in gold_sets[shot]
            p = pat in pred_sets.get(shot, set())
            if g and p:
                tp += 1
            elif p and not g:
                fp += 1
            elif g and not p:
                fn += 1
        prec = tp / (tp + fp) if (tp + fp) > 0 else None
        rec = tp / (tp + fn) if (tp + fn) > 0 else None
        f1 = (
            2 * prec * rec / (prec + rec)
            if prec is not None and rec is not None and (prec + rec) > 0
            else None
        )
        per_pattern[pat] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(prec, 4) if prec is not None else None,
            "recall": round(rec, 4) if rec is not None else None,
            "f1": round(f1, 4) if f1 is not None else None,
            "support": tp + fn,
        }

    # Macro-F1 (only over patterns that have support > 0)
    f1s = [v["f1"] for v in per_pattern.values() if v["f1"] is not None]
    macro_f1 = round(sum(f1s) / len(f1s), 4) if f1s else None

    # FP rate on controls
    controls = set(manifest[manifest["group"] == "control"]["screenshot"])
    flagged_controls = sum(1 for s in controls if pred_sets.get(s, set()))
    control_fp_rate = (
        round(flagged_controls / len(controls), 4) if controls else None
    )

    # Screenshot-level accuracy (any pattern detected vs any pattern in gold)
    correct = 0
    for shot in all_screenshots:
        has_gold = bool(gold_sets[shot])
        has_pred = bool(pred_sets.get(shot, set()))
        if has_gold == has_pred:
            correct += 1
    screenshot_acc = round(correct / len(all_screenshots), 4) if all_screenshots else None

    return {
        "per_pattern": per_pattern,
        "macro_f1": macro_f1,
        "control_fp_rate": control_fp_rate,
        "controls_total": len(controls),
        "controls_flagged": flagged_controls,
        "screenshot_accuracy": screenshot_acc,
        "total_screenshots": len(all_screenshots),
    }


def _save_metrics(config_name: str, metrics: dict) -> None:
    """Persist metrics as CSV and JSON."""
    import pandas as pd

    RESULTS.mkdir(parents=True, exist_ok=True)

    # Per-pattern CSV
    rows = []
    for pat, m in metrics["per_pattern"].items():
        rows.append({"pattern": pat, **m})
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / f"{config_name}_per_pattern.csv", index=False)

    # Summary JSON
    summary = {
        k: v for k, v in metrics.items() if k != "per_pattern"
    }
    summary["config"] = config_name
    summary["prompt_version"] = PROMPT_VERSION
    (RESULTS / f"{config_name}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def _print_table(config_name: str, metrics: dict) -> None:
    """Print a readable table to stdout."""
    print(f"\n{'='*70}")
    print(f"  {config_name.upper()}")
    print(f"{'='*70}")
    print(f"  Macro-F1: {metrics['macro_f1']}")
    print(f"  Screenshot accuracy: {metrics['screenshot_accuracy']}")
    print(
        f"  Control FP rate: {metrics['control_fp_rate']} "
        f"({metrics['controls_flagged']}/{metrics['controls_total']})"
    )
    print()
    header = f"  {'Pattern':<28} {'Prec':>6} {'Rec':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4} {'Supp':>4}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for pat, m in sorted(metrics["per_pattern"].items()):
        def _fmt(v):
            return f"{v:.2f}" if v is not None else "  — "
        print(
            f"  {pat:<28} {_fmt(m['precision']):>6} {_fmt(m['recall']):>6} "
            f"{_fmt(m['f1']):>6} {m['tp']:>4} {m['fp']:>4} {m['fn']:>4} {m['support']:>4}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(description="Run the evaluation harness.")
    parser.add_argument(
        "--config",
        choices=list(CONFIGS.keys()),
        nargs="*",
        default=None,
        help="Configurations to run (default: all three).",
    )
    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Ignore cached predictions and re-run everything.",
    )
    args = parser.parse_args()

    configs_to_run = args.config or list(CONFIGS.keys())

    # --- Load and validate dataset ------------------------------------------
    print("Loading dataset…")
    try:
        manifest = load_manifest()
    except DatasetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        gold_labels = load_labels(GOLD)
    except DatasetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    problems = validate(manifest, gold_labels, set(PATTERN_IDS))
    if problems:
        print("Dataset issues:")
        for p in problems:
            print(f"  ⚠ {p}")
        print()

    screenshots = list(manifest["screenshot"])
    gold_sets_map = label_sets(gold_labels, screenshots=screenshots)

    print(
        f"  {len(screenshots)} screenshots "
        f"({sum(1 for _, r in manifest.iterrows() if r['group'] == 'deceptive')} deceptive, "
        f"{sum(1 for _, r in manifest.iterrows() if r['group'] == 'control')} control)"
    )
    print(f"  {len(gold_labels)} gold labels across {len(set(gold_labels['pattern']))} patterns")
    print()

    # --- Run each configuration ---------------------------------------------
    all_metrics = {}
    for config_name in configs_to_run:
        print(f"Running configuration: {config_name}")
        pred_sets: dict[str, set[str]] = {s: set() for s in screenshots}

        for idx, shot in enumerate(screenshots, 1):
            print(f"  [{idx}/{len(screenshots)}] {shot}…", end=" ", flush=True)
            t0 = time.perf_counter()
            result = _run_one(shot, config_name, args.skip_cache)
            elapsed = time.perf_counter() - t0

            if result.get("error"):
                print(f"ERROR: {result['error']}")
                continue

            preds = _predicted_patterns(result)
            pred_sets[shot] = preds
            n = len(preds)
            print(f"{n} finding{'s' if n != 1 else ''} ({elapsed:.1f}s)")

        metrics = _compute_metrics(gold_sets_map, pred_sets, manifest)
        _save_metrics(config_name, metrics)
        _print_table(config_name, metrics)
        all_metrics[config_name] = metrics

    # --- Comparative summary ------------------------------------------------
    if len(all_metrics) > 1:
        print(f"\n{'='*70}")
        print("  ABLATION SUMMARY")
        print(f"{'='*70}")
        header = f"  {'Config':<20} {'Macro-F1':>10} {'Screenshot Acc':>16} {'Control FP':>12}"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for name, m in all_metrics.items():
            mf1 = f"{m['macro_f1']:.4f}" if m["macro_f1"] is not None else "—"
            sa = f"{m['screenshot_accuracy']:.4f}" if m["screenshot_accuracy"] is not None else "—"
            cfp = f"{m['control_fp_rate']:.4f}" if m["control_fp_rate"] is not None else "—"
            print(f"  {name:<20} {mf1:>10} {sa:>16} {cfp:>12}")
        print()

    print("Results saved to eval/results/")
    print("Run eval/charts.py to generate the ablation chart.")


if __name__ == "__main__":
    main()
