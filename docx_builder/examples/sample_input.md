---
title: "Platform Architecture Overview\nAnsible Automation Platform"
department: "Infrastructure & Operations"
status: "Draft"
version: "0.1"
date: "2026-03-14"
author: "A. Smith"
owner: "Platform Engineering"
audience:
  - Architecture Review Board
  - Platform Engineering
  - Server Operations
related_docs:
  - "Enterprise Automation Strategy v1.0"
  - "Network Segmentation Design v2.1"
revision_history:
  - version: "0.1"
    date: "2026-03-14"
    author: "A. Smith"
    description: "Initial draft for ARB review"
---

## Overview

This document describes the platform architecture for the Ansible Automation Platform (AAP)
deployment within the Infrastructure & Operations environment. It covers the logical
architecture, integration points, and key design decisions.

## Background

The organization currently manages infrastructure automation through a combination of
ad-hoc scripts and manual processes. This initiative establishes AAP as the standard
automation platform for server provisioning, configuration management, and lifecycle operations.

### Current State

- Manual provisioning via runbooks in approximately 40% of server builds
- Inconsistent configuration baseline across server populations
- Limited visibility into automation activity and audit trails

### Drivers

- Reduce provisioning cycle time
- Establish consistent configuration compliance
- Support zero-touch provisioning for standard server builds

## Architecture

### Logical Architecture

The platform consists of the following components:

| Component | Role | Notes |
|---|---|---|
| AAP Controller | Orchestration engine | Active/passive HA pair |
| Execution Environments | Isolated execution contexts | Container-based |
| Private Automation Hub | Content management | Air-gapped content mirror |
| Event-Driven Ansible | Event-triggered automation | Integrates with monitoring |

### Integration Points

The platform integrates with the following systems:

- **ServiceNow** — Change ticket validation and closure
- **Satellite** — RHEL content delivery and subscription management
- **Vault** — Secrets management for credential injection
- **Splunk** — Audit log forwarding and activity monitoring

### Network Placement

AAP Controller nodes are placed in the Infrastructure Management zone. Managed nodes
are reached via the standard management network. No direct internet access is required
for execution nodes — content is pulled from the Private Automation Hub.

## Security Considerations

> Authentication to AAP Controller is federated through Active Directory via SAML.
> Service accounts used by AAP for managed node access follow the principle of
> least privilege and are rotated via Vault on a defined schedule.

All automation activity is logged to Splunk via syslog forwarding from the Controller.
Audit records include the user, playbook, target inventory, and execution result.

## Key Decisions

See `decisions/accepted/` for full ADRs. Summary:

1. **AAP as primary automation platform** — Replaces ad-hoc scripting
2. **Container-based execution environments** — Isolation and reproducibility
3. **Private Automation Hub as content mirror** — Air-gap compliance

## Open Items

- [ ] Confirm network zone placement with Network Architecture team
- [ ] Validate Vault integration approach with Security team
- [ ] Determine retention policy for execution logs in Splunk

---

*This document was generated from Markdown source using `docx-build`.*
