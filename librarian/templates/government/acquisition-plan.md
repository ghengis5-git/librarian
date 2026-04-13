---
template_id: acquisition-plan
display_name: Acquisition Plan
preset: government
description: >-
  Government acquisition plan per FAR Part 7. Covers requirements definition,
  market research, acquisition strategy, evaluation criteria, cost estimates,
  milestones, and approvals. Used for procurement actions above the simplified
  acquisition threshold.
suggested_tags: [acquisition, procurement, planning]
suggested_folder: plans/
typical_cross_refs:
  - memorandum
  - policy-directive
  - security-plan
recommended_with:
  - security-plan
requires: []
sections:
  - Acquisition Overview
  - Requirements
  - Market Research Summary
  - Acquisition Strategy
  - Source Selection
  - Cost Estimate
  - Milestone Schedule
  - Risk Assessment
  - Approvals
---

# Acquisition Plan: {{title}}

**Document ID:** *[AP-XXXX]*
**Date:** {{date}}
**Version:** {{version}}
**Contracting Officer:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
{% endif %}

---

## Acquisition Overview

| Attribute | Detail |
|-----------|--------|
| **Requiring Activity** | *[Organization / Program Office]* |
| **Program/Project Name** | *[Name]* |
| **Estimated Value** | *[$X — total contract value including options]* |
| **Contract Type** | *[FFP / T&M / CPFF / CPAF / IDIQ / BPA]* |
| **NAICS Code** | *[Code — description]* |
| **Small Business Set-Aside** | *[Full / Partial / None — justify if none]* |
| **Period of Performance** | *[Base: X months + Options: Y months]* |
| **Funding Source** | *[Appropriation / Fund cite]* |
| **Competition** | *[Full & Open / Limited / Sole Source — justify if limited]* |

---

## Requirements

### Statement of Need
*[Why is this acquisition necessary? What capability gap or mission requirement does it address?]*

### Performance Requirements

| # | Requirement | Performance Standard | Acceptable Quality Level |
|---|-------------|---------------------|------------------------|
| 1 | *[Requirement]* | *[Measurable standard]* | *[AQL %]* |
| 2 | *[Requirement]* | *[Measurable standard]* | *[AQL %]* |

### Independent Government Cost Estimate (IGCE)

| CLIN | Description | Qty | Unit Price | Extended |
|------|-------------|-----|-----------|---------|
| 0001 | *[Base year — description]* | *[X]* | *[$X]* | *[$X]* |
| 0002 | *[Option year 1]* | *[X]* | *[$X]* | *[$X]* |
| | **Total Estimated Value** | | | **$X** |

{% if "dod_5200" in compliance %}
### Security Requirements
- **Clearance Level Required:** *[None / Confidential / Secret / Top Secret / SCI]*
- **Facility Clearance Required:** *[Yes / No]*
- **DD Form 254 Required:** *[Yes / No]*
- **ITAR/EAR Controlled:** *[Yes / No — cite control]*
- **CUI Handling Required:** *[Yes / No — categories]*
{% endif %}

---

## Market Research Summary

### Research Conducted

| Method | Date | Results |
|--------|------|---------|
| *[SAM.gov search]* | *[Date]* | *[X vendors identified]* |
| *[RFI / Sources Sought]* | *[Date]* | *[X responses received]* |
| *[Industry day]* | *[Date]* | *[X attendees]* |
| *[GSA Schedule review]* | *[Date]* | *[X schedule holders]* |

### Capable Sources Identified

| Vendor | Size | Capability | Past Performance |
|--------|------|-----------|-----------------|
| *[Vendor 1]* | *[Small / Large]* | *[Assessment]* | *[Satisfactory / Exceptional]* |
| *[Vendor 2]* | *[Small / Large]* | *[Assessment]* | *[Rating]* |

---

## Acquisition Strategy

### Selected Approach
*[Describe the acquisition strategy and rationale. Include contract type rationale.]*

### Small Business Considerations
- **Small Business Set-Aside:** *[Total / Partial / None]*
- **Subcontracting Plan Required:** *[Yes — if > $750K and not small business set-aside]*
- **SBA Coordination:** *[If sole source > $4.5M to other-than-small]*

### Contract Type Justification
*[Explain why the selected contract type is appropriate given the risk allocation and requirement maturity.]*

---

## Source Selection

### Evaluation Methodology
*[Best value tradeoff / Lowest price technically acceptable (LPTA) / Highest technically rated]*

### Evaluation Factors

| Factor | Weight | Subfactors |
|--------|--------|-----------|
| *[Technical Capability]* | *[X%]* | *[Approach, staffing, experience]* |
| *[Past Performance]* | *[X%]* | *[Relevance, quality, schedule]* |
| *[Price/Cost]* | *[X%]* | *[Reasonableness, realism, completeness]* |
| *[Small Business Participation]* | *[X%]* | *[Subcontracting plan]* |

### Evaluation Team

| Role | Name | Organization |
|------|------|-------------|
| Source Selection Authority | *[Name]* | *[Org]* |
| Technical Evaluator | *[Name]* | *[Org]* |
| Cost/Price Analyst | *[Name]* | *[Org]* |
| Contracting Officer | *[Name]* | *[Org]* |
| Legal Advisor | *[Name]* | *[Org]* |

---

## Cost Estimate

| Phase | Estimated Cost | Basis |
|-------|---------------|-------|
| Base Period | *[$X]* | *[IGCE / Historical / Market]* |
| Option Year 1 | *[$X]* | *[Escalation rate: X%]* |
| Option Year 2 | *[$X]* | *[Escalation rate: X%]* |
| **Total Ceiling** | **$X** | |

---

## Milestone Schedule

| Milestone | Target Date | Responsible |
|-----------|-----------|-------------|
| Acquisition plan approved | *[Date]* | KO |
| Solicitation issued | *[Date]* | KO |
| Proposals due | *[Date]* | Vendors |
| Evaluation complete | *[Date]* | Eval team |
| Award decision | *[Date]* | SSA |
| Contract award | *[Date]* | KO |
| Period of performance start | *[Date]* | Contractor |

---

## Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | *[Protest risk]* | *[H/M/L]* | *[Schedule delay]* | *[Thorough documentation, legal review]* |
| 2 | *[Insufficient competition]* | *[H/M/L]* | *[Higher cost]* | *[Broader market research, RFI]* |
| 3 | *[Technical risk]* | *[H/M/L]* | *[Performance shortfall]* | *[Detailed evaluation, past performance weight]* |

---

## Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Contracting Officer | {{author}} | ________________ | {{date}} |
| Requirements Owner | *[Name]* | ________________ | |
| Legal Counsel | *[Name]* | ________________ | |
| Competition Advocate | *[Name]* | ________________ | |
| Approving Authority | *[Name]* | ________________ | |

---

*Document generated by librarian v{{librarian_version}} from template `acquisition-plan`.*
