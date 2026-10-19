"""Dark Pattern Auditor — Streamlit front end.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import json

import streamlit as st

from capture import CaptureError, capture
from config import MODEL
from pipeline import audit
from render import annotate, build_pdf
from render.overlay import SEVERITY_COLOUR
from taxonomy import PROMPT_VERSION, load_taxonomy

st.set_page_config(page_title="Dark Pattern Auditor", page_icon="🔍", layout="wide")

SEVERITY_BADGE = {
    sev: f"rgb({r},{g},{b})" for sev, (r, g, b) in SEVERITY_COLOUR.items()
}


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.subheader("Audit configuration")

    mode = st.radio(
        "Detector prompt",
        options=["rubric", "zero_shot"],
        format_func=lambda m: (
            "Full taxonomy (rubrics)" if m == "rubric" else "Zero-shot (ablation baseline)"
        ),
        help=(
            "Zero-shot withholds the inclusion/exclusion tests. Use it to show what the "
            "taxonomy is worth."
        ),
    )
    use_verifier = st.toggle(
        "Adversarial verifier",
        value=True,
        help="Second pass that re-examines each candidate and drops weak findings.",
    )
    do_rewrite = st.toggle("Generate honest redesign", value=True)

    st.divider()
    st.caption(f"Model `{MODEL}`")
    st.caption(f"Prompt version `{PROMPT_VERSION}`")

    with st.expander("The 13 patterns"):
        for p in load_taxonomy()["patterns"]:
            flag = "" if p["single_frame_decidable"] else " ⚠︎"
            st.markdown(f"**{p['name']}**{flag}  \n{p['definition'].strip()}")
        st.caption("⚠︎ cannot be settled from a single screenshot")


# --------------------------------------------------------------------------- #
# Header + input
# --------------------------------------------------------------------------- #
st.title("Dark Pattern Auditor")
st.markdown(
    "Audits an interface against the **CCPA Guidelines for Prevention and Regulation of "
    "Dark Patterns, 2023** — naming the tactic, boxing the offending element, and "
    "generating the honest version."
)

upload_tab, url_tab = st.tabs(["Upload a screenshot", "Capture a URL"])

image_bytes: bytes | None = None
html: str | None = None
source_label = "uploaded screenshot"

with upload_tab:
    uploaded = st.file_uploader("Screenshot of a checkout, signup or consent screen", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        image_bytes = uploaded.getvalue()
        source_label = uploaded.name

with url_tab:
    url = st.text_input("Public page URL", placeholder="https://example.com/checkout")
    st.caption(
        "Public pages only. robots.txt is honoured and captures are rate-limited. "
        "Never point this at a page behind a login."
    )
    if st.button("Capture and audit", disabled=not url):
        try:
            with st.spinner("Capturing page…"):
                image_bytes, html = capture(url)
            source_label = url
        except CaptureError as exc:
            st.error(str(exc))

run = st.button("Run audit", type="primary", disabled=image_bytes is None)

if image_bytes is None:
    st.info("Upload a screenshot or capture a URL to begin.")
    st.stop()

if not run and html is None:
    st.image(image_bytes, caption="Ready to audit", width=520)
    st.stop()


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
with st.spinner("Auditing interface…"):
    try:
        result = audit(
            image_bytes,
            mode=mode,
            use_verifier=use_verifier,
            html=html,
            do_rewrite=do_rewrite,
        )
    except Exception as exc:
        st.error(f"Audit failed: {exc}")
        st.stop()

findings = result.sorted_findings()

# --- Summary strip ---------------------------------------------------------
cols = st.columns(4)
cols[0].metric("Findings", len(findings))
cols[1].metric("High severity", sum(1 for f in findings if f.severity == "high"))
cols[2].metric("Rejected on review", len(result.dropped))
cols[3].metric("Time", f"{result.meta['elapsed_s']}s")

if result.clean:
    st.success(
        "No dark patterns detected in this frame. A clean result covers the captured frame "
        "only — subscription traps and drip pricing often appear later in a flow."
    )

st.divider()

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Annotated interface")
    st.image(annotate(result.image, findings), use_container_width=True)
    st.caption("Numbered regions correspond to the findings alongside.")

with right:
    st.subheader("Findings")
    if not findings:
        st.caption("Nothing flagged.")
    for i, f in enumerate(findings, start=1):
        colour = SEVERITY_BADGE.get(f.severity, "grey")
        st.markdown(
            f"<span style='background:{colour};color:white;padding:2px 8px;"
            f"border-radius:10px;font-size:0.75rem'>{i} · {f.severity}</span>"
            f" &nbsp;**{f.pattern.replace('_', ' ').title()}**",
            unsafe_allow_html=True,
        )
        st.markdown(f"> {f.evidence}")
        st.write(f.explanation)
        st.caption(f"{f.provision} · confidence {f.confidence:.2f}")
        if f.dom_corroboration:
            st.caption(f"✓ Confirmed in page source — {f.dom_corroboration}")
        if f.verified is None and use_verifier:
            st.caption("⚠︎ Not reviewed by the verifier.")
        st.markdown("")

# --- Honest redesign -------------------------------------------------------
rewritten = [f for f in findings if f.honest_rewrite]
if rewritten:
    st.divider()
    st.subheader("Honest redesign")
    for f in rewritten:
        hr = f.honest_rewrite
        st.caption(f"Repairing: {f.pattern.replace('_', ' ')}")
        before, after = st.columns(2)
        with before:
            st.markdown("**Currently**")
            st.error(hr.get("original_copy", f.evidence))
        with after:
            st.markdown("**Honest version**")
            st.success(hr.get("honest_copy", ""))
        for step in hr.get("layout_fix", []):
            st.markdown(f"- {step}")
        st.caption(f"Restores: **{hr.get('principle', '')}**. {hr.get('note', '')}")

# --- Transparency ----------------------------------------------------------
if result.dropped or result.missed_by_vision:
    st.divider()
    with st.expander("What the pipeline rejected or missed"):
        if result.dropped:
            st.markdown("**Candidates discarded by the verifier**")
            for f in result.dropped:
                st.markdown(
                    f"- *{f.pattern.replace('_', ' ')}* — “{f.evidence}” — {f.verifier_note}"
                )
        if result.missed_by_vision:
            st.markdown("**Proven in the page source but not seen in the image**")
            for s in result.missed_by_vision:
                st.markdown(f"- *{s.pattern_hint}* — {s.detail}")
            st.caption("These are detector recall failures worth reporting in the evaluation.")

# --- Export ----------------------------------------------------------------
st.divider()
dl1, dl2 = st.columns(2)
with dl1:
    st.download_button(
        "Download PDF report",
        data=build_pdf(result, source_label=source_label),
        file_name="dark-pattern-audit.pdf",
        mime="application/pdf",
    )
with dl2:
    st.download_button(
        "Download JSON",
        data=json.dumps(result.to_dict(), indent=2),
        file_name="dark-pattern-audit.json",
        mime="application/json",
    )

st.caption(
    "Model output, not a legal determination. Findings are indicative and require human "
    "review before being relied upon."
)
