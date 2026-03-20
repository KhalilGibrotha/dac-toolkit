---
title: "Automation Request: [Short Action-Oriented Title]"
doc_type: "request"
domain: "automation"
department: "[Department]"
owner: "[Requesting Team]"
status: "Draft"
version: "0.1"
date: "YYYY-MM-DD"
author: "First Last"
audience:
  - "Automation Engineering"
  - "Operations Management"
---

> **Template Note** — Delete this block before publishing.
>
> **Document type:** `request` | **Diátaxis:** — (intake artifact)
>
> An Automation Request captures a need for new or enhanced automation in enough
> detail to create a Jira Story or Epic. The requestor fills this out; the
> automation engineer does not complete it on their behalf.
>
> **Story vs. Epic:** If the work can be delivered in a single sprint and has one
> clear outcome, create a Story. If it spans multiple sprints, has multiple
> deliverables, or requires discovery before scoping, create an Epic and break it
> into Stories after the discovery session.
>
> **Jira field mapping:**
> | This document | Jira field |
> |---|---|
> | Title | Summary |
> | Request Type | Issue Type (Story / Epic) |
> | Background & Business Justification | Description |
> | Acceptance Criteria | Acceptance Criteria |
> | Approved Scope | Label / Component |
> | Priority | Priority |
> | Requestor | Reporter |
> | Manager Approval | Approver (custom field) |
>
> **Suggested location:** `initiatives/[name]/` or `governance/`
> **File naming:** `request_automation_[short-title].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# Automation Request: [Short Action-Oriented Title]

_One sentence describing the automation being requested and the problem it solves._

---

## Request Type

- [ ] **Story** — Single deliverable, completable in one sprint
- [ ] **Epic** — Multiple deliverables or requires discovery before scoping

---

## Requestor

**Name:**
**Team:**
**Intake Date:**

---

## Background & Business Justification

_Why is this automation needed? Tie to pain points, incidents, compliance
requirements, or operational burden. Be specific — "it would save time" is
not sufficient justification._

---

## Technical Scope Assessment

_Answer this question before proceeding to the technical sections below._

> **Can you describe the systems, data flows, and integration points this
> automation will touch — with enough detail to fill out the Requirements
> section below?**

- [ ] **Yes** — Continue to Approved Scope and Requirements below.
- [ ] **No** — Stop here. Submit this request with only the Background &
  Business Justification completed. Architecture will conduct a scoping
  session before the technical sections are filled in.

  > **What happens next:** An architecture review will be scheduled to assess
  > technical scope, integration requirements, and configuration impact. The
  > findings will be documented in an Automation Discovery artifact and
  > attached to this request before backlog entry.

_If you selected **No**, skip to [Manager Approval](#manager-approval) and submit._

---

## Approved Scope

_Select the scope category this request falls under. All automation work must
align with an approved category. Replace the placeholders below with your
organization's automation strategy pillars._

- [ ] **[Scope Category 1]** — _Brief description of what this category covers._

- [ ] **[Scope Category 2]** — _Brief description of what this category covers._

- [ ] **[Scope Category 3]** — _Brief description of what this category covers._

- [ ] **[Scope Category 4]** — _Brief description of what this category covers._

- [ ] **[Scope Category 5]** — _Brief description of what this category covers._

- [ ] **Platform or Process Enhancement** — Improvements to the automation
  platform infrastructure or automation development processes.

  > **Note:** Platform or Process Enhancement is distinct from the operational
  > automation categories above. Use this category only when the work improves
  > *how automation is built or delivered* — not the automation itself. This
  > category requires additional justification and may require architecture
  > review before approval.

---

## Requirements

### Acceptance Criteria

_What must be true for this automation to be considered complete?
Write criteria that are independently verifiable._

- [ ] _A verifiable acceptance criterion, e.g. "Job runs successfully against test inventory"_
- [ ] _Another verifiable criterion, e.g. "Log platform receives job completion event"_
- [ ]

### Non-Functional Requirements

_Performance, security, compliance, or reliability requirements._

-
-

### Integration Requirements

_Identify every system this automation must connect to. For each, indicate
whether an integration is required, what access level is needed, and the
current state of that integration._

**Integration maturity key:**
- **Established** — Standard integration patterns exist; engineer can reference prior work
- **Limited** — Partial capability only; may require additional discovery or custom development
- **Not Available** — No current integration exists; requires architecture review before implementation

> **Note:** Replace the system categories below with your organization's tool suite.

| System / Tool Category | Required? | Privilege Level | Integration Maturity | Notes |
|---|---|---|---|---|
| Monitoring / Observability Platform | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| Log Aggregation / SIEM | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| ITSM / Ticketing System | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| CMDB / Asset Management | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| IPAM / Network Management | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| OS Lifecycle / Content Management | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| Vulnerability / Compliance Scanning | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| Identity / Directory Services | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| Source Control / CI-CD | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| Secrets / Credential Management | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |
| Other: _______________ | ☐ Yes ☐ No | ☐ Read ☐ Write ☐ Both | | |

> **New integration flag:** If any row above is marked **Not Available** or
> requires a system not listed, this request must route through Architecture
> for integration scoping before entering the backlog. Check the box if this
> applies:
>
> - [ ] This request requires establishing a new integration that does not
>   currently exist. _(Architecture review required before backlog entry.)_

---

## Configuration & Compliance Impact

_Check all configuration domains this automation will read or modify. Every
checked domain must align with the governing standard before implementation.
"Unknown" is acceptable at intake — it will be resolved during discovery._

> **Note:** Replace governance alignment references with your organization's
> applicable standards and policies.

| Configuration Domain | Impact | Governance Alignment Required |
|---|---|---|
| Monitoring / Alerting configuration | ☐ Yes ☐ No ☐ Unknown | _[Monitoring standard]_ |
| Logging / Audit log configuration | ☐ Yes ☐ No ☐ Unknown | _[Logging and retention policy]_ |
| OS hardening / baseline settings | ☐ Yes ☐ No ☐ Unknown | _[Hardening standard]_ |
| RBAC / Service account provisioning | ☐ Yes ☐ No ☐ Unknown | _[Access control policy]_ |
| Network / Firewall rules | ☐ Yes ☐ No ☐ Unknown | _[Network change process]_ |
| Certificate / Key management | ☐ Yes ☐ No ☐ Unknown | _[Key management standard]_ |
| Backup / Recovery configuration | ☐ Yes ☐ No ☐ Unknown | _[Backup policy]_ |
| Change management classification | ☐ Standard ☐ Normal ☐ Emergency | _[Change management policy]_ |

> **Any "Yes" response in this section** indicates a configuration side-effect
> that must be reviewed for standard alignment before the implementation sprint.
> The engineer assigned to this request is responsible for confirming alignment
> and documenting exceptions.

---

## Constraints

_Technical or organizational constraints the automation must work within._

- **Technical:** _e.g. OS version, execution environment limitations, existing integrations_
- **Organizational:** _e.g. maintenance windows, RBAC, approval requirements_

---

## Success Criteria

_How will success be measured post-implementation? Write observable, measurable outcomes._

-
-

---

## Impact Measurement

_Captured at intake, validated post-implementation._

| Metric | Estimated | Validated |
|--------|-----------|-----------|
| Hours saved per month | | |
| Cost avoided or saved ($) | | |
| Risk reduction | | |
| Compliance improvement | | |

---

## Manager Approval

_Required before backlog refinement. Manager must sign off on scope and priority._

- [ ] Approved
**Manager:** _______________
**Date:** _______________

---

## Notes

_Additional context, links to supporting documentation, related incidents, or
references to existing processes._
