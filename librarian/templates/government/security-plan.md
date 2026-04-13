---
template_id: security-plan
display_name: Security Plan
preset: government
description: >-
  Facility or information system security plan for government organizations.
  Covers physical security, personnel security, information security,
  threat assessment, countermeasures, and incident response. Supports
  DoD 5200.01, NIST SP 800-53, and FISMA requirements.
suggested_tags: [security, plan, information-assurance]
suggested_folder: plans/
typical_cross_refs:
  - policy-directive
  - standard-operating-procedure
  - after-action-report
recommended_with:
  - policy-directive
  - standard-operating-procedure
requires: []
sections:
  - Executive Summary
  - System / Facility Description
  - Security Categorization
  - Security Controls
  - Personnel Security
  - Physical Security
  - Incident Response
  - Contingency Planning
  - Authorization
---

# Security Plan: {{title}}

**Plan Number:** *[SP-XXXX]*
**Date:** {{date}}
**Version:** {{version}}
**Author:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
**Classified By:** *[Original Classification Authority]*
**Declassify On:** *[Date or event]*
{% endif %}

---

## Executive Summary

*[1–2 paragraph overview of the security posture, scope of this plan, key risks, and overall security assessment (Satisfactory / Marginal / Unsatisfactory).]*

---

## System / Facility Description

| Attribute | Detail |
|-----------|--------|
| **Name** | *[System or facility name]* |
| **Location** | *[Address / building / enclave]* |
| **Mission** | *[Primary mission or function]* |
| **Owner** | *[Responsible organization]* |
| **Authorizing Official** | *[Name/Title]* |
| **Information System Security Officer (ISSO)** | *[Name]* |
| **Operational Status** | *[Operational / Under development / Major modification]* |

### System Boundary
*[Define what is included in and excluded from this security plan's scope.]*

---

## Security Categorization

{% if "dod_5200" in compliance %}
### Information Classification
| Information Type | Classification | Handling Caveat |
|-----------------|---------------|----------------|
| *[Type 1]* | *[UNCLASSIFIED / CUI / CONFIDENTIAL / SECRET / TOP SECRET]* | *[NOFORN / REL TO / etc.]* |
| *[Type 2]* | *[Level]* | *[Caveat]* |

### Overall System Classification: *[Highest classification level processed]*
{% endif %}

### FIPS 199 Categorization (if applicable)

| Security Objective | Impact Level | Justification |
|-------------------|-------------|---------------|
| Confidentiality | *[Low / Moderate / High]* | *[Rationale]* |
| Integrity | *[Low / Moderate / High]* | *[Rationale]* |
| Availability | *[Low / Moderate / High]* | *[Rationale]* |
| **Overall** | **[Low / Moderate / High]** | |

---

## Security Controls

### Control Families (NIST SP 800-53 / CNSSI 1253)

| Family | # Applicable | # Implemented | # Planned | Gaps |
|--------|-------------|---------------|-----------|------|
| AC — Access Control | *[X]* | *[X]* | *[X]* | *[X]* |
| AU — Audit & Accountability | *[X]* | *[X]* | *[X]* | *[X]* |
| CM — Configuration Management | *[X]* | *[X]* | *[X]* | *[X]* |
| IA — Identification & Authentication | *[X]* | *[X]* | *[X]* | *[X]* |
| SC — System & Communications Protection | *[X]* | *[X]* | *[X]* | *[X]* |
| SI — System & Information Integrity | *[X]* | *[X]* | *[X]* | *[X]* |

### Key Controls Detail

| Control ID | Control Name | Implementation Status | Description |
|-----------|-------------|---------------------|-------------|
| AC-2 | Account Management | *[Implemented / Planned / N/A]* | *[How implemented]* |
| AU-6 | Audit Review, Analysis, and Reporting | *[Status]* | *[How implemented]* |
| IA-2 | Identification and Authentication | *[Status]* | *[How implemented]* |
| SC-8 | Transmission Confidentiality | *[Status]* | *[How implemented]* |

### Plan of Action & Milestones (POA&M) Summary

| # | Weakness | Control | Severity | Scheduled Completion | Status |
|---|----------|---------|----------|---------------------|--------|
| 1 | *[Weakness]* | *[Control ID]* | *[High/Med/Low]* | *[Date]* | *[Open/Closed]* |

---

## Personnel Security

| Requirement | Standard | Status |
|------------|----------|--------|
| Background investigations | *[Tier 1/3/5 / Public Trust / etc.]* | *[Current / X pending]* |
| Security awareness training | *[Annual — last completed date]* | *[X% compliant]* |
| Insider threat program | *[Established / In development]* | *[Status]* |
| Access agreements | *[NDA, AUP, rules of behavior]* | *[X% signed]* |
| Separation procedures | *[Defined / Documented]* | *[Status]* |

{% if "dod_5200" in compliance %}
### Clearance Requirements
| Position | Clearance Level | Investigation Type | Adjudication |
|----------|----------------|-------------------|-------------|
| *[ISSO]* | *[Secret / TS / TS/SCI]* | *[Tier 3 / Tier 5]* | *[DCSA / Agency]* |
| *[System Admin]* | *[Level]* | *[Type]* | *[Agency]* |
| *[User]* | *[Level]* | *[Type]* | *[Agency]* |
{% endif %}

---

## Physical Security

| Control | Implementation | Status |
|---------|---------------|--------|
| Perimeter access control | *[Badge / Guard / Fence / etc.]* | *[Compliant / Gap]* |
| Visitor management | *[Escort policy, logging]* | *[Compliant / Gap]* |
| Server/data center security | *[Access list, cameras, alarms]* | *[Compliant / Gap]* |
| Media protection | *[Storage, transport, destruction]* | *[Compliant / Gap]* |
| Environmental controls | *[Fire, HVAC, water, power]* | *[Compliant / Gap]* |

---

## Incident Response

### Incident Response Plan Summary

| Phase | Key Actions | Responsible |
|-------|-------------|-------------|
| **Preparation** | *[Training, tools, contacts]* | ISSO |
| **Detection** | *[Monitoring, alerting, reporting]* | SOC / ISSO |
| **Analysis** | *[Triage, scope, severity determination]* | ISSO / CIRT |
| **Containment** | *[Isolate, preserve evidence]* | ISSO / SA |
| **Eradication** | *[Remove threat, patch, rebuild]* | SA |
| **Recovery** | *[Restore, validate, monitor]* | SA / ISSO |
| **Post-Incident** | *[Lessons learned, report, improve]* | ISSO |

### Reporting Requirements

| Incident Type | Report To | Timeline |
|--------------|----------|----------|
| *[Data breach / PII]* | *[US-CERT / Agency SOC]* | *[1 hour / 24 hours]* |
| *[Classified spillage]* | *[Security Manager / DCSA]* | *[Immediately]* |
| *[Malware / Intrusion]* | *[SOC / US-CERT]* | *[1 hour]* |

---

## Contingency Planning

- **Backup Strategy:** *[Full/Incremental, frequency, offsite location]*
- **Recovery Time Objective (RTO):** *[X hours/days]*
- **Recovery Point Objective (RPO):** *[X hours of data loss acceptable]*
- **Alternate Processing Site:** *[Location, activation procedure]*
- **Last Test Date:** *[Date — test results: Pass/Fail]*

---

## Authorization

### Authorization to Operate (ATO)

| Field | Detail |
|-------|--------|
| **ATO Status** | *[Authorized / Interim ATO / Denied / Expired]* |
| **ATO Date** | *[Date]* |
| **ATO Expiration** | *[Date — typically 3 years]*  |
| **Authorizing Official** | *[Name/Title]* |
| **Conditions** | *[Any conditions on the authorization]* |

---

## Approval

- **ISSO (Name):** ____________________  **Date:** __________
- **ISSM (Name):** ____________________  **Date:** __________
- **Authorizing Official (Name):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `security-plan`.*
