# DAC Toolkit

Documentation-as-Code toolkit that converts Markdown with YAML front matter into
styled DOCX documents with cover pages, table of contents, revision history,
auto-numbered headings, and embedded Mermaid diagrams.

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
│   └── render-diagrams.sh  Batch render Mermaid .mmd files and fences
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
└── exports/        Generated DOCX output
```

### Build all documents in a content repo

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

---

## License

MIT
