"""Shared dataset loading for the evaluation scripts.

Importing this also puts Source-Code/ on sys.path, so the eval scripts can be run
from either the project root or the eval directory:

    python eval/run_eval.py
    cd eval && python run_eval.py
"""

from __future__ import annotations

import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
SRC_DIR = EVAL_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd  # noqa: E402

DATASET = EVAL_DIR / "dataset"
IMAGES = DATASET / "images"
CACHE = EVAL_DIR / "cache"
RESULTS = EVAL_DIR / "results"

MANIFEST = DATASET / "manifest.csv"
GOLD = DATASET / "labels-final.csv"
ANNOTATORS = {
    "ayan": DATASET / "labels-ayan.csv",
    "aditya": DATASET / "labels-aditya.csv",
}

LABEL_COLUMNS = ["screenshot", "pattern", "evidence", "severity", "uncertain", "notes"]


class DatasetError(RuntimeError):
    pass


def load_manifest() -> pd.DataFrame:
    if not MANIFEST.exists():
        raise DatasetError(
            f"{MANIFEST} not found. Copy manifest.example.csv to manifest.csv and fill it in — "
            "see ANNOTATION-GUIDE.md."
        )
    df = pd.read_csv(MANIFEST)
    missing = {"screenshot", "group"} - set(df.columns)
    if missing:
        raise DatasetError(f"manifest.csv is missing column(s): {sorted(missing)}")
    df["group"] = df["group"].str.strip().str.lower()
    bad = set(df["group"]) - {"deceptive", "control"}
    if bad:
        raise DatasetError(f"manifest.csv has unknown group value(s): {sorted(bad)}")
    return df


def load_labels(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DatasetError(f"{path} not found — see ANNOTATION-GUIDE.md.")
    df = pd.read_csv(path)
    for col in LABEL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["screenshot"] = df["screenshot"].astype(str).str.strip()
    df["pattern"] = df["pattern"].astype(str).str.strip()
    df["uncertain"] = (
        df["uncertain"].astype(str).str.strip().str.lower().isin(["yes", "y", "true", "1"])
    )
    return df


def label_sets(
    labels: pd.DataFrame, *, screenshots: list[str], include_uncertain: bool = True
) -> dict[str, set[str]]:
    """screenshot -> set of pattern ids.

    Every screenshot in `screenshots` is present, mapping to an empty set when it
    carries no labels. That is what makes a clean control screenshot countable.
    """
    if not include_uncertain:
        labels = labels[~labels["uncertain"]]
    out: dict[str, set[str]] = {s: set() for s in screenshots}
    for row in labels.itertuples():
        if row.screenshot in out:
            out[row.screenshot].add(row.pattern)
    return out


def validate(manifest: pd.DataFrame, labels: pd.DataFrame, known_patterns: set[str]) -> list[str]:
    """Return a list of dataset problems. Empty list means the dataset is sound."""
    problems = []

    known_shots = set(manifest["screenshot"])
    for shot in set(labels["screenshot"]) - known_shots:
        problems.append(f"label references unknown screenshot: {shot}")

    for pat in set(labels["pattern"]) - known_patterns:
        problems.append(f"label uses unknown pattern id: {pat}")

    if IMAGES.exists():
        on_disk = {p.name for p in IMAGES.iterdir() if p.is_file()}
        for shot in known_shots - on_disk:
            problems.append(f"manifest lists a file not in images/: {shot}")

    controls = manifest[manifest["group"] == "control"]["screenshot"]
    labelled_controls = set(controls) & set(labels["screenshot"])
    for shot in sorted(labelled_controls):
        problems.append(
            f"control screenshot carries a label: {shot} "
            "(controls are expected clean — move it to the deceptive group if the label is right)"
        )

    return problems
