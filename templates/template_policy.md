---
title: "[Noun Phrase] Policy"
doc_type: "policy"
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
  - "Security Architecture"
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
> **Document type:** `policy` | **Diátaxis:** Concept (with directive authority)
>
> A Policy establishes organizational intent, constraints, and accountability for
> a domain or practice area. It answers *why* something is required and *who* is
> accountable — not *what* specific requirements apply (that belongs in a linked
> standard) or *how* to implement them (that belongs in a linked pattern or runbook).
>
> Policy statements are principle-level: they set direction and assign ownership.
> They should not contain implementation detail, specific commands, or numbered
> procedural steps. If you find yourself writing "run `ansible-playbook`..." you
> are writing a runbook, not a policy.
>
> Policies typically authorize one or more standards. Reference those standards
> explicitly so readers know where to go for specific requirements.
>
> **Do not use** for technical specifications, step-by-step procedures, or
> reference tables. Policies are organizational commitments, not implementation guides.
>
> **Suggested location:** `governance/`
> **File naming:** `policy_[domain]_[descriptor].md`
> **Status lifecycle:** Draft → In Review → Accepted → Retired

# [Noun Phrase] Policy

This policy establishes the organizational intent, guiding principles, and
accountability structure for [subject area] within the Infrastructure & Operations
organization.

---

## Policy Statement

_One to three sentences stating the organizational commitment this policy
represents. Write at the principle level — no implementation detail._

[Organization] requires that [subject area] be managed in a manner that [desired
outcome — e.g. "protects the confidentiality of sensitive data, ensures
operational continuity, and supports audit requirements"].

---

## Scope

_Who and what does this policy apply to? Define the boundaries explicitly._

This policy applies to:

-

This policy does not apply to:

-

---

## Principles

_List the high-level principles that guide decisions in this domain. These are
the "why" behind the standards and patterns that implement this policy._

1. **[Principle Name]** — _One sentence explaining the principle and why it matters._
2. **[Principle Name]** — _One sentence._
3. **[Principle Name]** — _One sentence._

---

## Roles and Responsibilities

| Role | Responsibility |
|---|---|
| **[Role]** | _What this role is accountable for under this policy_ |
| **[Role]** | |
| **[Role]** | |

---

## Policy Requirements

_High-level requirements that this policy mandates. These are the constraints all
implementations must satisfy. Specific, verifiable requirements belong in a
linked standard._

-
-

---

## Authorized Standards and Patterns

_List the standards and patterns that implement this policy. These documents
contain the specific, verifiable requirements._

| Document | Relationship |
|---|---|
| | _Standard implementing this policy_ |
| | _Pattern implementing this policy_ |

---

## Exceptions

_Who may grant exceptions, under what conditions, and how exceptions are
documented and reviewed._

Exceptions to this policy require approval from [authority, e.g. the Architecture
Review Board]. All approved exceptions must be documented, time-bound, and
reviewed at the next policy review cycle.

---

## Compliance and Enforcement

_How is compliance with this policy measured? What happens when the policy is
violated?_

Compliance is verified through [mechanism — e.g. quarterly architecture reviews,
automated scanning, audit findings]. Non-compliance must be escalated to
[authority] and remediated within [timeframe] unless an exception is approved.

---

## Review Cycle

This policy is reviewed [annually / on a defined trigger — e.g. major platform
change, regulatory update, or incident] by [authority].

---

_Generated from Markdown source using `docx-build`._
