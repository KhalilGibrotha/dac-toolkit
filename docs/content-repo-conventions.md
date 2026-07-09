# Content Repository Conventions

This document describes the target conventions for repositories that want a
low-friction Documentation-as-Code workflow with `dac-toolkit`.

## Objectives

- Keep document authoring conventions predictable
- Avoid hard-coding repo-specific paths into the renderer
- Make it easy for wrapper tooling to discover logos, org metadata, manifests,
  and outputs

## Recommended Repository Shape

```text
content-repo/
├── docs/
├── decisions/
├── patterns/
├── assets/
│   └── logo/
│       └── logo.png
├── vars/
│   └── org.yaml
├── manifests/
│   └── render-manifest.yaml
└── .docx-work/
```

Not every repository needs all of these folders, but the workflow should prefer
conventions like these over one-off path wiring.

## Intended Defaults

### Organization metadata

- Preferred shared file: `vars/org.yaml`
- Per-document override remains valid through front matter

### Logo

- Preferred shared path: `assets/logo/logo.png`
- JPG should also remain supported when PNG is not available

### Output naming

- Default output filename should match the source Markdown basename
- A document-specific override should exist when the output name must differ

### Output location

- Render output should prefer an unversioned working area
- The working area should mirror the repository name and output folder
  structure
- Wrapper tooling may provision this area differently by platform, but the
  resulting shape should stay predictable to the user

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
