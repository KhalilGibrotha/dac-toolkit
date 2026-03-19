---
title: "[Action]: [System or Procedure Name]"
doc_type: "runbook"
domain: "[domain]"
department: "Infrastructure & Operations"
owner: "Operations"
status: "Draft"
version: "0.1"
date: "YYYY-MM-DD"
author: "First Last"
audience:
  - "Operations"
  - "Platform Engineering"
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
> **Document type:** `runbook` | **Diátaxis:** Procedure
>
> A Runbook documents the steps required to perform a specific operational task:
> starting or stopping a service, responding to an alert, executing a failover,
> or performing routine maintenance. It is designed for use at execution time,
> including under pressure during an incident.
>
> Write for the engineer executing the task, not for the reviewer reading for
> compliance. Front-load the Quick Reference so experienced operators can move
> fast without reading the full document. Keep steps terse, numbered, and
> independently executable. If a step needs extensive explanation, that explanation
> belongs in a linked concept document — not here.
>
> **Do not use** for design-time architecture patterns — use `template_pattern.md`.
> Runbooks are day-2 operational artifacts.
>
> **Suggested location:** `runbooks/`
> **File naming:** `runbook_[domain]_[descriptor].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# [Action]: [System or Procedure Name]

_One sentence stating what this runbook accomplishes and under what condition it is used._

---

## Quick Reference

_Summary for experienced operators who have run this procedure before.
Critical commands only — no explanation._

```bash
# Step 1 — brief label
command-one

# Step 2 — brief label
command-two
```

**Estimated duration:** _e.g. 15–30 minutes_
**Impact:** _e.g. Service interruption / No user impact / Requires maintenance window_
**Reversible:** Yes / No — _link to rollback procedure if yes_

---

## Purpose

_What does this runbook accomplish? What system or service does it affect?_

## Scope

_What environment, cluster, or service tier does this apply to?
What is explicitly out of scope?_

---

## Prerequisites

_Everything that must be true before starting: access, credentials, tool versions,
and any pre-checks required. Do not begin the procedure until all items are confirmed._

- [ ] Access: _e.g. `cluster-admin` on target cluster_
- [ ] Tools: _e.g. `oc` CLI ≥ 4.14, `ansible-navigator` installed_
- [ ] Pre-check: _e.g. Confirm no active change windows conflict_

---

## Procedure

_Number every step. One action per step. Include the expected output where it
helps confirm success before moving to the next step._

### Phase 1 — [Phase Name, e.g. Preparation]

1. _Step one._

   ```bash
   # example command
   ```

   _Expected output: ..._

2. _Step two._

### Phase 2 — [Phase Name, e.g. Execution]

3. _Step three._

4. _Step four._

### Phase 3 — [Phase Name, e.g. Verification]

5. _Verify the expected outcome._

---

## Verification

_How does the operator confirm the procedure completed successfully?_

- [ ] _Confirmation check 1_
- [ ] _Confirmation check 2_

---

## Rollback

_If the procedure must be reversed, describe the rollback steps or link to a
dedicated rollback runbook._

> **Rollback trigger:** _Describe the condition that requires rollback._

1. _Rollback step one._
2. _Rollback step two._

---

## Escalation

_Who to contact if the procedure fails or produces unexpected results._

| Condition | Contact | Method |
|-----------|---------|--------|
| _Procedure fails at step X_ | | |
| _Service does not recover_ | | |

---

_Generated from Markdown source using `docx-build`._
