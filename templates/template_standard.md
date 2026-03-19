---
title: "[Noun Phrase] Standard"
doc_type: "standard"
domain: "[domain]"
department: "Infrastructure & Operations"
owner: "Infrastructure Architecture"
status: "Draft"
version: "0.1"
date: "YYYY-MM-DD"
author: "First Last"
audience:
  - "Infrastructure Architecture"
  - "Operations"
  - "Platform Engineering"
related_docs: []
revision_history:
  - version: "0.1"
    date: "YYYY-MM-DD"
    author: "First Last"
    description: "Initial draft"
---

> **Template Note** — Delete this block before publishing.
>
> **Document type:** `standard` | **Diátaxis:** Reference (with directive authority)
>
> A Standard defines mandatory technical requirements that must be met for a
> specific domain, platform, or practice area. It answers *what is required* —
> not why (that belongs in a linked policy) and not how (that belongs in a linked
> pattern or runbook).
>
> Standards use **SHALL** for mandatory requirements, **SHOULD** for strongly
> recommended practices, and **MAY** for permitted options. Avoid vague language:
> every requirement must be verifiable. If you can't confirm compliance, it isn't
> a requirement — it's a guideline.
>
> Write requirements as atomic statements. One requirement per line. If a
> requirement needs significant explanation, move the rationale to a linked
> concept document and keep only the requirement here.
>
> **Do not use** for operational procedures, architecture patterns, or policy
> intent statements. Standards are *what*, not *how* or *why*.
>
> **Suggested location:** `governance/`
> **File naming:** `standard_[domain]_[descriptor].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# [Noun Phrase] Standard

This standard defines mandatory requirements for [subject area] within the
Infrastructure & Operations organization.

---

## Scope

_What systems, services, teams, or environments does this standard apply to?
What is explicitly excluded?_

**In scope:**

-

**Out of scope:**

-

---

## Authority and Enforcement

| Field | Value |
|---|---|
| **Issuing authority** | _e.g. Infrastructure Architecture / ARB_ |
| **Effective date** | YYYY-MM-DD |
| **Review cycle** | _e.g. Annual_ |
| **Compliance owner** | _Team responsible for verifying adherence_ |
| **Exception process** | _e.g. Submit exception request to Architecture Review Board_ |

---

## Requirements

_Use **SHALL** for mandatory, **SHOULD** for strongly recommended, **MAY** for
permitted. Number every requirement. Keep each requirement atomic and verifiable._

### [Requirement Category 1]

| ID | Requirement | Level |
|---|---|---|
| STD-[domain]-001 | _Systems SHALL ..._ | SHALL |
| STD-[domain]-002 | _Configurations SHOULD ..._ | SHOULD |

### [Requirement Category 2]

| ID | Requirement | Level |
|---|---|---|
| STD-[domain]-003 | _Access controls SHALL ..._ | SHALL |

---

## Definitions

_Define any domain-specific terms used in the requirements above that may be
interpreted differently across teams._

| Term | Definition |
|---|---|
| | |

---

## Exceptions

_Describe the conditions under which an exception to this standard may be
granted, who approves it, and how it is documented._

Exceptions to this standard require written approval from [authority]. Approved
exceptions must be:

1. Documented in the CMDB or exception register.
2. Time-bound with a defined remediation or renewal date.
3. Reviewed at the next architecture review cycle.

---

## Compliance Verification

_How is compliance measured? List the checks, tools, or processes used to verify
adherence. Be specific enough that an auditor can reproduce the check._

| Check | Method | Frequency |
|---|---|---|
| _Requirement ID_ | _e.g. Ansible playbook / automated scan / manual audit_ | _e.g. Quarterly_ |

---

## Related Documents

| Document | Relationship |
|---|---|
| | _e.g. Parent policy that mandates this standard_ |
| | _e.g. Pattern implementing this standard_ |

---

_Generated from Markdown source using `docx-build`._
