# Contributing to dac-toolkit

dac-toolkit is a public, MIT-licensed documentation toolchain. Contributions are welcome.

## Branch Model

```text
main        — the trunk; PRs target here, and merging is what releases
feat/*      — short-lived feature branches from main, deleted on merge
fix/*       — short-lived fix branches
chore/*     — dependency bumps, config, release plumbing
docs/*      — documentation-only changes
```

Do not push directly to `main`; every change arrives by pull request. There
is no `develop` branch — the release gate is the `v*` tag plus a green
Release QA run, so a second long-lived branch would only be somewhere for
work to go stale.

> **Note:** `devfile.yaml` targets `revision: main`, which is also the branch
> you contribute against.

## Getting Started

```bash
git clone https://github.com/KhalilGibrotha/dac-toolkit.git
cd dac-toolkit
git checkout -b feat/your-feature-name
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

1. Target `main`.
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

Releases are tagged on `main`. Tag format: `vMAJOR.MINOR.PATCH`. The Docker
image tag aligns with the release tag, and a tag build only publishes if a
Release QA run passed on that exact commit.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.
