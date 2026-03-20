# Contributing to dac-toolkit

dac-toolkit is a public, MIT-licensed documentation toolchain. Contributions are welcome.

## Branch Model

```text
main        — stable, tagged releases only
develop     — integration branch; all PRs target here
feature/*   — short-lived feature branches from develop
fix/*       — short-lived fix branches from develop
```

Do not push directly to `main`. All changes flow through `develop` via pull request.

> **Note:** The `devfile.yaml` in this repo targets `revision: main` for workspace users who want a stable environment. As a contributor, clone the repo normally and branch from `develop` as described in Getting Started below.

## Getting Started

```bash
git clone https://github.com/KhalilGibrotha/dac-toolkit.git
cd dac-toolkit
git checkout develop
git checkout -b feature/your-feature-name
```

## Making Changes

- Keep changes focused. One feature or fix per PR.
- If your change touches `docx_builder`, test it with a real Markdown document before submitting.
- If your change modifies the devcontainer or Dockerfile, test in a Dev Spaces or local container environment.
- Templates should be generic — no org-specific terminology, product names, or internal references.

## Commit Messages

Use the imperative mood and a concise subject line:

```text
Fix keepNext insertion order when pStyle is present
Add template_standard.md to flat template library
Update devfile to use UDI base image
```

Avoid:
- `Fixed...`, `Fixes...`, `Adding...`
- Vague messages like `updates` or `misc fixes`

## Pull Requests

1. Target `develop`, not `main`.
2. Include a short description of what changed and why.
3. Link any related issues in the PR body.
4. Automated review agents (Gemini, Copilot, Codex) will comment — address legitimate findings before merge.

## Reporting Bugs

Open a GitHub issue with:
- A description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Relevant error output or screenshots

## Proposing Changes

Open an issue before starting significant work. This avoids duplicated effort and ensures the change fits the project direction. For small fixes, a PR without a prior issue is fine.

## Release Process

Releases are tagged on `main` from `develop` after sufficient stability. Tag format: `vMAJOR.MINOR.PATCH`. The Docker image tag aligns with the release tag.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.
