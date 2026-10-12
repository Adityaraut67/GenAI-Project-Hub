# Presentation

`Project-Presentation.pptx` is generated from `make_ppt.js` rather than hand-built, so the deck can
be restyled or corrected by editing one file and re-running.

## Build

```bash
node make_ppt.js
```

Requires `pptxgenjs` (`npm install pptxgenjs` if the require fails). The script also calls
`apply_theme.js` from the pptx skill to write theme colours into the deck — pptxgenjs cannot do
that itself. If that path has moved, point at it:

```bash
PPTX_SKILL_DIR=/path/to/skills/pptx node make_ppt.js
```

## Structure — 18 slides

| # | Slide | Covers the required section |
|---|-------|-----------------------------|
| 1 | Title | Project title, team members |
| 2 | You have all seen these | Problem, made concrete |
| 3 | Illegal, but unenforceable at scale | Problem statement |
| 4 | Why this needs Generative AI | Justification for the approach |
| 5 | Objectives | Objectives |
| 6 | A screenshot goes in, an audit comes out | Proposed solution |
| 7 | System architecture | System architecture / workflow |
| 8 | The 13 prohibited patterns | Taxonomy |
| 9 | Every pattern carries an exclusion test | Key technical contribution |
| 10 | Technologies used | Technologies used |
| 11 | Implementation | Implementation |
| 12 | What one finding looks like | Results / output |
| 13 | How we measure it | Evaluation design |
| 14 | The ablation | Evaluation design |
| 15 | Where the project stands | Status and limitations |
| 16 | Future scope | Future scope |
| 17 | Conclusion | Conclusion |
| 18 | References | References |

Every slide carries speaker notes with the point to make aloud and the likely examiner question.

At roughly 1.5 minutes a slide this runs about 25 minutes. For a 15-minute slot, cut slides 10 and
14 and compress 13 — slides 4, 9 and 15 are the ones that earn marks and should not be dropped.

## Before submitting

1. Replace slide 12's illustrative finding with a real audit from your own dataset, and add
   annotated screenshots from `../Screenshots/` to slides 6 and 12.
2. Fill in the measured numbers on slides 14 and 15 once `eval/run_eval.py` has run on the full
   labelled dataset. Slide 14 currently states the ablation as a hypothesis, which is accurate
   until then — do not put numbers on it before they exist.
3. Verify the Annexure numbering on slides 9 and 18 against the original CCPA gazette notification.

## QA

```bash
node make_ppt.js && markitdown Project-Presentation.pptx
```

For a visual check, convert to images and look at every slide:

```bash
soffice --headless --convert-to pdf Project-Presentation.pptx && pdftoppm -jpeg -r 150 Project-Presentation.pdf slide
```
