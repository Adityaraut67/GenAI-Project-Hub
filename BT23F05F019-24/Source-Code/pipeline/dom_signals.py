"""Stage 4 — DOM cross-check.

Only runs for URL inputs. This is deliberately *not* a model call: it looks for
hard, mechanical evidence in the page source that either corroborates or
undercuts what the vision model claimed to see.

Having two independent evidence types — one perceptual, one structural — is what
lets the report distinguish "the model thinks this box looks pre-ticked" from
"this input carries the checked attribute."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from .finding import Finding

# Copy that signals a consent or marketing opt-in.
_CONSENT_WORDS = re.compile(
    r"\b(consent|agree|subscribe|newsletter|marketing|promotion|offers|terms|"
    r"insurance|warranty|protection|donat|tip|auto[- ]?renew)\w*",
    re.I,
)

# "do not ... not", "untick ... not" and friends — the trap-question shape.
_DOUBLE_NEGATIVE = re.compile(
    r"\b(?:do\s+not|don'?t|un(?:tick|check)|opt\s+out)\b[^.?!]{0,60}?\b"
    r"(?:not|never|no longer|stop)\b",
    re.I,
)

_TIMER_HINT = re.compile(r"(countdown|timer|time[- ]?left|expires?[- ]?in|deal[- ]?end)", re.I)
_CLOCK_TEXT = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")

_HIDDEN_STYLE = re.compile(
    r"(display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?!\.)|"
    r"font-size\s*:\s*[0-5](?:\.\d+)?px)",
    re.I,
)


@dataclass
class DomSignal:
    kind: str
    pattern_hint: str
    detail: str


def extract_signals(html: str) -> list[DomSignal]:
    """Scan page source for structural evidence of dark patterns."""
    soup = BeautifulSoup(html, "html.parser")
    signals: list[DomSignal] = []

    # 1. Pre-ticked opt-ins. The single most mechanically checkable pattern.
    for box in soup.find_all("input", {"type": re.compile("^checkbox$", re.I)}):
        if not box.has_attr("checked"):
            continue
        label = _label_for(soup, box)
        hint = "saas_billing" if re.search(r"auto[- ]?renew|subscri", label, re.I) else "basket_sneaking"
        signals.append(
            DomSignal(
                kind="pre_checked_input",
                pattern_hint=hint,
                detail=f"Checkbox is checked by default: {label[:120]!r}",
            )
        )

    # 2. Consent text that exists in the DOM but is hidden or sub-legible.
    for el in soup.find_all(style=_HIDDEN_STYLE):
        text = el.get_text(" ", strip=True)
        if text and _CONSENT_WORDS.search(text):
            signals.append(
                DomSignal(
                    kind="suppressed_disclosure",
                    pattern_hint="interface_interference",
                    detail=f"Consent/charge text hidden by inline style: {text[:120]!r}",
                )
            )

    # 3. Countdown machinery. A timer in the markup does not prove false urgency —
    #    it proves there is a clock to re-check on reload, which is the test.
    for el in soup.find_all(
        lambda t: t.has_attr("class") and _TIMER_HINT.search(" ".join(t.get("class", [])))
        or t.has_attr("id") and _TIMER_HINT.search(t.get("id", ""))
    ):
        text = el.get_text(" ", strip=True)
        if _CLOCK_TEXT.search(text) or _TIMER_HINT.search(text):
            signals.append(
                DomSignal(
                    kind="countdown_element",
                    pattern_hint="false_urgency",
                    detail=(
                        f"Countdown element present ({text[:60]!r}). Reload the page and "
                        "compare: a timer that resets is fabricated urgency."
                    ),
                )
            )
            break  # one is enough; carousels repeat them

    # 4. Inverted-polarity consent wording.
    for lbl in soup.find_all(["label", "span", "p"]):
        text = lbl.get_text(" ", strip=True)
        if text and _DOUBLE_NEGATIVE.search(text) and _CONSENT_WORDS.search(text):
            signals.append(
                DomSignal(
                    kind="inverted_consent_wording",
                    pattern_hint="trap_question",
                    detail=f"Consent control uses negated phrasing: {text[:120]!r}",
                )
            )

    return signals


def _label_for(soup: BeautifulSoup, box) -> str:
    """Best-effort label text for a checkbox."""
    if box.has_attr("id"):
        lbl = soup.find("label", {"for": box["id"]})
        if lbl:
            return lbl.get_text(" ", strip=True)
    parent_label = box.find_parent("label")
    if parent_label:
        return parent_label.get_text(" ", strip=True)
    if box.has_attr("aria-label"):
        return box["aria-label"]
    if box.has_attr("name"):
        return box["name"]
    return "(unlabelled checkbox)"


def corroborate(findings: list[Finding], signals: list[DomSignal]) -> list[Finding]:
    """Annotate findings that the page source independently supports."""
    by_pattern: dict[str, list[DomSignal]] = {}
    for s in signals:
        by_pattern.setdefault(s.pattern_hint, []).append(s)

    for f in findings:
        matches = by_pattern.get(f.pattern, [])
        if matches:
            f.dom_corroboration = " | ".join(m.detail for m in matches[:2])
            # Structural confirmation is strong evidence, so lift confidence —
            # but never past the single-frame cap for undecidable patterns.
            f.confidence = min(1.0, max(f.confidence, 0.8))

    return findings


def unmatched_signals(findings: list[Finding], signals: list[DomSignal]) -> list[DomSignal]:
    """Signals the vision model missed — i.e. detector recall failures.

    Worth surfacing in the report and in the evaluation write-up: these are cases
    where the page source proves a pattern the model did not see.
    """
    seen = {f.pattern for f in findings}
    return [s for s in signals if s.pattern_hint not in seen]
