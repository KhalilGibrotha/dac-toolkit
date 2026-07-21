# DAC Toolkit

Documentation-as-Code toolkit that converts Markdown with YAML front matter into
styled DOCX documents with cover pages, table of contents, revision history,
auto-numbered headings, and embedded diagrams (Mermaid plus any
Kroki-supported language — PlantUML, Graphviz, D2, and more).

---

## Quick Start

```bash
cd docx_builder
pip install -e .

# Build a document
docx-build doc.md --output doc.docx

# With logo and org identity
docx-build doc.md --logo assets/logo/logo.png --org vars/org.yaml --output doc.docx
```

---

## What It Produces

Each DOCX has four sections:

| Section | Content |
|---|---|
| 1 — Cover | Logo or org name, document title, department, copyright footer |
| 2 — TOC | Table of contents (Word field + static fallback entries) |
| 3 — Revision | Revision history table and document metadata |
| 4 — Body | Rendered Markdown with auto-numbered headings |

---

## Repository Structure

```text
dac-toolkit/
├── docx_builder/           Python package — the DOCX renderer
│   ├── src/docx_builder/   Source modules
│   ├── tests/              Unit tests
│   ├── examples/           Sample input document
│   └── pyproject.toml      Package config (pip install -e .)
├── scripts/
│   ├── build-docs.sh       Full pipeline: diagrams + DOCX for a content repo
│   ├── docx_manifest.py    Manifest-driven content-repo render wrapper
│   ├── render-diagrams.sh  Batch render Mermaid .mmd files and fences
│   ├── render-decks.sh     Render Quarto .qmd decks to PowerPoint + QA gallery
│   └── lint-decks.py       Deck gate: source↔render pairing and package integrity
├── presentations/          Quarto → PowerPoint example (template, theme, palette)
├── templates/              Generic document templates (gap analysis, ADR, etc.)
├── diagrams/
│   └── mermaid-theme.css   Custom Mermaid CSS theme for mmdc
├── examples/
│   └── org.yaml            Example org identity config
├── .devcontainer/          Offline dev environment (Podman / Docker)
├── .vscode/                Editor settings, extensions, spellcheck
├── devfile.yaml            OpenShift Dev Spaces multi-repo workspace
└── .markdownlint.json      Markdown linting rules
```

---

## Presentations (Quarto → PowerPoint)

Alongside DOCX, the toolkit renders **Markdown-source presentation decks** to
PowerPoint. Author a `.qmd`, render to `.pptx`, and review per-slide PNGs —
figures come from executable Python chunks so charts stay on-brand and
regenerate from source. The bundled `presentations/` directory is a generic,
runnable example (template, code theme, matplotlib palette).

```bash
bash scripts/render-decks.sh --smoke                     # render the example (self-test)
bash scripts/render-decks.sh /path/to/content-repo --qa  # render a content repo's decks + QA gallery
python scripts/lint-decks.py /path/to/content-repo       # enforce source↔render pairing
```

Full routine, authoring rules, and the content-repo layout:
**[presentations/README.md](presentations/README.md)**.

---

## Using with a Content Repo

The toolkit is designed to sit alongside one or more content repos. A content
repo holds your Markdown documents, diagrams, and org-specific config:

```text
content-repo/
├── docs/           Published architecture content
├── initiatives/    Active initiative work
├── patterns/       Reusable patterns
├── governance/     ARB artifacts
├── decisions/      Architecture Decision Records
├── diagrams/       Source .mmd files and exported PNGs
├── vars/
│   └── org.yaml    Your org identity (name, dept, address, URL)
├── assets/
│   └── logo/logo.png   Your org logo
├── presentations/  Quarto decks + your branded template/theme/palette (optional)
└── exports/        Generated DOCX output
```

## Choosing What Gets Rendered

The toolkit supports two first-class ways to select which documents get
rendered, plus the original shell pipeline. All three are supported — none is
deprecated. Pick the one that matches how your repo decides what is
publishable.

| Approach | In one sentence |
|---|---|
| **Scan** — `docx-build-all` + `docx-build.yml` | Renders everything under the configured `scan:` folders, minus `exclude:` paths and status filters. |
| **Manifest** — `scripts/docx_manifest.py` + `manifests/render-manifest.yaml` | Renders exactly the documents listed in the manifest, nothing else. |
| **Shell pipeline** — `scripts/build-docs.sh` | The original path: pre-renders diagrams, then builds every front-mattered Markdown file under the conventional content folders. No config file required. |

### When to choose which

**Choose scan** when the repo's working set *is* the publication set: everything
under `docs/`, `governance/`, etc. should ship, and the interesting decisions
are which folders are in scope and which statuses to hold back. Its incremental
render index and `mirror` layout make it the right fit for repeatedly syncing
`exports/` to a document library as a folder.

**Choose manifest** when publication is curated: a deliberate subset of the
repo ships, and the explicit list is itself the governance artifact — a
reviewable, diffable record of what the org has agreed to publish. Also the
right fit when documents need per-document org/logo/output overrides, or when
pre-rendered diagram PNGs should be committed as reviewable assets (the
manifest wrapper rewrites fences to PNG files before the build; the builder
itself also renders any Kroki-supported fence inline on every path).

**Choose the shell pipeline** when you want zero configuration: point
`build-docs.sh` at a content repo shaped like the layout above and it builds
everything with front matter. It remains fully supported.

### Capability comparison

| Capability | `build-docs.sh` (shell) | `docx-build-all` (scan) | `docx_manifest.py` (manifest) |
|---|---|---|---|
| Selection model | Conventional folders (override via `DAC_DOC_DIRS`) | `scan:` + `exclude:` in `docx-build.yml` | Explicit `documents:` list in `render-manifest.yaml` |
| Config required | None | `docx-build.yml` | `manifests/render-manifest.yaml` |
| Output layout | Mirrors source tree under `exports/` | `status` (grouped by review state) or `mirror` | Mirrors source tree under `exports/` (per-document `output:` override) |
| Incremental rebuild | No — always rebuilds | Yes — render index skips unchanged version/status | No — always rebuilds |
| Status filtering | No | `skip_retired`, `skip_informational` | No — the list is the filter |
| Diagram handling | Pre-renders Mermaid sources, then the builder handles inline fences | Builder handles inline fences for any Kroki-supported language | Rewrites any Kroki-supported fence (Mermaid, PlantUML, Graphviz, D2, ...) to PNG via a Kroki service, then calls `docx-build` |
| Logo | Auto-detects `assets/logo/logo.png` | `logo:` key, `--logo` flag, or auto-detects `assets/logo/logo.png` | Per-document `logo:` key, or auto-detects `assets/logo/logo.png` |
| Org identity | Auto-detects `vars/org.yaml` | `org:` key, `--org` flag, or front matter | Per-document `org:` key, or auto-detects `vars/org.yaml` |
| Environment | Needs `docx-build` on PATH | Needs `docx-build-all` on PATH | Bootstraps its own `.venv-docx-render/` |

### Scan: build all documents with docx-build-all

Create `docx-build.yml` at the content repo root:

```yaml
export_root: exports/          # required — root folder for DOCX output
org: vars/org.yaml             # optional — org identity YAML (same as --org flag)
logo: assets/logo/logo.png     # optional — cover logo; auto-detected at this path if omitted
layout: mirror                 # optional — 'status' (default) or 'mirror'

scan:                          # required — folders to render
  - docs/
  - governance/
  - references/

exclude:                       # optional — paths to skip even if under scan
  - templates/
  - archive/

options:                       # optional
  skip_retired: true           # default: true
  skip_informational: false    # default: false
```

Then run it from anywhere inside the repo (it searches upward for the config):

```bash
docx-build-all                 # render changed documents
docx-build-all --dry-run       # report what would render, write nothing
docx-build-all --force         # re-render everything
```

Paths in the config are resolved relative to the config file's directory.
`--org` and `--logo` flags override the config keys.

### Manifest: build a curated list with docx_manifest.py

Create `manifests/render-manifest.yaml` at the content repo root:

```yaml
documents:
  - id: segmentation-overview
    input: docs/overview_segmentation_poc-architecture.md
  - id: aap-dr-adr
    input: decisions/adr_automation_aap-dr.md
    output: exports/published/adr_automation_aap-dr.docx   # optional override
```

Each entry needs `id` and `input`; `output`, `org`, and `logo` are optional
per-document overrides. Then run the wrapper from the content repo root:

```bash
python3 ../dac-toolkit/scripts/docx_manifest.py list --content-root . --manifest manifests/render-manifest.yaml
python3 ../dac-toolkit/scripts/docx_manifest.py validate --content-root . --manifest manifests/render-manifest.yaml
python3 ../dac-toolkit/scripts/docx_manifest.py render --content-root . --manifest manifests/render-manifest.yaml
```

The render wrapper:

- resolves manifest paths relative to the content repo
- falls back to `vars/org.yaml` and `assets/logo/logo.png` when present
- creates a local `.venv-docx-render/` and installs `docx-build` automatically if needed
- rewrites Kroki-supported fenced diagrams to generated PNG assets before calling `docx-build`

### Shell pipeline: build all documents with build-docs.sh

```bash
bash scripts/build-docs.sh /path/to/content-repo
```

The script auto-detects `vars/org.yaml` and `assets/logo/logo.png` in the
content directory and passes them to `docx-build`.

### Build a single document

```bash
docx-build /path/to/content-repo/docs/my-doc.md \
  --org /path/to/content-repo/vars/org.yaml \
  --output /path/to/content-repo/exports/my-doc.docx
```

---

## CLI Reference

```text
docx-build INPUT [--logo PATH] [--org PATH] [--output PATH]
```

| Flag | Description |
|---|---|
| `INPUT` | Path to Markdown file with YAML front matter |
| `--logo PATH` | Logo image (PNG/JPG) for cover page. Falls back to org name text. |
| `--org PATH` | YAML file with org identity overrides (name, dept, addr1, addr2, url) |
| `--output PATH` | Output .docx path. Defaults to input filename with .docx extension. |

```text
docx-build-all [--config PATH] [--org PATH] [--logo PATH] [--dry-run] [--force] [--report-file PATH]
```

| Flag | Description |
|---|---|
| `--config PATH` | Path to `docx-build.yml`. Defaults to searching upward from CWD. |
| `--org PATH` | Org identity YAML. Takes precedence over the `org:` config key. |
| `--logo PATH` | Logo image (PNG/JPG). Takes precedence over the `logo:` config key. |
| `--dry-run` | Report what would render; write nothing. |
| `--force` | Re-render all documents regardless of version or status match. |
| `--report-file PATH` | Write the build report to a file in addition to stdout. |

---

## Supported Markdown Elements

| Element | Rendered as |
|---|---|
| `# H1` `## H2` `### H3` | Auto-numbered headings: `1 — Title`, `1.1 — Subtitle` |
| Paragraphs | Body text, 10pt Calibri |
| `- bullet` `1. list` | Unordered and ordered lists with indent |
| `> blockquote` | Indented italic text |
| `` ```code``` `` | Monospace code block with gray background |
| `---` | Horizontal rule |
| `**bold**` `_italic_` | Inline bold and italic |
| `` `code` `` | Inline monospace |
| GFM pipe tables | Styled tables with header row and alternating row colors |
| `![alt](path)` | Embedded images (path relative to source .md file) |
| `` ```mermaid ``` `` | Mermaid diagrams rendered to PNG and embedded inline |
| `` ```plantuml ``` `` etc. | Any Kroki-supported diagram fence (PlantUML, Graphviz, D2, ...) rendered to PNG via Kroki — set `DOCX_BUILDER_KROKI_URL` for a self-hosted instance |

### Heading Numbering

All headings are automatically numbered. **Do not add manual numbers.**

| Write this | Renders as |
|---|---|
| `# Overview` | `1 — Overview` |
| `## Purpose` | `1.1 — Purpose` |
| `# Background` | `2 — Background` |

---

## Organization Identity

The cover page footer shows org name, department, address, and URL. Three ways
to set these (highest priority wins):

1. **`--org` CLI flag** — points to a YAML file (see `examples/org.yaml`)
2. **`org:` front matter block** — per-document override in Markdown
3. **`constants.py` defaults** — compiled-in fallback values

---

## Development Environment

The repo includes a containerized dev environment with all dependencies
pre-installed. See `.devcontainer/README.md` for setup.

| Environment | Config file |
|---|---|
| VS Code + Podman or Docker | `.devcontainer/devcontainer.json` |
| OpenShift Dev Spaces | `devfile.yaml` |

Both enforce offline operation — no outbound network connections at runtime.

### Workflow Boundaries

This repository is the long-term home for the documentation renderer and
documentation-first workflow. The intended split between this repo and the
Dev Space wrapper repo is documented here:

- [docs/repo-boundaries.md](docs/repo-boundaries.md)
- [docs/content-repo-conventions.md](docs/content-repo-conventions.md)
- [docs/backlog.md](docs/backlog.md)

### Multi-Repo Dev Spaces Workspace

Edit `devfile.yaml` to add your content repos to the `projects:` block:

```yaml
projects:
  - name: dac-toolkit
    git:
      remotes:
        origin: https://github.com/KhalilGibrotha/dac-toolkit
  - name: my-docs
    git:
      remotes:
        origin: https://github.com/your-org/my-docs
```

---

## Dependencies

```text
python-docx>=1.1.0
PyYAML>=6.0
mistune>=3.0
lxml>=4.9
```

Python 3.10+ required. Install with `pip install -e docx_builder`.

**Deck rendering** additionally needs Quarto plus `jupyter`, `matplotlib`, and
`pymupdf` for the figure chunks — all baked into the container images. The
optional `--qa` PNG gallery also needs LibreOffice, which is *not* in the images
(unavailable from the UBI9 repositories); `.pptx` rendering is unaffected.
Locally: `pip install jupyter matplotlib pymupdf`, plus Quarto and LibreOffice
if you want the gallery.

---

## License

MIT
