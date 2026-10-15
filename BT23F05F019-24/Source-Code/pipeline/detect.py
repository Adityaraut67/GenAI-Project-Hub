"""Stage 2 — detection.

Sends the screenshot to the vision model with the taxonomy rubrics and returns
candidate findings. This stage is tuned for recall; verify.py tightens precision.
"""

from __future__ import annotations

from config import BBOX_SCALE
from taxonomy import PATTERN_IDS, detector_system_prompt, pattern_by_id

from .finding import Finding
from .llm import call_tool

DETECT_TOOL = {
    "name": "report_findings",
    "description": (
        "Report every dark pattern visible in the screenshot. Call with an empty findings "
        "list if the interface is honest."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "description": "One entry per distinct violation. Empty if none.",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "enum": PATTERN_IDS,
                            "description": "Taxonomy id of the pattern.",
                        },
                        "evidence": {
                            "type": "string",
                            "description": (
                                "Text quoted verbatim from the screenshot, or a short "
                                "description of the offending element if it has no text."
                            ),
                        },
                        "bbox": {
                            "type": "array",
                            "description": (
                                f"[x1, y1, x2, y2] normalised to 0-{BBOX_SCALE}, "
                                "tightly around the offending element."
                            ),
                            "items": {"type": "integer"},
                            "minItems": 4,
                            "maxItems": 4,
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Consumer harm if the user acts on this element.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": (
                                "Two sentences of plain language for a non-technical "
                                "consumer: what this does to the person using it."
                            ),
                        },
                        "confidence": {
                            "type": "number",
                            "description": (
                                "0.0-1.0. How firmly this screenshot alone establishes the "
                                "finding."
                            ),
                        },
                    },
                    "required": [
                        "pattern",
                        "evidence",
                        "bbox",
                        "severity",
                        "explanation",
                        "confidence",
                    ],
                },
            }
        },
        "required": ["findings"],
    },
}


def detect(image_block: dict, mode: str = "rubric") -> list[Finding]:
    """Find candidate dark patterns in one screenshot.

    mode="rubric" is the real system; "zero_shot" is the ablation baseline that
    withholds the inclusion/exclusion tests.
    """
    payload = call_tool(
        system=detector_system_prompt(mode),
        content=[
            image_block,
            {
                "type": "text",
                "text": (
                    "Audit this interface screenshot. Report only patterns you can anchor "
                    "to something visible in the image."
                ),
            },
        ],
        tool=DETECT_TOOL,
    )

    findings = [Finding.from_model(raw) for raw in payload.get("findings", [])]

    # Attach the provision reference from the taxonomy rather than trusting the
    # model to recite it — it is a legal citation and must be exact.
    for f in findings:
        spec = pattern_by_id(f.pattern)
        if spec:
            f.provision = f"CCPA Dark Patterns Guidelines 2023, {spec['provision_ref']}"
            # A pattern that cannot be settled from one frame gets its confidence
            # capped here too, in case the model ignored the instruction.
            if not spec["single_frame_decidable"]:
                f.confidence = min(f.confidence, 0.5)

    return findings
