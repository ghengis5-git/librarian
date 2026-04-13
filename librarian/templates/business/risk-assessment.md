---
template_id: risk-assessment
display_name: Risk Assessment
preset: business
description: >-
  Comprehensive risk identification, analysis, and management plan. Covers risk assessment matrix,
  mitigation strategies, ownership, monitoring plan, and contingency strategies. Used for governance,
  strategic planning, and project management decisions.
suggested_tags: [risk, assessment, governance]
suggested_folder: risk-management/
typical_cross_refs: [strategic-plan, business-case, project-management-plan]
recommended_with: [strategic-plan, project-management-plan]
requires: []
sections:
  - Executive Summary
  - Risk Identification
  - Risk Analysis
  - Risk Matrix
  - Mitigation Strategies
  - Risk Owners
  - Monitoring Plan
  - Contingency Plans
  - Review Schedule
---

# Risk Assessment: {{title}}

**Document ID:** {{title}} / {{version}}  
**Date:** {{date}}  
**Author:** {{author}}  
**Status:** {{status}}

---

## Executive Summary

*[1–2 paragraph overview of the key risks identified, overall risk level (Low/Medium/High/Critical), and summary of mitigation strategy. Highlight the top 3 risks and their mitigation approach.]*

### Risk Profile Summary

| Category | # of Risks | High/Critical | Mitigation Status |
|----------|-----------|---------------|--------------------|
| Strategic | *[X]* | *[Y]* | *[% Mitigated]* |
| Operational | *[X]* | *[Y]* | *[% Mitigated]* |
| Financial | *[X]* | *[Y]* | *[% Mitigated]* |
| Compliance/Regulatory | *[X]* | *[Y]* | *[% Mitigated]* |
| Technical | *[X]* | *[Y]* | *[% Mitigated]* |
| **Total** | *[X]* | *[Y]* | *[% Mitigated]* |

### Overall Risk Level
**Assessment:** *[Low / Medium / High / Critical]*  
**Confidence:** *[High / Medium / Low]* — *[Basis for confidence level]*

---

## Risk Identification

### Risk Categories
Risks have been identified across the following domains:

1. **Strategic Risks** – Market conditions, competitive threats, business model viability
2. **Operational Risks** – Process execution, resource availability, organizational capability
3. **Financial Risks** – Budget overruns, revenue shortfalls, cost escalation, pricing pressure
4. **Compliance/Regulatory Risks** – Legal, contractual, regulatory, audit, data privacy
5. **Technical Risks** – Technology platform, integration, security, scalability
6. **Personnel Risks** – Key person dependencies, turnover, skill gaps

### Risk Identification Process
*[Describe how risks were identified: stakeholder interviews, workshops, lessons learned from similar initiatives, expert review, external benchmarking, etc.]*

### Risk Sources
- *[Source 1: e.g., "Executive steering committee workshops (3 sessions, X participants)"]*
- *[Source 2: e.g., "Subject matter expert interviews (X interviews, X hours)"]*
- *[Source 3: e.g., "Historical project data and lessons learned"]*
- *[Source 4: e.g., "External regulatory guidance and industry benchmarks"]*

---

## Risk Analysis

### Probability & Impact Definitions

**Probability Levels:**
- **High (>50%):** Risk is very likely to occur; expect it to happen
- **Medium (20–50%):** Risk has reasonable chance of occurring
- **Low (<20%):** Risk is unlikely but possible; monitor for early warning signs

**Impact Levels:**
- **Critical:** Threatens viability of initiative; could cascade to organizational level ($X M+ impact)
- **High:** Significant impact on objectives; major mitigation required ($X–$Y M impact)
- **Medium:** Moderate impact; mitigation plan advised ($X–$Y M impact)
- **Low:** Minor impact; monitor; mitigation optional (<$X M impact)

### Risk Scoring
Risk Score = Probability × Impact (on 1–5 scale)
- **Red (Score 15+):** Critical risk, immediate action required
- **Yellow (Score 9–14):** High risk, mitigation plan required
- **Green (Score 1–8):** Acceptable risk; monitor and manage

---

## Risk Matrix

### Comprehensive Risk Register

| # | Risk Description | Category | Probability | Impact | Score | Status | Trend |
|---|------------------|----------|-------------|--------|-------|--------|-------|
| **R1** | *[Risk: e.g., "Market demand lower than forecast"]* | Strategic | High | High | 16 | Red | ↑ |
| **R2** | *[Risk: e.g., "Key technical leader departs"]* | Personnel | Medium | High | 12 | Yellow | → |
| **R3** | *[Risk: e.g., "Budget overrun >20%"]* | Financial | Medium | Medium | 9 | Yellow | ↓ |
| **R4** | *[Risk: e.g., "Regulatory change impacts timeline"]* | Compliance | Low | High | 8 | Green | ↑ |
| **R5** | *[Risk: e.g., "Vendor contract dispute"]* | Operational | Low | Medium | 6 | Green | → |
| **R6** | *[Risk: e.g., "Data security breach"]* | Technical | Low | Critical | 10 | Yellow | ↓ |

### Visual Risk Matrix (Heatmap)

```
Impact
   |
   | Critical  [R6]                    [R1]
   | High              [R2,R3]
   | Medium     [R5]
   | Low
   |________________
      Low   Medium   High    Probability
```

**Legend:** ↑ Risk increasing | ↓ Risk decreasing | → Risk stable

---

## Mitigation Strategies

### R1: Market Demand Lower Than Forecast

**Current Status:** Red (High probability, High impact)  
**Owner:** Chief Commercial Officer  
**Root Cause:** *[e.g., "Uncertain customer adoption, competitive pricing pressure"]*

**Mitigation Strategy:**
1. *[Action 1: e.g., "Conduct market validation with 50+ customer interviews before full launch"]*
2. *[Action 2: e.g., "Develop alternative revenue model (subscription vs. perpetual) for pricing flexibility"]*
3. *[Action 3: e.g., "Build contingency plan to pivot target segment if primary market softens"]*

**Expected Outcome:** Reduce probability from High to Medium by Q3 2026

**Mitigation Owner:** *[Name/Title]*  
**Timeline:** *[Start date – Target completion]*  
**Resource Required:** *[$X budget, X FTE hours]*

---

### R2: Key Technical Leader Departs

**Current Status:** Yellow (Medium probability, High impact)  
**Owner:** Chief Technology Officer  
**Root Cause:** *[e.g., "Competitive offers, work-life balance concerns"]*

**Mitigation Strategy:**
1. *[Action 1: e.g., "Cross-train backup engineer on critical systems"]*
2. *[Action 2: e.g., "Implement retention bonus and career development plan"]*
3. *[Action 3: e.g., "Document all key technical decisions and architecture in wiki"]*
4. *[Action 4: e.g., "Recruit 1 senior engineer to reduce key-person risk"]*

**Expected Outcome:** Reduce impact from High to Medium by building team redundancy

**Mitigation Owner:** CHRO / Head of Engineering  
**Timeline:** Q2–Q4 2026  
**Resource Required:** *[$X recruitment budget, $Y retention bonus]*

---

### R3–R6: Additional Risks
*[Follow same template for each identified risk.]*

{% if "iso_9001" in compliance %}
### ISO 9001 § 8.1 Process Risk Management
This risk assessment aligns with ISO 9001 process risk requirements. All identified risks have documented mitigation strategies, assigned owners, and monitoring plans. Risks are reviewed at minimum quarterly and updated whenever process changes occur.

**Quality Assurance:** *[Responsibility for risk register accuracy and completeness]*
{% endif %}

{% if "iso_27001" in compliance %}
### ISO 27001 Information Security Risk
The following risks pertain specifically to information security (CIA – Confidentiality, Integrity, Availability):

- **R-SEC1:** *[Unauthorized data access during system integration]*
  - **Mitigation:** Implement role-based access control (RBAC), encryption at rest/transit, regular penetration testing
- **R-SEC2:** *[Data exfiltration from third-party vendor]*
  - **Mitigation:** Vendor security assessment, DPA/BAA, data segregation, audit logging
- **R-SEC3:** *[Ransomware/malware affecting production systems]*
  - **Mitigation:** Endpoint detection and response (EDR), air-gapped backups, incident response playbook

**Security Owner:** Chief Information Security Officer (CISO)
{% endif %}

---

## Risk Owners

### Owner Assignments

| Risk ID | Risk Description | Owner | Backup | Contact Info |
|---------|------------------|-------|--------|--------------|
| R1 | *[Market demand]* | *[Name/Title]* | *[Backup]* | *[Email/Phone]* |
| R2 | *[Key person]* | *[Name/Title]* | *[Backup]* | *[Email/Phone]* |
| R3 | *[Budget]* | *[Name/Title]* | *[Backup]* | *[Email/Phone]* |

### Owner Responsibilities
- Monitor risk indicators and early warning signs
- Execute mitigation plan and report progress monthly
- Escalate if risk score increases or mitigation is off track
- Participate in quarterly risk review meetings
- Document changes and decisions in risk log

---

## Monitoring Plan

### Risk Monitoring Metrics & KPIs

| Risk | Leading Indicator | Acceptable Range | Review Frequency |
|------|-------------------|------------------|------------------|
| R1 | Customer discovery feedback (satisfaction score) | >7/10 | Weekly |
| R2 | Key person retention indicator (engagement score) | >80 | Monthly |
| R3 | Budget variance (actuals vs. forecast) | Within ±10% | Monthly |
| R4 | Regulatory guidance updates (new rules, court decisions) | 0 new critical rules | Monthly |
| R5 | Vendor performance (SLA compliance) | >95% uptime | Monthly |
| R6 | Security incidents (breaches, vulnerabilities) | 0 critical | Daily alerts + monthly review |

### Monitoring Dashboard
*[Describe how risks will be tracked and visualized. Tools: Excel, Jira, ServiceNow, BI dashboard, etc.]*

### Escalation Triggers
Risk escalates to Steering Committee if:
- Risk score increases by 5+ points
- Mitigation plan is off-track by 2+ weeks
- New High/Critical risk identified
- Owner changes or cannot commit resources

---

## Contingency Plans

### R1: Market Demand Contingency (If Probability Becomes Certain)

**Trigger:** *[e.g., "After market validation, <30% customer interest OR 50% price resistance"]*

**Contingency Actions:**
1. *[Action 1: e.g., "Reduce scope to core feature set and defer advanced features to Year 2"]*
2. *[Action 2: e.g., "Shift to freemium model with lower initial customer acquisition cost"]*
3. *[Action 3: e.g., "Pursue alternative market segment or geographic region"]*
4. *[Action 4: e.g., "Partner with integrator to reach customers via channel"]*

**Decision Authority:** Executive Steering Committee  
**Timeline for Decision:** By Q3 2026  
**Financial Impact:** *[Reduce Year 1 revenue target by $X M; adjust budget by $Y M]*

### R2: Key Person Contingency (If Departure Occurs)

**Trigger:** *[Notice given or person becomes unavailable]*

**Immediate Actions (within 24 hours):**
1. Activate documented process runbooks and knowledge transfer
2. Empower backup engineer to make critical decisions
3. Escalate to CTO for resource allocation (hire emergency contractor if needed)

**30-Day Actions:**
1. Begin accelerated recruitment for senior replacement
2. Provide temporary coverage from external consultant
3. Conduct technical review to identify additional at-risk knowledge

**Financial Impact:** *[Additional $X contractor cost; potential $Y delay cost]*

---

## Review Schedule

### Risk Review Cadence
- **Monthly:** Risk Owner 1:1 with Risk Manager to update risk register
- **Quarterly:** Steering Committee reviews top 10 risks, trends, and mitigation effectiveness
- **Semi-annually:** Comprehensive risk reassessment with stakeholder workshops
- **Annually:** Risk assessment update and planning cycle refresh

### Review Participants
- **Monthly:** Risk Owner + PMO + Risk Manager
- **Quarterly:** Executive Steering Committee + Risk Owners + PMO
- **Semi-annual:** Board committee + Executive team + risk consultant

### Next Scheduled Review
- **Monthly Review:** *[Date]*
- **Quarterly Review:** *[Date]*
- **Annual Refresh:** *[Date]*

---

## Sign-Off

**Risk Assessment Approval:**

- **Risk Sponsor (Name/Title):** ____________________  **Date:** __________
- **Executive Steering Committee Chair (Name/Title):** ____________________  **Date:** __________
- **Chief Risk Officer / CFO (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `risk-assessment`.*
