"""Evaluation charts — the visual evidence in the Results section.

Usage:
    python eval/charts.py

Reads the per-pattern and summary CSVs/JSONs produced by run_eval.py and
generates publication-ready charts:

  1. Three-bar ablation chart (macro-F1: zero_shot → rubric → rubric_verifier)
  2. Per-pattern F1 heatmap across all three configurations
  3. Precision-recall scatter per pattern (rubric_verifier config)
  4. Control false-positive rate comparison
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from common import RESULTS, SRC_DIR  # noqa: F401

CONFIGS = ["zero_shot", "rubric", "rubric_verifier"]
CONFIG_LABELS = {
    "zero_shot": "Zero-shot",
    "rubric": "+ Taxonomy rubrics",
    "rubric_verifier": "+ Rubrics + Verifier",
}
CONFIG_COLOURS = {
    "zero_shot": "#7B8FA1",
    "rubric": "#5B9BD5",
    "rubric_verifier": "#2E75B6",
}

# Sensible defaults for publication-quality figures
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
    "font.family": "sans-serif",
})


def _load_summaries() -> dict:
    out = {}
    for cfg in CONFIGS:
        p = RESULTS / f"{cfg}_summary.json"
        if p.exists():
            out[cfg] = json.loads(p.read_text(encoding="utf-8"))
    return out


def _load_per_pattern() -> dict[str, pd.DataFrame]:
    out = {}
    for cfg in CONFIGS:
        p = RESULTS / f"{cfg}_per_pattern.csv"
        if p.exists():
            out[cfg] = pd.read_csv(p)
    return out


def chart_ablation_bars(summaries: dict) -> None:
    """Three-bar ablation chart — the headline result."""
    available = [c for c in CONFIGS if c in summaries]
    if not available:
        print("  ⚠ No summaries found — run run_eval.py first.")
        return

    fig, axes = plt.subplots(1, 3, figsize=(10, 4.5), sharey=False)

    metrics = [
        ("macro_f1", "Macro-F1", (0, 1)),
        ("screenshot_accuracy", "Screenshot Accuracy", (0, 1)),
        ("control_fp_rate", "Control FP Rate ↓", (0, 1)),
    ]

    for ax, (key, label, ylim) in zip(axes, metrics):
        vals = []
        colours = []
        labels = []
        for cfg in available:
            v = summaries[cfg].get(key)
            vals.append(v if v is not None else 0)
            colours.append(CONFIG_COLOURS.get(cfg, "#999999"))
            labels.append(CONFIG_LABELS.get(cfg, cfg))

        bars = ax.bar(range(len(vals)), vals, color=colours, width=0.6, edgecolor="white")
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        ax.set_ylim(ylim)
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

        # Value labels on bars
        for bar, val in zip(bars, vals):
            if val is not None:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.02,
                    f"{val:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

    fig.suptitle("Ablation: Effect of Taxonomy Rubrics and Verifier", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = RESULTS / "ablation_bars.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out}")


def chart_per_pattern_heatmap(per_pattern: dict[str, pd.DataFrame]) -> None:
    """Per-pattern F1 as a heatmap across configurations."""
    available = [c for c in CONFIGS if c in per_pattern]
    if len(available) < 1:
        return

    # Build the matrix
    patterns = sorted(per_pattern[available[0]]["pattern"].unique())
    data = np.full((len(patterns), len(available)), np.nan)

    for j, cfg in enumerate(available):
        df = per_pattern[cfg].set_index("pattern")
        for i, pat in enumerate(patterns):
            if pat in df.index:
                v = df.loc[pat, "f1"]
                data[i, j] = v if pd.notna(v) else np.nan

    fig, ax = plt.subplots(figsize=(max(6, len(available) * 2.5), max(5, len(patterns) * 0.4)))
    im = ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(len(available)))
    ax.set_xticklabels([CONFIG_LABELS.get(c, c) for c in available], fontsize=9)
    ax.set_yticks(range(len(patterns)))
    ax.set_yticklabels([p.replace("_", " ").title() for p in patterns], fontsize=9)

    # Annotate cells
    for i in range(len(patterns)):
        for j in range(len(available)):
            v = data[i, j]
            if np.isnan(v):
                ax.text(j, i, "—", ha="center", va="center", fontsize=8, color="#999")
            else:
                colour = "white" if v < 0.4 or v > 0.85 else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8, color=colour)

    ax.set_title("Per-Pattern F1 Across Configurations", fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, label="F1 Score", shrink=0.8)
    fig.tight_layout()
    out = RESULTS / "per_pattern_heatmap.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out}")


def chart_precision_recall_scatter(per_pattern: dict[str, pd.DataFrame]) -> None:
    """Precision vs recall scatter for the best configuration."""
    # Use the most complete config available
    for cfg in reversed(CONFIGS):
        if cfg in per_pattern:
            df = per_pattern[cfg].copy()
            break
    else:
        return

    df = df.dropna(subset=["precision", "recall"])
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 6))

    # F1 iso-lines
    for f1_target in [0.2, 0.4, 0.6, 0.8]:
        r_range = np.linspace(0.01, 1.0, 200)
        p_from_f1 = f1_target * r_range / (2 * r_range - f1_target)
        valid = (p_from_f1 >= 0) & (p_from_f1 <= 1)
        ax.plot(r_range[valid], p_from_f1[valid], "--", color="#ddd", linewidth=0.8)
        # Label the iso-line
        idx = np.argmin(np.abs(r_range - 0.95))
        if valid[idx]:
            ax.annotate(
                f"F1={f1_target}",
                (r_range[idx], p_from_f1[idx]),
                fontsize=7,
                color="#bbb",
            )

    scatter = ax.scatter(
        df["recall"],
        df["precision"],
        s=df["support"] * 30 + 40,
        c=df["f1"],
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
        edgecolors="white",
        linewidths=1.2,
        zorder=5,
    )

    for _, row in df.iterrows():
        ax.annotate(
            row["pattern"].replace("_", " "),
            (row["recall"], row["precision"]),
            fontsize=7,
            xytext=(5, 5),
            textcoords="offset points",
        )

    ax.set_xlabel("Recall", fontsize=11)
    ax.set_ylabel("Precision", fontsize=11)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(
        f"Precision vs Recall by Pattern ({CONFIG_LABELS.get(cfg, cfg)})",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_aspect("equal")
    fig.colorbar(scatter, ax=ax, label="F1 Score", shrink=0.8)
    fig.tight_layout()
    out = RESULTS / "precision_recall_scatter.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out}")


def chart_control_fp(summaries: dict) -> None:
    """Control false-positive rate bar."""
    available = [c for c in CONFIGS if c in summaries]
    if not available:
        return

    vals = [summaries[c].get("control_fp_rate", 0) or 0 for c in available]
    labels = [CONFIG_LABELS.get(c, c) for c in available]
    colours = [CONFIG_COLOURS.get(c, "#999") for c in available]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.barh(range(len(vals)), vals, color=colours, height=0.5, edgecolor="white")
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, max(1, max(vals) * 1.3 if vals else 1))
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_title("False-Positive Rate on Clean Controls ↓", fontsize=11, fontweight="bold")

    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.0%}",
            va="center",
            fontsize=9,
        )

    fig.tight_layout()
    out = RESULTS / "control_fp_rate.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {out}")


def main():
    print("Generating evaluation charts…")
    print(f"Reading from: {RESULTS}")
    print()

    summaries = _load_summaries()
    per_pattern = _load_per_pattern()

    if not summaries and not per_pattern:
        print("ERROR: No results found. Run eval/run_eval.py first.", file=sys.stderr)
        sys.exit(1)

    chart_ablation_bars(summaries)
    chart_per_pattern_heatmap(per_pattern)
    chart_precision_recall_scatter(per_pattern)
    chart_control_fp(summaries)

    print(f"\nAll charts saved to {RESULTS}/")


if __name__ == "__main__":
    main()
