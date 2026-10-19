# Source Code — Setup and Run

Everything here runs locally. One API key, one command.

---

## 1. Requirements

- **Python 3.11+**
- An API key for a **vision-capable model with tool-calling support** — Groq or Anthropic
- Chromium for Playwright, only if you want to audit live URLs (uploading screenshots works
  without it)

## 2. Install

```bash
cd Source-Code
python -m venv .venv
```

Activate it — Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

For live URL capture, also:

```bash
playwright install chromium
```

## 3. Configure

```bash
cp .env.example .env
```

Open `.env` and set **one** provider:

| Provider | Variables |
|----------|-----------|
| Groq | `GROQ_API_KEY` and `DPA_MODEL` set to a Groq vision model id |
| Anthropic | `ANTHROPIC_API_KEY` and `DPA_MODEL` set to a Claude model id |

`config.py` picks the client from whichever key is present, preferring Groq when both are set.

> **`DPA_MODEL` must match the provider you configured.** The default in `config.py` is a Claude
> model id, so if you set `GROQ_API_KEY` without also setting `DPA_MODEL`, every audit fails with
> an unknown-model error. This is the first thing to check if nothing works.

Never commit `.env` — it is in `.gitignore`.

## 4. Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Two ways in:

- **Upload a screenshot** — any PNG or JPEG of a checkout, signup, consent or cancellation screen.
- **Capture a URL** — public pages only. `robots.txt` is honoured and captures are rate-limited to
  one every three seconds per host. Never point this at a page behind a login.

The sidebar controls the detector prompt (full rubrics or the zero-shot ablation baseline), the
adversarial verifier, and the honest-redesign generator. Export the result as a PDF audit or JSON.

## 5. Audit one screenshot from Python

```python
from pipeline import audit

result = audit(open("screenshot.png", "rb").read())

for f in result.sorted_findings():
    print(f.severity, f.pattern, repr(f.evidence))
    print("  ", f.explanation)
```

`audit()` accepts `mode="zero_shot"` to disable the rubrics, `use_verifier=False` to skip the
second pass, `html=...` to enable the DOM cross-check, and `do_rewrite=False` to skip the redesign.

---

## 6. Run the evaluation

The dataset is not committed (`eval/dataset/images/` is gitignored), so this needs the screenshots
in place first. See [eval/ANNOTATION-GUIDE.md](eval/ANNOTATION-GUIDE.md) for the collection and
labelling protocol.

**Inter-annotator agreement** — run this *before* reconciling the two label files:

```bash
python eval/kappa.py
```

**The full ablation** — all three configurations over the whole dataset:

```bash
python eval/run_eval.py
```

One configuration only:

```bash
python eval/run_eval.py --config rubric_verifier
```

Predictions are cached per image under `eval/cache/`, so re-running costs no API calls. To force
fresh predictions after changing a prompt:

```bash
python eval/run_eval.py --skip-cache
```

**Charts** for the Results section:

```bash
python eval/charts.py
```

Writes the ablation bars, per-pattern F1 heatmap, precision-recall scatter and control
false-positive comparison into `eval/results/`.

---

## 7. Module map

| Path | Role |
|------|------|
| `app.py` | Streamlit front end |
| `config.py` | Model, temperature, paths, bbox scale, client factory |
| `imaging.py` | Load, downscale and base64-encode screenshots |
| `capture/screenshot.py` | Playwright capture with robots.txt and rate limiting |
| `taxonomy/patterns.yaml` | The 13 CCPA rubrics — inclusion test, exclusion test, examples |
| `taxonomy/prompts.py` | Versioned detector, verifier and rewriter prompts |
| `pipeline/llm.py` | Schema-constrained tool call wrapper (Groq and Anthropic paths) |
| `pipeline/detect.py` | Stage 2 — candidate findings |
| `pipeline/verify.py` | Stage 3 — adversarial pruning |
| `pipeline/dom_signals.py` | Stage 4 — structural DOM evidence, no model call |
| `pipeline/rewrite.py` | Stage 5 — honest redesign |
| `pipeline/finding.py` | The `Finding` record passed between stages |
| `render/overlay.py` | Severity-coloured bounding boxes on the screenshot |
| `render/report.py` | PDF audit report |
| `eval/` | Dataset, annotation guide, metrics harness, κ, charts |

---

## 8. Reproducibility

Three things make an evaluation run repeatable:

- **Temperature pinned to 0** in `config.py`.
- **Prompt versioning** — a SHA-256 of all three prompts plus the taxonomy version is computed as
  `PROMPT_VERSION` and written into every result and cache entry. If the hash changes, previously
  collected numbers are not comparable and the cache must be cleared.
- **Legal citations are looked up, never generated.** `detect.py` attaches `provision` from
  `patterns.yaml` after the model returns, so a hallucinated Annexure reference is impossible.

After editing any prompt or the taxonomy, clear the cache before re-running:

```bash
rm -rf eval/cache
```

---

## 9. Troubleshooting

| Symptom | Cause |
|---------|-------|
| `Neither GROQ_API_KEY nor ANTHROPIC_API_KEY is set` | `.env` missing or not loaded — you are probably not in `Source-Code/` |
| Unknown / invalid model error | `DPA_MODEL` does not match the provider whose key you set (see §3) |
| `Model did not call report_findings` | The configured model does not support tool calling, or is not vision-capable |
| `Playwright is not installed` | Run `playwright install chromium` |
| `robots.txt disallows fetching this URL` | Expected and intentional. Capture the screenshot by hand and upload it |
| Bounding boxes in the wrong place | Normalised 0–1000 coordinates assume the model saw the whole image; check the screenshot is not absurdly tall |
| `manifest.csv not found` | Copy `manifest.example.csv` and fill it in — see the annotation guide |

---

## 10. Scope and ethics

Only publicly reachable pages are captured: no authenticated flows, no completed purchases, no
personal data. Any incidental PII is blurred before a screenshot enters the dataset. Every report
carries the disclaimer that findings are model output, not legal determinations.

Out of scope by design: browser extension packaging, multi-step flow analysis, native mobile app
teardown, languages beyond English and Hindi, and any automated enforcement action.
