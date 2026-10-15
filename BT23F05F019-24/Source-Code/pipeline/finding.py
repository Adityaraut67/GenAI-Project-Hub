"""The Finding record — the single data structure the whole pipeline passes around."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from config import SEVERITY_ORDER


@dataclass
class Finding:
    """One detected dark pattern.

    bbox is in the normalised 0-BBOX_SCALE space the model is asked to use, as
    [x1, y1, x2, y2]. render/overlay.py converts to pixels.
    """

    pattern: str
    evidence: str
    bbox: list[int]
    severity: str
    explanation: str
    confidence: float
    provision: str = ""

    # Filled in by the verifier pass.
    verified: bool | None = None
    verifier_note: str = ""

    # Filled in by the DOM cross-check, when a live URL was audited.
    dom_corroboration: str = ""

    # Filled in by the rewriter.
    honest_rewrite: dict[str, Any] = field(default_factory=dict)

    @property
    def severity_rank(self) -> int:
        return SEVERITY_ORDER.get(self.severity, 99)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_model(cls, raw: dict[str, Any]) -> "Finding":
        """Build from a model tool-call payload, tolerating sloppy fields.

        The model is schema-constrained, but confidence occasionally arrives as a
        string and bboxes occasionally arrive as floats, so coerce rather than
        crash mid-audit.
        """
        bbox = raw.get("bbox") or [0, 0, 0, 0]
        try:
            bbox = [int(round(float(v))) for v in bbox][:4]
        except (TypeError, ValueError):
            bbox = [0, 0, 0, 0]
        while len(bbox) < 4:
            bbox.append(0)

        try:
            confidence = float(raw.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        severity = str(raw.get("severity", "medium")).lower()
        if severity not in SEVERITY_ORDER:
            severity = "medium"

        return cls(
            pattern=str(raw.get("pattern", "unknown")),
            evidence=str(raw.get("evidence", "")).strip(),
            bbox=bbox,
            severity=severity,
            explanation=str(raw.get("explanation", "")).strip(),
            confidence=max(0.0, min(1.0, confidence)),
            provision=str(raw.get("provision", "")),
        )
