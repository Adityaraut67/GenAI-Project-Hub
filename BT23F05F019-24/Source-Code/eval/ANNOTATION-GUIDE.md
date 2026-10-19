# Annotation Guide

The labelled dataset is what turns this from a demo into a result. Two annotators
(**Ayan** and **Aditya**) label every screenshot independently, then reconcile. Agreement is
measured and reported.

Read this fully before labelling anything. Consistency between the two of you matters more than
either of you being individually "right" — disagreement that comes from different reading of the
rules is noise we can eliminate, and that is exactly what this guide is for.

---

## 1. What goes in the dataset

**Target: 60–80 screenshots**, split roughly:

| Group | Count | What |
|-------|-------|------|
| `deceptive` | ~45–55 | Checkout, signup, consent, subscription and cancellation screens from public e-commerce, travel, ticketing, food-delivery and news sites |
| `control` | ~15–25 | Screens we expect to be clean: government portals, bank statements of charges, university sites, minimal SaaS pricing pages |

**The controls are not optional.** A detector that flags something on every screen looks
impressive and is worthless. Controls are the only way to measure that, and the false-positive
rate on controls is one of our headline numbers.

Aim for **coverage across patterns**, not just volume. Before you stop collecting, check the
tally per pattern. If `trap_question` has one example and `drip_pricing` has twelve, the
per-pattern metrics for `trap_question` will be meaningless. Target **at least 4 examples of each
pattern** you intend to report on; if a pattern stays below 4, say so explicitly in the results
rather than reporting a precision computed from two samples.

### Capture rules

- **Public pages only.** No logged-in flows, no completed purchases, no payment pages reached
  with real card details.
- **No personal data.** Blur names, addresses, phone numbers, order IDs and any face before the
  file enters `dataset/images/`. Blur in the saved PNG, not just visually — the file is the record.
- Capture at a consistent viewport (**1366×900**, full page) so the model sees a consistent
  rendering. Use the app's URL capture tab where robots.txt permits; capture by hand otherwise.
- Record the source URL and date in `manifest.csv`. We need provenance for the references
  section, and a pattern can disappear when a site redeploys.
- Rate-limit yourself. Do not hammer one site for twenty screenshots in a minute.

### Filenames

`<group>-<NNN>-<site-slug>.png` — e.g. `deceptive-013-travel-booking.png`,
`control-004-govt-portal.png`. Zero-padded, lowercase, no spaces.

---

## 2. How to label

Open `taxonomy/patterns.yaml` beside you. **Label against the rubrics, not against your
instinct.** Each pattern has an inclusion test and an exclusion test; a screenshot earns a label
only when the inclusion test is satisfied *and* the exclusion test does not apply.

Write **one row per (screenshot, pattern)** pair in your own labels file. A screenshot with three
patterns gets three rows. A clean screenshot gets **no rows** — its absence from the file is its
label, which is why `manifest.csv` must list every image.

### The four questions, in order

For each candidate element, ask:

1. **Is it actually in the image?** You can only label what is visible. Do not label what you know
   the site does elsewhere.
2. **Does the inclusion test fit?** Quote the exact text that satisfies it into the `evidence`
   column. If you cannot quote something, you probably cannot justify the label.
3. **Does the lawful lookalike apply?** This is where most mistakes happen. `Sale ends 31 December`
   is not false urgency. A labelled `Sponsored` post is not a disguised advertisement. A solid
   Save button next to an outlined Cancel button is not interface interference.
4. **Would a reasonable consumer be misled or pressured?** Not merely advertised to. Persuasion is
   lawful.

If you answer yes, yes, no, yes — label it.

### Judgement calls, settled in advance

These are the cases that will otherwise produce disagreement, so they are decided here:

- **Truth you cannot check.** "Only 2 left!" might be true. Label `false_urgency` only when there
  is positive reason to think it is manufactured — the same low count on every item, a timer with
  no stated consequence, a deadline that is not a date. When genuinely unsure, leave it unlabelled
  and note it in `notes`. We would rather under-label the gold set than inflate it.
- **One element, two patterns.** Label both only if both inclusion tests independently hold. A
  pre-ticked auto-renewal box is `basket_sneaking` *and* `saas_billing`; a pre-ticked newsletter
  box is only `basket_sneaking`.
- **One pattern, two elements.** Two separate pre-ticked add-ons on one page is **one** row for
  `basket_sneaking`, with both quoted in `evidence`. Metrics are per-pattern-per-screenshot.
- **Cookie banners.** Extremely common and easy to over-label. `interface_interference` applies
  when the reject path is visually suppressed — grey-on-grey, buried under a text link, or absent
  from the first layer. A clearly legible "Reject all" button beside "Accept all" is compliant.
- **Fine print.** Disclosure that exists but is deliberately sub-legible counts as
  `interface_interference` or `saas_billing` depending on what is being hidden. Disclosure that is
  simply long does not.
- **Severity.** Use the pattern's `default_severity` unless this instance is clearly worse or
  milder, and say why in `notes`. Severity is not a scored metric; it drives report ordering.
- **Patterns flagged `single_frame_decidable: false`.** You may still label these from the
  screenshot, but mark `uncertain = yes`. They are reported separately, because we cannot hold
  the model to a standard the evidence does not support.

---

## 3. Files and schema

```text
eval/dataset/
├── images/                      # the PNGs
├── manifest.csv                 # every image, with provenance  (shared)
├── labels-ayan.csv              # Ayan's independent pass
├── labels-aditya.csv            # Aditya's independent pass
└── labels-final.csv             # reconciled gold standard  (used for all metrics)
```

### `manifest.csv`

| column | meaning |
|--------|---------|
| `screenshot` | filename inside `images/` |
| `group` | `deceptive` or `control` |
| `sector` | `ecommerce`, `travel`, `ticketing`, `food`, `news`, `saas`, `government`, `education` |
| `source_url` | where it came from |
| `captured_on` | `YYYY-MM-DD` |
| `notes` | anything relevant (e.g. "cookie wall appeared after 2s") |

### `labels-*.csv`

| column | meaning |
|--------|---------|
| `screenshot` | filename, must exist in `manifest.csv` |
| `pattern` | taxonomy id, exactly as written in `patterns.yaml` |
| `evidence` | the copy or element you are labelling, quoted verbatim |
| `severity` | `high` / `medium` / `low` |
| `uncertain` | `yes` / `no` — set `yes` for single-frame-undecidable patterns or genuine doubt |
| `notes` | free text; required when you deviate from the default severity |

---

## 4. Procedure

1. **Collect** into `images/` and fill `manifest.csv` together. Collection is shared work.
2. **Label independently.** Do not discuss screenshots while labelling and do not look at each
   other's files. Agreement is only meaningful if it was reached independently — this is the one
   rule that, if broken, invalidates the headline kappa number.
3. **Measure agreement** before reconciling:
   ```bash
   python eval/kappa.py
   ```
   Record the kappa you get here. **This is the number that goes in the report** — not the one
   after you have talked it through.
4. **Reconcile.** Work through every disagreement together. For each, decide which reading the
   rubric actually supports. If the rubric is genuinely ambiguous, *fix the rubric* in
   `patterns.yaml`, note the change, and re-check any earlier screenshots it affects. Write the
   agreed labels to `labels-final.csv`.
5. **Freeze.** Once `labels-final.csv` is written, stop changing it. If you later find a labelling
   error, fix it and re-run every configuration — never fix the gold set against the model's
   output after seeing the model's output. That is how you accidentally fake a result.

### Interpreting kappa

| κ | Reading |
|---|---------|
| < 0.40 | The rubrics are too vague. Fix them and re-label; do not proceed. |
| 0.40 – 0.60 | Moderate. Usable, but identify which patterns drive the disagreement. |
| 0.60 – 0.80 | Substantial. Good for a subjective task like this. |
| > 0.80 | Strong. |

Report per-pattern kappa too. Expect `interface_interference` and `false_urgency` to be your
weakest, and say so — a low kappa on a pattern is an honest statement about task difficulty and
sets the ceiling for what the model can be expected to achieve.

---

## 5. Division of work

| Task | Owner |
|------|-------|
| Screenshot collection, manifest | Ayan + Aditya (shared) |
| Independent labelling pass | Both, separately |
| Reconciliation into `labels-final.csv` | Both, together |
| Running `run_eval.py`, charts, results write-up | Aditya |
| Taxonomy fixes arising from reconciliation | Ayan |

---

## 6. Ethics

Every screenshot in this dataset is of a publicly accessible page, captured for academic
evaluation. We are measuring a detector, not accusing companies. In the presentation and any
public demo, anonymise brand marks wherever a finding is arguable. The subject of this project is
the pattern, not the company.
