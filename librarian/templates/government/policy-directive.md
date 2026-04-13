---
template_id: policy-directive
display_name: Policy Directive
preset: government
description: >-
  Official policy directive establishing organizational rules, standards, and requirements.
  Follows government document format with classification markings, distribution statement,
  authority chain, and compliance tracking. Supports DoD 5200.01 classification requirements.
suggested_tags: [policy, directive, governance]
suggested_folder: directives/
typical_cross_refs:
  - standard-operating-procedure
  - memorandum
  - security-plan
recommended_with:
  - standard-operating-procedure
requires: []
sections:
  - Header & Classification
  - Purpose
  - Applicability
  - Authority
  - Policy
  - Responsibilities
  - Procedures
  - Effective Date & Review
  - Distribution
---

# Policy Directive: {{title}}

**Directive Number:** *[ORG-DIR-XXXX]*
**Effective Date:** {{date}}
**Version:** {{version}}
**Originator:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
**Classified By:** *[Original Classification Authority]*
**Reason:** *[1.4(a)-(h) — cite specific reason]*
**Declassify On:** *[Date or event]*

---

### CLASSIFICATION MARKING
This document is classified **{{classification}}** in accordance with DoD 5200.01 and the original classification authority's determination. Handle, store, transmit, and destroy in accordance with the appropriate security classification guide.
{% endif %}

---

## Purpose

*[State the purpose of this directive in 2–3 sentences. What policy does it establish or revise? What organizational need does it address?]*

---

## Applicability

- **Organizations:** *[All subordinate organizations / Specific units]*
- **Personnel:** *[All personnel / Military / Civilian / Contractors]*
- **Scope:** *[Geographic or functional scope]*
- **Exceptions:** *[Any exemptions or waivers]*

---

## Authority

| Reference | Description |
|-----------|-------------|
| *[Public Law / Executive Order]* | *[Title and citation]* |
| *[DoD Directive/Instruction]* | *[Number and title]* |
| *[Agency regulation]* | *[Citation]* |
| *[Predecessor directive]* | *[Number — this directive supersedes]*  |

---

## Policy

### General Policy

1. *[Policy statement 1 — use directive language: "shall", "will", "must"]*
2. *[Policy statement 2]*
3. *[Policy statement 3]*

### Specific Requirements

*[Detail specific requirements, standards, or mandates. Organize by topic area if multiple areas are covered.]*

{% if "dod_5200" in compliance %}
### Classification & Handling Requirements
- All derivative classification must cite this directive or the applicable Security Classification Guide (SCG)
- Classified information shall be transmitted only through approved channels (SIPRNET, cleared courier, etc.)
- Storage requirements: GSA-approved containers, minimum
- Reproduction of classified material requires approval from *[authority]*
{% endif %}

{% if "iso_9001" in compliance %}
### Quality Management System Alignment
This directive is incorporated into the organization's Quality Management System per ISO 9001 § 7.5. Changes require the approval of the designated document control authority and must follow the established change management process.
{% endif %}

---

## Responsibilities

| Office / Role | Responsibilities |
|--------------|-----------------|
| *[Director / Commander]* | *[Overall authority, resource allocation, compliance enforcement]* |
| *[Department heads]* | *[Implementation within department, training, reporting]* |
| *[Compliance officer]* | *[Monitoring, auditing, reporting to leadership]* |
| *[All personnel]* | *[Comply with directive, report violations, complete required training]* |

---

## Procedures

### Implementation

1. *[Step 1: Dissemination — how the directive is communicated]*
2. *[Step 2: Training — required training and timeline]*
3. *[Step 3: Compliance verification — how compliance is checked]*

### Reporting

*[Describe reporting requirements: what reports, to whom, how frequently.]*

### Exceptions & Waivers

*[Process for requesting exceptions or waivers to this directive.]*
- **Waiver Authority:** *[Title/position]*
- **Request Format:** *[Memo / Form / Electronic]*
- **Approval Timeline:** *[X business days]*

---

## Effective Date & Review

| Field | Detail |
|-------|--------|
| **Effective Date** | {{date}} |
| **Supersedes** | *[Prior directive number and date, or "None — new policy"]* |
| **Review Cycle** | *[Annual / Biennial / As required]* |
| **Next Review** | *[Date]* |
| **Expiration** | *[Date, if applicable — otherwise "Until superseded or rescinded"]* |

---

## Distribution

{% if "dod_5200" in compliance %}
**Distribution Statement:** *[A through F per DoD 5230.24]*

- **A:** Approved for public release; distribution unlimited
- **B:** Authorized to U.S. Government agencies only
- **C:** Authorized to U.S. Government agencies and contractors
- **D:** Authorized to DoD and DoD contractors only
- **E:** Authorized to DoD components only
- **F:** Further dissemination only as directed by *[controlling authority]*
{% else %}
**Distribution:** *[All personnel / Specific distribution list]*
{% endif %}

---

## Approval

- **Originator (Name/Title):** ____________________  **Date:** __________
- **Legal Review (Name/Title):** ____________________  **Date:** __________
- **Approving Authority (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `policy-directive`.*
