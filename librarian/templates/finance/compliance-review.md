---
template_id: compliance-review
display_name: Compliance Review
preset: finance
description: >-
  Periodic compliance review for financial services firms. Covers regulatory
  requirements, policy adherence, deficiency findings, remediation actions,
  and attestation. Aligned with SEC, FINRA, and firm WSP requirements.
suggested_tags: [compliance, regulatory, review]
suggested_folder: compliance/
typical_cross_refs:
  - audit-finding
  - regulatory-filing-checklist
  - risk-assessment-finance
recommended_with:
  - audit-finding
  - regulatory-filing-checklist
requires: []
sections:
  - Review Summary
  - Scope & Methodology
  - Regulatory Framework
  - Findings
  - Remediation Plan
  - Testing Results
  - Attestation
---

# Compliance Review: {{title}}

**Review Period:** *[Start date]* — *[End date]*
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**Version:** {{version}}
**Classification:** {{classification}}

---

## Review Summary

*[1–2 paragraph overview of the compliance review scope, key findings (number and severity), overall compliance posture, and areas requiring immediate attention.]*

### Findings Summary

| Severity | Count | Remediated | Open |
|----------|-------|-----------|------|
| Critical | *[X]* | *[X]* | *[X]* |
| High | *[X]* | *[X]* | *[X]* |
| Medium | *[X]* | *[X]* | *[X]* |
| Low / Observation | *[X]* | *[X]* | *[X]* |

---

## Scope & Methodology

### Areas Reviewed

| Area | Reviewed | Method |
|------|----------|--------|
| *[Trading compliance]* | ☐ | *[Transaction sampling, exception review]* |
| *[KYC/AML]* | ☐ | *[File review, SAR analysis]* |
| *[Advertising / Marketing]* | ☐ | *[Material review, FINRA 2210]* |
| *[Books & Records]* | ☐ | *[Record retention audit]* |
| *[Supervisory procedures]* | ☐ | *[WSP review, supervisor interviews]* |
| *[Code of ethics / Personal trading]* | ☐ | *[Attestation review, trade comparison]* |
| *[Cybersecurity]* | ☐ | *[Policy review, incident log]* |
| *[Business continuity]* | ☐ | *[BCP test results, plan currency]* |

### Sample Methodology
- **Population:** *[X transactions / accounts / records]*
- **Sample Size:** *[X (Y% of population)]*
- **Selection Method:** *[Random / Risk-based / Targeted]*
- **Review Period:** *[Dates]*

{% if "sec_finra" in compliance %}
### Regulatory Basis
This review addresses requirements under:
- SEC Rule 206(4)-7 (Compliance Programs for Investment Advisers)
- FINRA Rule 3110 (Supervision)
- FINRA Rule 3120 (Supervisory Control System)
- FINRA Rule 4511 (General Requirements — Books and Records)
- SEC Rule 17a-4 (Records Retention)
- SEC Regulation S-P (Privacy)
- FinCEN BSA/AML requirements
{% endif %}

---

## Regulatory Framework

| Regulation | Applicable | Key Requirements | Compliance Status |
|-----------|-----------|------------------|-------------------|
| *[SEC Rule 206(4)-7]* | *[Yes/No]* | *[Annual review, CCO designated]* | *[Compliant / Gap]* |
| *[FINRA Rule 3110]* | *[Yes/No]* | *[Written supervisory procedures]* | *[Compliant / Gap]* |
| *[BSA/AML]* | *[Yes/No]* | *[CIP, SAR filing, CTR]* | *[Compliant / Gap]* |
| *[Reg S-P]* | *[Yes/No]* | *[Privacy notices, safeguards]* | *[Compliant / Gap]* |

---

## Findings

### Finding 1: *[Title]*

| Attribute | Detail |
|-----------|--------|
| **Severity** | *[Critical / High / Medium / Low]* |
| **Regulation** | *[Specific rule/section]* |
| **Description** | *[Factual description of the deficiency]* |
| **Root Cause** | *[Process gap / Training / System / Oversight]* |
| **Impact** | *[Regulatory risk, financial exposure, client impact]* |
| **Evidence** | *[Transaction #, date, supporting documentation reference]* |

### Finding 2: *[Title]*
*[Follow same structure.]*

### Finding 3: *[Title]*
*[Follow same structure.]*

---

## Remediation Plan

| # | Finding | Remediation Action | Owner | Deadline | Status |
|---|---------|-------------------|-------|----------|--------|
| 1 | *[Finding 1]* | *[Corrective action]* | *[Name/Title]* | *[Date]* | *[Open / In Progress / Complete]* |
| 2 | *[Finding 2]* | *[Corrective action]* | *[Name/Title]* | *[Date]* | *[Status]* |
| 3 | *[Finding 3]* | *[Corrective action]* | *[Name/Title]* | *[Date]* | *[Status]* |

---

## Testing Results

### Quantitative Results

| Test Area | Population | Sample | Exceptions | Exception Rate | Threshold | Pass/Fail |
|-----------|-----------|--------|-----------|---------------|-----------|-----------|
| *[Trade surveillance]* | *[X]* | *[X]* | *[X]* | *[X%]* | *[<5%]* | *[Pass/Fail]* |
| *[KYC file completeness]* | *[X]* | *[X]* | *[X]* | *[X%]* | *[<2%]* | *[Pass/Fail]* |

---

## Attestation

I certify that this compliance review has been conducted in accordance with the firm's compliance program and applicable regulatory requirements. The findings and remediation plans have been communicated to relevant business unit heads.

- **Chief Compliance Officer (Name):** ____________________  **Date:** __________
- **CEO / Managing Principal (Name):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `compliance-review`.*
