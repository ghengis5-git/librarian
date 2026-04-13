---
template_id: cost-analysis
display_name: Cost Analysis
preset: business
description: >-
  Detailed breakdown of project, product, or operational costs. Covers direct costs, indirect costs,
  one-time vs. recurring expenses, cost projections, and sensitivity analysis. Used for business cases,
  investment decisions, and budgeting.
suggested_tags: [finance, cost, analysis]
suggested_folder: finance/
typical_cross_refs: [strategic-plan, business-case]
recommended_with: [business-case]
requires: []
sections:
  - Executive Summary
  - Cost Categories
  - Direct Costs
  - Indirect Costs
  - One-Time vs Recurring
  - Cost Projections
  - Sensitivity Analysis
  - Funding Sources
  - Recommendations
---

# Cost Analysis: {{title}}

**Document ID:** {{title}} / {{version}}  
**Date:** {{date}}  
**Author:** {{author}}  
**Status:** {{status}}

---

## Executive Summary

*[1-paragraph overview of the total cost estimate, major cost drivers, and key assumptions. Include Year 1 and multi-year totals.]*

### Cost-at-a-Glance

| Period | Direct Costs | Indirect Costs | Total |
|--------|--------------|----------------|-------|
| Year 1 | *[$M]* | *[$M]* | *[$M]* |
| Year 2 | *[$M]* | *[$M]* | *[$M]* |
| Year 3 | *[$M]* | *[$M]* | *[$M]* |
| **3-Year Total** | *[$M]* | *[$M]* | *[$M]* |

---

## Cost Categories

### Overview
*[Describe the main cost buckets for this project or initiative. Explain the methodology (e.g., bottom-up estimate, industry benchmarks, comparable projects).]*

| Category | Year 1 | Year 2 | Year 3 | Notes |
|----------|--------|--------|--------|-------|
| *[Category A]* | *[$M]* | *[$M]* | *[$M]* | *[Notes on scope, inflation]* |
| *[Category B]* | *[$M]* | *[$M]* | *[$M]* | *[Notes on scope, inflation]* |
| *[Category C]* | *[$M]* | *[$M]* | *[$M]* | *[Notes on scope, inflation]* |

---

## Direct Costs

### Personnel & Staffing
- **FTE Count:** *[X FTEs, ramp plan]*
- **Annual Salary Cost:** *[$M]*
- **Benefits (25–35%):** *[$M]*
- **Total Personnel Year 1:** *[$M]*

*[Provide FTE composition by role (engineers, managers, etc.) and hiring timeline.]*

### Technology & Infrastructure
- **Hardware:** *[$M, specify: servers, workstations, etc.]*
- **Software Licenses:** *[$M, specify: SaaS tools, platforms, etc.]*
- **Cloud Infrastructure:** *[$M, specify: compute, storage, bandwidth]*
- **Development Tools & Platforms:** *[$M]*
- **Total Technology Year 1:** *[$M]*

### Materials & Vendors
- **Procurement:** *[$M, specify commodities or outsourced services]*
- **Contractor/Consultant Fees:** *[$M]*
- **Equipment & Facilities:** *[$M]*
- **Total Materials Year 1:** *[$M]*

---

## Indirect Costs

### Overhead Allocation
*[Describe how corporate overhead, facilities, utilities, insurance, and administrative support are allocated to this project.]*

- **Facilities & Utilities:** *[$M]*
- **HR & Recruiting:** *[$M]*
- **Finance & Legal:** *[$M]*
- **Executive Management:** *[$M]*
- **Total Overhead Year 1:** *[$M]*

### Contingency Reserve
- **Contingency (typically 5–15%):** *[$M]*
- **Justification:** *[Risk factors and historical variance]*

---

## One-Time vs Recurring

### One-Time (Capital) Costs
| Item | Amount | Year | Amortization |
|------|--------|------|--------------|
| *[Initial setup, tooling, training]* | *[$M]* | *[Year 1]* | *[N years]* |
| *[Equipment purchase]* | *[$M]* | *[Year 1]* | *[N years]* |

**Total One-Time:** *[$M]*

### Recurring (Operating) Costs
| Item | Year 1 | Year 2 | Year 3 | Notes |
|------|--------|--------|--------|-------|
| *[Salary & benefits]* | *[$M]* | *[$M]* | *[$M]* | *[Annual escalation rate]*
| *[Software & subscriptions]* | *[$M]* | *[$M]* | *[$M]* | *[Annual escalation rate]* |
| *[Maintenance & support]* | *[$M]* | *[$M]* | *[$M]* | *[Annual escalation rate]* |

**Total Recurring (Annual):** *[$M]* (Year 1), *[$M]* (Year 2), *[$M]* (Year 3)

---

## Cost Projections

### 3-Year Cost Trajectory
```
Cost Estimate by Year
Year 1: $X.X M (ramp period)
Year 2: $X.X M (full run-rate)
Year 3: $X.X M (optimization)
```

*[Provide narrative explanation of cost changes across years. Highlight periods of higher investment and expected efficiency gains.]*

### Inflation Assumptions
- **Personnel:** *[Typically 3–4% annually]*
- **Technology:** *[Typically 2–3% annually, or -1% for cloud]*
- **Materials:** *[Typically 2–4% annually, or market-dependent]*
- **Facilities:** *[Typically 2–3% annually]*

---

## Sensitivity Analysis

### Cost Drivers & Scenarios
*[Identify the 3–5 largest cost drivers and model "upside" (10% higher) and "downside" (10% lower) scenarios.]*

| Scenario | Year 1 Total | Year 3 Total | Key Assumptions |
|----------|-------------|-------------|-----------------|
| **Base Case** | *[$M]* | *[$M]* | *[Baseline staffing, timeline, tech stack]* |
| **Upside (10% higher)** | *[$M]* | *[$M]* | *[Additional scope, hiring delays, cost overruns]* |
| **Downside (10% lower)** | *[$M]* | *[$M]* | *[Faster automation, vendor discounts, deferred scope]* |

### Sensitivity Table
| Cost Driver | Sensitivity | Year 1 Impact | Year 3 Impact |
|-------------|-------------|--------------|--------------|
| *[Personnel costs]* | +1% → *[$M]* increase | +/- *[%]* | +/- *[%]* |
| *[Technology capex]* | +$1M → *[$M]* increase | +/- *[%]* | +/- *[%]* |

---

## Funding Sources

### Proposed Funding Mix

| Source | Amount | Year | Notes |
|--------|--------|------|-------|
| *[Operating budget]* | *[$M]* | *[Annual]* | *[Internal allocation]* |
| *[Capital allocation]* | *[$M]* | *[2026]* | *[Board-approved capex]* |
| *[External financing]* | *[$M]* | *[As needed]* | *[Debt, equity, or grant]* |
| **Total** | *[$M]* | | |

{% if "sec_finra" in compliance %}
### Audit Trail & Financial Controls
This cost analysis is subject to internal audit and SEC/FINRA record-retention requirements. All supporting documentation (quotes, invoices, timesheets, vendor contracts) must be retained for {{retention_period_days}} days and made available for regulatory review.

**Approval Authority:** CFO or Board Finance Committee  
**Record Location:** *[Finance shared drive / system reference]*
{% endif %}

---

## Recommendations

### Cost Optimization Opportunities
1. *[Opportunity 1: e.g., "Leverage existing software licenses to reduce Year 2 capex by $X"]*
2. *[Opportunity 2: e.g., "Offshore 30% of development work to reduce labor cost by $X"]*
3. *[Opportunity 3: e.g., "Negotiate multi-year vendor contracts for 10% discount"]*

### Risk-Adjusted Recommendation
*[Based on sensitivity analysis, contingency planning, and funding availability, recommend the base case, upside, or downside scenario. Justify with 2–3 sentences on cost-risk trade-offs.]*

---

*Document generated by librarian v{{librarian_version}} from template `cost-analysis`.*
