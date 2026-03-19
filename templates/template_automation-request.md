---
title: "Automation Request: [Short Action-Oriented Title]"
doc_type: "request"
domain: "automation"
department: "Infrastructure & Operations"
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

## Approved Scope

_Select the scope category this request falls under. All automation work must
align with an approved category._

- [ ] **Server Provisioning & Builds** — Standardized VM/physical builds, OS image
  deployment, baseline security hardening.
- [ ] **Patching & Compliance** — Automated patch rollout, compliance checks,
  and reporting.
- [ ] **Monitoring & Alerting** — Automated health checks, log analysis, and
  alert response playbooks.
- [ ] **Pre/Post Maintenance Health Checks** — Automated checks of server health
  before and after reboot.
- [ ] **Backup & Recovery Validation** — Automated testing and verification of
  backup jobs and restore checks.
- [ ] **Capacity & Lifecycle Management** — Storage usage reporting, EOL/EOS
  system tracking, and forecasting automation.
- [ ] **Operational Runbooks** — Routine server operations tasks.
- [ ] **Platform or Process Enhancement** — Improvements to the automation
  platform infrastructure or automation development processes.

  > **Note:** Platform or Process Enhancement is distinct from the operational
  > automation categories above. Use this category only when the work improves
  > *how automation is built or delivered* — not the automation itself. Examples:
  > new Execution Environment builds, AAP platform upgrades, credential management
  > improvements, or pipeline tooling. This category requires additional
  > justification and may require architecture review before approval.

---

## Requirements

### Acceptance Criteria

_What must be true for this automation to be considered complete?
Write criteria that are independently verifiable._

- [ ] *A verifiable acceptance criterion, e.g. "Job runs successfully against test inventory"*
- [ ] *Another verifiable criterion, e.g. "Splunk index receives job completion event"*
- [ ]

### Non-Functional Requirements

_Performance, security, compliance, or reliability requirements._

-
-

### Integration Requirements

_Systems this automation must connect to (e.g., Satellite, Splunk, ITSM, CMDB)._

-
-

---

## Constraints

_Technical or organizational constraints the automation must work within._

- **Technical:** _e.g. OS version, EE limitations, existing integrations_
- **Organizational:** _e.g. maintenance windows, RBAC, approval requirements_

---

## Success Criteria

_How will success be measured post-implementation? Be specific._

Examples:
- "Job runs successfully against testing inventory"
- "Splunk shows compliance logging"
- "Patch compliance rate +95% on testing inventory"

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
