---
template_id: due-diligence-report
display_name: Due Diligence Report
preset: finance
description: >-
  Investment due diligence report covering financial analysis, market position,
  risk assessment, legal/regulatory review, and investment recommendation.
  Used for M&A, fund investments, and credit decisions.
suggested_tags: [due-diligence, investment, analysis]
suggested_folder: due-diligence/
typical_cross_refs:
  - investment-memo
  - compliance-review
  - risk-assessment-finance
recommended_with:
  - investment-memo
  - risk-assessment-finance
requires: []
sections:
  - Executive Summary
  - Company Overview
  - Financial Analysis
  - Market & Competitive Position
  - Management Assessment
  - Legal & Regulatory Review
  - Risk Factors
  - Valuation
  - Recommendation
---

# Due Diligence Report: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**Classification:** {{classification}}

---

## Executive Summary

*[1–2 paragraph summary of the target, transaction rationale, key findings, and recommendation (Proceed / Proceed with Conditions / Decline).]*

### Key Metrics

| Metric | Value | Commentary |
|--------|-------|-----------|
| Revenue (LTM) | *[$X M]* | *[Growth trend]* |
| EBITDA (LTM) | *[$X M]* | *[Margin %]* |
| Net Debt | *[$X M]* | *[Leverage ratio]* |
| Enterprise Value | *[$X M]* | *[Implied multiple]* |
| Revenue Growth (3-yr CAGR) | *[X%]* | *[Accelerating/Decelerating]* |

---

## Company Overview

- **Legal Name:** *[Full legal name]*
- **Jurisdiction:** *[State/Country of incorporation]*
- **Founded:** *[Year]*
- **Headquarters:** *[City, State]*
- **Employees:** *[X FTEs]*
- **Business Description:** *[2–3 sentence description]*
- **Key Products/Services:** *[List]*
- **Major Customers:** *[Top 3–5 by revenue concentration]*

---

## Financial Analysis

### Income Statement Summary

| ($M) | FY-2 | FY-1 | LTM | Proj Y1 | Proj Y2 |
|------|------|------|-----|---------|---------|
| Revenue | | | | | |
| Gross Profit | | | | | |
| Gross Margin % | | | | | |
| EBITDA | | | | | |
| EBITDA Margin % | | | | | |
| Net Income | | | | | |

### Balance Sheet Highlights

| ($M) | Current | Prior Year | Notes |
|------|---------|-----------|-------|
| Cash & Equivalents | | | |
| Total Debt | | | |
| Net Debt | | | |
| Total Assets | | | |
| Shareholders' Equity | | | |

### Cash Flow Analysis

| ($M) | FY-2 | FY-1 | LTM |
|------|------|------|-----|
| Operating Cash Flow | | | |
| Capital Expenditures | | | |
| Free Cash Flow | | | |
| FCF Conversion (% of EBITDA) | | | |

### Quality of Earnings Adjustments

| Adjustment | Amount ($M) | Rationale |
|-----------|-------------|-----------|
| *[Adjustment 1]* | *[+/- $X]* | *[Reason]* |
| *[Adjustment 2]* | *[+/- $X]* | *[Reason]* |
| **Adjusted EBITDA** | **$X** | |

{% if "sec_finra" in compliance %}
### SEC/FINRA Compliance Notes
- Financial data sourced from *[audited statements / SEC filings / management reports]*
- Audit opinion: *[Unqualified / Qualified / Adverse / Disclaimer]*
- Material weaknesses or significant deficiencies: *[None / Describe]*
- SEC filing status: *[Current / Delinquent — describe]*
- FINRA Rule 2111 suitability considerations documented
{% endif %}

---

## Market & Competitive Position

### Market Overview
- **Total Addressable Market (TAM):** *[$X B]*
- **Market Growth Rate:** *[X% CAGR]*
- **Market Structure:** *[Fragmented / Concentrated / Oligopolistic]*

### Competitive Landscape

| Competitor | Revenue | Market Share | Key Differentiator |
|-----------|---------|-------------|-------------------|
| Target | *[$X M]* | *[X%]* | *[Differentiator]* |
| *[Comp 1]* | *[$X M]* | *[X%]* | *[Differentiator]* |
| *[Comp 2]* | *[$X M]* | *[X%]* | *[Differentiator]* |

---

## Management Assessment

| Name | Title | Tenure | Background | Assessment |
|------|-------|--------|-----------|-----------|
| *[Name]* | CEO | *[X yr]* | *[Background]* | *[Strong/Adequate/Concern]* |
| *[Name]* | CFO | *[X yr]* | *[Background]* | *[Strong/Adequate/Concern]* |

### Key Person Risk: *[Low / Medium / High]*

---

## Legal & Regulatory Review

| Area | Finding | Risk Level |
|------|---------|-----------|
| Pending litigation | *[Description]* | *[Low/Medium/High]* |
| Regulatory compliance | *[Description]* | *[Low/Medium/High]* |
| Intellectual property | *[Description]* | *[Low/Medium/High]* |
| Environmental | *[Description]* | *[Low/Medium/High]* |
| Tax | *[Description]* | *[Low/Medium/High]* |
| Employment | *[Description]* | *[Low/Medium/High]* |

{% if "hipaa" in compliance %}
### HIPAA Due Diligence (Healthcare Target)
If the target handles PHI:
- **HIPAA compliance program:** *[In place / Partial / Not in place]*
- **Recent OCR audit or breach:** *[None / Describe]*
- **Business Associate Agreements:** *[Current / Gaps identified]*
- **Risk assessment (current):** *[Yes — date / No — liability risk]*
{% endif %}

---

## Risk Factors

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | *[Risk description]* | *[H/M/L]* | *[H/M/L]* | *[Mitigation]* |
| 2 | *[Risk description]* | *[H/M/L]* | *[H/M/L]* | *[Mitigation]* |
| 3 | *[Risk description]* | *[H/M/L]* | *[H/M/L]* | *[Mitigation]* |

---

## Valuation

### Methodology

| Method | Implied Value ($M) | Key Assumptions |
|--------|-------------------|----------------|
| DCF | *[$X – $Y]* | *[WACC X%, terminal growth Y%]* |
| Comparable Companies | *[$X – $Y]* | *[EV/EBITDA range]* |
| Precedent Transactions | *[$X – $Y]* | *[Control premium X%]* |
| **Blended Range** | **$X – $Y** | |

### Offer vs. Valuation
- **Proposed Price:** *[$X M]*
- **vs. Blended Range:** *[X% premium / discount]*

---

## Recommendation

**Recommendation:** *[Proceed / Proceed with Conditions / Decline]*

**Rationale:** *[2–3 sentences]*

**Conditions (if applicable):**
1. *[Condition 1]*
2. *[Condition 2]*

---

## Approval

- **Analyst (Name/Title):** ____________________  **Date:** __________
- **Senior Reviewer (Name/Title):** ____________________  **Date:** __________
- **Investment Committee Chair (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `due-diligence-report`.*
