# Presentation Rendering

Markdown-source presentation decks rendered to PowerPoint (`.pptx`) via Quarto.
The `.qmd` source is the artifact you author and review; the `.pptx` is a
generated build product. Figures come from executable Python chunks
(matplotlib), so charts are on-brand and regenerate from source.

This directory is a **working example**. In practice the toolkit renders decks
for a *content repo* that brings its own template, theme, and `.qmd` sources —
see [Using with a content repo](#using-with-a-content-repo).

---

## Quick start

```bash
# from the toolkit (renders this example)
bash scripts/render-decks.sh --smoke

# render every deck in a content repo
bash scripts/render-decks.sh /path/to/content-repo

# render one deck, then export per-slide PNGs for visual review
bash scripts/render-decks.sh /path/to/content-repo --qa my-deck.qmd
```

`render-decks.sh` reads decks from `CONTENT_DIR/presentations/*.qmd` and writes
`.pptx` into `CONTENT_DIR/presentations/exports/`. `CONTENT_DIR` defaults to
`$WORKSPACE` or the current directory. QA images go to `$TMPDIR/deck-qa/<deck>/`
— never into a repo.

---

## The routine

1. **Author** a `.qmd` deck. Each `## Heading` starts a slide (`slide-level: 2`).
2. **Render** with `render-decks.sh` — Quarto runs the executable chunks and
   builds the `.pptx`.
3. **Review** the output. `--qa` converts each slide to a PNG (LibreOffice →
   PDF → pymupdf) and writes a dark contact-sheet `index.html` — the "QA floor."
   Inspect every slide for overflow and clipping; the most common defect is a
   last bullet falling off the frame.
4. **Commit the `.pptx` beside its source** in the same change. A stale render
   is a defect; `lint-decks.py` enforces the pairing (see below).

```bash
python scripts/lint-decks.py /path/to/content-repo
```

The lint gate checks that every non-underscore `.qmd` has a committed,
package-intact `.pptx` in `exports/`, and that no orphan `.pptx` lingers.
Rendering is **not** run in CI; freshness is a review convention (re-render in
the same PR that edits a source).

---

## Authoring rules

- `## Heading` starts a slide; keep **one idea per slide**.
- Write titles as **claims**, not labels ("Costs fell 30% after the migration",
  not "Cost trend").
- Put the narrative in **speaker notes** (`::: {.notes}` … `:::`), not on the slide.
- **A table OR a list on a slide, not both** — pandoc splits a slide carrying a
  table *and* a list into two slides. Move one into the notes.
- Underscore-prefixed files (`_scratch.qmd`) are **skipped** by the renderer and
  the lint gate — use them for scratch/iteration.

---

## Figures

Hero visuals are executable Python chunks styled by `assets/deck_mpl.py`:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path("assets").resolve()))
import deck_mpl
deck_mpl.use()          # applies the palette + transparent figure background
```

`deck_mpl.py` ships a **generic placeholder palette**. Swap the hex values for
your brand and re-validate them for a dark chart surface before production —
bright accent hues are line/label steps only; solid fills use the darker
in-band `*_FILL` steps. (Any categorical-palette validator that checks
lightness band, chroma floor, colorblind separation, and contrast will do.)

Requires `jupyter` and `matplotlib` in the environment (baked into the
container image; `pip install jupyter matplotlib` locally).

---

## Deck front matter

```yaml
---
title: "Example Deck"
subtitle: "One line under the title"
format:
  pptx:
    reference-doc: "templates/example-dark.pptx"   # your template
    highlight-style: "themes/deck-code.theme"       # code colors
    monofont: Consolas
execute:
  echo: false
  warning: false
jupyter: python3
---
```

Do **not** set `author`/`date` in deck front matter — pandoc appends them into
the subtitle placeholder. Put presenter identity in the template's title-slide
art instead.

`_quarto.yml` in this directory sets `output-dir: exports` so renders land in
`exports/` rather than beside the source.

---

## What ships here

```text
presentations/
├── README.md                     this file
├── _quarto.yml                   output-dir: exports
├── example_deck.qmd              the example / smoke corpus
├── exports/example_deck.pptx     committed render (review copy)
├── assets/deck_mpl.py            generic matplotlib palette helper
├── templates/example-dark.pptx   generic dark reference template
└── themes/deck-code.theme        generic terminal code-highlight theme
```

---

## Using with a content repo

The toolkit owns the rendering; your content repo owns its identity. A content
repo mirrors this layout with **its own** template, theme, palette, and sources:

```text
content-repo/
└── presentations/
    ├── assets/<brand>_mpl.py      your palette (swap deck_mpl's colors)
    ├── templates/<brand>.pptx     your branded reference template
    ├── themes/<brand>.theme       your code theme
    ├── exports/                   committed renders
    └── *.qmd                      your decks
```

Then render from anywhere:

```bash
bash /path/to/dac-toolkit/scripts/render-decks.sh /path/to/content-repo --qa
```

No org identity, template, or content lives in this toolkit — only the engine
and this generic example.

---

## In Dev Spaces / containers

The container image bakes in Quarto, pandoc, and the Python figure
dependencies (`jupyter`, `matplotlib`, `pymupdf`) — verified by rendering a
deck end to end inside the image. It does **not** include LibreOffice, which
is unavailable from the UBI9 repositories, so the `--qa` slide-image gallery
does not run in-container. `.pptx` rendering is unaffected. Clone the toolkit
and your content repo into the workspace, then:

```bash
bash dac-toolkit/scripts/render-decks.sh my-content-repo --qa
```

Rendering the `.pptx` needs only Quarto + Python; the `--qa` PNG gallery
additionally needs LibreOffice. Where LibreOffice is absent — including the
current container image — rendering still succeeds and `--qa` reports the
skipped gallery. Review the `.pptx` directly, or run `--qa` on a host that has
LibreOffice installed.
