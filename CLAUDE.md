# DAC Toolkit — Claude Instructions

This is the public Documentation-as-Code toolkit. It provides the rendering engine, devcontainer, and automation scripts.

## Related Repos

This toolkit is designed to work alongside a private content repo and optionally
a knowledge-base vault. Each content repo has its own CLAUDE.md with authoring
conventions (document model, front matter requirements, style guide).

## This Repo Contains

- `docx_builder/` — Python package: Markdown + YAML → styled DOCX
- `.devcontainer/` — Offline devcontainer (Dockerfile, Dockerfile.devspaces, docker-compose)
- `scripts/` — build-docs.sh, render-diagrams.sh, vale-bootstrap.sh
- `templates/` — Document templates (generic, no org identity)
- `examples/` — Example org.yaml and sample inputs

## Key Constraints

1. **No org-specific content.** This is a public repo. Org identity comes from the content repo's `vars/org.yaml` via the `--org` flag.
2. **Offline by design.** The devcontainer runs with `network_mode: "none"`. All dependencies (Python, Node, mmdc, Vale, Chromium) are baked into the Docker image at build time.
3. **Vale styles are pre-baked.** `.vale-bootstrap.ini` defines packages downloaded during `docker build`. `scripts/vale-bootstrap.sh` copies them into content workspaces at container start.

## Critical Fragile Areas

1. `add_draft_watermark()` in cover_page.py — raw VML XML; namespaces must stay inline
2. `build_toc_page()` in toc.py — native Word TOC field + static fallback entries
3. Section sequencing in builder.py — Cover → TOC → Revision → Body
4. `_fix_zoom_attribute()` in builder.py — post-save ZIP patch; required
5. Schema ordering in xml_helpers.py — tcBorders before shd; pBdr at index 0

## Testing Changes

```bash
# Build a sample document
docx-build examples/sample_input.md --output /tmp/test.docx

# Build with org identity
docx-build examples/sample_input.md --org examples/org.yaml --output /tmp/test.docx

# Run tests
cd docx_builder && python -m pytest tests/
```
