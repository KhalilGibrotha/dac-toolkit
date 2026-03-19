---
title: "[Platform or Product] Release Notes"
doc_type: "release-notes"
domain: "[domain]"
department: "Infrastructure & Operations"
owner: "Infrastructure Architecture"
status: "Draft"
version: "rolling"
date: "YYYY-MM-DD"
author: "Infrastructure Architecture"
audience:
  - "Platform Engineering"
  - "Operations"
  - "Architecture Review Board"
related_docs:
  - ""
---

> **Template Note** — Delete this block before publishing.
>
> **Document type:** `release-notes` | **Diátaxis:** Reference
>
> Release Notes are a rolling reference document. Each release adds a new section
> at the top of the document, maintaining a complete changelog newest-first.
> Use this for platform releases, automation development milestones, or internal
> tooling versions.
>
> Keep entries factual and concise. The audience is engineers and ops staff who
> need to understand what changed, what broke, and what action they must take.
> Link to relevant ADRs, patterns, or runbooks where significant changes require
> operator action.
>
> **Do not use** for incident reports — use `template_rca.md`.
> Do not use for planned work or roadmap items — use `template_proposal.md`.
>
> **Suggested location:** `releases/`
> **File naming:** `release-notes_[domain]_[platform-or-product].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# [Platform or Product] Release Notes

_Release notes for [Platform or Product]. Entries are listed newest-first._

---

<!-- ============================================================ -->
<!-- Add new releases at the TOP of this file, above this marker. -->
<!-- ============================================================ -->

---

## [Version] — YYYY-MM-DD

### Summary

_One to three sentences describing the most significant changes in this release
and any action required from operators or consumers._

### New Features

_Capabilities that did not exist in the previous release._

-

### Changes

_Modifications to existing behavior, configuration, or interfaces._

-

### Bug Fixes

-

### Deprecations

_Features or interfaces that still work but will be removed in a future release.
State the planned removal version._

-

### Breaking Changes

> **Action required** — _Describe what operators or consumers must do before upgrading._

-

### Known Issues

| Issue | Workaround | Target Fix |
|-------|-----------|------------|
| | | |

### Upgrade Notes

_Prerequisites, configuration changes, or migration steps required to upgrade
from the previous version. If none, write "No upgrade steps required."_

1.

---

## [Previous Version] — YYYY-MM-DD

_Repeat the structure above for each prior release._

---

_Generated from Markdown source using `docx-build`._
