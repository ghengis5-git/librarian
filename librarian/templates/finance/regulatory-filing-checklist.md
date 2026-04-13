---
template_id: regulatory-filing-checklist
display_name: Regulatory Filing Checklist
preset: finance
description: >-
  Pre-filing checklist for regulatory submissions (SEC, FINRA, state regulators, FinCEN).
  Tracks filing requirements, deadlines, review workflow, supporting documentation,
  and submission confirmation. Prevents missed filings and ensures completeness.
suggested_tags: [regulatory, filing, checklist]
suggested_folder: regulatory-filings/
typical_cross_refs:
  - compliance-review
  - audit-finding
recommended_with:
  - compliance-review
requires: []
sections:
  - Filing Overview
  - Filing Calendar
  - Pre-Filing Checklist
  - Supporting Documentation
  - Review & Approval
  - Submission Record
  - Post-Filing Requirements
---

# Regulatory Filing Checklist: {{title}}

**Filing Type:** *[Form ADV / Form PF / FOCUS Report / SAR / CTR / Form U4/U5 / 13F / Other]*
**Filing Period:** *[Period covered]*
**Due Date:** *[Regulatory deadline]*
**Date:** {{date}}
**Prepared By:** {{author}}
**Status:** {{status}}
**Version:** {{version}}

---

## Filing Overview

| Attribute | Detail |
|-----------|--------|
| **Regulator** | *[SEC / FINRA / State / FinCEN / CFTC / NFA]* |
| **Filing System** | *[EDGAR / IARD / EFT / FinCEN BSA / Web CRD / Other]* |
| **Filing Type** | *[Initial / Annual / Amended / Event-driven]* |
| **Entity Filing** | *[Firm legal name, CRD #, SEC file #]* |
| **Reporting Period** | *[Date range]* |
| **Regulatory Deadline** | *[Date — include grace period if applicable]* |
| **Internal Deadline** | *[Date — typically 5–10 business days before regulatory]*  |

{% if "sec_finra" in compliance %}
### Applicable Rules
- **SEC:** *[Rule citation — e.g., Rule 204-1 (Form ADV), Rule 204(b)-1 (Form PF)]*
- **FINRA:** *[Rule citation — e.g., Rule 4521 (FOCUS), Rule 4530 (Customer Complaint)]*
- **Penalty for Late Filing:** *[Describe — deficiency letter, fine, suspension, etc.]*
{% endif %}

---

## Filing Calendar

### Annual Filing Schedule

| Filing | Regulator | Frequency | Due Date | Internal Deadline | Owner | Status |
|--------|-----------|-----------|----------|-------------------|-------|--------|
| *[Form ADV Annual]* | SEC/State | Annual | *[March 31]* | *[March 15]* | *[CCO]* | ☐ |
| *[Form PF]* | SEC | *[Quarterly/Annual]* | *[60/120 days]* | *[Internal]* | *[CFO/CCO]* | ☐ |
| *[FOCUS Report]* | FINRA | *[Monthly/Quarterly]* | *[17/17 bus days]* | *[Internal]* | *[FINOP]* | ☐ |
| *[13F]* | SEC | Quarterly | *[45 days]* | *[Internal]* | *[Compliance]* | ☐ |
| *[Form D]* | SEC | Event-driven | *[15 days after first sale]* | *[Immediately]* | *[Legal]* | ☐ |

---

## Pre-Filing Checklist

### Data Gathering

| # | Item | Source | Responsible | Complete |
|---|------|--------|-------------|----------|
| 1 | *[AUM calculation (current period)]* | *[Portfolio system]* | *[Operations]* | ☐ |
| 2 | *[Client count by type]* | *[CRM]* | *[Operations]* | ☐ |
| 3 | *[Fee schedule changes]* | *[Legal/Compliance]* | *[CCO]* | ☐ |
| 4 | *[Disciplinary history updates]* | *[Legal]* | *[CCO]* | ☐ |
| 5 | *[Financial statements (if required)]* | *[Accounting]* | *[CFO]* | ☐ |
| 6 | *[Custody confirmation]* | *[Operations]* | *[CCO]* | ☐ |

### Accuracy Verification

| # | Check | Verified By | Date | Pass |
|---|-------|-----------|------|------|
| 1 | *[All numerical fields reconcile to source]* | *[Name]* | | ☐ |
| 2 | *[All dates and periods correct]* | *[Name]* | | ☐ |
| 3 | *[Entity information unchanged or updated]* | *[Name]* | | ☐ |
| 4 | *[Prior period comparison — material changes flagged]* | *[Name]* | | ☐ |
| 5 | *[Disclosure language reviewed by legal (if applicable)]* | *[Name]* | | ☐ |

---

## Supporting Documentation

| # | Document | Location | On File |
|---|----------|----------|---------|
| 1 | *[Source data / workpapers]* | *[File path or system]* | ☐ |
| 2 | *[Prior period filing (for comparison)]* | *[File path]* | ☐ |
| 3 | *[Audited financial statements (if required)]* | *[File path]* | ☐ |
| 4 | *[Board resolution (if required)]* | *[File path]* | ☐ |

---

## Review & Approval

| Step | Reviewer | Date | Approved |
|------|---------|------|---------|
| Preparer review | *[Name/Title]* | | ☐ |
| Compliance review | *[CCO Name]* | | ☐ |
| Legal review (if required) | *[Counsel Name]* | | ☐ |
| Senior management sign-off | *[CEO/Managing Partner]* | | ☐ |
| External auditor review (if required) | *[Firm Name]* | | ☐ |

---

## Submission Record

| Field | Detail |
|-------|--------|
| **Filed By** | *[Name]* |
| **Filing Date** | *[Date]* |
| **Filing System** | *[EDGAR / IARD / etc.]* |
| **Confirmation #** | *[System-generated confirmation]* |
| **Filed On Time** | *[Yes / No — if no, document reason and late filing procedure]* |

---

## Post-Filing Requirements

- [ ] Confirmation receipt saved to records
- [ ] Filing copy retained per retention policy (*[X years]*)
- [ ] Brochure delivery to clients (if Form ADV — within 120 days or material change)
- [ ] State notice filings updated (if applicable)
- [ ] Internal filing calendar updated for next period
- [ ] Any deficiency letter response tracked

---

*Document generated by librarian v{{librarian_version}} from template `regulatory-filing-checklist`.*
