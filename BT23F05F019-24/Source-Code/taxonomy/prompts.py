"""Prompt construction from the YAML taxonomy.

Three prompts matter here:

  detector  — finds candidate dark patterns in a screenshot
  verifier  — adversarially re-examines each candidate and drops weak ones
  rewriter  — produces the honest redesign for a confirmed finding

`detector_system_prompt(mode=...)` is the ablation switch. "zero_shot" deliberately
withholds the rubrics so the evaluation can show what the taxonomy is worth.

Every prompt is hashed into PROMPT_VERSION. Log it with each result: if the hash
changes, previously collected numbers are no longer comparable.
"""

from __future__ import annotations

import functools
import hashlib
from typing import Any, Literal

import yaml

from config import BBOX_SCALE, TAXONOMY_PATH

DetectorMode = Literal["zero_shot", "rubric"]


@functools.lru_cache(maxsize=1)
def load_taxonomy() -> dict[str, Any]:
    with open(TAXONOMY_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@functools.lru_cache(maxsize=1)
def _patterns() -> list[dict[str, Any]]:
    return load_taxonomy()["patterns"]


PATTERN_IDS: list[str] = [p["id"] for p in _patterns()]


def pattern_by_id(pattern_id: str) -> dict[str, Any] | None:
    return next((p for p in _patterns() if p["id"] == pattern_id), None)


def _render_rubrics() -> str:
    """Turn the YAML into the rubric block the detector reasons against.

    The exclusion test and the single-frame flag are the two fields doing real
    work: the first suppresses false positives on lawful lookalikes, the second
    tells the model when a static screenshot simply cannot settle the question.
    """
    blocks = []
    for p in _patterns():
        undecidable = "" if p["single_frame_decidable"] else (
            "\n  CANNOT BE SETTLED FROM ONE FRAME: a single screenshot is weak evidence for this\n"
            "  pattern. You may still report it, but cap confidence at 0.5 and say in the\n"
            "  explanation what further observation would be needed to establish it."
        )
        blocks.append(
            f"""### {p['id']}  —  {p['name']}
  Provision: {p['provision_ref']}
  Definition: {p['definition'].strip()}
  FLAG IT WHEN: {p['inclusion_test'].strip()}
  DO NOT FLAG: {p['exclusion_test'].strip()}
  Violating example:    {p['positive_example']}
  Lawful lookalike:     {p['negative_example']}
  Default severity: {p['default_severity']}{undecidable}"""
        )
    return "\n\n".join(blocks)


_DETECTOR_PREAMBLE = """You audit user interfaces for manipulative design, in the role of a \
consumer-protection analyst applying India's CCPA Guidelines for Prevention and Regulation of \
Dark Patterns, 2023.

You will be shown one screenshot of an interface. Report the dark patterns actually visible in it.

How to behave:

- Quote evidence verbatim from the screenshot. Never paraphrase interface copy, and never report
  a finding you cannot anchor to something visible in the image.
- A persuasive interface is not automatically an unlawful one. Marketing is lawful; deception is
  not. When a design is merely assertive, do not report it.
- Precision matters more than coverage here. A false accusation against a compliant interface is
  a worse error than missing a borderline pattern. If you are unsure, omit it.
- Report each distinct violation once. Do not split one manipulative element into several findings.
- If the screenshot contains no dark patterns, return an empty findings list. This is a normal and
  expected outcome; some interfaces are honest.

Coordinates: give every bounding box in a normalised integer space of 0-{scale}, where [0,0] is the
top-left of the image and [{scale},{scale}] the bottom-right, ordered [x1, y1, x2, y2]. Box the
specific offending element, not the whole page.

Explanations are read by non-technical consumers. Say what the design does to the person using it,
in two sentences of plain language. No jargon, no restating the category name.
"""


def detector_system_prompt(mode: DetectorMode = "rubric") -> str:
    """Build the detector prompt.

    mode="rubric"    full taxonomy with inclusion/exclusion tests (the real system)
    mode="zero_shot" category names only (ablation baseline)
    """
    base = _DETECTOR_PREAMBLE.format(scale=BBOX_SCALE)

    if mode == "zero_shot":
        return (
            base
            + "\nClassify anything you find into one of these categories:\n"
            + "\n".join(f"- {p['id']} ({p['name']})" for p in _patterns())
        )

    return (
        base
        + "\nThe thirteen prohibited patterns, each with the test for flagging it and the lawful\n"
        "lookalike that must not be flagged:\n\n"
        + _render_rubrics()
    )


_VERIFIER_PROMPT = """You are the second reviewer on a dark-pattern audit, and your job is to \
throw out weak findings.

A first-pass detector has proposed the findings below for the attached screenshot. Detectors of
this kind over-report: they mistake ordinary visual hierarchy for interface interference, read
truthful scarcity as false urgency, and flag labelled advertising as disguised advertising.

Judge each finding independently. Keep it only if all of these hold:

1. The quoted evidence genuinely appears in the screenshot. If you cannot find that text or
   element, drop the finding.
2. The evidence actually satisfies the category's inclusion test, rather than merely resembling it.
3. The lawful lookalike for that category has been ruled out. State how you ruled it out.
4. A reasonable consumer would be misled or pressured by it — not merely advertised to.

Default to dropping. Keeping a wrong finding is the expensive error; losing a marginal one is not.

For each finding return a verdict of "keep" or "drop", a one-sentence justification naming the
decisive reason, and — for kept findings — a corrected confidence in 0.0-1.0 reflecting how firmly
the screenshot alone establishes it.
"""


def verifier_system_prompt() -> str:
    return _VERIFIER_PROMPT


_REWRITE_PROMPT = """You repair manipulative interfaces.

Given a screenshot and one confirmed dark-pattern finding, produce the honest version of the
offending element.

Constraints:

- Preserve the business's legitimate goal. An honest interface may still sell, advertise, charge a
  fee, or run a subscription. What it may not do is mislead or coerce. Do not simply delete the
  commercial intent.
- Rewrite the copy into neutral, accurate wording a consumer can act on. Keep it short enough to
  fit the same space.
- Describe the layout or affordance change in one or two concrete steps a developer could
  implement — which control to untick by default, what to disclose and where, which element needs
  equal visual weight.
- Name the principle the fix restores: informed consent, symmetric choice, price transparency, or
  reversibility.
"""


def rewrite_system_prompt() -> str:
    return _REWRITE_PROMPT


def _version_hash() -> str:
    payload = "".join(
        [
            detector_system_prompt("rubric"),
            detector_system_prompt("zero_shot"),
            _VERIFIER_PROMPT,
            _REWRITE_PROMPT,
            str(load_taxonomy().get("version")),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


PROMPT_VERSION: str = _version_hash()
