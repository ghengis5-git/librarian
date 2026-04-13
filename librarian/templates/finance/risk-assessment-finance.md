---
template_id: risk-assessment-finance
display_name: Risk Assessment (Finance)
preset: finance
description: >-
  Financial services risk assessment covering market, credit, operational,
  liquidity, and compliance risks. Includes risk appetite statement,
  control effectiveness evaluation, and risk-adjusted return analysis.
suggested_tags: [risk, assessment, controls]
suggested_folder: risk-management/
typical_cross_refs:
  - due-diligence-report
  - compliance-review
  - audit-finding
recommended_with:
  - compliance-review
  - due-diligence-report
requires: []
sections:
  - Executive Summary
  - Risk Appetite Statement
  - Risk Identification
  - Risk Assessment Matrix
  - Control Environment
  - Key Risk Indicators
  - Stress Scenarios
  - Remediation Plan
  - Governance & Review
---

# Risk Assessment: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**Classification:** {{classification}}
**Assessment Period:** *[Start]* — *[End]*

---

## Executive Summary

*[1–2 paragraph overview of risk posture, material changes since prior assessment, top risks, and recommended actions.]*

---

## Risk Appetite Statement

*[Firm's board-approved risk appetite. What level and types of risk is the firm willing to accept in pursuit of its objectives?]*

| Risk Category | Appetite | Limit | Current Exposure | Within Appetite |
|--------------|----------|-------|-----------------|----------------|
| Market Risk | *[Low/Moderate/High]* | *[VaR $X M]* | *[$X M]* | *[Yes/No]* |
| Credit Risk | *[Low/Moderate/High]* | *[Max exposure $X M]* | *[$X M]* | *[Yes/No]* |
| Operational Risk | *[Low]* | *[Loss <$X M/yr]* | *[$X M LTM]* | *[Yes/No]* |
| Liquidity Risk | *[Low]* | *[Min X days coverage]* | *[X days]* | *[Yes/No]* |
| Compliance Risk | *[Zero tolerance]* | *[0 material violations]* | *[X violations]* | *[Yes/No]* |

---

## Risk Identification

### Risk Categories

| # | Risk | Category | Description | New/Existing |
|---|------|----------|-------------|-------------|
| 1 | *[Risk name]* | Market | *[Description]* | *[New/Existing]* |
| 2 | *[Risk name]* | Credit | *[Description]* | *[New/Existing]* |
| 3 | *[Risk name]* | Operational | *[Description]* | *[New/Existing]* |
| 4 | *[Risk name]* | Liquidity | *[Description]* | *[New/Existing]* |
| 5 | *[Risk name]* | Compliance | *[Description]* | *[New/Existing]* |
| 6 | *[Risk name]* | Reputational | *[Description]* | *[New/Existing]* |

---

## Risk Assessment Matrix

| # | Risk | Likelihood | Impact | Inherent Score | Control Effectiveness | Residual Score | Trend |
|---|------|-----------|--------|---------------|----------------------|---------------|-------|
| 1 | *[Risk]* | *[1–5]* | *[1–5]* | *[X]* | *[Strong/Adequate/Weak]* | *[X]* | *[↑↓→]* |
| 2 | *[Risk]* | *[1–5]* | *[1–5]* | *[X]* | *[S/A/W]* | *[X]* | *[↑↓→]* |

{% if "sec_finra" in compliance %}
### Regulatory Risk Detail
| Regulation | Risk Area | Current Status | Gap | Priority |
|-----------|----------|---------------|-----|----------|
| SEC Rule 206(4)-7 | Compliance program | *[Status]* | *[None/Gap]* | *[H/M/L]* |
| FINRA Rule 3110 | Supervision | *[Status]* | *[None/Gap]* | *[H/M/L]* |
| BSA/AML | Transaction monitoring | *[Status]* | *[None/Gap]* | *[H/M/L]* |
| Reg S-P | Client privacy | *[Status]* | *[None/Gap]* | *[H/M/L]* |
{% endif %}

---

## Control Environment

### Controls by Risk Area

| Risk | Control | Type | Owner | Frequency | Effectiveness |
|------|---------|------|-------|-----------|--------------|
| *[Risk 1]* | *[Control description]* | *[Preventive/Detective]* | *[Name]* | *[Daily/Weekly/etc.]* | *[Strong/Adequate/Weak]* |

---

## Key Risk Indicators

| KRI | Threshold (Yellow) | Threshold (Red) | Current Value | Status |
|-----|--------------------|-----------------|---------------|--------|
| *[VaR utilization]* | *[>70%]* | *[>90%]* | *[X%]* | *[Green/Yellow/Red]* |
| *[Concentration %]* | *[>20%]* | *[>30%]* | *[X%]* | *[G/Y/R]* |
| *[Trade breaks (aged >3 days)]* | *[>5]* | *[>10]* | *[X]* | *[G/Y/R]* |
| *[Compliance exceptions]* | *[>3/mo]* | *[>5/mo]* | *[X]* | *[G/Y/R]* |

---

## Stress Scenarios

| Scenario | Assumptions | Impact on P&L | Impact on Capital | Mitigant |
|----------|-----------|--------------|-------------------|---------|
| Market crash (–20%) | *[Equity -20%, rates +200bp]* | *[$X M loss]* | *[Capital ratio X%]* | *[Hedges, stops]* |
| Credit event | *[Top 3 counterparties default]* | *[$X M loss]* | *[Capital ratio X%]* | *[Diversification, collateral]* |
| Liquidity squeeze | *[Redemptions 25% in 30 days]* | *[Forced liquidation cost]* | *[Days to meet]* | *[Liquidity buffer, credit facility]* |

---

## Remediation Plan

| # | Risk/Gap | Action | Owner | Deadline | Status |
|---|---------|--------|-------|----------|--------|
| 1 | *[Gap description]* | *[Remediation]* | *[Name]* | *[Date]* | *[Status]* |

---

## Governance & Review

- **Risk Committee Review:** *[Quarterly — next date]*
- **Board Reporting:** *[Semi-annually — next date]*
- **Assessment Refresh:** *[Annually or upon material change]*
- **External Review:** *[Next regulatory exam expected: date]*

---

## Approval

- **Chief Risk Officer (Name):** ____________________  **Date:** __________
- **Chief Compliance Officer (Name):** ____________________  **Date:** __________
- **CEO (Name):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `risk-assessment-finance`.*
