# Dark Pattern Auditor

An AI auditor that looks at a user interface the way a consumer-protection regulator would: it finds
manipulative design, names the tactic, cites the rule it breaks, and rewrites the interface honestly.

> Status: **Working prototype.** Pipeline, Streamlit UI, PDF export, and evaluation harness are
> built. Pending: dataset collection, labelling, and final results.

---

## Team Members

| # | Name | Roll No. | Primary Responsibility |
|---|------|----------|------------------------|
| 1 | Ayan Farooque | BT23F05F019 | Taxonomy rubrics, prompt engineering, verifier pass, DOM cross-check, annotation & dataset collection |
| 2 | Aditya | BT23F05F024 | Capture pipeline, Streamlit UI, overlay renderer, PDF report, evaluation harness, charts & results |

Both members contributed to all phases of the project; the table reflects primary ownership, not
exclusive authorship.

---

## Problem Statement

Online interfaces routinely use **dark patterns** — design choices that manipulate users into
spending more, consenting to more, or staying subscribed longer than they intended. A pre-ticked
insurance add-on, a countdown timer that resets on reload, an unsubscribe button labelled
*"No thanks, I enjoy paying full price"*: none of these are bugs. They are deliberate.

India's Central Consumer Protection Authority (CCPA) responded with the **Guidelines for Prevention
and Regulation of Dark Patterns, 2023**, which name and prohibit **13 specific patterns**. But
enforcement today depends on *manual human review of screenshots*. That approach is slow,
inconsistent between reviewers, and cannot keep pace with the number of interfaces that need
checking. Meanwhile the consumer being manipulated has no way to recognise it in the moment.

**The gap:** there is no accessible tool that can look at an interface and explain, in plain language
and against a legal taxonomy, how it is manipulating the person using it.

### Why this needs Generative AI

This problem resists conventional automation, and that is the point:

- **It is not keyword matching.** *"Only 2 left in stock!"* is helpful if true and illegal if
  fabricated. The same string is compliant or non-compliant depending on context.
- **It is not a CSS rule.** Interface interference works through visual hierarchy — a greyed-out
  decline button beside a saturated accept button. Both are valid CSS.
- **It requires pragmatic reasoning.** Detecting confirm shaming means recognising *shame as a
  persuasion mechanism* in a sentence that is otherwise grammatically unremarkable.
- **The output must be explanatory.** A severity score is not useful to a consumer; an explanation
  of the manipulation is.

Joint visual + linguistic + intent reasoning over an image is precisely what a vision-language model
provides and what a classifier or rule engine cannot.

---

## Objectives

1. Detect and localise dark patterns in a UI screenshot against the 13-category CCPA taxonomy.
2. Produce, for each finding, a structured audit record: tactic, evidence quoted from the interface,
   region, severity, the provision it implicates, and a plain-language explanation.
3. Generate an **honest redesign** — rewritten copy and corrected affordances for the worst offender.
4. Corroborate visual findings with hard DOM evidence where a live URL is available.
5. Measure detection quality on a hand-labelled dataset with inter-annotator agreement, and report
   per-pattern precision and recall rather than anecdotes.

---

## Proposed Solution

A screenshot (or a URL) goes in. A structured compliance audit comes out.

```
┌──────────────┐
│ Screenshot   │   or   URL ──► Playwright capture ──► full-page PNG + DOM dump
│   upload     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 1. PRE-PROCESS                                          │
│    downscale to model limits, retain original           │
│    coordinate space for overlay rescaling               │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 2. DETECTOR  (vision-language model)                    │
│    13-pattern rubric + few-shot positive/negative       │
│    examples ──► strict JSON array of candidate findings  │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 3. VERIFIER  (second, adversarial pass)                 │
│    re-reads image + each candidate, must justify why    │
│    the claim is deceptive ──► keep / drop                │
│    → this is the precision lever, and an ablation axis   │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 4. DOM CROSS-CHECK  (URL inputs only)                   │
│    pre-checked inputs, display:none consent text,       │
│    timers that reset across reloads, injected           │
│    cart items ──► corroborates or contradicts findings   │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 5. REPORT                                               │
│    annotated image · severity-ranked findings table ·   │
│    generated honest rewrite · exportable PDF            │
└─────────────────────────────────────────────────────────┘
```

### The taxonomy

Detection targets the 13 patterns prohibited by the CCPA guidelines: *false urgency, basket
sneaking, confirm shaming, forced action, subscription trap, interface interference, bait and
switch, drip pricing, disguised advertisement, nagging, trap question, SaaS billing,* and *rogue
malware.* Each is encoded in the prompt as a rubric with an inclusion test, an exclusion test, and
one positive and one negative example — the exclusion tests are what keep legitimate urgency and
legitimate advertising from being flagged.

> **To verify before citing:** reproduce the exact category names and wording from the official
> CCPA notification (30 November 2023) rather than from secondary sources, since the audit output
> quotes the provision.

### Finding schema

```json
{
  "pattern": "confirm_shaming",
  "evidence": "No thanks, I'd rather pay full price",
  "bbox": [412, 889, 690, 921],
  "severity": "high",
  "provision": "CCPA Dark Patterns Guidelines 2023, Annexure I(3)",
  "explanation": "The decline option is phrased to make refusing feel foolish, attaching a social cost to the free choice rather than describing it neutrally.",
  "honest_rewrite": "No thanks",
  "confidence": 0.86
}
```

---

## Technologies Used

| Layer | Choice | Why |
|-------|--------|-----|
| Reasoning | Groq or Anthropic Claude, behind one pluggable client factory | Vision + schema-constrained tool calling. `config.py` selects the provider from whichever API key is present, so the pipeline is not tied to either vendor |
| Capture | Playwright (headless Chromium) | Full-page screenshots and DOM dump in one pass |
| Annotation | Pillow | Draw bounding boxes and labels on the original image |
| Interface | Streamlit | Fastest route to a demonstrable UI |
| Evaluation | pandas, scikit-learn, matplotlib | Metrics, agreement, result charts |
| Reporting | ReportLab | Exportable PDF audit |

Deliberately boring infrastructure. The novelty is the task, not the stack.

---

## Implementation

**To install and run, see [Source-Code/README.md](Source-Code/README.md).** In short: one virtual
environment, `pip install -r requirements.txt`, one API key in `.env`, then
`streamlit run app.py`.

```text
Source-Code/
├── app.py                       # Streamlit entry point — upload or URL → full audit
├── config.py                    # Central config: model, temperature, paths, bbox scale
├── imaging.py                   # Image load, downscale, base64 encoding for API calls
│
├── capture/
│   └── screenshot.py            # Playwright capture: robots.txt, rate-limit, full-page PNG + DOM
│
├── taxonomy/
│   ├── patterns.yaml            # The 13 CCPA rubrics with inclusion/exclusion tests
│   └── prompts.py               # Versioned detector, verifier and rewriter system prompts
│
├── pipeline/
│   ├── __init__.py              # audit() orchestrator — the main entry point
│   ├── finding.py               # Finding dataclass with severity, bbox, confidence, rewrite
│   ├── llm.py                   # Thin wrapper: image + tool schema → structured JSON
│   ├── detect.py                # Stage 2: vision model finds candidate dark patterns
│   ├── verify.py                # Stage 3: adversarial second pass prunes false positives
│   ├── dom_signals.py           # Stage 4: structural DOM checks (pre-checked boxes, hidden text)
│   └── rewrite.py               # Stage 5: honest-redesign generator for the worst finding
│
├── render/
│   ├── overlay.py               # Pillow: draw severity-coloured bounding boxes + labels
│   └── report.py                # ReportLab PDF: annotated image, findings table, rewrite
│
└── eval/
    ├── ANNOTATION-GUIDE.md      # Labelling rules, schema, procedure, ethics
    ├── common.py                # Shared dataset loading, validation, label_sets()
    ├── run_eval.py              # Runs all three ablation configs, computes P/R/F1, macro-F1
    ├── kappa.py                 # Cohen's κ for inter-annotator agreement
    ├── charts.py                # Ablation bars, per-pattern heatmap, P-R scatter, control FP
    └── dataset/
        ├── images/              # Captured PNGs (not committed — see .gitignore)
        ├── manifest.csv         # Provenance for every image
        ├── labels-ayan.csv      # Independent labels
        ├── labels-aditya.csv    # Independent labels
        └── labels-final.csv     # Reconciled gold standard
```

### Key design decisions

- **Schema-constrained tool calls, not free-text JSON.** Every model call declares a JSON-Schema
  tool and forces the model to call it, which is more reliable than asking for JSON in prose.
- **Normalised bounding boxes (0–1000).** The model never sees real pixel dimensions; `overlay.py`
  scales them back. This decouples detection from resolution.
- **Prompt versioning.** A SHA-256 hash of all three prompts plus the taxonomy version is logged
  with every result. If the hash changes, prior numbers are invalidated.
- **Temperature pinned to 0** for reproducibility across evaluation runs.
- **Prediction caching.** `run_eval.py` caches per-image results to disk so re-running the
  evaluation after adding a chart does not re-call the API.

---

## Evaluation Plan

Results are a separately scored criterion, so this is treated as a first-class part of the project
rather than an afterthought.

**Dataset.** 60–80 screenshots: live public e-commerce, travel, ticketing and food-delivery flows,
plus a set of **clean controls** (government portals, minimal interfaces) that contain no dark
patterns. Controls exist to measure the false-positive rate — a detector that flags everything is
worthless, and only controls expose that.

**Annotation.** Two team members label every screenshot independently against the 13 categories,
then reconcile. **Cohen's kappa** is reported for inter-annotator agreement, which also establishes
how hard the task is for humans — the honest ceiling for the model.

**Metrics.** Per-pattern precision / recall / F1, macro-F1 across categories, false-positive rate on
clean controls, and loose bounding-box accuracy (did it point at the right region).

**Ablations.** Three configurations, which become the central results chart:

1. Zero-shot prompt ("find dark patterns in this image")
2. + full taxonomy rubric with exclusion tests
3. + adversarial verifier pass

The expected story is that rubrics lift recall and the verifier lifts precision. If the data says
otherwise, that is the more interesting finding and gets reported as such.

**Expected failure modes**, to be examined rather than hidden: *interface interference* (needs fine
visual-salience judgement), *disguised advertisement* (depends on knowing what is sponsored), and
*false urgency* (genuinely undecidable from a single frame — a timer needs two observations to be
proven fake). These limitations are reported, not papered over.

---

## Results / Output

The evaluation harness (`eval/run_eval.py`) runs the full pipeline over the labelled dataset in
three configurations — the ablation axis — and reports:

| Metric | What it measures |
|--------|------------------|
| Per-pattern precision | Of the instances flagged for this pattern, how many were correct? |
| Per-pattern recall | Of the instances labelled for this pattern, how many were found? |
| Per-pattern F1 | Harmonic mean of the above |
| Macro-F1 | Average F1 across all patterns with support > 0 |
| Screenshot accuracy | Binary: did it correctly classify the screenshot as clean / deceptive? |
| Control FP rate | Fraction of clean control screenshots that received any finding |
| Cohen's κ | Inter-annotator agreement between Ayan and Aditya, overall and per-pattern |

### Ablation configurations

1. **Zero-shot** — the model is told the 13 category names but given no rubrics or examples.
2. **+ Taxonomy rubrics** — full inclusion/exclusion tests, positive/negative examples.
3. **+ Rubrics + Verifier** — an adversarial second pass re-examines and can drop weak findings.

The expected story: rubrics lift recall (the model knows what to look for) and the verifier lifts
precision (it removes false alarms). Charts are generated by `eval/charts.py`:

- `ablation_bars.png` — three-bar macro-F1 comparison (the headline result)
- `per_pattern_heatmap.png` — F1 by pattern across configurations
- `precision_recall_scatter.png` — per-pattern precision vs recall
- `control_fp_rate.png` — false-positive rate on clean controls

_Numeric results will be filled in after the dataset is labelled and the evaluation is run._

## Screenshots

See [`../Screenshots/`](../Screenshots/), which contains eight captures covering the app before an
audit, a completed annotated audit, a single finding in detail, the honest-redesign panel, a clean
control returning nothing, the verifier's rejected candidates, a page of the exported PDF, and the
ablation chart. [Screenshots/README.md](../Screenshots/README.md) lists the exact filenames and the
capture rules (resolution, PII blurring, brand anonymisation).

---

## Scope Boundaries

Explicitly **out of scope**, to keep the project small and finishable:

- Browser extension packaging (listed under Future Scope instead)
- Multi-step flow or video analysis — single-frame audit only
- Native mobile app teardown
- Languages beyond English and Hindi interface copy
- Any automated enforcement action or report filing

## Ethical and Legal Considerations

- Only **publicly reachable pages** are captured. No authenticated flows, no checkout completion,
  no personal data; any incidental PII is blurred before the screenshot enters the dataset.
- Findings are **model output, not legal determinations.** Every report carries that disclaimer.
- For the presentation and public demo, brand marks are anonymised where a finding is disputable.
  The subject of this project is the pattern, not any particular company.
- Capture is rate-limited and respects `robots.txt`.

## Future Scope

- Browser extension that audits the page the user is actually on, in real time
- Flow-level auditing across a multi-step checkout, which would make false urgency and subscription
  traps properly decidable
- Regional language output with voice, for users who are most exposed to these patterns
- A longitudinal tracker measuring whether a given site's patterns change after regulation

## References

### Regulation

1. Central Consumer Protection Authority. *Guidelines for Prevention and Regulation of Dark
   Patterns, 2023.* Ministry of Consumer Affairs, Food and Public Distribution, Government of
   India. Notified 30 November 2023. — the source of the 13-category taxonomy in
   `taxonomy/patterns.yaml`, and of every `provision` string the auditor emits.
2. OECD. *Dark Commercial Patterns.* OECD Digital Economy Papers, 2022. — international context
   and the economic harm framing.

### Prior work on dark patterns

3. Mathur, A., Acar, G., Friedman, M. J., Lucherini, E., Mayer, J., Chetty, M., & Narayanan, A.
   *Dark Patterns at Scale: Findings from a Crawl of 11K Shopping Websites.* Proceedings of the ACM
   on Human-Computer Interaction, 3(CSCW), Article 81, 2019. — the automated-detection precedent;
   their crawl-based approach is what a vision-language model replaces.
4. Gray, C. M., Kou, Y., Battles, B., Hoggatt, J., & Toombs, A. L. *The Dark (Patterns) Side of UX
   Design.* Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems, Paper
   534, 2018. — the practitioner-intent framing behind our inclusion/exclusion test structure.
5. Brignull, H. *Deceptive Design* (formerly darkpatterns.org). — the original pattern taxonomy
   that the regulatory categories descend from.

### Evaluation methodology

6. Cohen, J. *A Coefficient of Agreement for Nominal Scales.* Educational and Psychological
   Measurement, 20(1), 37–46, 1960. — the agreement statistic reported in `eval/kappa.py`.
7. Landis, J. R., & Koch, G. G. *The Measurement of Observer Agreement for Categorical Data.*
   Biometrics, 33(1), 159–174, 1977. — the κ interpretation bands used in
   `eval/ANNOTATION-GUIDE.md`.

### Models, APIs and libraries

8. Groq. *Groq API documentation* — vision input and tool calling. https://console.groq.com/docs
9. Anthropic. *Claude API documentation* — vision and tool use. https://docs.anthropic.com
10. Playwright — headless browser automation. https://playwright.dev
11. Streamlit — application framework. https://docs.streamlit.io
12. Pillow (PIL Fork) — image processing. https://pillow.readthedocs.io
13. ReportLab — PDF generation. https://docs.reportlab.com
14. scikit-learn — `cohen_kappa_score` and metrics. https://scikit-learn.org
15. pandas, matplotlib, PyYAML, BeautifulSoup — official documentation.

No datasets were downloaded for this project; every screenshot in the evaluation set was captured
by the team from publicly accessible pages.

> Before final submission, verify the exact category names and Annexure numbering in reference 1
> against the original gazette notification rather than a secondary source — the audit output
> quotes the provision, so it has to be right.

## Demo / Deployment Link

The project runs locally — see [Source-Code/README.md](Source-Code/README.md) for setup. A recorded
walkthrough and the sample exported audit are in [`../Demo/`](../Demo/), and
[Demo/README.md](../Demo/README.md) contains the demonstration script: the run order, the fallback
if the API is unavailable, and the answers to the questions the demo reliably attracts.

_Deployment link: to be added if the Streamlit app is hosted._

---

## Acknowledgements

All datasets, APIs, models, libraries and papers used are credited in the References section.
Screenshots in the evaluation dataset were captured by the team from publicly accessible pages for
academic research purposes.
