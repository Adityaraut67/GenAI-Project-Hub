# Screenshots

Output captures for the project README and the presentation. Add these eight; the filenames are
referenced from the main README and the PPT build notes, so keep them exactly as written.

| File | What it shows | Used in |
|------|---------------|---------|
| `01-app-home.png` | The Streamlit app before an audit — upload tab, sidebar controls visible | Source-Code README, PPT slide 6 |
| `02-audit-annotated.png` | A completed audit: annotated screenshot on the left, findings panel on the right | Main README, PPT slide 12 |
| `03-finding-detail.png` | One finding close up — boxed region, provision citation, confidence | PPT slide 12 |
| `04-honest-redesign.png` | The before/after redesign panel, red above green | Main README, PPT slide 12 |
| `05-clean-control.png` | A control screenshot returning no findings | PPT slide 13 |
| `06-verifier-rejections.png` | The "what the pipeline rejected or missed" expander, open | PPT slide 14 |
| `07-pdf-report.png` | A page of the exported PDF audit | Main README |
| `08-ablation-chart.png` | `eval/results/ablation_bars.png` once the evaluation has run | Main README, PPT slide 14 |

## Capture rules

- **1920×1080 or larger.** Screenshots that get scaled up in a slide look amateurish.
- **Light mode**, consistent browser chrome, no bookmarks bar, no personal tabs visible.
- **Blur any PII** — names, addresses, order IDs, phone numbers, faces. Blur in the saved PNG, not
  just visually in the viewer.
- **Anonymise brand marks** wherever the finding is arguable. The subject of this project is the
  pattern, not any particular company. For a clear-cut pre-ticked checkbox you can leave the brand
  visible; for a borderline interface-interference call, blur it.
- Crop to the relevant region for `03-finding-detail.png`. Full-page screenshots of a tall checkout
  are unreadable at slide size.

## Note on 08

`08-ablation-chart.png` cannot be captured until `eval/run_eval.py` has run over the full labelled
dataset. Until then, slide 14 of the presentation states the ablation as a hypothesis, which is
accurate — do not substitute a mock chart.
