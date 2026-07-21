# DAC Toolkit Backlog

This backlog tracks work that belongs in the documentation renderer and
documentation-first workflow owned by `dac-toolkit`.

## Scope

- Renderer behavior, document layout, and asset handling
- Documentation-focused developer workflow
- Validation, diagnostics, and repeatable render quality
- Future migration of shared manifest behavior into the toolkit when the schema
  is stable

## Proposed Backlog

### Near Term

1. Define the repo boundary between `dac-toolkit` and `ansible-devspaces`.
   The target state should be:
   - `dac-toolkit` owns the documentation workflow, sample docs, render rules,
     and docs-focused Dev Space behavior.
   - `ansible-devspaces` owns automation development behavior and only the
     minimum integration needed to consume the documentation tooling.
2. Improve logo handling diagnostics.
   The renderer should make it obvious whether a logo path is missing, the file
   format is unsupported, or the image can be read but cannot be embedded
   cleanly.
3. Continue layout polish around heading and diagram pagination.
   The current keep-with-next behavior is an improvement, but diagram sections
   still need a clearer policy for keeping headings and rendered content
   together when space allows.
4. Evaluate an SVG-first render pipeline with a controlled PNG fallback.
   This should focus on readability for PlantUML and C4-PlantUML while keeping
   Word compatibility and predictable sizing.
5. Add a documented error taxonomy for preflight, lint, render, and DOCX
   assembly failures so content authors get the right feedback at the right
   stage.

### Next

6. Decide whether manifest behavior should remain wrapper-owned or move into
   the toolkit once the manifest schema settles.
7. Add smoke-test fixtures that exercise representative real-world documents in
   addition to the synthetic samples.
8. Add reusable render diagnostics for image dimensions, diagram format
   selection, and page-fit decisions to make troubleshooting easier.
9. Document recommended authoring guardrails for diagram-heavy documents,
   including image assets, heading structure, and diagram sizing expectations.

## Additional Recommended Items

1. Add CI smoke renders for the sample corpus so layout regressions are caught
   before promotion.
2. Add explicit test coverage for JPG, PNG, and SVG logo inputs.
3. Document the intended steady-state architecture once the docs-focused
   Dev Space is split from the automation-focused Dev Space.
