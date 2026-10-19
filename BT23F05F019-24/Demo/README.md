# Demo

What to put in this folder, and how to run the live demonstration.

---

## Contents to add

| File | What |
|------|------|
| `demo-video.mp4` | 3–5 minute screen recording of a full audit, with narration |
| `demo-url.txt` | Deployment link, if you host the Streamlit app |
| `sample-audit.pdf` | One exported PDF audit report, as a static artefact |
| `sample-audit.json` | The matching JSON export |

A recorded video is worth having even if you demo live — if the API is slow or the network drops
during evaluation, you still have something to show.

---

## Before the demo

1. `.env` configured and **one audit already run successfully today.** Model availability changes;
   do not discover this in the room.
2. Three screenshots pre-loaded in a folder on the desktop:
   - a **clear offender** — a checkout with a pre-ticked add-on and a countdown
   - a **subtle case** — a cookie wall where the reject path is visually suppressed
   - a **clean control** — a government portal or a plain pricing page
3. Streamlit already running (`streamlit run app.py`) with the browser open. Do not spend demo
   time on a cold start.
4. The exported PDF from a previous run open in another tab, as the fallback.

---

## Run order (about 6 minutes)

**1. The clear offender — 90 seconds**

Upload it. While it runs, say what is about to happen: the screenshot goes to a vision model
carrying thirteen rubrics, and a second pass will try to throw the findings out.

When the result appears, do not read the whole table. Point at **one** boxed region and read its
plain-language explanation aloud. That is the product.

**2. The honest redesign — 60 seconds**

Scroll to the before/after. This is the slide-worthy moment: the deceptive copy in red, the
repaired copy in green, and the layout fix underneath. Make the point that the business still gets
to make its offer — it just cannot shame the user out of refusing.

**3. The clean control — 45 seconds**

Upload it. It should come back clean. Say why this matters: a detector that flags everything looks
impressive and is useless, and the control set is how we measure that.

> If the control comes back with a finding, **do not hide it.** Say "this is a false positive, and
> it is the kind our control set exists to count" and move on. That answer is stronger than a
> clean run.

**4. The verifier, shown by switching it off — 90 seconds**

Turn off **Adversarial verifier** in the sidebar and re-run the subtle case. Then turn it back on
and re-run. Show the rejected candidates in the "What the pipeline rejected or missed" expander.

This is the single most convincing 90 seconds in the demo — it makes the precision argument
visible instead of asserted.

**5. The zero-shot ablation — 45 seconds**

Switch the detector prompt to **Zero-shot** and re-run the clear offender. Fewer or sloppier
findings, no exclusion reasoning. Say: this is what the taxonomy is worth, and it is why slide 9
exists.

**6. Export — 30 seconds**

Download the PDF. Open it. Point at the provision citation and the disclaimer line.

---

## What to say if asked

**"Why not a classifier or a rule engine?"**
The same string is lawful or unlawful depending on whether it is true. "Only 2 left" is helpful if
accurate and illegal if fabricated. No string-matching or CSS rule can make that call.

**"How do you know it is accurate?"**
We measure it. Per-pattern precision and recall over a hand-labelled set that includes clean
controls, plus Cohen's κ between two independent annotators to establish how hard the task is for
humans. Show `eval/results/`.

**"What stops it inventing a law?"**
The model never writes the legal citation. `detect.py` attaches the provision from
`patterns.yaml` by lookup after the model returns.

**"What does it get wrong?"**
Five of the thirteen patterns cannot be settled from a single frame — proving a timer is fake needs
two observations — so confidence is capped at 0.50 for those. Interface interference and disguised
advertisement are the hardest categories. Be specific here; a vague answer reads worse than a
known limitation.

---

## Recording the video

```bash
streamlit run app.py
```

Record the screen at 1080p. Follow steps 1, 2, 4 and 6 above — skip 3 and 5 to stay under five
minutes. Narrate; silent screen recordings are hard to follow.

Blur or crop any brand marks where a finding is arguable before you publish the video. The subject
of this project is the pattern, not the company.
