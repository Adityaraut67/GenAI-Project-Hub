"""Stage 5a — the honest redesign.

For the worst confirmed finding, generate the repaired version of the element:
neutral copy, a concrete layout fix, and the consumer-protection principle the
fix restores. This is the output that makes the demo land — a side-by-side of
the deceptive element and its honest replacement.
"""

from __future__ import annotations

from taxonomy import pattern_by_id, rewrite_system_prompt

from .finding import Finding
from .llm import call_tool

REWRITE_TOOL = {
    "name": "report_rewrite",
    "description": "Return the honest replacement for the offending interface element.",
    "input_schema": {
        "type": "object",
        "properties": {
            "original_copy": {
                "type": "string",
                "description": "The manipulative copy as it currently appears.",
            },
            "honest_copy": {
                "type": "string",
                "description": (
                    "Neutral, accurate replacement wording, short enough to fit the same "
                    "space. Keeps the legitimate commercial intent."
                ),
            },
            "layout_fix": {
                "type": "array",
                "description": "One or two concrete changes a developer could implement.",
                "items": {"type": "string"},
            },
            "principle": {
                "type": "string",
                "enum": [
                    "informed consent",
                    "symmetric choice",
                    "price transparency",
                    "reversibility",
                ],
                "description": "The consumer-protection principle the fix restores.",
            },
            "note": {
                "type": "string",
                "description": (
                    "One sentence on what the business still legitimately achieves after "
                    "the fix."
                ),
            },
        },
        "required": ["original_copy", "honest_copy", "layout_fix", "principle"],
    },
}


def rewrite(image_block: dict, finding: Finding) -> dict:
    """Generate the honest version of one confirmed finding.

    The result is also stored on the finding itself so callers can serialise a
    single object.
    """
    spec = pattern_by_id(finding.pattern) or {}

    payload = call_tool(
        system=rewrite_system_prompt(),
        content=[
            image_block,
            {
                "type": "text",
                "text": (
                    "Confirmed finding to repair:\n\n"
                    f"  pattern:    {finding.pattern} ({spec.get('name', '')})\n"
                    f"  definition: {spec.get('definition', '').strip()}\n"
                    f"  evidence:   {finding.evidence!r}\n"
                    f"  region:     {finding.bbox}\n"
                    f"  why it is manipulative: {finding.explanation}\n\n"
                    "Produce the honest replacement for this element."
                ),
            },
        ],
        tool=REWRITE_TOOL,
        max_tokens=1024,
    )

    finding.honest_rewrite = payload
    return payload
