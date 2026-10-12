/**
 * Builds PPT/Project-Presentation.pptx for the Dark Pattern Auditor project.
 *
 *   cd BT23F05F019-24/PPT
 *   node make_ppt.js
 *
 * Structured deck: one theme, five layouts, named placeholders, sections. Restyle
 * by editing THEME below and re-running — nothing hard-codes a colour.
 */

const path = require("path");
const pptxgen = require("pptxgenjs");

// apply_theme.js ships with the pptx skill; pptxgenjs cannot write theme colours
// itself. Override with PPTX_SKILL_DIR if the skill lives elsewhere.
const SKILL_DIR =
  process.env.PPTX_SKILL_DIR ||
  "C:/Users/Hp/AppData/Local/Claude-3p/local-agent-mode-sessions/skills-plugin/" +
    "00000000-0000-4000-8000-000000000001/234c931e-5c0f-4637-a960-5a071885496c/skills/pptx";

const OUT = path.join(__dirname, "Project-Presentation.pptx");

/* ------------------------------------------------------------------ theme -- */
// Severity colours are lifted straight from render/overlay.py, so the deck and
// the tool's annotated screenshots read as one system.
const THEME = {
  name: "Dark Pattern Auditor",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1C1C21", // near-black charcoal — dark slide ground
    lt1: "FFFFFF",
    dk2: "36454F", // charcoal slate — body text
    lt2: "F2F3F5", // card tint
    accent1: "D7263D", // crimson — high severity / the deceptive signal
    accent2: "E8A33D", // amber — medium severity
    accent3: "4A7BA7", // slate blue — low severity
    accent4: "2A9D5C", // green — the honest redesign
    accent5: "6B7280", // muted grey — captions
    accent6: "8C1C2B", // deep crimson
    hlink: "4A7BA7",
    folHlink: "6B7280",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Ayan Farooque, Aditya";
pres.title = "Dark Pattern Auditor";
pres.subject = "Generative AI project — automated dark pattern auditing";

const C = pres.SchemeColor;

const M = 0.6; // page margin
const W = 13.3 - 2 * M; // usable width = 12.1
const FOOTER =
  "Dark Pattern Auditor  ·  Ayan Farooque & Aditya  ·  BT23F05F019 / BT23F05F024";

/* ---------------------------------------------------------------- layouts -- */
const footerObjects = [
  {
    text: {
      text: FOOTER,
      options: {
        x: M,
        y: 7.0,
        w: 9.5,
        h: 0.3,
        fontSize: 9,
        color: C.accent5,
        isTextBox: true,
        margin: 0,
        valign: "middle",
      },
    },
  },
];

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    {
      placeholder: {
        options: {
          name: "title",
          type: "title",
          x: 0.9,
          y: 2.35,
          w: 11.5,
          h: 1.5,
          fontSize: 44,
          bold: true,
          color: C.background1,
          valign: "bottom",
          margin: 0,
        },
      },
    },
    {
      placeholder: {
        options: {
          name: "body",
          type: "body",
          x: 0.9,
          y: 4.0,
          w: 11.5,
          h: 2.0,
          fontSize: 15,
          color: C.background2,
          valign: "top",
          margin: 0,
        },
      },
    },
  ],
});

pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: C.text1 },
  objects: [
    {
      placeholder: {
        options: {
          name: "title",
          type: "title",
          x: M,
          y: 0.75,
          w: W,
          h: 0.95,
          fontSize: 36,
          bold: true,
          color: C.background1,
          valign: "middle",
          margin: 0,
        },
      },
    },
    {
      placeholder: {
        options: {
          name: "body",
          type: "body",
          x: M,
          y: 2.1,
          w: W,
          h: 4.3,
          fontSize: 17,
          color: C.background2,
          valign: "top",
          margin: 0,
        },
      },
    },
  ],
});

// Title position is identical on CONTENT and TITLE_ONLY so it never drifts
// between content slides.
const contentTitle = {
  name: "title",
  type: "title",
  x: M,
  y: 0.45,
  w: W,
  h: 0.85,
  fontSize: 32,
  bold: true,
  color: C.text1,
  valign: "middle",
  margin: 0,
};

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  slideNumber: { x: 12.5, y: 7.0, fontSize: 9, color: C.accent5 },
  objects: [
    { placeholder: { options: { ...contentTitle } } },
    {
      placeholder: {
        options: {
          name: "body",
          type: "body",
          x: M,
          y: 1.55,
          w: W,
          h: 5.1,
          fontSize: 15,
          color: C.text2,
          valign: "top",
          margin: 0,
        },
      },
    },
    ...footerObjects,
  ],
});

pres.defineSlideMaster({
  title: "TITLE_ONLY",
  background: { color: C.background1 },
  slideNumber: { x: 12.5, y: 7.0, fontSize: 9, color: C.accent5 },
  objects: [{ placeholder: { options: { ...contentTitle } } }, ...footerObjects],
});

/* ---------------------------------------------------------------- helpers -- */
function card(slide, o) {
  slide.addShape(pres.ShapeType.roundRect, {
    x: o.x,
    y: o.y,
    w: o.w,
    h: o.h,
    rectRadius: 0.06,
    fill: { color: o.fill || C.background2 },
    line: o.line ? { color: o.line, width: 1 } : { color: o.fill || C.background2, width: 0 },
    objectName: o.name,
  });
}

function text(slide, str, o) {
  slide.addText(str, { isTextBox: true, margin: 0, fontSize: 14, color: C.text2, ...o });
}

function numberBadge(slide, n, x, y, d, fill) {
  slide.addShape(pres.ShapeType.ellipse, {
    x,
    y,
    w: d,
    h: d,
    fill: { color: fill || C.accent1 },
    line: { color: fill || C.accent1, width: 0 },
    objectName: `badge-${n}`,
  });
  slide.addText(String(n), {
    x,
    y,
    w: d,
    h: d,
    align: "center",
    valign: "middle",
    fontSize: d > 0.5 ? 16 : 13,
    bold: true,
    color: C.background1,
    isTextBox: true,
    margin: 0,
  });
}

function sectionHead(slide, str, x, y, w) {
  text(slide, str, { x, y, w, h: 0.4, fontSize: 20, bold: true, color: C.text1 });
}

function caption(slide, str, x, y, w, h) {
  text(slide, str, { x, y, w, h: h || 0.4, fontSize: 11, color: C.accent5, italic: true });
}

function bullets(slide, items, o) {
  slide.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i !== items.length - 1 },
    })),
    {
      isTextBox: true,
      margin: 0,
      fontSize: o.fontSize || 13.5,
      color: o.color || C.text2,
      paraSpaceAfter: o.paraSpaceAfter || 8,
      ...o,
    }
  );
}

/* ============================================================ 1. TITLE ==== */
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  s.addText("Dark Pattern Auditor", { placeholder: "title" });
  s.addText(
    [
      {
        text: "Automated detection of manipulative interface design, audited against India's CCPA Dark Patterns Guidelines, 2023",
        options: { breakLine: true, fontSize: 16, color: C.background2 },
      },
      {
        text: "Ayan Farooque (BT23F05F019)   ·   Aditya (BT23F05F024)",
        options: { breakLine: true, fontSize: 14, color: C.accent2, bold: true },
      },
      {
        text: "Final Year, Computer Science and Engineering   ·   Generative AI Project",
        options: { fontSize: 12, color: C.accent5 },
      },
    ],
    { placeholder: "body" }
  );
  s.addNotes(
    "Open with the hook, not the architecture. Say: every one of us has been caught by a " +
      "pre-ticked add-on or a countdown timer. Since November 2023 those are illegal in India, " +
      "and nobody can check at scale. That is what we built."
  );
}

/* ============================================= 2. THE PROBLEM, CONCRETE === */
pres.addSection({ title: "Problem" });
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Problem" });
  s.addText("You have all seen these", { placeholder: "title" });

  const examples = [
    {
      quote: "\u201cTravel protection  \u20b9299\u201d",
      sub: "The checkbox was already ticked. You never asked for it, and it is in your total.",
      tag: "BASKET SNEAKING",
    },
    {
      quote: "\u201cOffer expires in 00:04:59\u201d",
      sub: "Reload the page and the clock starts again. The deadline was never real.",
      tag: "FALSE URGENCY",
    },
    {
      quote: "\u201cNo thanks, I like paying full price\u201d",
      sub: "Declining is written to make you feel foolish for choosing it.",
      tag: "CONFIRM SHAMING",
    },
  ];

  examples.forEach((ex, i) => {
    const x = M + i * 4.15;
    card(s, { x, y: 1.75, w: 3.8, h: 2.75, name: `example-${i}` });
    text(s, ex.quote, {
      x: x + 0.25,
      y: 2.0,
      w: 3.3,
      h: 0.95,
      fontSize: 15,
      bold: true,
      italic: true,
      color: C.text1,
    });
    text(s, ex.sub, { x: x + 0.25, y: 3.05, w: 3.3, h: 0.95, fontSize: 12, color: C.text2 });
    text(s, ex.tag, {
      x: x + 0.25,
      y: 4.1,
      w: 3.3,
      h: 0.28,
      fontSize: 10,
      bold: true,
      charSpacing: 1,
      color: C.accent1,
    });
  });

  text(s, "None of these are accidents. They are engineered — and since November 2023, illegal.", {
    x: M,
    y: 5.0,
    w: W,
    h: 0.6,
    fontSize: 21,
    bold: true,
    color: C.text1,
  });
  caption(
    s,
    "Dark patterns work because they exploit how people actually read interfaces, not because users are careless.",
    M,
    5.75,
    W,
    0.5
  );
  s.addNotes(
    "Spend time here — the audience needs to feel the problem before they care about the " +
      "pipeline. Ask them to raise a hand if they have ever paid for an add-on they did not " +
      "choose. Then name each tactic."
  );
}

/* ====================================== 3. PROBLEM STATEMENT / THE GAP ==== */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Problem" });
  s.addText("Illegal, but unenforceable at scale", { placeholder: "title" });

  const stats = [
    {
      n: "13",
      label: "dark patterns named and prohibited by the CCPA Guidelines, 2023",
      colour: C.accent1,
    },
    {
      n: "1",
      label: "enforcement method available today: a human reviewing screenshots by hand",
      colour: C.accent2,
    },
  ];
  stats.forEach((st, i) => {
    const y = 1.7 + i * 2.3;
    card(s, { x: M, y, w: 5.3, h: 2.0, name: `stat-${i}` });
    text(s, st.n, {
      x: M + 0.3,
      y: y + 0.15,
      w: 1.9,
      h: 1.1,
      fontSize: 60,
      bold: true,
      color: st.colour,
      valign: "middle",
    });
    text(s, st.label, {
      x: M + 0.3,
      y: y + 1.3,
      w: 4.7,
      h: 0.6,
      fontSize: 12.5,
      color: C.text2,
    });
  });

  sectionHead(s, "The gap", 6.5, 1.7, 6.2);
  bullets(
    s,
    [
      "Manual review is slow, and two reviewers often disagree on the same screenshot.",
      "The number of interfaces that need checking grows far faster than the number of reviewers.",
      "A site can redeploy and change the pattern before a complaint is ever processed.",
      "The consumer being manipulated has no way to recognise it in the moment — which is exactly when it matters.",
    ],
    { x: 6.5, y: 2.3, w: 6.2, h: 2.9, fontSize: 13.5 }
  );
  text(
    s,
    "There is no accessible tool that looks at an interface and explains, in plain language and against the legal taxonomy, how it is manipulating the person using it.",
    {
      x: 6.5,
      y: 5.4,
      w: 6.2,
      h: 1.0,
      fontSize: 14,
      bold: true,
      color: C.accent6,
    }
  );
  s.addNotes(
    "The regulation already exists — we are not proposing policy. The gap is purely one of " +
      "enforcement capacity and consumer awareness, and that is a software problem."
  );
}

/* ================================== 4. WHY THIS NEEDS GENERATIVE AI ======= */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Problem" });
  s.addText("Why this needs Generative AI", { placeholder: "title" });

  const reasons = [
    [
      "Not keyword matching",
      "\u201cOnly 2 left in stock!\u201d is lawful if true and unlawful if fabricated. The identical string is compliant or non-compliant depending on context no string can carry.",
    ],
    [
      "Not a CSS rule",
      "Interface interference works through visual hierarchy — a greyed-out decline beside a saturated accept. Both are perfectly valid CSS.",
    ],
    [
      "Needs pragmatic reasoning",
      "Detecting confirm shaming means recognising shame as a persuasion mechanism inside a sentence that is grammatically unremarkable.",
    ],
    [
      "The output must explain",
      "A severity score helps nobody. The deliverable is an explanation a non-technical consumer can read and act on.",
    ],
  ];

  reasons.forEach((r, i) => {
    const y = 1.7 + i * 1.22;
    numberBadge(s, i + 1, 0.65, y + 0.12, 0.55);
    text(s, r[0], { x: 1.45, y: y + 0.1, w: 3.2, h: 0.6, fontSize: 15, bold: true, color: C.text1 });
    text(s, r[1], { x: 4.85, y: y + 0.05, w: 7.85, h: 1.0, fontSize: 12.5, color: C.text2 });
  });

  text(
    s,
    "Joint visual + linguistic + intent reasoning over an image is what a vision-language model does and a rule engine cannot.",
    { x: M, y: 6.45, w: W, h: 0.45, fontSize: 13, bold: true, color: C.accent6 }
  );
  s.addNotes(
    "This is the slide the viva turns on. Expect the question 'why not a classifier?' — the " +
      "answer is reason 1: the label depends on the truth of the claim, which is not in the " +
      "pixels or the string. Have the 'Only 2 left' example ready to say out loud."
  );
}

/* ================================================== 5. OBJECTIVES ========= */
pres.addSection({ title: "Solution" });
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Solution" });
  s.addText("Objectives", { placeholder: "title" });

  const objectives = [
    "Detect and localise dark patterns in a UI screenshot against the 13-category CCPA taxonomy.",
    "Produce a structured audit record per finding: tactic, quoted evidence, region, severity, provision and a plain-language explanation.",
    "Generate an honest redesign — rewritten copy and corrected affordances for the worst offender.",
    "Corroborate visual findings with hard DOM evidence wherever a live URL is available.",
    "Measure detection quality on a hand-labelled dataset and report per-pattern precision and recall, not anecdotes.",
  ];
  objectives.forEach((o, i) => {
    const y = 1.75 + i * 1.0;
    numberBadge(s, i + 1, 0.65, y, 0.45, i === 4 ? C.accent4 : C.accent1);
    text(s, o, { x: 1.35, y: y - 0.05, w: 11.35, h: 0.75, fontSize: 14, color: C.text2 });
  });
  caption(s, "Objective 5 is weighted as heavily as the build: a detector without measured error rates is a demo, not a result.", M, 6.75, W);
  s.addNotes(
    "Call out that objective 5 is deliberate. Anyone can show one screenshot that works; the " +
      "project claim is that we know how often it works and where it fails."
  );
}

/* ============================================= 6. PROPOSED SOLUTION ======= */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Solution" });
  s.addText("A screenshot goes in, a compliance audit comes out", { placeholder: "title" });

  card(s, { x: M, y: 1.7, w: 5.6, h: 4.4, name: "input-card" });
  sectionHead(s, "Input", M + 0.3, 1.95, 5.0);
  bullets(
    s,
    [
      "A screenshot of any checkout, signup, consent or cancellation screen — uploaded directly, or",
      "A public URL, captured headlessly as a full-page PNG plus its DOM",
      "No login, no purchase, no personal data — robots.txt honoured and captures rate-limited",
    ],
    { x: M + 0.3, y: 2.55, w: 5.0, h: 3.3, fontSize: 13 }
  );

  card(s, { x: 7.1, y: 1.7, w: 5.6, h: 4.4, fill: C.background2, name: "output-card" });
  sectionHead(s, "Output", 7.4, 1.95, 5.0);
  bullets(
    s,
    [
      "The tactic, named against the 13 legal categories",
      "The offending region, boxed on the image",
      "The evidence, quoted verbatim from the interface",
      "The provision it implicates, cited exactly",
      "Severity and a calibrated confidence",
      "The honest redesign — repaired copy and layout",
    ],
    { x: 7.4, y: 2.55, w: 5.0, h: 3.3, fontSize: 13 }
  );

  text(
    s,
    "Exportable as an annotated PDF audit report or as JSON for downstream analysis.",
    { x: M, y: 6.35, w: W, h: 0.45, fontSize: 13.5, bold: true, color: C.text1 }
  );
  s.addNotes(
    "Frame the output as a regulator-style artefact, not a chatbot answer. The PDF is the thing " +
      "a consumer-protection officer could actually file."
  );
}

/* ============================================ 7. SYSTEM ARCHITECTURE ====== */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Solution" });
  s.addText("System architecture", { placeholder: "title" });

  const stages = [
    ["Capture", "Playwright grabs a full-page PNG and the DOM, or the user uploads a screenshot"],
    ["Pre-process", "Downscale to the model's limits while keeping a normalised coordinate space"],
    ["Detect", "Vision model reads the image against 13 rubrics → schema-constrained JSON findings"],
    ["Verify", "Adversarial second pass re-reads the image and drops findings that do not hold up"],
    ["Cross-check & report", "DOM signals corroborate the findings; annotate, rewrite, export PDF"],
  ];

  stages.forEach((st, i) => {
    const y = 1.6 + i * 0.95;
    const isModel = i === 2 || i === 3;
    card(s, {
      x: M,
      y,
      w: W,
      h: 0.85,
      fill: isModel ? C.background2 : C.background1,
      line: isModel ? C.accent1 : "D8DBE0",
      name: `stage-${i}`,
    });
    numberBadge(s, i + 1, M + 0.25, y + 0.17, 0.5, isModel ? C.accent1 : C.accent5);
    text(s, st[0], {
      x: M + 0.95,
      y: y + 0.2,
      w: 2.5,
      h: 0.45,
      fontSize: 14.5,
      bold: true,
      color: C.text1,
    });
    text(s, st[1], { x: M + 3.5, y: y + 0.19, w: 8.3, h: 0.5, fontSize: 12, color: C.text2 });
  });

  text(
    s,
    "Two model calls per audit (detect, then verify) plus one for the rewrite. Stages 3 and 4 are the generative core; everything else is deterministic.",
    { x: M, y: 6.45, w: W, h: 0.45, fontSize: 12.5, italic: true, color: C.accent5 }
  );
  s.addNotes(
    "Stress that the DOM cross-check is NOT a model call. Two independent evidence types — one " +
      "perceptual, one structural — is what separates 'the model thinks the box looks ticked' " +
      "from 'the input carries the checked attribute'."
  );
}

/* ================================================== 8. THE TAXONOMY ======= */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Solution" });
  s.addText("The 13 prohibited patterns", { placeholder: "title" });

  const patterns = [
    ["False urgency", true],
    ["Basket sneaking", false],
    ["Confirm shaming", false],
    ["Forced action", false],
    ["Subscription trap", true],
    ["Interface interference", false],
    ["Bait and switch", true],
    ["Drip pricing", true],
    ["Disguised advertisement", false],
    ["Nagging", true],
    ["Trap question", false],
    ["SaaS billing", false],
    ["Rogue malware", false],
  ];

  patterns.forEach((p, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = M + col * 4.15;
    const y = 1.7 + row * 0.95;
    card(s, {
      x,
      y,
      w: 3.8,
      h: 0.8,
      fill: p[1] ? C.background1 : C.background2,
      line: p[1] ? C.accent2 : null,
      name: `pattern-${i}`,
    });
    text(s, (p[1] ? "\u26a0  " : "") + p[0], {
      x: x + 0.25,
      y,
      w: 3.3,
      h: 0.8,
      fontSize: 12.5,
      bold: true,
      color: C.text1,
      valign: "middle",
    });
  });

  text(
    s,
    [
      { text: "\u26a0  ", options: { color: THEME.colors.accent2, bold: true, fontSize: 13 } },
      {
        text: "Five patterns cannot be settled from a single screenshot. The system still reports them, but caps confidence at 0.50 and states what further observation would be needed.",
        options: { fontSize: 12.5, color: THEME.colors.dk2 },
      },
    ],
    { x: M, y: 6.5, w: W, h: 0.5, isTextBox: true, margin: 0 }
  );
  s.addNotes(
    "Do not read all 13 aloud. Point at the five flagged ones and explain the honesty " +
      "mechanism: proving a timer is fake needs two observations, so we refuse to claim high " +
      "confidence from one frame. Examiners reward this."
  );
}

/* =========================================== 9. THE RUBRIC CONTRIBUTION === */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Solution" });
  s.addText("Every pattern carries an exclusion test", { placeholder: "title" });

  const headerOpts = {
    fill: { color: THEME.colors.accent1 },
    color: THEME.colors.lt1,
    bold: true,
    fontSize: 12.5,
  };
  const rows = [
    [
      { text: "Pattern", options: headerOpts },
      { text: "Flag it when", options: { ...headerOpts } },
      { text: "Never flag", options: { ...headerOpts } },
    ],
    [
      "False urgency",
      "\u201cOnly 1 left — expires in 00:04:59\u201d on every product page",
      "\u201cSale ends 31 December 2026\u201d — a specific, checkable date",
    ],
    [
      "Disguised advertisement",
      "A review article in the feed with no sponsorship disclosure",
      "\u201cSponsored · Brand\u201d labelled legibly above the creative",
    ],
    [
      "Interface interference",
      "Bright \u201cAccept all\u201d beside grey-on-grey \u201cmanage preferences\u201d",
      "Solid Save beside outlined Cancel — both clearly legible",
    ],
  ];

  s.addTable(rows, {
    x: M,
    y: 1.7,
    w: W,
    colW: [2.6, 4.75, 4.75],
    rowH: [0.42, 0.78, 0.78, 0.78],
    border: { type: "solid", color: "D8DBE0", pt: 0.75 },
    fontSize: 12,
    fontFace: THEME.bodyFontFace,
    color: THEME.colors.dk2,
    valign: "middle",
    margin: 0.1,
  });

  card(s, { x: M, y: 4.85, w: W, h: 1.35, fill: C.background2, name: "insight" });
  text(
    s,
    "This is the engineering contribution. A detector given only category names flags every assertive interface it sees; the exclusion tests are what make it an auditor rather than an alarm.",
    { x: M + 0.35, y: 5.05, w: W - 0.7, h: 0.95, fontSize: 14.5, bold: true, color: C.text1 }
  );
  caption(
    s,
    "All 13 rubrics live in taxonomy/patterns.yaml — inclusion test, exclusion test, a violating example and a lawful lookalike for each.",
    M,
    6.4,
    W
  );
  s.addNotes(
    "If you only get one technical point across, make it this one. Marketing is lawful; " +
      "deception is not — and the only way a model can tell them apart is if you tell it what " +
      "the lawful version looks like."
  );
}

/* ============================================ 10. TECHNOLOGIES USED ======= */
pres.addSection({ title: "Implementation" });
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Implementation" });
  s.addText("Technologies used", { placeholder: "title" });

  const tech = [
    ["REASONING", "Groq / Anthropic", "Vision + schema-constrained tool calling, behind one pluggable client factory"],
    ["CAPTURE", "Playwright", "Headless Chromium: full-page PNG and DOM dump in a single pass"],
    ["ANNOTATION", "Pillow", "Severity-coloured bounding boxes and numbered labels on the original image"],
    ["INTERFACE", "Streamlit", "Upload or URL, live audit, side-by-side honest redesign"],
    ["REPORTING", "ReportLab", "Exportable PDF audit with findings table and disclaimer"],
    ["EVALUATION", "pandas · scikit-learn · matplotlib", "Metrics, Cohen's \u03ba, ablation charts"],
  ];

  tech.forEach((t, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = M + col * 4.15;
    const y = 1.8 + row * 2.3;
    card(s, { x, y, w: 3.8, h: 2.05, name: `tech-${i}` });
    text(s, t[0], {
      x: x + 0.28,
      y: y + 0.22,
      w: 3.25,
      h: 0.28,
      fontSize: 9.5,
      bold: true,
      charSpacing: 1.2,
      color: C.accent1,
    });
    text(s, t[1], {
      x: x + 0.28,
      y: y + 0.58,
      w: 3.25,
      h: 0.5,
      fontSize: 14.5,
      bold: true,
      color: C.text1,
    });
    text(s, t[2], { x: x + 0.28, y: y + 1.15, w: 3.25, h: 0.75, fontSize: 11.5, color: C.text2 });
  });

  caption(
    s,
    "Deliberately boring infrastructure. The novelty is the task definition, not the stack.",
    M,
    6.3,
    W
  );
  s.addNotes(
    "If asked why not fine-tune a model: we have 60-80 labelled screenshots. That is a " +
      "rubric-and-prompt problem, not a training-data problem, and the rubrics are auditable by " +
      "a human in a way model weights are not."
  );
}

/* ================================================ 11. IMPLEMENTATION ===== */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Implementation" });
  s.addText("Implementation", { placeholder: "title" });

  card(s, { x: M, y: 1.7, w: 5.9, h: 4.7, name: "tree-card" });
  text(s, "Module map", {
    x: M + 0.3,
    y: 1.9,
    w: 5.3,
    h: 0.35,
    fontSize: 15,
    bold: true,
    color: C.text1,
  });
  text(
    s,
    [
      "app.py            Streamlit entry point",
      "config.py         model, temperature, paths",
      "imaging.py        downscale + encode",
      "capture/          robots-aware URL capture",
      "taxonomy/         13 rubrics + prompts",
      "pipeline/         detect, verify, dom, rewrite",
      "render/           overlay + PDF report",
      "eval/             harness, \u03ba, charts, dataset",
    ].join("\n"),
    {
      x: M + 0.3,
      y: 2.4,
      w: 5.3,
      h: 3.7,
      fontSize: 11,
      fontFace: "Courier New",
      color: C.text2,
      isTextBox: true,
      margin: 0,
      lineSpacingMultiple: 1.35,
    }
  );

  sectionHead(s, "Key design decisions", 7.0, 1.8, 5.7);
  bullets(
    s,
    [
      "Schema-constrained tool calls, never free-text JSON — the model is forced to call a declared JSON-Schema tool.",
      "Bounding boxes normalised to 0–1000, so detection is independent of screenshot resolution.",
      "Prompts SHA-256 versioned; the hash is logged with every result. If it changes, prior numbers are void.",
      "Temperature pinned to 0 for reproducible evaluation runs.",
      "Per-image prediction cache — re-running the charts costs no API calls.",
      "Legal citations are attached from the taxonomy, never recited by the model.",
    ],
    { x: 7.0, y: 2.4, w: 5.7, h: 3.9, fontSize: 12.5, paraSpaceAfter: 9 }
  );
  s.addNotes(
    "The last bullet matters: we never let the model generate the provision reference, because " +
      "a hallucinated legal citation is the single worst failure this system could produce. It " +
      "comes from patterns.yaml by lookup."
  );
}

/* ============================================= 12. OUTPUT & REDESIGN ===== */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Implementation" });
  s.addText("What one finding looks like", { placeholder: "title" });

  card(s, { x: M, y: 1.7, w: 5.9, h: 4.5, name: "json-card" });
  text(
    s,
    [
      '{',
      '  "pattern":    "confirm_shaming",',
      '  "evidence":   "No thanks, I\u2019d rather',
      '                 pay full price",',
      '  "bbox":       [412, 889, 690, 921],',
      '  "severity":   "high",',
      '  "provision":  "CCPA 2023, Ann. I(3)",',
      '  "confidence": 0.86',
      '}',
    ].join("\n"),
    {
      x: M + 0.3,
      y: 1.95,
      w: 5.3,
      h: 2.5,
      fontSize: 11,
      fontFace: "Courier New",
      color: C.text2,
      isTextBox: true,
      margin: 0,
      lineSpacingMultiple: 1.3,
    }
  );
  text(
    s,
    "Plus a two-sentence explanation written for a non-technical consumer, and the DOM evidence where a URL was audited.",
    { x: M + 0.3, y: 4.75, w: 5.3, h: 1.1, fontSize: 12, color: C.text2 }
  );

  sectionHead(s, "The honest redesign", 7.0, 1.8, 5.7);
  card(s, { x: 7.0, y: 2.35, w: 5.7, h: 1.2, fill: "FBE9EC", name: "before" });
  text(s, "CURRENTLY", {
    x: 7.3,
    y: 2.5,
    w: 5.1,
    h: 0.25,
    fontSize: 9.5,
    bold: true,
    charSpacing: 1.2,
    color: C.accent1,
  });
  text(s, "\u201cNo thanks, I\u2019d rather pay full price\u201d", {
    x: 7.3,
    y: 2.8,
    w: 5.1,
    h: 0.6,
    fontSize: 14,
    italic: true,
    color: C.text1,
  });

  card(s, { x: 7.0, y: 3.7, w: 5.7, h: 1.2, fill: "E7F4ED", name: "after" });
  text(s, "HONEST VERSION", {
    x: 7.3,
    y: 3.85,
    w: 5.1,
    h: 0.25,
    fontSize: 9.5,
    bold: true,
    charSpacing: 1.2,
    color: C.accent4,
  });
  text(s, "\u201cNo thanks\u201d", {
    x: 7.3,
    y: 4.15,
    w: 5.1,
    h: 0.6,
    fontSize: 14,
    bold: true,
    color: C.text1,
  });

  bullets(
    s,
    [
      "Layout fix: give both options equal visual weight and remove the evaluative wording.",
      "Restores: symmetric choice.",
      "The business still gets to make the offer — it just cannot shame the user out of refusing.",
    ],
    { x: 7.0, y: 5.1, w: 5.7, h: 1.25, fontSize: 12, paraSpaceAfter: 6 }
  );
  s.addNotes(
    "The redesign is what makes this constructive rather than accusatory. Make the point that " +
      "we deliberately preserve the commercial intent — an honest interface may still sell, " +
      "advertise and charge; it may not mislead."
  );
}

/* ============================================= 13. EVALUATION DESIGN ===== */
pres.addSection({ title: "Evaluation" });
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Evaluation" });
  s.addText("How we measure it", { placeholder: "title" });

  card(s, { x: M, y: 1.7, w: 5.9, h: 4.5, name: "dataset-card" });
  sectionHead(s, "Dataset", M + 0.3, 1.95, 5.3);
  const comp = [
    ["~45–55", "deceptive", "e-commerce, travel, ticketing, food delivery, news"],
    ["~15–25", "clean controls", "government portals, university sites, minimal interfaces"],
  ];
  comp.forEach((c, i) => {
    const y = 2.55 + i * 1.1;
    text(s, c[0], {
      x: M + 0.3,
      y,
      w: 1.5,
      h: 0.45,
      fontSize: 20,
      bold: true,
      color: i === 0 ? C.accent1 : C.accent4,
    });
    text(s, c[1], {
      x: M + 1.85,
      y: y + 0.05,
      w: 3.4,
      h: 0.35,
      fontSize: 13,
      bold: true,
      color: C.text1,
    });
    text(s, c[2], { x: M + 0.3, y: y + 0.5, w: 5.3, h: 0.45, fontSize: 11.5, color: C.text2 });
  });
  text(
    s,
    "The controls are not optional. A detector that flags something on every screen looks impressive and is worthless — controls are the only way to expose that.",
    { x: M + 0.3, y: 4.9, w: 5.3, h: 1.1, fontSize: 12, bold: true, color: C.accent6 }
  );

  sectionHead(s, "Metrics", 7.0, 1.95, 5.7);
  bullets(
    s,
    [
      "Per-pattern precision, recall and F1",
      "Macro-F1 across all patterns with support",
      "False-positive rate on the clean controls",
      "Screenshot-level clean / deceptive accuracy",
      "Cohen's \u03ba between both annotators, overall and per pattern",
    ],
    { x: 7.0, y: 2.55, w: 5.7, h: 2.2, fontSize: 13 }
  );
  card(s, { x: 7.0, y: 4.85, w: 5.7, h: 1.35, fill: C.background2, name: "kappa-note" });
  text(
    s,
    "\u03ba also tells us how hard the task is for humans — which sets the honest ceiling for what the model can be expected to reach.",
    { x: 7.3, y: 5.05, w: 5.1, h: 1.0, fontSize: 12.5, color: C.text1 }
  );
  s.addNotes(
    "Both of us label all screenshots independently, without discussing them, then measure " +
      "agreement BEFORE reconciling. The pre-reconciliation kappa is the number that goes in " +
      "the report — measuring it after talking it through would be meaningless."
  );
}

/* ================================================= 14. ABLATION ========== */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Evaluation" });
  s.addText("The ablation: what the taxonomy is worth", { placeholder: "title" });

  const configs = [
    ["Zero-shot", "The 13 category names and nothing else — no rubrics, no examples.", "Baseline", C.accent5],
    ["+ Taxonomy rubrics", "Full inclusion and exclusion tests, with a violating example and a lawful lookalike for each.", "Expect recall \u2191", C.accent2],
    ["+ Adversarial verifier", "A second pass re-reads the image and must justify each finding or drop it.", "Expect precision \u2191", C.accent1],
  ];

  configs.forEach((cf, i) => {
    const x = M + i * 4.15;
    card(s, { x, y: 1.8, w: 3.8, h: 3.0, name: `config-${i}` });
    numberBadge(s, i + 1, x + 0.28, 2.05, 0.5, cf[3]);
    text(s, cf[0], {
      x: x + 0.28,
      y: 2.7,
      w: 3.25,
      h: 0.6,
      fontSize: 15,
      bold: true,
      color: C.text1,
    });
    text(s, cf[1], { x: x + 0.28, y: 3.35, w: 3.25, h: 1.1, fontSize: 11.5, color: C.text2 });
    text(s, cf[2], {
      x: x + 0.28,
      y: 4.4,
      w: 3.25,
      h: 0.3,
      fontSize: 11.5,
      bold: true,
      color: cf[3],
    });
  });

  card(s, { x: M, y: 5.1, w: W, h: 1.4, fill: C.background2, name: "honesty" });
  text(
    s,
    "These are hypotheses, not results. The numbers go in once the dataset is labelled — and if the data contradicts them, that is the more interesting finding and gets reported as such.",
    { x: M + 0.35, y: 5.3, w: W - 0.7, h: 1.0, fontSize: 14, bold: true, color: C.text1 }
  );
  s.addNotes(
    "Say the honesty line out loud. Examiners have heard a hundred decks claim 95% accuracy " +
      "with no dataset behind it. Stating the hypothesis before the result, and committing to " +
      "report a negative one, is the stronger position."
  );
}

/* ========================================== 15. STATUS & LIMITATIONS ===== */
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Evaluation" });
  s.addText("Where the project stands", { placeholder: "title" });

  card(s, { x: M, y: 1.7, w: 5.9, h: 4.6, fill: "E7F4ED", name: "done" });
  sectionHead(s, "Built and working", M + 0.3, 1.95, 5.3);
  bullets(
    s,
    [
      "All 13 rubrics encoded with inclusion and exclusion tests",
      "Detect → verify → DOM cross-check → rewrite pipeline",
      "Streamlit app: upload or URL, live annotated audit",
      "Pillow overlay renderer and ReportLab PDF export",
      "Evaluation harness with per-image prediction caching",
      "Cohen's \u03ba script and ablation chart generation",
      "Annotation guide with the labelling protocol and ethics rules",
    ],
    { x: M + 0.3, y: 2.5, w: 5.3, h: 3.6, fontSize: 12.5, paraSpaceAfter: 7 }
  );

  card(s, { x: 7.0, y: 1.7, w: 5.7, h: 4.6, name: "pending" });
  sectionHead(s, "Pending, and known limits", 7.3, 1.95, 5.1);
  bullets(
    s,
    [
      "Dataset collection and independent labelling of the full 60–80 screenshots",
      "The \u03ba on our 5-image pilot is not a reportable agreement figure — both label files are currently the same seed file",
      "5 of 13 patterns cannot be settled from one frame; confidence is capped at 0.50 for those",
      "Interface interference and disguised advertisement are expected to be the weakest categories",
      "Single-frame only: no multi-step flow analysis, no mobile app teardown",
    ],
    { x: 7.3, y: 2.5, w: 5.1, h: 3.6, fontSize: 12, paraSpaceAfter: 8 }
  );
  s.addNotes(
    "Be straight about the pilot. The harness is verified end to end on a 5-image smoke set; " +
      "the real dataset is in collection. Claiming a kappa of 1.0 from duplicate label files " +
      "would be the kind of thing a good examiner catches immediately."
  );
}

/* ================================================ 16. FUTURE SCOPE ======= */
pres.addSection({ title: "Closing" });
{
  const s = pres.addSlide({ masterName: "TITLE_ONLY", sectionTitle: "Closing" });
  s.addText("Future scope", { placeholder: "title" });

  const future = [
    ["Browser extension", "Audit the page the user is actually on, at the moment they are being manipulated — which is where the value really is."],
    ["Flow-level auditing", "Capture a multi-step checkout and compare frames. This makes false urgency, drip pricing and subscription traps properly decidable instead of capped at 0.50."],
    ["Regional languages with voice", "The users most exposed to these patterns are least likely to read English fine print."],
    ["Longitudinal tracking", "Re-audit the same sites over months and measure whether patterns actually disappear after regulation."],
  ];
  future.forEach((f, i) => {
    const y = 1.8 + i * 1.18;
    numberBadge(s, i + 1, 0.65, y + 0.1, 0.5, C.accent3);
    text(s, f[0], { x: 1.45, y: y + 0.08, w: 3.2, h: 0.55, fontSize: 15, bold: true, color: C.text1 });
    text(s, f[1], { x: 4.85, y: y + 0.03, w: 7.85, h: 1.0, fontSize: 12.5, color: C.text2 });
  });
  caption(s, "Flow-level auditing is the single highest-value extension: it removes the project's main stated limitation.", M, 6.6, W);
  s.addNotes(
    "If asked 'what would you do with another month', the answer is flow-level capture — " +
      "because it converts five of the thirteen patterns from undecidable to decidable."
  );
}

/* ================================================== 17. CONCLUSION ======= */
{
  const s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Closing" });
  s.addText("Conclusion", { placeholder: "title" });
  s.addText(
    [
      {
        text: "Dark patterns are already illegal in India. Enforcement is still done by hand, one screenshot at a time.",
        options: { breakLine: true, fontSize: 18, color: C.background1, bold: true },
      },
      {
        text: "",
        options: { breakLine: true, fontSize: 8 },
      },
      {
        text: "We built an auditor that names the tactic, boxes the evidence, cites the provision, explains the manipulation in plain language, and generates the honest version of the interface.",
        options: { breakLine: true, fontSize: 15, color: C.background2 },
      },
      {
        text: "",
        options: { breakLine: true, fontSize: 8 },
      },
      {
        text: "The technical contribution is the exclusion test — telling the model what the lawful lookalike of each pattern is. That is what separates an auditor from an alarm.",
        options: { breakLine: true, fontSize: 15, color: C.background2 },
      },
      {
        text: "",
        options: { breakLine: true, fontSize: 8 },
      },
      {
        text: "Next: label the full dataset, measure agreement, and publish the per-pattern numbers — including the ones that do not flatter the system.",
        options: { fontSize: 15, color: THEME.colors.accent2, italic: true },
      },
    ],
    { placeholder: "body" }
  );
  s.addNotes(
    "Close on the last line. Committing in advance to publishing unflattering numbers is the " +
      "most credible thing you can say in a project viva."
  );
}

/* ================================================== 18. REFERENCES ======= */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Closing" });
  s.addText("References", { placeholder: "title" });
  s.addText(
    [
      "Central Consumer Protection Authority, Guidelines for Prevention and Regulation of Dark Patterns, 2023. Ministry of Consumer Affairs, Government of India, 30 November 2023.",
      "Mathur, A. et al. Dark Patterns at Scale: Findings from a Crawl of 11K Shopping Websites. CSCW, 2019.",
      "Gray, C. M. et al. The Dark (Patterns) Side of UX Design. CHI, 2018.",
      "Groq API documentation — vision input and tool calling.",
      "Anthropic Claude API documentation — vision and structured tool use.",
      "Playwright, Streamlit, Pillow, ReportLab, scikit-learn — official library documentation.",
    ].map((t, i, arr) => ({
      text: t,
      options: { bullet: { type: "number" }, breakLine: i !== arr.length - 1 },
    })),
    { placeholder: "body", fontSize: 13, paraSpaceAfter: 10 }
  );
  s.addNotes(
    "Verify the exact category names and Annexure numbering against the original gazette " +
      "notification before submission — the audit output quotes the provision, so it has to be right."
  );
}

/* -------------------------------------------------------------- write out -- */
(async () => {
  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(SKILL_DIR + "/scripts/apply_theme.js");
  await applyTheme(OUT, THEME);
  console.log("Wrote " + OUT);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
