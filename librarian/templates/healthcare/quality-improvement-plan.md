---
template_id: quality-improvement-plan
display_name: Quality Improvement Plan
preset: healthcare
description: >-
  Structured quality improvement plan using PDSA (Plan-Do-Study-Act) methodology.
  Covers performance metrics, root cause analysis, intervention design, measurement
  strategy, and sustainability planning. Aligns with Joint Commission and CMS requirements.
suggested_tags: [quality, improvement, performance]
suggested_folder: quality-assurance/
typical_cross_refs:
  - clinical-protocol
  - incident-report
  - policy-document
recommended_with:
  - clinical-protocol
  - incident-report
requires: []
sections:
  - Executive Summary
  - Problem Statement
  - Current State Analysis
  - Root Cause Analysis
  - Improvement Goals
  - Intervention Plan
  - Measurement Strategy
  - PDSA Cycles
  - Sustainability Plan
  - Reporting & Governance
---

# Quality Improvement Plan: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**QI Project Sponsor:** *[Name/Title]*

---

## Executive Summary

*[1–2 paragraph overview of the quality gap, proposed intervention, expected outcomes, and timeline.]*

---

## Problem Statement

*[Concise description of the quality issue. Use data to quantify the gap between current and desired performance.]*

- **Metric:** *[e.g., "Central line-associated bloodstream infection (CLABSI) rate"]*
- **Current Performance:** *[e.g., "2.1 per 1,000 central line days"]*
- **Benchmark / Target:** *[e.g., "NHSN 50th percentile: 0.8 per 1,000 central line days"]*
- **Gap:** *[e.g., "162% above benchmark"]*
- **Impact:** *[Patient harm, cost, regulatory risk, staff burden]*

---

## Current State Analysis

### Process Map
*[Describe or diagram the current workflow related to the quality issue.]*

### Data Summary

| Metric | Baseline (Last 12 months) | Trend | Data Source |
|--------|--------------------------|-------|-------------|
| *[Primary metric]* | *[Value ± CI]* | *[↑↓→]* | *[Registry/EHR/manual]* |
| *[Secondary metric]* | *[Value]* | *[↑↓→]* | *[Source]* |
| *[Balancing measure]* | *[Value]* | *[↑↓→]* | *[Source]* |

### Stakeholder Input
*[Summary of staff interviews, patient feedback, or survey results.]*

---

## Root Cause Analysis

### Method Used
*[Fishbone diagram / 5 Whys / Pareto analysis / Failure mode analysis]*

### Contributing Factors

| Category | Root Cause | Evidence | Addressable |
|----------|-----------|----------|------------|
| Process | *[e.g., "Inconsistent hand hygiene compliance"]* | *[Observation data]* | Yes |
| People | *[e.g., "Staff knowledge gap on bundle elements"]* | *[Survey results]* | Yes |
| Equipment | *[e.g., "Supply access barriers"]* | *[Staff reports]* | Yes |
| Environment | *[e.g., "High patient-to-nurse ratio"]* | *[Staffing data]* | Partial |

---

## Improvement Goals

### SMART Goals

| Goal | Specific | Measurable | Achievable | Relevant | Time-bound |
|------|---------|-----------|-----------|----------|-----------|
| Primary | *[Reduce CLABSI rate]* | *[to <1.0/1000 line days]* | *[Based on peer data]* | *[Patient safety]* | *[Within 12 months]* |
| Secondary | *[Improve bundle compliance]* | *[to >95%]* | *[Based on pilot data]* | *[Supports primary goal]* | *[Within 6 months]* |

---

## Intervention Plan

### Planned Interventions

| # | Intervention | Owner | Start Date | Evidence Base |
|---|-------------|-------|-----------|---------------|
| 1 | *[e.g., "Standardize insertion checklist"]* | *[Name]* | *[Date]* | *[Citation]* |
| 2 | *[e.g., "Daily necessity review rounds"]* | *[Name]* | *[Date]* | *[Citation]* |
| 3 | *[e.g., "Staff education program"]* | *[Name]* | *[Date]* | *[Citation]* |

### Resources Required

| Resource | Estimated Cost | Funding Source | Status |
|----------|---------------|---------------|--------|
| *[Staff time for training]* | *[$X]* | *[Operating budget]* | *[Approved/Pending]* |
| *[Supplies/equipment]* | *[$X]* | *[Capital budget]* | *[Approved/Pending]* |

{% if "hipaa" in compliance %}
### HIPAA Considerations
If this QI project involves PHI for measurement or reporting:
- **IRB Determination:** *[QI — not research / IRB-exempt / IRB-approved]*
- **Minimum Necessary:** Data limited to *[describe minimum PHI needed]*
- **De-identification:** Aggregate reporting only; no individual patient identifiers in QI reports
{% endif %}

{% if "iso_9001" in compliance %}
### ISO 9001 Alignment (§ 10.3 — Continual Improvement)
This QI plan fulfills the continual improvement requirement. Nonconformity identified via *[audit/complaint/data analysis]*, root cause analysis completed, corrective actions documented with effectiveness verification planned.
{% endif %}

---

## Measurement Strategy

### Outcome Measures

| Measure | Definition | Data Source | Collection Frequency | Responsible |
|---------|-----------|-------------|---------------------|-------------|
| *[Primary outcome]* | *[Operational definition]* | *[EHR/Registry]* | *[Monthly]* | *[Name]* |

### Process Measures

| Measure | Definition | Target | Collection Frequency |
|---------|-----------|--------|---------------------|
| *[Bundle compliance rate]* | *[% of eligible patients with all bundle elements]* | *[>95%]* | *[Weekly]* |

### Balancing Measures

| Measure | Purpose | Acceptable Range |
|---------|---------|-----------------|
| *[e.g., "Line utilization ratio"]* | *[Ensure lines aren't removed prematurely]* | *[Within ±10% of baseline]* |

---

## PDSA Cycles

### Cycle 1: *[Intervention Name]*

| Phase | Details |
|-------|---------|
| **Plan** | *[What change? Who? When? Where? What data to collect?]* |
| **Do** | *[Carry out the test. Document observations and problems.]* |
| **Study** | *[Analyze results. Compare to predictions. Summarize learnings.]* |
| **Act** | *[Adopt / Adapt / Abandon. Describe next steps.]* |

### Cycle 2: *[Intervention Name]*
*[Follow same structure.]*

---

## Sustainability Plan

- **Hardwiring:** *[Embed changes into EHR order sets, checklists, or standing orders]*
- **Ongoing Monitoring:** *[Transition from weekly to monthly measurement after 6 months of sustained improvement]*
- **Accountability:** *[Assign permanent owner for ongoing compliance monitoring]*
- **Staff Onboarding:** *[Include in new employee orientation and annual competencies]*

---

## Reporting & Governance

| Audience | Report | Frequency |
|----------|--------|-----------|
| QI Committee | Full QI report with run charts | Monthly |
| Medical Executive Committee | Summary dashboard | Quarterly |
| Board Quality Committee | Executive summary + trend | Semi-annually |
| *[Regulatory body if required]* | *[Specified format]* | *[As required]* |

---

## Approval

- **QI Project Lead (Name/Title):** ____________________  **Date:** __________
- **Department Chief (Name/Title):** ____________________  **Date:** __________
- **Quality Director (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `quality-improvement-plan`.*
