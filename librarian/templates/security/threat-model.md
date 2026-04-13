---
template_id: threat-model
display_name: Threat Model
preset: security
description: >-
  Structured threat model using STRIDE methodology. Identifies assets, threat actors,
  attack surfaces, and mitigations. Applicable to software systems, infrastructure,
  and organizational processes.
suggested_tags: [security, threat-model, risk]
suggested_folder: docs/
typical_cross_refs:
  - vulnerability-assessment
  - security-architecture-review
  - incident-response-plan
recommended_with:
  - vulnerability-assessment
  - security-architecture-review
requires: []
sections:
  - Executive Summary
  - System Description
  - Asset Inventory
  - Threat Actors
  - Attack Surface Analysis
  - STRIDE Analysis
  - Risk Rating
  - Mitigations
  - Residual Risk
  - Review Schedule
---

# Threat Model: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
{% endif %}

---

## Executive Summary

*[1–2 paragraph overview of the system being modeled, key threats identified, overall risk rating, and top 3 mitigations recommended.]*

---

## System Description

### Architecture Overview
*[High-level description of the system, its purpose, and key components. Include or reference an architecture diagram.]*

### Trust Boundaries

| Boundary | Description | Crosses |
|----------|------------|---------|
| *[Boundary 1]* | *[e.g., "Internet ↔ DMZ"]* | *[Data types crossing]* |
| *[Boundary 2]* | *[e.g., "DMZ ↔ Internal network"]* | *[Data types crossing]* |
| *[Boundary 3]* | *[e.g., "Application ↔ Database"]* | *[Data types crossing]* |

### Data Flow Summary
*[Describe how data moves through the system, including entry points, processing, storage, and exit points.]*

---

## Asset Inventory

| Asset | Type | Sensitivity | Location | Owner |
|-------|------|------------|----------|-------|
| *[Asset 1]* | *[Data / Service / Infrastructure]* | *[Critical / High / Medium / Low]* | *[Where stored/processed]* | *[Team/person]* |
| *[Asset 2]* | *[Type]* | *[Sensitivity]* | *[Location]* | *[Owner]* |

{% if "hipaa" in compliance %}
### PHI Assets
| PHI Element | System | Storage | Encryption | Access Control |
|------------|--------|---------|-----------|---------------|
| *[PHI type]* | *[System]* | *[At rest / In transit]* | *[AES-256 / TLS 1.3 / None]* | *[RBAC / ACL]* |
{% endif %}

---

## Threat Actors

| Actor | Motivation | Capability | Likelihood | Target Assets |
|-------|-----------|-----------|-----------|--------------|
| *[External attacker]* | *[Financial / Espionage / Disruption]* | *[High / Medium / Low]* | *[H/M/L]* | *[Assets]* |
| *[Insider (malicious)]* | *[Financial / Revenge]* | *[High (authorized access)]* | *[L]* | *[Assets]* |
| *[Insider (accidental)]* | *[N/A — unintentional]* | *[Medium]* | *[H]* | *[Assets]* |
| *[Nation-state]* | *[Espionage / Disruption]* | *[Very High]* | *[L/M]* | *[Assets]* |

{% if "dod_5200" in compliance %}
### Adversary Assessment (DoD Context)
| Adversary Category | Collection Capability | OPSEC Concern |
|-------------------|---------------------|---------------|
| *[Near-peer state]* | *[SIGINT, HUMINT, Cyber]* | *[High]* |
| *[Non-state actor]* | *[OSINT, Cyber]* | *[Medium]* |
| *[Insider threat]* | *[Direct access]* | *[High]* |
{% endif %}

---

## Attack Surface Analysis

### Entry Points

| # | Entry Point | Protocol | Authentication | Exposure |
|---|------------|----------|---------------|----------|
| 1 | *[Web application]* | *[HTTPS]* | *[OAuth2 / Session]* | *[Internet]* |
| 2 | *[API endpoint]* | *[REST/HTTPS]* | *[API key / JWT]* | *[Internet]* |
| 3 | *[Admin interface]* | *[SSH / HTTPS]* | *[MFA / Certificate]* | *[VPN only]* |
| 4 | *[Database port]* | *[TCP/5432]* | *[Password]* | *[Internal only]* |

---

## STRIDE Analysis

### Spoofing

| # | Threat | Target | Likelihood | Impact | Mitigation |
|---|--------|--------|-----------|--------|------------|
| S1 | *[Credential theft via phishing]* | *[User accounts]* | *[H]* | *[H]* | *[MFA, training]* |
| S2 | *[API key leakage]* | *[API access]* | *[M]* | *[H]* | *[Key rotation, vault]* |

### Tampering

| # | Threat | Target | Likelihood | Impact | Mitigation |
|---|--------|--------|-----------|--------|------------|
| T1 | *[SQL injection]* | *[Database]* | *[M]* | *[Critical]* | *[Parameterized queries, WAF]* |
| T2 | *[Log manipulation]* | *[Audit trail]* | *[L]* | *[H]* | *[Append-only logs, SIEM]* |

### Repudiation

| # | Threat | Target | Likelihood | Impact | Mitigation |
|---|--------|--------|-----------|--------|------------|
| R1 | *[Unsigned transactions]* | *[Financial records]* | *[M]* | *[H]* | *[Digital signatures, audit log]* |

### Information Disclosure

| # | Threat | Target | Likelihood | Impact | Mitigation |
|---|--------|--------|-----------|--------|------------|
| I1 | *[Data exfiltration]* | *[Customer data]* | *[M]* | *[Critical]* | *[DLP, encryption, access controls]* |

### Denial of Service

| # | Threat | Target | Likelihood | Impact | Mitigation |
|---|--------|--------|-----------|--------|------------|
| D1 | *[DDoS on web tier]* | *[Availability]* | *[H]* | *[H]* | *[CDN, rate limiting, WAF]* |

### Elevation of Privilege

| # | Threat | Target | Likelihood | Impact | Mitigation |
|---|--------|--------|-----------|--------|------------|
| E1 | *[Privilege escalation via misconfiguration]* | *[Admin access]* | *[M]* | *[Critical]* | *[Least privilege, regular audit]* |

---

## Risk Rating

| Threat ID | Likelihood | Impact | Risk Score | Priority |
|-----------|-----------|--------|-----------|----------|
| S1 | High | High | Critical | Immediate |
| T1 | Medium | Critical | High | Short-term |
| I1 | Medium | Critical | High | Short-term |
| D1 | High | High | Critical | Immediate |

---

## Mitigations

| # | Mitigation | Addresses | Priority | Owner | Status |
|---|-----------|----------|----------|-------|--------|
| 1 | *[Implement MFA for all users]* | S1 | Immediate | *[Team]* | *[Status]* |
| 2 | *[Deploy WAF with SQL injection rules]* | T1, D1 | Immediate | *[Team]* | *[Status]* |
| 3 | *[Encrypt data at rest with AES-256]* | I1 | Short-term | *[Team]* | *[Status]* |

{% if "iso_27001" in compliance %}
### ISO 27001 Control Mapping
| Mitigation | ISO 27001 Control | Annex A Reference |
|-----------|-------------------|-------------------|
| *[MFA]* | A.9.4.2 — Secure log-on procedures | Access control |
| *[Encryption]* | A.10.1.1 — Cryptographic controls | Cryptography |
| *[WAF]* | A.13.1.1 — Network controls | Communications security |
{% endif %}

---

## Residual Risk

*[After mitigations, what risks remain? Document accepted residual risk with justification.]*

| Threat | Residual Risk Level | Acceptance Rationale |
|--------|-------------------|---------------------|
| *[Threat]* | *[Low / Medium]* | *[Cost-benefit / Risk transfer / Monitoring]* |

---

## Review Schedule

- **Next Review:** *[Date or trigger — e.g., "Before next major release" or "Quarterly"]*
- **Trigger Events:** Architecture change, new feature with data access, security incident, new compliance requirement

---

## Approval

- **Author (Name/Title):** ____________________  **Date:** __________
- **Security Lead (Name/Title):** ____________________  **Date:** __________
- **System Owner (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `threat-model`.*
