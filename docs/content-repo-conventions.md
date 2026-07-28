# Content Repository Conventions

This document describes the target conventions for repositories that want a
low-friction Documentation-as-Code workflow with `dac-toolkit`.

## Objectives

- Keep document authoring conventions predictable
- Avoid hard-coding repo-specific paths into the renderer
- Make it easy for wrapper tooling to discover logos, org metadata, manifests,
  and outputs

## Recommended Repository Shape

`dac/` is the machinery folder, holding everything the toolchain needs that
isn't content, and it is the canonical layout. Get it with `dac-init` rather
than assembling it by hand; see the toolkit README's Quick Start.

```text
content-repo/
├── docs/
├── decisions/
├── patterns/
├── dac/
│   ├── org.yaml               # org identity — copy from org.yaml.example
│   ├── logo.png                # you add this
│   ├── docx-build.yml          # scan-based selection (docx-build-all)
│   └── render-manifest.yaml    # curated selection (docx_manifest.py)
└── exports/
```

Not every repository needs all of these folders, but the workflow should prefer
conventions like these over one-off path wiring.

A root-level `docx-build.yml` with `vars/org.yaml` and `assets/logo/logo.png`
is the legacy shape. `docx-build-all` still finds a config there, but it
predates `dac/` and isn't the target for new repos.

## Intended Defaults

### Organization metadata

- Preferred shared file: `dac/org.yaml`
- Per-document override remains valid through front matter
- `docx-build-all` requires this as an explicit `org:` key (or `--org` flag);
  there is no auto-detected default for org identity

### Logo

- Preferred shared path: `dac/logo.png`, set explicitly via the `logo:` key
  in `dac/docx-build.yml`
- JPG should also remain supported when PNG is not available
- Auto-detection without an explicit `logo:` key checks `dac/logo.png`
  first and falls back to `assets/logo/logo.png` at the repo root (the
  legacy path). `docx-build-all`, `docx_manifest.py`, and `build-docs.sh`
  all follow this order; the latter two also honor `DAC_LOGO` /
  `DAC_ORG_YAML` environment overrides.

### Output naming

- Default output filename should match the source Markdown basename
- A document-specific override should exist when the output name must differ

### Output location

- Render output should prefer an unversioned working area
- The working area should mirror the repository name and output folder
  structure
- Wrapper tooling may provision this area differently by platform, but the
  resulting shape should stay predictable to the user

## Content Selection: Two First-Class Approaches

A content repo declares what gets rendered in one of two ways. Both are
supported long-term — they answer different governance questions, and a repo
picks the one that matches how it decides what is publishable.

### Scan (`dac/docx-build.yml` + `docx-build-all`)

The repo's working set is the publication set. `docx-build.yml` names the
folders in scope (`scan:`), carve-outs (`exclude:`), and status filters;
everything that qualifies renders. This suits repos that publish the whole
working set and sync `exports/` to a document library as a folder — the
incremental render index and the `mirror` layout exist for exactly that
workflow.

### Manifest (`dac/render-manifest.yaml` + `docx_manifest.py`)

Publication is curated. The manifest is an explicit, reviewable list of
documents, and the list itself is the governance artifact: a diff to the
manifest *is* the record of a publication decision. This suits repos where a
deliberate subset ships, where documents need per-document org/logo/output
overrides, or where diagram fences should be pre-rendered to committed PNG
assets (the wrapper rewrites any Kroki-supported fence type; the builder also
renders those fences inline on every path).

`build-docs.sh` remains the original zero-config shell path — conventional
folders, everything with front matter — and stays supported alongside both.

See the toolkit README for a full capability comparison and worked examples
of each config.

## Manifest Direction

The current manifest experiments belong in the wrapper layer, but the target
behavior is clear:

- a repo can provide one root manifest for common defaults
- child manifests can segment large repositories
- shared `logo` and `org` settings should be inherited unless overridden
- authors should not need to repeat output filenames when the default name is
  acceptable

## Validation Expectations

The full workflow should eventually fail at the earliest correct layer:

1. Authoring and repo-shape issues at preflight time
2. Diagram syntax and renderability during lint/render validation
3. DOCX assembly issues during final document build

That separation should remain part of the toolkit contract even when wrappers
add platform-specific convenience.
