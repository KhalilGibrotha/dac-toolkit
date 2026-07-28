# DAC Toolkit

Documentation-as-Code toolkit that converts Markdown with YAML front matter into
styled DOCX documents with cover pages, table of contents, revision history,
auto-numbered headings, and embedded diagrams (Mermaid plus any
Kroki-supported language — PlantUML, Graphviz, D2, and more).

---

## Quick Start: Adopt This Engine

This toolkit ships as a container image. Content repos consume that image;
they never clone `dac-toolkit`. Adopting it means getting the managed file
set into your repo, getting the image running, and building.

### 1. Get a repo with the managed files

**New repo:** start from the
[dac-starter](https://github.com/KhalilGibrotha/dac-starter) template.
Either click **Use this template** on that repo's GitHub page, or clone and
re-init:

```bash
git clone https://github.com/KhalilGibrotha/dac-starter my-docs
cd my-docs
rm -rf .git && git init
```

**Existing repo:** run `dac-init` (below) instead of copying files by hand.
It installs the managed set (the devfile, lint config, CI workflow, and
everything under `dac/` except your org identity) and never touches a file
you already have.

### 2. Get the tools running

Every tool the workflow needs (`docx-build-all`, Vale, markdownlint, the lint
scripts, `dac-init`, `dac-update`) lives in the image. There are two ways to
reach it.

**Locally with podman** works on any machine, no cluster required:

```bash
podman machine start    # macOS/Windows only, if the machine isn't already up
podman run --rm -v "$PWD:/work:Z" -w /work \
  ghcr.io/khalilgibrotha/dac-toolkit:latest docx-build-all
```

> The `$PWD` form above is for bash/zsh on Linux or macOS. Two other shells
> need a different form — both verified:
>
> **Windows Git Bash** silently mangles the `-v` path through MSYS's path
> conversion. Use this instead:
>
> ```bash
> MSYS_NO_PATHCONV=1 podman run --rm -v "C:\path\to\repo://work:z" -w //work \
>   ghcr.io/khalilgibrotha/dac-toolkit:latest docx-build-all
> ```
>
> **Windows PowerShell** rejects bare `$PWD` in a quoted string — the colon
> after it parses as a drive reference. Brace the variable:
>
> ```powershell
> podman run --rm -v "${PWD}:/work:Z" -w /work `
>   ghcr.io/khalilgibrotha/dac-toolkit:latest docx-build-all
> ```
>
> **If a command hangs or fails to connect,** the podman machine is probably
> stopped, not the tooling: `podman machine list` shows its state; `podman
> machine start` brings it up. This is the single most common first-run
> failure and it looks like broken tooling if you don't know to check it.

**OpenShift Dev Spaces**, if your organization runs it: paste the repo's Git
URL into **Import from Git**. The workspace starts on this image with every
tool preinstalled. Ask your platform team for your organization's Dev Spaces
URL — it isn't a fixed address this doc can print.

### 3. Set your org identity

Copy `dac/org.yaml.example` to `dac/org.yaml` and fill in your
organization's name, department, and address. Add a logo as `dac/logo.png`
and uncomment the `logo: dac/logo.png` line in `dac/docx-build.yml`.

### 4. Write and build

Copy a template from `dac/templates/` into `docs/` (or another content
folder), fill in the front matter, and write. Then:

```bash
docx-build-all
```

Your styled Word document lands in `exports/`.

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

## dac-init: Adopting or Re-Syncing the Managed File Set

`dac-init` installs the toolkit's managed file set into any git repo:
`devfile.yaml`, `.vale.ini`, `.markdownlint.json`, `.pre-commit-config.yaml`,
`.github/workflows/lint.yml`, `.vscode/settings.json`, `.vscode/extensions.json`,
and everything under `dac/` except `dac/org.yaml`, `dac/logo.png`, and
`dac/.dac-manifest.json`. Those three hold your identity and this tool's own
records, so it never touches them.

```bash
podman run --rm -v "$PWD:/work:Z" -w /work \
  ghcr.io/khalilgibrotha/dac-toolkit:latest dac-init --dry-run   # report only
podman run --rm -v "$PWD:/work:Z" -w /work \
  ghcr.io/khalilgibrotha/dac-toolkit:latest dac-init             # install
```

(On Windows, see the Git Bash / PowerShell forms under Quick Start step 2 above.)

- **Never overwrites an existing file.** A file already present is left
  alone and reported as `present, skip`.
- **Idempotent.** A second run against a fully-adopted repo changes nothing:
  `0 installed, N already present`.
- **`--force` replaces the whole managed set, not one file.** Every file it
  overwrites is saved as `<file>.orig` first, but the replacement isn't a
  per-file diff; it's all-or-nothing. `dac-update` (below) is the
  per-file-aware tool.
- **`--dry-run` writes nothing.** It lists exactly what would install.
- Every real run records provenance in `dac/.dac-manifest.json`: starter
  version, engine image, install date, and a hash per installed file.
- Requires a `.git` directory at the target when run against the current
  directory. Pass `--path <dir>` to target a different repo; doing so skips
  the `.git` check.

`dac-init` doesn't create your content folders, `dac/org.yaml`, or
`dac/logo.png`. It gets the tooling in place. Org identity and your first
documents are still yours to add (step 3 in the Quick Start above).

Hand-copying the same files works too, and remains a documented fallback,
but `dac-init` is the supported path: it won't clobber something you already
customized, and it's the only path `dac-update` (below) knows how to build
on.

---

## dac-update: Upgrading an Adopted Repo

`dac-update` is the supported upgrade path for a repo that has already run
`dac-init`. It requires `dac/.dac-manifest.json`; if that file is missing,
`dac-update` fails and tells you to run `dac-init` first.

> `dac-update` ships in `scripts/` on this branch but had not yet reached the
> published `:latest` image as of this writing — the `podman run` commands
> below will work once a release ships it. Until then, run the script
> directly from a `dac-toolkit` checkout, pointing `--starter-dir` at a
> staged starter tree (see `CLAUDE.md`'s Testing Changes section):
> `python scripts/dac-update --path <target-repo> --starter-dir <vendor-dir>`.

```bash
podman run --rm -v "$PWD:/work:Z" -w /work \
  ghcr.io/khalilgibrotha/dac-toolkit:latest dac-update --dry-run
podman run --rm -v "$PWD:/work:Z" -w /work \
  ghcr.io/khalilgibrotha/dac-toolkit:latest dac-update
```

(On Windows, see the Git Bash / PowerShell forms under Quick Start step 2 above.)

For every managed file, `dac-update` compares your copy against the history
of stock revisions and picks one of four outcomes:

| Outcome | Meaning | What happens |
|---|---|---|
| `skip` | Your file already matches the current stock version | Nothing |
| `replace` | Your file is unmodified, but an older stock revision | Updated in place |
| `keep+new` | Your file matches no known stock revision — it's locally customized | Your file is untouched; the new stock version is written beside it as `<file>.new` |
| `install` | The file is new to the managed set since you last synced | Installed |

`keep+new` is a normal outcome, not an error — it means you changed
something, and `dac-update` won't guess which version to keep. Scan the
output for `keep+new` lines, review each `<file>.new` by hand, merge what you
want, then delete the `.new` copy.

The comparison normalizes content first (strips a BOM, unifies line endings,
collapses to one trailing newline), so a Windows checkout with CRLF line
endings is correctly seen as unmodified. Line endings alone never produce a
false `keep+new`.

`--dry-run` reports the same four-way breakdown without writing anything.
Every run, dry or real, ends with a count summary. The exit code is
non-zero only for setup problems: no starter tree available, no `.git`, no
`dac/.dac-manifest.json`. A run that reports `keep+new` files still exits 0.
Reconciling those `.new` files is a manual step you have to look for; it
doesn't fail the run.

---

## Knowing What Version You're On

Nothing in the build path (`docx-build`, `docx-build-all`) prints a version
tied to a release. `docx_builder`'s internal version string isn't wired to
the image tag. Two places record something checkable instead:

- **`dac/.dac-manifest.json`**, written by `dac-init` and updated by
  `dac-update`. `starter_version` and `engine_image` say which stock
  revision and which image your repo last synced against; `installed` and
  `updated` record the dates.
- **`devfile.yaml`**'s `image:` line pins (or leaves at `:latest`) the
  container image your Dev Spaces workspace runs. CI's
  `.github/workflows/lint.yml` pins its own image reference the same way,
  and the two should agree.

There's currently no CHANGELOG or release notes tying a stock revision to
what changed in it. A repo that wants to know what changed since its last
`dac-update` has nothing to read for that beyond `stock-hashes.json`'s raw
hash history and the toolkit's own commit log. That's a real gap worth
closing, not one this document can paper over.

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
│   ├── dac-init            Install the managed file set into a content repo
│   ├── dac-update          Sync an adopted repo's managed files to current stock
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
repo holds your Markdown documents, diagrams, and org-specific config. `dac/`
is the machinery folder, holding everything the toolchain needs that isn't
content, and it is the canonical layout for new and existing repos alike:

```text
content-repo/
├── docs/               Published architecture content
├── initiatives/        Active initiative work
├── patterns/           Reusable patterns
├── governance/         ARB artifacts
├── decisions/          Architecture Decision Records
├── diagrams/           Source .mmd files and exported PNGs
├── dac/
│   ├── docx-build.yml       Scan config for docx-build-all
│   ├── org.yaml              Your org identity — copy from org.yaml.example
│   ├── logo.png               Your org logo (you add this)
│   ├── templates/             Document templates — copy one to start a document
│   └── render-manifest.yaml  Optional, for the manifest render path
├── presentations/      Quarto decks + your branded template/theme/palette (optional)
└── exports/            Generated DOCX output
```

Get this layout with `dac-init` (above) rather than copying files by hand.
Hand-copying remains a documented fallback for repos that can't run the
image against themselves, but it isn't the primary path. It skips the
never-overwrite protection and the `dac/.dac-manifest.json` record that
`dac-update` depends on later.

> **Legacy layout.** A root-level `docx-build.yml` with `vars/org.yaml` and
> `assets/logo/logo.png` still works. `docx-build-all` finds a
> `docx-build.yml` at the repo root the same way it finds one in `dac/`, but
> it predates the `dac/` layout and is not what new repos should adopt. If
> you're on it, migrating to `dac/` is worth doing; nothing about the legacy
> layout is a supported target for new work.

## Choosing What Gets Rendered

The toolkit supports two first-class ways to select which documents get
rendered, plus the original shell pipeline. All three are supported — none is
deprecated. Pick the one that matches how your repo decides what is
publishable.

| Approach | In one sentence |
|---|---|
| **Scan** — `docx-build-all` + `dac/docx-build.yml` | Renders everything under the configured `scan:` folders, minus `exclude:` paths and status filters. |
| **Manifest** — `scripts/docx_manifest.py` + `render-manifest.yaml` | Renders exactly the documents listed in the manifest, nothing else. |
| **Shell pipeline** — `scripts/build-docs.sh` | The original path: pre-renders diagrams, then builds every front-mattered Markdown file under the conventional content folders. No config file required. |

Scan is the only one of the three that understands the `dac/` layout today —
it finds `dac/docx-build.yml` on its own and anchors relative paths at the
repo root. The manifest wrapper and the shell pipeline still default to the
legacy `vars/org.yaml` / `assets/logo/logo.png` paths; under `dac/`, point
them at `dac/` explicitly (shown below). Migrating those two defaults to
`dac/` is open engineering work, not yet done.

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
| Selection model | Conventional folders (override via `DAC_DOC_DIRS`) | `scan:` + `exclude:` in `dac/docx-build.yml` | Explicit `documents:` list in a manifest YAML |
| Config required | None | `dac/docx-build.yml` (or root `docx-build.yml`, legacy) | A manifest file, e.g. `dac/render-manifest.yaml` |
| Output layout | Mirrors source tree under `exports/` | `status` (grouped by review state) or `mirror` | Mirrors source tree under `exports/` (per-document `output:` override) |
| Incremental rebuild | No — always rebuilds | Yes — render index skips unchanged version/status | No — always rebuilds |
| Status filtering | No | `skip_retired`, `skip_informational` | No — the list is the filter |
| Diagram handling | Pre-renders Mermaid sources, then the builder handles inline fences | Builder handles inline fences for any Kroki-supported language | Rewrites any Kroki-supported fence (Mermaid, PlantUML, Graphviz, D2, ...) to PNG via a Kroki service, then calls `docx-build` |
| Logo | Hardcoded to `assets/logo/logo.png` | `logo:` key (required under `dac/` — see below), `--logo` flag, or auto-detects `assets/logo/logo.png` at the repo root | Per-document `logo:` key, or auto-detects `assets/logo/logo.png` |
| Org identity | Hardcoded to `vars/org.yaml` | `org:` key, `--org` flag, or front matter | Per-document `org:` key, or auto-detects `vars/org.yaml` |
| Environment | Needs `docx-build` on PATH | Needs `docx-build-all` on PATH | Bootstraps its own `.venv-docx-render/` |

### Scan: build all documents with docx-build-all

Create `dac/docx-build.yml`:

```yaml
export_root: exports/          # required — root folder for DOCX output
org: dac/org.yaml              # optional — org identity YAML (same as --org flag)
logo: dac/logo.png             # optional — cover logo; set explicitly under dac/, see note below
layout: mirror                 # optional — 'status' (default) or 'mirror'

scan:                          # required — folders to render
  - docs/
  - governance/
  - references/

exclude:                       # optional — paths to skip even if under scan
  - dac/
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

When `docx-build.yml` lives in `dac/`, `scan:`, `exclude:`, and
`export_root:` resolve relative to the repo root, not `dac/` — `scan:
docs/` means `<repo>/docs`, and the shipped starter config's `exclude: -
dac/` follows the same rule. `--org` and `--logo` flags override the config
keys.

> **Logo auto-detection only checks `assets/logo/logo.png` at the repo
> root**, the legacy path, even when the config lives in `dac/`. Under the
> `dac/` layout, set `logo: dac/logo.png` explicitly (uncomment it in the
> starter's config) rather than relying on auto-detect. `org:` has no
> auto-detect fallback either way — set it explicitly or the cover falls
> back to front matter, then compiled-in defaults.

### Manifest: build a curated list with docx_manifest.py

Create a manifest, e.g. `dac/render-manifest.yaml`:

```yaml
documents:
  - id: segmentation-overview
    input: docs/overview_segmentation_poc-architecture.md
    org: dac/org.yaml                                       # explicit under dac/ — see note below
  - id: aap-dr-adr
    input: decisions/adr_automation_aap-dr.md
    output: exports/published/adr_automation_aap-dr.docx    # optional override
```

Each entry needs `id` and `input`; `output`, `org`, and `logo` are optional
per-document overrides. Then run the wrapper from the content repo root:

```bash
python3 ../dac-toolkit/scripts/docx_manifest.py list --content-root . --manifest dac/render-manifest.yaml
python3 ../dac-toolkit/scripts/docx_manifest.py validate --content-root . --manifest dac/render-manifest.yaml
python3 ../dac-toolkit/scripts/docx_manifest.py render --content-root . --manifest dac/render-manifest.yaml
```

The render wrapper:

- resolves manifest paths relative to the content repo
- defaults to `--manifest manifests/render-manifest.yaml` if you omit the
  flag — under `dac/`, always pass `--manifest dac/render-manifest.yaml`
  explicitly
- falls back to `vars/org.yaml` and `assets/logo/logo.png` when present and
  no per-document `org:`/`logo:` is set — this fallback does not know about
  `dac/`, so set `org: dac/org.yaml` (and `logo:`, if you use one) per
  document under the `dac/` layout, as shown above
- creates a local `.venv-docx-render/` and installs `docx-build` automatically if needed
- rewrites Kroki-supported fenced diagrams to generated PNG assets before calling `docx-build`

### Shell pipeline: build all documents with build-docs.sh

```bash
bash scripts/build-docs.sh /path/to/content-repo
```

The script looks for `vars/org.yaml` and `assets/logo/logo.png` in the
content directory and passes them to `docx-build` if found — this is a fixed
legacy path with no `dac/` awareness and no override flag yet. On a `dac/`-
layout repo, `build-docs.sh` builds documents without org identity or a logo
unless you also keep a `vars/org.yaml` around, or build single documents with
`docx-build` directly (below) and pass `dac/org.yaml` yourself.

### Build a single document

```bash
docx-build /path/to/content-repo/docs/my-doc.md \
  --org /path/to/content-repo/dac/org.yaml \
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

> **This section is for people developing `dac-toolkit` itself** — changing
> `docx_builder`'s Python source, the lint scripts, or the image. If you're
> adopting the engine for a content repo, you want the Quick Start at the top
> of this document instead; you never clone this repo for that.

### Quick Start (Toolkit Maintainers)

```bash
cd docx_builder
pip install -e .

# Build the bundled sample
docx-build examples/sample_input.md --org ../examples/org.yaml --output /tmp/t.docx

# With a logo too
docx-build doc.md --logo path/to/logo.png --org path/to/org.yaml --output doc.docx
```

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
