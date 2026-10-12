"""Stage 3 — adversarial verification.

The detector over-reports: ordinary visual hierarchy reads as interface
interference, truthful scarcity reads as false urgency, labelled ads read as
disguised ones. This pass re-examines each candidate against the image and drops
the ones that do not hold up.

This is the precision lever, and the third bar in the ablation chart.
"""

from __future__ import annotations

from taxonomy import pattern_by_id, verifier_system_prompt

from .finding import Finding
from .llm import call_tool

VERIFY_TOOL = {
    "name": "report_verdicts",
    "description": "Return one verdict for every candidate finding, by index.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": "Index of the candidate finding being judged.",
                        },
                        "verdict": {
                            "type": "string",
                            "enum": ["keep", "drop"],
                        },
                        "justification": {
                            "type": "string",
                            "description": (
                                "One sentence naming the decisive reason. For a keep, say how "
                                "the lawful lookalike was ruled out. For a drop, say which "
                                "test failed."
                            ),
                        },
                        "corrected_confidence": {
                            "type": "number",
                            "description": "0.0-1.0, for kept findings.",
                        },
                    },
                    "required": ["index", "verdict", "justification"],
                },
            }
        },
        "required": ["verdicts"],
    },
}


def _describe_candidates(findings: list[Finding]) -> str:
    lines = []
    for i, f in enumerate(findings):
        spec = pattern_by_id(f.pattern)
        lines.append(
            f"[{i}] pattern={f.pattern}\n"
            f"     evidence quoted: {f.evidence!r}\n"
            f"     region (0-1000): {f.bbox}\n"
            f"     detector reasoning: {f.explanation}\n"
            f"     inclusion test: {(spec or {}).get('inclusion_test', 'n/a').strip()}\n"
            f"     lawful lookalike to rule out: "
            f"{(spec or {}).get('exclusion_test', 'n/a').strip()}"
        )
    return "\n\n".join(lines)


def verify(image_block: dict, findings: list[Finding]) -> list[Finding]:
    """Return only the findings that survive review, annotated with the reason.

    Dropped findings are discarded from the returned list but the verifier note
    is attached first, so a caller holding the original list can still inspect
    why something was rejected.
    """
    if not findings:
        return []

    payload = call_tool(
        system=verifier_system_prompt(),
        content=[
            image_block,
            {
                "type": "text",
                "text": (
                    "Candidate findings to review against this screenshot:\n\n"
                    + _describe_candidates(findings)
                    + "\n\nReturn exactly one verdict per index."
                ),
            },
        ],
        tool=VERIFY_TOOL,
    )

    verdicts = {}
    for v in payload.get("verdicts", []):
        try:
            verdicts[int(v["index"])] = v
        except (KeyError, TypeError, ValueError):
            continue

    kept: list[Finding] = []
    for i, f in enumerate(findings):
        v = verdicts.get(i)
        if v is None:
            # The verifier skipped this one. Keep it rather than silently losing a
            # finding to an omission, but mark it unreviewed so it is visible in
            # the report and excluded from precision claims about the verifier.
            f.verified = None
            f.verifier_note = "Not reviewed — verifier returned no verdict for this finding."
            kept.append(f)
            continue

        f.verifier_note = str(v.get("justification", "")).strip()
        if str(v.get("verdict", "")).lower() == "keep":
            f.verified = True
            if v.get("corrected_confidence") is not None:
                try:
                    f.confidence = max(0.0, min(1.0, float(v["corrected_confidence"])))
                except (TypeError, ValueError):
                    pass
            # Re-apply the single-frame cap; the verifier may have raised it.
            spec = pattern_by_id(f.pattern)
            if spec and not spec["single_frame_decidable"]:
                f.confidence = min(f.confidence, 0.5)
            kept.append(f)
        else:
            f.verified = False

    return kept
