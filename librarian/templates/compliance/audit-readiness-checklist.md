---
template_id: audit-readiness-checklist
display_name: Audit Readiness Checklist
preset: compliance
description: >-
  Pre-audit readiness checklist for preparing for internal audits, external audits,
  regulatory examinations, or certification assessments. Covers documentation,
  evidence gathering, personnel preparation, and logistics.
suggested_tags: [compliance, audit, readiness]
suggested_folder: docs/
typical_cross_refs:
  - sox-controls-matrix
  - iso27001-statement-of-applicability
  - vendor-risk-assessment
recommended_with:
  - vendor-risk-assessment
requires: []
sections:
  - Audit Overview
  - Documentation Checklist
  - Evidence Gathering
  - Personnel Preparation
  - Logistics
  - Post-Audit Actions
---

# Audit Readiness Checklist: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}

---

## Audit Overview

| Attribute | Detail |
|-----------|--------|
| **Audit Type** | *[Internal / External / Regulatory / Certification]* |
| **Standard/Framework** | *[ISO 27001 / SOX / HIPAA / PCI-DSS / SOC 2 / Custom]* |
| **Auditor** | *[Firm name or internal audit team]* |
| **Audit Dates** | *[Start — End]* |
| **Scope** | *[Systems, processes, time period]* |
| **Primary Contact** | *[Name — internal audit liaison]* |

---

## Documentation Checklist

### Policies & Procedures

| # | Document | Current Version | Location | Ready |
|---|----------|----------------|----------|-------|
| 1 | *[Information security policy]* | *[V X.Y]* | *[Path/System]* | ☐ |
| 2 | *[Access control policy]* | *[V X.Y]* | *[Path/System]* | ☐ |
| 3 | *[Incident response plan]* | *[V X.Y]* | *[Path/System]* | ☐ |
| 4 | *[Business continuity plan]* | *[V X.Y]* | *[Path/System]* | ☐ |
| 5 | *[Risk assessment]* | *[V X.Y]* | *[Path/System]* | ☐ |

{% if "iso_9001" in compliance or "iso_27001" in compliance %}
### ISO-Specific Documentation

| # | Document | ISO Clause | Ready |
|---|----------|-----------|-------|
| 1 | ISMS scope statement | 4.3 | ☐ |
| 2 | Risk assessment methodology | 6.1.2 | ☐ |
| 3 | Risk treatment plan | 6.1.3 | ☐ |
| 4 | Statement of Applicability | 6.1.3(d) | ☐ |
| 5 | Internal audit reports | 9.2 | ☐ |
| 6 | Management review minutes | 9.3 | ☐ |
| 7 | Corrective action records | 10.1 | ☐ |
{% endif %}

{% if "hipaa" in compliance %}
### HIPAA-Specific Documentation

| # | Document | HIPAA Reference | Ready |
|---|----------|----------------|-------|
| 1 | Risk assessment (current) | § 164.308(a)(1)(ii)(A) | ☐ |
| 2 | Policies and procedures | § 164.316(a) | ☐ |
| 3 | Business Associate Agreements | § 164.308(b)(1) | ☐ |
| 4 | Training records | § 164.308(a)(5)(i) | ☐ |
| 5 | Incident/breach log | § 164.308(a)(6)(ii) | ☐ |
| 6 | Sanction policy | § 164.308(a)(1)(ii)(C) | ☐ |
{% endif %}

{% if "sec_finra" in compliance %}
### SEC/FINRA-Specific Documentation

| # | Document | Rule Reference | Ready |
|---|----------|---------------|-------|
| 1 | Written supervisory procedures (WSPs) | FINRA 3110 | ☐ |
| 2 | Annual compliance review | SEC 206(4)-7 | ☐ |
| 3 | Books and records index | SEC 17a-4 | ☐ |
| 4 | Business continuity plan | FINRA 4370 | ☐ |
{% endif %}

{% if "dod_5200" in compliance %}
### DoD-Specific Documentation

| # | Document | Reference | Ready |
|---|----------|-----------|-------|
| 1 | System Security Plan (SSP) | NIST 800-53 | ☐ |
| 2 | POA&M | FISMA | ☐ |
| 3 | ATO package | RMF | ☐ |
| 4 | Security Classification Guide | DoD 5200.01 | ☐ |
{% endif %}

---

## Evidence Gathering

### Evidence by Control Area

| # | Evidence Type | Period | Source | Gathered |
|---|-------------|--------|--------|---------|
| 1 | *[Access review evidence]* | *[Last 12 months]* | *[IAM system]* | ☐ |
| 2 | *[Change management records]* | *[Last 12 months]* | *[Ticketing system]* | ☐ |
| 3 | *[Training completion records]* | *[Current year]* | *[LMS]* | ☐ |
| 4 | *[Vulnerability scan results]* | *[Last quarter]* | *[Scanner]* | ☐ |
| 5 | *[Incident response records]* | *[Last 12 months]* | *[Incident system]* | ☐ |
| 6 | *[Backup and recovery test results]* | *[Last test]* | *[IT operations]* | ☐ |

---

## Personnel Preparation

| # | Action | Owner | Complete |
|---|--------|-------|---------|
| 1 | Brief key personnel on audit scope and schedule | *[Audit liaison]* | ☐ |
| 2 | Confirm availability of process owners during audit | *[Managers]* | ☐ |
| 3 | Prepare subject matter experts for interviews | *[SMEs]* | ☐ |
| 4 | Review previous audit findings and remediation evidence | *[Compliance]* | ☐ |
| 5 | Conduct mock audit / dry run on high-risk areas | *[Internal audit]* | ☐ |

---

## Logistics

| # | Item | Detail | Confirmed |
|---|------|--------|----------|
| 1 | Audit room / workspace | *[Room / virtual meeting details]* | ☐ |
| 2 | Network / system access for auditors | *[Guest accounts, VPN]* | ☐ |
| 3 | Opening meeting scheduled | *[Date/Time]* | ☐ |
| 4 | Closing meeting scheduled | *[Date/Time]* | ☐ |
| 5 | Document request list received | *[Date]* | ☐ |
| 6 | Document request list fulfilled | *[Date]* | ☐ |

---

## Post-Audit Actions

- [ ] Receive preliminary findings from auditor
- [ ] Review findings for accuracy — respond within *[X days]*
- [ ] Develop remediation plan for any findings
- [ ] Track remediation to closure
- [ ] Archive audit evidence package per retention policy
- [ ] Schedule follow-up assessment if required

---

*Document generated by librarian v{{librarian_version}} from template `audit-readiness-checklist`.*
