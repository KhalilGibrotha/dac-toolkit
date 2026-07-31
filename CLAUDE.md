# dac-toolkit — Claude Instructions

The engine of the docs-as-code system: a self-contained container image that
content repos consume via devfile and CI. Content repos never clone this repo.

## Where Commands Run

**Container lane, and this repo builds the container.** Tests, renders, and
`dac-init` smoke runs go inside the image, not on the Windows host. Build and
run from **PowerShell** — Git Bash rewrites container mount paths and fails
with a misleading "workdir does not exist".

Scripts under `scripts/` execute in a Linux image. Author and test them there:
a CRLF ending or a lost exec bit is invisible on Windows and fatal in the
image, and `.gitattributes` cannot rescue a file git already classified as
binary (check `git ls-files --eol`, treat `i/-text` as the real signal).

**This is a PUBLIC repo.** No organization identifiers in files, commit
messages, or PR text. A session rooted in the private `architecture-docs` can
edit here freely, because the permission scope spans all of `E:\dev` — so that
constraint must be held deliberately rather than inferred from surroundings.

**Sibling repos** (full map in the global instructions): `E:\dev\dac-starter`
is the vendored starter, also public; `E:\dev\architecture-docs` is the private
production consumer of this image.

## Architecture

- **Image** (`ghcr.io/khalilgibrotha/dac-toolkit`): docx_builder installed as
  a package (`docx-build`, `docx-build-all`); `scripts/` on PATH at
  `/opt/dac-toolkit/scripts`; Vale + synced styles, markdownlint-cli2,
  pre-commit, Pandoc, Quarto, Mermaid CLI, prose-tuned vim/nano baked in.
- **`/opt/dac-toolkit/starter/`**: the dac-starter repo vendored at the pinned
  `STARTER_REF` (env in `docker-build.yml`), plus `manifest.json` and the
  append-only `stock-hashes.json`. This is the stock source for `dac-init`.
- **Layout contract:** `docx-build-all` finds `docx-build.yml` at a content
  repo's root or in its `dac/` folder; a `dac/` config anchors relative paths
  at the repo root.

## Two Different Devcontainers

`.devcontainer/` here is for **developing the engine**: it builds
`.devcontainer/Dockerfile` through compose, mounts this repo at `/workspace`,
runs `network_mode: none`, and editable-installs docx_builder.

Content repos carry a different one that **consumes the published image** —
no build, no compose, just `image:` plus the extension list. Do not copy this
repo's devcontainer into a content repo; they solve opposite problems.

`.devcontainer/devcontainer.json` is not in `MANAGED_ROOT_FILES`, so `dac-init`
does not install the content-repo devcontainer into an existing repository. It
arrives only by templating from dac-starter. Adding it to the managed set is a
deliberate change: it puts the file under `dac-update` control and requires a
`stock-hashes.json` append.

**Known defect — `scripts/vale-bootstrap.sh` has CRLF line endings.** The
`StylesPath` extraction fails under the container's bash, so it silently falls
back to the legacy `.vale/styles` path and reports success, leaving styles
where Vale will not look. `/opt/vale-styles` also bakes only RedHat and
write-good, not the `ai-tells` package content repos declare. Until both are
fixed, content repos sync Vale styles themselves rather than calling this
script.

Shell scripts in this repo run on Linux. Author and edit them in the Linux lane
— CRLF endings and lost exec bits are invisible on Windows and fatal in the
image.

## Key Constraints

1. **Public repo.** No organization identifiers anywhere — files, commit
   messages, PR and issue text. Org identity enters at build time in content
   repos via `--org`.
2. **Branch flow `develop → main`.** The image builds only on push to `main`
   (path-filtered) and on `v*` tags.

## Critical Fragile Areas

1. `add_draft_watermark()` in cover_page.py — raw VML XML; namespaces must stay inline
2. `build_toc_page()` in toc.py — native Word TOC field + static fallback entries
3. Section sequencing in builder.py — Cover → TOC → Revision → Body
4. `_fix_zoom_attribute()` in builder.py — post-save ZIP patch; required
5. Schema ordering in xml_helpers.py — tcBorders before shd; pBdr at index 0

## Release Process

1. Merge `develop → main`. The docker-build workflow runs: starter vendor +
   hash-history gate → Trivy gate (HIGH/CRITICAL, ignore-unfixed) → push
   `:latest` + `:sha` → provenance attestation + CycloneDX SBOM + cosign
   keyless signing.
2. Dispatch the **Release QA** workflow (runs inside the published image:
   tool presence, starter-tree integrity, dac-init contract, end-to-end
   render). Green is the precondition for tagging — the tag build verifies
   this mechanically.
3. Tag `vX.Y.Z` on main — the image publishes under that tag. Create the
   GitHub release with the digest and the cosign verify block.
4. **Starter changes:** after any edit to dac-starter's managed files, run
   `gen-stock-hashes.py --starter <checkout> --append` there and commit
   `stock-hashes.json`, or the image build gate fails. Bumping `STARTER_REF`
   in `docker-build.yml` is the deliberate human step that ships new stock
   configs into the image.

## Trivy Gate Fix Patterns

- **Base-layer RPM CVEs:** `dnf upgrade` early in the Dockerfile handles
  fixable erratas. If the gate still fires on a fixable RPM, the GHA layer
  cache is stale — invalidate and rebuild.
- **npm transitive CVEs:** never `npm install` a fix inside a globally
  installed package (npm nests the package inside itself). Pattern: dedicated
  `/opt/<tool>` install with a `package.json` using `overrides`, bin
  symlinked onto PATH. Example: `/opt/markdownlint`.
- **Prebuilt Go binaries** (gh, vale, esbuild): Go-stdlib CVEs compiled in
  upstream; path-scoped `skip-files` entries in the workflow, version-pinned
  so a bump re-asks the question.

## Testing Changes

```bash
docx-build examples/sample_input.md --org examples/org.yaml --output /tmp/t.docx
cd docx_builder && python -m pytest tests/
# dac-init smoke (no image needed): stage a vendor dir, then
python scripts/dac-init --path <tmp-repo> --starter-dir <vendor> --dry-run
```

## Cross-Repo Tooling

Repo-management scripts live in `../claude-repo-tools` — see that repo's
README for the current command set. `verify-docx.sh` (render + heading tree)
is the one used routinely from here.
