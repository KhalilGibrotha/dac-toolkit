---
title: "RCA: [Incident Title or ID]"
doc_type: "rca"
domain: "[domain, e.g. platform, network, identity]"
department: "Infrastructure & Operations"
owner: "Operations"
status: "Draft"
version: "0.1"
date: "YYYY-MM-DD"
author: "First Last"
audience:
  - "Operations Management"
  - "Platform Engineering"
  - "Infrastructure Architecture"
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
> **Document type:** `rca` | **Diátaxis:** Reference
>
> A Root Cause Analysis (RCA) is a structured post-incident document aligned to
> ITIL Problem Management. Its purpose is to identify the underlying cause of a
> service disruption, document the timeline, and produce corrective actions that
> feed into the Problem record in your ITSM tool.
>
> This document complements — it does not replace — the incident record in your
> ITSM. Link the ITSM ticket in the header. Focus on depth of analysis and
> actionable corrective measures. RCAs are blameless: the goal is systemic
> improvement, not attribution.
>
> Conduct the RCA after service restoration, ideally within five business days
> while the incident is still fresh.
>
> **Do not use** to document active incidents — this is a post-incident artifact.
>
> **Suggested location:** `incidents/`
> **File naming:** `rca_[domain]_[incident-id-or-descriptor].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# RCA: [Incident Title or ID]

_One sentence summarizing the incident and its business impact._

---

## Incident Overview

| Field | Value |
|-------|-------|
| **Incident ID** | _ITSM ticket number_ |
| **Problem Record ID** | _ITSM problem record number_ |
| **Date of Incident** | YYYY-MM-DD |
| **Detection Time** | HH:MM (timezone) |
| **Resolution Time** | HH:MM (timezone) |
| **Total Duration** | _e.g. 2 hours 14 minutes_ |
| **Severity** | _P1 / P2 / P3_ |
| **Affected Systems** | |
| **Incident Commander** | |
| **RCA Author** | |

---

## Impact Assessment

_Quantify the impact where possible. Be specific about scope and affected population._

| Impact Type | Description |
|-------------|-------------|
| **User Impact** | _e.g. 450 users unable to authenticate for 2h 14m_ |
| **Business Impact** | _e.g. Loan processing paused; no transactions processed_ |
| **Systems Affected** | |
| **Data Impact** | _e.g. No data loss / 12 transactions requiring manual review_ |
| **SLA Breach** | Yes / No |

---

## Incident Timeline

_Chronological record of events from first symptom to resolution.
Include the source of each data point (alert, user report, monitoring system, engineer observation)._

| Time | Event | Source | Actor |
|------|-------|--------|-------|
| HH:MM | _First symptom detected_ | _Alert / User report / Monitoring_ | |
| HH:MM | _Incident declared_ | | |
| HH:MM | _[key action or finding]_ | | |
| HH:MM | _Service restored_ | | |
| HH:MM | _Incident closed_ | | |

---

## Root Cause Analysis

_Identify the root cause using the 5-Whys method. Start from the presenting
symptom and ask "why" at each level until you reach the systemic or process
root cause. Stop when the answer is outside the team's control or when further
inquiry would not produce a different corrective action._

**Presenting symptom:** _What the end user or monitoring system observed._

| Level | Question | Answer |
|-------|----------|--------|
| Why 1 | Why did [symptom] occur? | |
| Why 2 | Why did [answer 1] occur? | |
| Why 3 | Why did [answer 2] occur? | |
| Why 4 | Why did [answer 3] occur? | |
| Why 5 | Why did [answer 4] occur? | |

**Root Cause:** _State the identified root cause clearly in one or two sentences._

---

## Contributing Factors

_Factors that made the incident worse or harder to detect and resolve,
even if they were not the root cause._

| Factor | Category | Description |
|--------|----------|-------------|
| | _Process / Technology / People / Environment_ | |

---

## Corrective Actions

_Each action should map to a specific gap identified in the root cause or
contributing factors. Assign an owner and target date for every item.
Track open items in the ITSM Problem record._

| # | Action | Type | Owner | Target Date | Status | ITSM Reference |
|---|--------|------|-------|-------------|--------|----------------|
| 1 | | _Preventive / Detective / Corrective_ | | YYYY-MM-DD | Open | |
| 2 | | | | YYYY-MM-DD | Open | |

---

## Lessons Learned

_What did the team learn from this incident? Include positive observations
(what worked well) alongside gaps (what did not)._

### What Went Well

-

### What Could Be Improved

-

### Knowledge or Tooling Gaps Identified

-

---

## Problem Record Reference

| Field | Value |
|-------|-------|
| **Problem Record** | _ITSM link_ |
| **Known Error** | Yes / No |
| **Workaround** | _If yes, describe the workaround available to users_ |
| **Problem Status** | Open / Known Error / Resolved |

---

_Generated from Markdown source using `docx-build`._
