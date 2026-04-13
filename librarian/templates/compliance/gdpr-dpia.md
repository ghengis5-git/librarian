---
template_id: gdpr-dpia
display_name: GDPR Data Protection Impact Assessment
preset: compliance
description: >-
  Data Protection Impact Assessment (DPIA) per GDPR Article 35. Assesses risks
  to data subjects from processing activities, evaluates necessity and proportionality,
  and documents risk mitigation measures.
suggested_tags: [compliance, gdpr, privacy, dpia]
suggested_folder: docs/
typical_cross_refs:
  - vendor-risk-assessment
  - audit-readiness-checklist
recommended_with:
  - vendor-risk-assessment
requires: []
sections:
  - Processing Description
  - Necessity & Proportionality
  - Risk Assessment
  - Mitigation Measures
  - Consultation
  - Decision
---

# GDPR Data Protection Impact Assessment: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**DPO Consulted:** *[Name / Date]*

---

## Processing Description

| Attribute | Detail |
|-----------|--------|
| **Data Controller** | *[Organization name]* |
| **Data Processor(s)** | *[Third parties, if any]* |
| **Processing Purpose** | *[Why this data is being processed]* |
| **Legal Basis** | *[Art. 6(1)(a) Consent / (b) Contract / (c) Legal obligation / (d) Vital interests / (e) Public task / (f) Legitimate interest]* |
| **Data Subjects** | *[Customers / Employees / Patients / Minors / etc.]* |
| **Data Categories** | *[Name, email, health data, financial, location, biometric, etc.]* |
| **Special Categories (Art. 9)** | *[Yes — specify / No]* |
| **Volume** | *[Approximate number of data subjects and records]* |
| **Retention Period** | *[Duration and legal basis for retention]* |
| **Cross-border Transfers** | *[Yes — mechanism (SCCs, adequacy) / No]* |

### Data Flow
*[Describe or diagram how personal data flows: collection → processing → storage → sharing → deletion.]*

{% if "hipaa" in compliance %}
### HIPAA Cross-Reference
If this processing involves health data subject to both GDPR and HIPAA:
- **HIPAA classification:** *[PHI / ePHI / De-identified]*
- **Dual compliance required:** *[Describe how both frameworks are satisfied]*
{% endif %}

---

## Necessity & Proportionality

### Necessity Assessment

| Question | Answer | Justification |
|----------|--------|---------------|
| Is this processing necessary for the stated purpose? | *[Yes/No]* | *[Explain]* |
| Could the purpose be achieved with less data? | *[Yes/No]* | *[Explain]* |
| Could the purpose be achieved without special category data? | *[Yes/No/N/A]* | *[Explain]* |
| Is there a less intrusive alternative? | *[Yes/No]* | *[If yes, why not chosen]* |

### Proportionality Assessment
*[Is the processing proportionate to the purpose? Does the benefit outweigh the risk to data subjects?]*

---

## Risk Assessment

### Risks to Data Subjects

| # | Risk | Likelihood | Severity | Overall Risk | Affected Rights |
|---|------|-----------|----------|-------------|----------------|
| 1 | *[Unauthorized access to personal data]* | *[H/M/L]* | *[H/M/L]* | *[H/M/L]* | *[Confidentiality]* |
| 2 | *[Inaccurate data leading to wrong decisions]* | *[H/M/L]* | *[H/M/L]* | *[H/M/L]* | *[Accuracy, fairness]* |
| 3 | *[Excessive data retention]* | *[H/M/L]* | *[H/M/L]* | *[H/M/L]* | *[Storage limitation]* |
| 4 | *[Cross-border transfer to inadequate jurisdiction]* | *[H/M/L]* | *[H/M/L]* | *[H/M/L]* | *[International transfer]* |
| 5 | *[Re-identification of pseudonymized data]* | *[H/M/L]* | *[H/M/L]* | *[H/M/L]* | *[Confidentiality]* |

---

## Mitigation Measures

| Risk # | Measure | Implementation Status | Residual Risk |
|--------|---------|---------------------|---------------|
| 1 | *[Encryption, access controls, audit logging]* | *[Implemented / Planned]* | *[Low]* |
| 2 | *[Data validation, correction procedures, Art. 16 process]* | *[Implemented / Planned]* | *[Low]* |
| 3 | *[Automated deletion, retention schedule enforcement]* | *[Implemented / Planned]* | *[Low]* |
| 4 | *[Standard Contractual Clauses, supplementary measures]* | *[Implemented / Planned]* | *[Medium]* |
| 5 | *[Pseudonymization techniques, access restrictions]* | *[Implemented / Planned]* | *[Low]* |

### Data Subject Rights Implementation

| Right | Implemented | Process |
|-------|-----------|---------|
| Access (Art. 15) | *[Yes/No]* | *[Describe process]* |
| Rectification (Art. 16) | *[Yes/No]* | *[Describe process]* |
| Erasure (Art. 17) | *[Yes/No]* | *[Describe process]* |
| Restriction (Art. 18) | *[Yes/No]* | *[Describe process]* |
| Portability (Art. 20) | *[Yes/No]* | *[Describe process]* |
| Objection (Art. 21) | *[Yes/No]* | *[Describe process]* |

---

## Consultation

### DPO Consultation

| Date | DPO Name | Advice | Incorporated |
|------|---------|--------|-------------|
| *[Date]* | *[Name]* | *[Summary of advice]* | *[Yes / Partially / No — reason]* |

### Supervisory Authority Consultation (Art. 36)
- **Required?** *[Yes — high residual risk / No]*
- **If yes, authority consulted:** *[DPA name]*
- **Date:** *[Date]*
- **Response:** *[Summary]*

---

## Decision

**Overall residual risk:** *[Low / Medium / High]*
**Decision:** *[Proceed / Proceed with conditions / Do not proceed]*

**Conditions (if applicable):**
1. *[Condition]*
2. *[Condition]*

**Review date:** *[Date — must be reviewed if processing changes or annually]*

---

## Approval

- **Data Protection Officer (Name):** ____________________  **Date:** __________
- **Processing Owner (Name/Title):** ____________________  **Date:** __________
- **Executive Sponsor (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `gdpr-dpia`.*
