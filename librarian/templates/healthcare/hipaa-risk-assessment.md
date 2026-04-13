---
template_id: hipaa-risk-assessment
display_name: HIPAA Risk Assessment
preset: healthcare
description: >-
  HIPAA Security Rule risk assessment per 45 CFR § 164.308(a)(1)(ii)(A). Identifies threats
  and vulnerabilities to ePHI, assesses likelihood and impact, and documents risk mitigation
  strategies. Required for all covered entities and business associates.
suggested_tags: [hipaa, risk, compliance, security]
suggested_folder: compliance/
typical_cross_refs:
  - policy-document
  - incident-report
  - clinical-protocol
recommended_with:
  - policy-document
  - incident-report
requires: []
sections:
  - Executive Summary
  - Scope & Methodology
  - Asset Inventory
  - Threat Identification
  - Vulnerability Assessment
  - Risk Analysis Matrix
  - Risk Mitigation Plan
  - Implementation Timeline
  - Review & Attestation
---

# HIPAA Risk Assessment: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**Assessment Period:** *[Start date]* — *[End date]*

---

## Executive Summary

*[1–2 paragraph overview of assessment scope, key findings, overall risk posture (Low/Medium/High), and top 3 risks requiring immediate attention.]*

### Risk Posture Summary

| Risk Level | Count | % of Total |
|-----------|-------|-----------|
| Critical | *[X]* | *[X%]* |
| High | *[X]* | *[X%]* |
| Medium | *[X]* | *[X%]* |
| Low | *[X]* | *[X%]* |
| **Total** | *[X]* | 100% |

---

## Scope & Methodology

### Scope
- **Covered Entity / Business Associate:** *[Organization name]*
- **Facilities Assessed:** *[List locations]*
- **Systems in Scope:** *[EHR, billing, email, mobile devices, etc.]*
- **ePHI Categories:** *[Demographics, clinical records, billing, lab results, imaging]*

### Methodology
This assessment follows the NIST SP 800-30 risk assessment framework as recommended by HHS OCR guidance. Each identified risk is scored on a Likelihood × Impact matrix (1–5 scale).

### Assessment Team

| Name | Role | Responsibility |
|------|------|---------------|
| *[Name]* | *[Privacy Officer]* | *[PHI inventory, policy review]* |
| *[Name]* | *[IT Security]* | *[Technical controls, vulnerability scanning]* |
| *[Name]* | *[Compliance]* | *[Regulatory alignment, gap analysis]* |

---

## Asset Inventory

### ePHI Data Flow

| System | ePHI Type | Volume | Storage | Transmission | Access |
|--------|----------|--------|---------|-------------|--------|
| *[EHR system]* | *[Full chart]* | *[X records]* | *[On-prem/Cloud]* | *[HL7/FHIR/VPN]* | *[X users]* |
| *[Billing]* | *[Demographics + insurance]* | *[X records]* | *[Cloud]* | *[TLS]* | *[X users]* |
| *[Email]* | *[Clinical notes via attachment]* | *[Variable]* | *[Cloud]* | *[TLS]* | *[X users]* |

### Physical Assets

| Asset | Location | ePHI Present | Physical Controls |
|-------|---------|-------------|-------------------|
| *[Server room]* | *[Building/floor]* | Yes | *[Badge access, cameras, climate]* |
| *[Workstations]* | *[Clinical areas]* | Yes | *[Auto-lock, privacy screens]* |
| *[Mobile devices]* | *[Various]* | *[Yes/No]* | *[MDM, encryption, remote wipe]* |

---

## Threat Identification

### Threat Categories

| Category | Threat | Source | Likelihood |
|----------|--------|--------|-----------|
| **Natural** | Flood/fire/power outage | Environment | *[1–5]* |
| **Human — Intentional** | Hacking, phishing, insider theft | External/Internal | *[1–5]* |
| **Human — Unintentional** | Misdirected fax/email, lost device | Staff | *[1–5]* |
| **Technical** | System failure, software vulnerability | Infrastructure | *[1–5]* |
| **Environmental** | HVAC failure, water damage | Facility | *[1–5]* |

---

## Vulnerability Assessment

| Vulnerability | HIPAA Standard | Current Control | Gap | Severity |
|--------------|---------------|----------------|-----|----------|
| *[Unencrypted laptops]* | § 164.312(a)(2)(iv) | *[Partial — 60% encrypted]* | *[40% unencrypted]* | High |
| *[No BAA with vendor X]* | § 164.308(b)(1) | *[None]* | *[Full gap]* | Critical |
| *[Weak password policy]* | § 164.312(d) | *[8 char, no MFA]* | *[Below standard]* | Medium |
| *[No audit log review]* | § 164.312(b) | *[Logs collected, not reviewed]* | *[Process gap]* | High |

---

## Risk Analysis Matrix

| # | Risk Description | HIPAA Ref | Likelihood | Impact | Score | Priority |
|---|------------------|-----------|-----------|--------|-------|----------|
| R1 | *[Unencrypted device with ePHI lost/stolen]* | § 164.312(a) | 4 | 5 | 20 | Critical |
| R2 | *[Business associate breach — no BAA]* | § 164.308(b) | 3 | 5 | 15 | Critical |
| R3 | *[Phishing leads to credential compromise]* | § 164.308(a)(5) | 4 | 4 | 16 | High |
| R4 | *[Audit logs not monitored]* | § 164.312(b) | 3 | 4 | 12 | High |
| R5 | *[Improper disposal of paper PHI]* | § 164.310(d)(2) | 2 | 3 | 6 | Medium |

### Scoring Guide
- **Likelihood:** 1 (Rare) — 5 (Almost certain)
- **Impact:** 1 (Negligible) — 5 (Catastrophic — breach notification required)
- **Score:** Likelihood × Impact (1–25)
- **Priority:** Critical (20+), High (12–19), Medium (6–11), Low (1–5)

---

## Risk Mitigation Plan

### R1: Unencrypted Device Loss (Critical)

**Current State:** 60% of laptops encrypted; no MDM on personal devices
**Target State:** 100% full-disk encryption; MDM on all devices accessing ePHI

| Action | Owner | Deadline | Cost | Status |
|--------|-------|----------|------|--------|
| Deploy BitLocker/FileVault to remaining devices | IT Security | *[Date]* | *[$X]* | *[Status]* |
| Implement MDM for BYOD | IT Security | *[Date]* | *[$X/yr]* | *[Status]* |
| Update device policy — no ePHI on unapproved devices | Privacy Officer | *[Date]* | $0 | *[Status]* |

### R2: Business Associate Compliance (Critical)

**Current State:** Vendor X processes ePHI without executed BAA
**Target State:** Executed BAA with all vendors handling ePHI

| Action | Owner | Deadline | Cost | Status |
|--------|-------|----------|------|--------|
| Inventory all vendors with ePHI access | Compliance | *[Date]* | $0 | *[Status]* |
| Execute BAAs with non-compliant vendors | Legal/Compliance | *[Date]* | *[Legal fees]* | *[Status]* |
| Terminate ePHI sharing with non-responsive vendors | Privacy Officer | *[Date]* | *[Migration cost]* | *[Status]* |

### R3–R5: Additional Mitigations
*[Follow same template for each risk.]*

{% if "iso_27001" in compliance %}
### ISO 27001 Alignment
This risk assessment maps to ISO 27001 Annex A controls. The following cross-reference ensures dual compliance:

| HIPAA Standard | ISO 27001 Control | Status |
|---------------|-------------------|--------|
| § 164.312(a) — Access Control | A.9.1, A.9.2 | *[Aligned/Gap]* |
| § 164.312(b) — Audit Controls | A.12.4 | *[Aligned/Gap]* |
| § 164.312(c) — Integrity | A.14.1 | *[Aligned/Gap]* |
| § 164.312(d) — Authentication | A.9.4 | *[Aligned/Gap]* |
| § 164.312(e) — Transmission Security | A.13.1, A.10.1 | *[Aligned/Gap]* |
{% endif %}

{% if "dod_5200" in compliance %}
### DoD 5200.01 Overlay
For facilities handling both PHI and classified information, additional controls apply:

- **Dual-use systems** must meet both HIPAA and NIST SP 800-171 requirements
- **Clearance verification** for staff with access to both PHI and classified data
- **Separate networks** for classified and PHI systems where feasible
{% endif %}

---

## Implementation Timeline

| Phase | Actions | Deadline | Owner | Status |
|-------|---------|----------|-------|--------|
| Immediate (0–30 days) | *[Critical risk mitigations]* | *[Date]* | *[Owner]* | |
| Short-term (30–90 days) | *[High risk mitigations]* | *[Date]* | *[Owner]* | |
| Medium-term (90–180 days) | *[Medium risk mitigations + policy updates]* | *[Date]* | *[Owner]* | |
| Ongoing | *[Monitoring, training, reassessment]* | Continuous | *[Owner]* | |

---

## Review & Attestation

### Review Requirements
- **Frequency:** At minimum annually, or after any of the following:
  - Security incident or breach
  - Significant change to systems or operations
  - New business associate relationship
  - Regulatory change affecting HIPAA requirements
- **Next Scheduled Review:** *[Date]*

### Attestation

I attest that this risk assessment has been conducted in accordance with 45 CFR § 164.308(a)(1)(ii)(A) and represents a thorough and accurate evaluation of risks to ePHI.

- **Privacy Officer (Name/Title):** ____________________  **Date:** __________
- **Security Officer (Name/Title):** ____________________  **Date:** __________
- **Executive Sponsor (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `hipaa-risk-assessment`.*
