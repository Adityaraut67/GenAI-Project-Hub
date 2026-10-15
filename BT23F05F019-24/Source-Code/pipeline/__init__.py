"""The audit pipeline.

    from pipeline import audit
    result = audit(screenshot_bytes)

Stages run in order: prepare -> detect -> verify -> DOM cross-check -> rewrite.
Each can be switched off, which is how the evaluation produces its ablation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from PIL import Image

from config import MODEL, TEMPERATURE
from imaging import prepare
from taxonomy import PROMPT_VERSION

from .detect import detect
from .dom_signals import DomSignal, corroborate, extract_signals, unmatched_signals
from .finding import Finding
from .rewrite import rewrite
from .verify import verify

__all__ = [
    "audit",
    "AuditResult",
    "Finding",
    "DomSignal",
    "detect",
    "verify",
    "rewrite",
    "extract_signals",
]


@dataclass
class AuditResult:
    findings: list[Finding] = field(default_factory=list)
    dropped: list[Finding] = field(default_factory=list)
    signals: list[DomSignal] = field(default_factory=list)
    missed_by_vision: list[DomSignal] = field(default_factory=list)
    image: Image.Image | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def clean(self) -> bool:
        return not self.findings

    @property
    def worst(self) -> Finding | None:
        """Highest-severity finding, breaking ties on confidence."""
        if not self.findings:
            return None
        return min(self.findings, key=lambda f: (f.severity_rank, -f.confidence))

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: (f.severity_rank, -f.confidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta,
            "findings": [f.to_dict() for f in self.sorted_findings()],
            "dropped": [f.to_dict() for f in self.dropped],
            "dom_signals": [s.__dict__ for s in self.signals],
            "missed_by_vision": [s.__dict__ for s in self.missed_by_vision],
        }


def audit(
    image_bytes: bytes,
    *,
    mode: str = "rubric",
    use_verifier: bool = True,
    html: str | None = None,
    do_rewrite: bool = True,
) -> AuditResult:
    """Audit one screenshot.

    mode          "rubric" (full taxonomy) or "zero_shot" (ablation baseline)
    use_verifier  run the adversarial second pass
    html          page source, when auditing a live URL, for the DOM cross-check
    do_rewrite    generate the honest redesign for the worst finding
    """
    started = time.perf_counter()
    image_block, original = prepare(image_bytes)

    candidates = detect(image_block, mode=mode)
    detect_count = len(candidates)

    if use_verifier:
        kept = verify(image_block, candidates)
        dropped = [f for f in candidates if f.verified is False]
    else:
        kept, dropped = candidates, []

    signals: list[DomSignal] = []
    missed: list[DomSignal] = []
    if html:
        signals = extract_signals(html)
        kept = corroborate(kept, signals)
        missed = unmatched_signals(kept, signals)

    result = AuditResult(
        findings=kept,
        dropped=dropped,
        signals=signals,
        missed_by_vision=missed,
        image=original,
    )

    if do_rewrite and result.worst is not None:
        rewrite(image_block, result.worst)

    result.meta = {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "prompt_version": PROMPT_VERSION,
        "mode": mode,
        "verifier": use_verifier,
        "dom_cross_check": bool(html),
        "image_size": list(original.size),
        "candidates_detected": detect_count,
        "findings_kept": len(kept),
        "findings_dropped": len(dropped),
        "elapsed_s": round(time.perf_counter() - started, 2),
    }
    return result
