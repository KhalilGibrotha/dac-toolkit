---
title: "[Activity] Checklist"
doc_type: "checklist"
domain: "[domain]"
department: "Infrastructure & Operations"
owner: "Infrastructure Architecture"
status: "Draft"
version: "0.1"
date: "YYYY-MM-DD"
author: "First Last"
audience:
  - "Platform Engineering"
  - "Operations"
related_docs:
  - ""
revision_history:
  - version: "0.1"
    date: "YYYY-MM-DD"
    author: "First Last"
    description: "Initial draft"
---

> **Template Note** — Delete this block before publishing.
>
> **Document type:** `checklist` | **Diátaxis:** Procedure
>
> A Checklist is a gate-oriented procedure used to verify readiness before, during,
> or after a significant activity — deployment, migration, cutover, decommission,
> or change window. It prioritizes completion verification over instruction.
>
> Each item should be independently verifiable. Avoid vague items like
> "confirm system is healthy" — write "Confirm all pods in Running state:
> `kubectl get pods -n <ns>`". If an item requires detailed instruction to complete,
> link to the relevant runbook or pattern rather than embedding steps here.
>
> **Do not use** for step-by-step how-to instructions — use `template_pattern.md`.
> Checklists verify; patterns instruct.
>
> **Suggested location:** `governance/` or `patterns/[subdomain]/`
> **File naming:** `checklist_[domain]_[descriptor].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# [Activity] Checklist

_One sentence identifying the activity this checklist gates and who executes it._

---

## Scope

_What is in scope for this checklist? What activity, system, and environment does it cover?_

**Activity:** _e.g. Pre-deployment validation for AAP controller upgrade_
**Environment:** _e.g. Production — all regions_
**Executed by:** _Role, not individual name_
**Reviewed by:** _Role_

---

## Prerequisites

_What must be true before beginning this checklist?_

- [ ]
- [ ]

---

## Pre-[Activity] Checklist

_Items to verify before the activity begins. Each item should be independently
confirmable without requiring judgment or interpretation._

| # | Check | How to Verify | Pass / Fail | Notes |
|---|-------|--------------|-------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## During [Activity]

_Key gates or decision points to check during execution. Keep this short —
if a step requires detailed instruction, link to the relevant runbook or pattern._

| # | Check | Expected State | Pass / Fail | Notes |
|---|-------|---------------|-------------|-------|
| 1 | | | | |

---

## Post-[Activity] Checklist

_Items to verify after the activity completes, confirming the expected outcome
was achieved and the system is in a known-good state._

| # | Check | How to Verify | Pass / Fail | Notes |
|---|-------|--------------|-------------|-------|
| 1 | | | | |
| 2 | | | | |

---

## Rollback Criteria

_Under what conditions should the activity be rolled back?
At what point is rollback no longer possible?_

**Rollback trigger:** _State the condition that mandates a rollback._
**Rollback cutoff:** _Time or milestone after which rollback is not feasible._
**Rollback procedure:** _Link to rollback runbook or pattern._

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Executor | | | |
| Reviewer | | | |

---

_Generated from Markdown source using `docx-build`._
