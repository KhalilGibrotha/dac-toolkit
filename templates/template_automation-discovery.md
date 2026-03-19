---
title: "Automation Discovery: [Project Name]"
doc_type: "checklist"
domain: "automation"
department: "Infrastructure & Operations"
owner: "Automation Engineering"
status: "Draft"
version: "0.1"
date: "YYYY-MM-DD"
author: "First Last"
audience:
  - "Automation Engineering"
---

> **Template Note** — Delete this block before publishing.
>
> **Document type:** `checklist` | **Diátaxis:** Procedure
>
> The Automation Discovery Guide is an **internal facilitation tool** for the
> automation engineer to use during a structured discovery session with the
> requestor. It is not given to the requestor to fill out independently.
>
> Run this session after an intake request has been submitted and approved for
> discovery. The output of this session feeds the Automation Spec
> (`template_automation-spec.md`). Capture notes and decisions here, then
> use them to complete the spec.
>
> Not every question applies to every project — skip sections that are clearly
> out of scope and note why.
>
> **Suggested location:** `initiatives/[name]/` or `governance/automation/`
> **File naming:** `discovery_automation_[project-name].md`
> **Status lifecycle:** Draft → Accepted (once spec is produced)

# Automation Discovery: [Project Name]

**Project:**
**Facilitator:**
**Date:**
**Stakeholders:**
**Linked Request:**

---

## 1. Purpose & Impact

_Understand the goal before touching technology._

- [ ] What is the goal of automating this workflow?
- [ ] Who consumes the output, and how is it used?
- [ ] What does the current manual process look like? _(brief overview)_
- [ ] What does "done" or "success" look like to the requestor?

**Notes:**

---

## 2. Workflow Breakdown

### Source

- [ ] What platform or system provides the input data?
- [ ] What data needs to be pulled or read?
- [ ] How is access handled? _(API token, service account, credentials)_
- [ ] Are there query constraints, rate limits, or pagination issues?

**Notes:**

---

### Transformation

- [ ] Is there existing automation or scripts that can be reused?
- [ ] What applications, packages, versions, or dependencies are required?
- [ ] Are there edge cases or data cleansing steps?
- [ ] Should the automation log output or errors? Where?

**Notes:**

---

### Destination

- [ ] Where should output be stored? _(file share type and address, S3, ITSM, etc.)_
- [ ] What is the expected file format and structure?
- [ ] How should files be named, versioned, or rotated?
- [ ] Are there permissions or access controls on the destination?

**Notes:**

---

## 3. Trigger & Frequency

- [ ] How often should the automation run? _(daily, weekly, on-demand)_
- [ ] Is it event-driven or scheduled?
- [ ] Should it notify someone or log results? Who and how?

**Notes:**

---

## 4. Validation & Error Handling

- [ ] How do we confirm the output data is accurate?
- [ ] Should we validate schema, row count, or specific fields?
- [ ] What happens if the output resource or file share is unavailable?
- [ ] Should failures trigger alerts, retries, and/or generate logs?
- [ ] Should we log to Splunk?

**Notes:**

---

## 5. Ansible Integration Points

- [ ] Will the automation run via script, command module, or an Ansible role?
- [ ] Should we build a custom Execution Environment with dependencies?
- [ ] Are credentials stored in Ansible Vault or another approved method?
- [ ] Do we need to tag tasks for audit or reporting?

**Notes:**

---

## 6. Documentation & Traceability

- [ ] Should we create a spec sheet or impact log for this automation?
- [ ] What naming conventions or folder structures apply?
- [ ] Are there stakeholders who need visibility into changes or outcomes?

**Notes:**

---

## Next Steps

_Capture action items before closing the session. Assign an owner to every item._

- [ ] Item — Owner
- [ ] Item — Owner
- [ ] Draft Automation Spec from this session — Automation Engineer

---

## Open Questions

_Questions that came up but could not be resolved in this session._

-
-
