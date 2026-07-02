# Repository Boundaries

This document defines the intended ownership split between `dac-toolkit` and
`ansible-devspaces`.

## Goal

The documentation workflow should be able to evolve independently from the
automation development workspace. The current implementation spans both repos,
but the steady-state design should reduce that overlap.

## Ownership Model

### `dac-toolkit` owns

- DOCX rendering behavior
- Diagram embedding behavior and image format decisions
- Logo, organization, and cover-page handling
- Author-facing validation rules and render diagnostics
- Documentation-focused examples, sample corpus, and workflow guidance
- Documentation-first Dev Space expectations once a dedicated docs workspace is
  carved out

### `ansible-devspaces` owns

- Automation-focused OpenShift Dev Spaces bootstrap behavior
- Repository cloning and workspace assembly for automation work
- Minimal wrapper commands required to invoke the documentation tooling from a
  Dev Space
- Integration-specific environment wiring such as paths, bootstrap, and local
  convenience commands

## Boundary Rules

1. Core rendering logic belongs in `dac-toolkit`.
   Wrapper scripts may orchestrate the renderer, but should not become a second
   rendering implementation.
2. Shared schema decisions should stabilize before they are promoted into the
   toolkit package.
   During experimentation, manifest orchestration can stay in the wrapper
   layer.
3. Documentation authoring conventions should be defined once, in the toolkit
   docs, and consumed by wrapper repos rather than redefined there.
4. Dev Space-specific convenience should not dictate the core renderer API.
   If a feature is generally useful outside OpenShift Dev Spaces, it should
   bias toward toolkit ownership.
5. Automation workspace concerns should not force documentation repos to adopt
   automation-specific folder layouts.

## Near-Term Direction

### Keep in `ansible-devspaces` for now

- `docx-render-one` and other Dev Space convenience targets
- Manifest discovery experiments
- Working-folder provisioning logic
- Bootstrap behavior for cloned repos
- Real-world corpus evaluation against `architecture-docs`

### Move or formalize in `dac-toolkit` once stable

- Reusable manifest schema and validation rules
- Author-facing render error taxonomy
- Default docs repo conventions for logos, org metadata, and outputs
- Sample corpus and renderer regression fixtures

## Decision Criteria for a Dedicated Docs Dev Space

A dedicated docs Dev Space becomes justified when most of the following are
true:

- The primary workflow is authoring and rendering documents rather than
  developing automation.
- The wrapper logic is mostly documentation-oriented.
- The default cloned repos are docs/content repos rather than automation repos.
- The editor settings, extensions, and storage model are optimized for document
  production rather than Ansible work.

Until then, `ansible-devspaces` should expose the documentation workflow as an
integration surface, not as its core identity.
