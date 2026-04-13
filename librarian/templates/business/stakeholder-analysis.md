---
template_id: stakeholder-analysis
display_name: Stakeholder Analysis
preset: business
description: >-
  Comprehensive stakeholder mapping and engagement plan. Identifies stakeholders, assesses
  power/interest, defines communication requirements, and outlines engagement strategy. Used for
  project governance, organizational change, and strategic initiatives.
suggested_tags: [stakeholder, analysis, communication]
suggested_folder: docs/
typical_cross_refs: [project-management-plan, strategic-plan]
recommended_with: [project-management-plan]
requires: []
sections:
  - Purpose
  - Stakeholder Register
  - Power-Interest Matrix
  - Communication Requirements
  - Engagement Strategy
  - RACI Matrix
  - Review Cadence
---

# Stakeholder Analysis: {{title}}

**Document ID:** {{title}} / {{version}}  
**Date:** {{date}}  
**Author:** {{author}}  
**Status:** {{status}}

---

## Purpose

### Context
*[Brief description of the initiative, program, or project for which this stakeholder analysis was conducted. Explain why stakeholder engagement is critical to success.]*

### Objectives
1. *[Objective 1: e.g., "Identify all individuals and groups affected by the initiative"]*
2. *[Objective 2: e.g., "Assess power and interest to prioritize engagement efforts"]*
3. *[Objective 3: e.g., "Define communication and engagement strategy for each stakeholder group"]*
4. *[Objective 4: e.g., "Establish clear roles and responsibilities via RACI matrix"]*

### Scope
*[Who is included: internal staff, board, external partners, customers, regulators, etc. Any stakeholder exclusions or out-of-scope parties.]*

---

## Stakeholder Register

### Complete Stakeholder List

| # | Stakeholder Name | Title | Department / Organization | Category | Role in Initiative | Email |
|---|------------------|-------|--------------------------|----------|---------------------|--------|
| *[S1]* | *[Name]* | *[Title]* | *[Dept/Org]* | Executive | Sponsor | *[Email]* |
| *[S2]* | *[Name]* | *[Title]* | *[Dept/Org]* | Functional Lead | Core Team | *[Email]* |
| *[S3]* | *[Name]* | *[Title]* | *[Dept/Org]* | Department Head | Supporter | *[Email]* |
| *[S4]* | *[Name]* | *[Title]* | *[Dept/Org]* | End User | Influencer | *[Email]* |
| *[S5]* | *[Name]* | *[Title]* | *[Dept/Org]* | External Partner | Key Stakeholder | *[Email]* |

### Stakeholder Categories
- **Executive:** C-suite, board members, senior leadership with strategic oversight
- **Functional Lead:** Department heads, program/project managers driving execution
- **Core Team:** Direct contributors (engineers, analysts, project staff)
- **Department Head:** Managers of affected departments or functions
- **End User:** Individuals who will use or be affected by the deliverable
- **External Partner:** Vendors, customers, regulatory bodies, partner organizations

---

## Power-Interest Matrix

### Strategic Positioning

```
Power
  |
  | Manage            Keep
  | Closely          Satisfied
  |___[S1,S3]___[S2,S5]___
  |
  | Monitor          Keep
  | / Inform         Informed
  |___[S6]________[S4,S7]___
  +-------------------------> Interest
```

### Quadrant Definitions & Strategy

#### MANAGE CLOSELY (High Power, High Interest)
*[Stakeholders who have significant influence and strong interest in the outcome.]*

| Stakeholder | Reason | Engagement Strategy |
|-------------|--------|---------------------|
| *[S1: CEO/Sponsor]* | *[Controls budget, strategic priority]* | *[Weekly 1:1s, board updates, executive steering]* |
| *[S3: CFO]* | *[Budget authority, financial controls]* | *[Monthly financial reviews, approval gates]* |

**Frequency:** Weekly/bi-weekly  
**Communication:** Direct, formal, executive-level briefings  
**Engagement:** Steering committee, approval gates, escalation path

#### KEEP SATISFIED (High Power, Low Interest)
*[Stakeholders with influence but less immediate engagement.]*

| Stakeholder | Reason | Engagement Strategy |
|-------------|--------|---------------------|
| *[S2: Chief Technical Officer]* | *[Approves architecture, controls resources]* | *[Monthly tech reviews, design decisions]*|
| *[S5: Partner CEO]* | *[Contract authority, partnership viability]* | *[Quarterly business reviews, milestone updates]* |

**Frequency:** Monthly/quarterly  
**Communication:** Strategic updates, milestone summaries  
**Engagement:** Review gates, partnership steering, risk escalation

#### KEEP INFORMED (Low Power, High Interest)
*[Stakeholders with strong interest but limited decision authority.]*

| Stakeholder | Reason | Engagement Strategy |
|-------------|--------|---------------------|
| *[S4: End User Champion]* | *[Will use solution daily, influential with peers]* | *[Bi-weekly updates, user feedback sessions, training]* |
| *[S7: Process Owner]* | *[Process change owner, training responsibility]* | *[Weekly standups, UAT coordination, training development]* |

**Frequency:** Bi-weekly/weekly  
**Communication:** Status updates, newsletters, feedback loops  
**Engagement:** User advisory group, UAT participation, training workshops

#### MONITOR / INFORM (Low Power, Low Interest)
*[Stakeholders with peripheral interest or limited involvement.]*

| Stakeholder | Reason | Engagement Strategy |
|-------------|--------|---------------------|
| *[S6: Admin Staff]* | *[Minimal direct impact, support only]* | *[Monthly newsletter, open office hours]* |

**Frequency:** Monthly or as-needed  
**Communication:** Newsletters, intranet, general announcements  
**Engagement:** Optional attendance at training, feedback survey

---

## Communication Requirements

### Communication Plan by Stakeholder Group

| Stakeholder Group | Message | Format | Frequency | Owner | Inputs |
|------------------|---------|--------|-----------|-------|--------|
| **Manage Closely** | *[Strategic progress, decisions, escalations]* | Exec briefing + email | Weekly | PM | Status, issues, risks |
| **Keep Satisfied** | *[Milestone achievement, resource needs, approvals]* | Formal letter + call | Monthly | PM | Gate status, budget |
| **Keep Informed** | *[Feature progress, user feedback, training]* | Newsletter + meeting | Bi-weekly | BA | UAT updates, process changes |
| **Monitor** | *[General updates, open invitations]* | Email + Slack | Monthly | PM | Highlights, go-live notifications |

### Content Guidelines
- **Executive Audience:** Focus on strategic impact, risk/issues, investment justification, competitive positioning
- **User Audience:** Focus on feature benefits, training, support, change impact
- **Partner Audience:** Focus on deliverables, milestone achievement, relationship/contract items
- **General Audience:** Focus on go-live dates, support availability, what's changed for them

### Key Messages (Campaign)

**Message 1:** *[Strategic rationale and vision, e.g., "This initiative positions us as market leader in X"]*

**Message 2:** *[Concrete benefits for each audience, e.g., "Users: 40% faster workflows; Executives: $X M cost savings; Partners: New market opportunity"]*

**Message 3:** *[Timeline and what to expect next, e.g., "Planning complete, development starts Q2 2026, go-live Q4 2026"]*

---

## Engagement Strategy

### Overall Engagement Approach
*[Describe the philosophy and high-level strategy for keeping stakeholders engaged and aligned throughout the initiative.]*

### Change Management & Resistance Mitigation
*[Address concerns about change, resistance points, and mitigation approach for each stakeholder group.]*

| Stakeholder Group | Potential Resistance | Root Cause | Mitigation |
|------------------|---------------------|-----------|-----------|
| *[End Users]* | *[Fear of job displacement, retraining burden]* | *[Process change, new tool learning curve]* | *[Emphasize job security, skills training, early involvement]* |
| *[Department Heads]* | *[Loss of control, budget impact, resource drain]* | *[Organizational change, resource competition]* | *[Clear communication, budget protection, resource sharing model]* |
| *[IT/Technical]* | *[Support burden, integration complexity]* | *[Operational risk, skill gaps]* | *[Phased rollout, dedicated support team, vendor SLA]* |

### Early Engagement / Co-Creation
- *[Approach 1: e.g., "User advisory board with monthly input sessions"]*
- *[Approach 2: e.g., "Executive steering committee with decision authority"]*
- *[Approach 3: e.g., "Department working groups defining process changes"]*

### Feedback & Course Correction
- **Monthly Feedback:** User surveys (NPS, satisfaction)
- **Quarterly Review:** Steering committee feedback on progress and course correction
- **Ad-hoc:** Open feedback channel and escalation path for concerns

---

## RACI Matrix

### Roles & Responsibilities

*[RACI = Responsible, Accountable, Consulted, Informed]*

| Activity / Decision | Sponsor (CEO) | Project Manager | Technical Lead | Finance Owner | Department Head | End Users |
|--------------------|---|---|---|---|---|---|
| **Strategic Direction** | A | R | C | I | C | I |
| **Scope Approval** | A | R | C | C | I | C |
| **Design Review** | I | R | A | C | C | I |
| **Budget Approval** | A | R | I | A | I | — |
| **Vendor Selection** | C | R | A | C | I | — |
| **Risk Management** | C | A | R | C | R | I |
| **Resource Allocation** | I | R | C | A | C | — |
| **Testing & UAT** | I | R | C | — | R | A |
| **Training Plan** | I | R | C | — | A | R |
| **Go-Live Decision** | A | R | A | C | R | I |
| **Benefits Realization** | A | R | C | A | R | C |
| **Lessons Learned** | C | A | R | I | I | C |

**Legend:**
- **A (Accountable):** Ultimate decision-maker / sign-off authority (typically 1 per decision)
- **R (Responsible):** Does the work / executes the decision (can be multiple)
- **C (Consulted):** Provides input, feedback, expertise (bidirectional communication)
- **I (Informed):** Kept in the loop but not asked for input (one-way communication)
- **— (Not involved):** No role in this decision/activity

### Role Descriptions

**Sponsor (CEO/Board):** Ultimate accountability for strategic alignment, investment approval, escalation authority

**Project Manager:** Owns day-to-day execution, timeline, status reporting, risk/issue management, stakeholder coordination

**Technical Lead:** Responsible for technical architecture, design decisions, integration, performance, security

**Finance Owner:** Accountable for budget approval, cost tracking, financial forecasting, ROI tracking

**Department Head:** Accountable for process changes in own department, training, resource availability, benefits realization

**End Users:** Provide feedback during design/UAT, adopt solution, champion change with peers

---

## Engagement Timeline

### Pre-Launch (Planning Phase)
**Months 1–2**
- Stakeholder kickoff meeting (all groups)
- Executive steering committee formation
- User advisory board formation
- Communication plan rollout
- Feedback loops established

### Launch (Execution Phase)
**Months 3–8**
- Weekly PM updates to core sponsors
- Monthly dept head updates and feedback sessions
- Bi-weekly user advisory board meetings
- Monthly all-hands update on progress
- User training ramp-up (Month 6 onward)

### Post-Launch (Stabilization Phase)
**Months 9–12**
- Bi-weekly executive updates (reduced from weekly)
- Monthly steering committee reviews
- User feedback and support
- Benefits tracking and reporting
- Lessons learned sessions (Month 12)

---

## Review Cadence

### Stakeholder Analysis Review Schedule
- **Quarterly:** Update stakeholder power/interest assessment based on initiative progress and organizational changes
- **As-needed:** Add new stakeholders or adjust engagement strategy if significant changes occur
- **Post-implementation:** Conduct full review to assess engagement effectiveness and lessons learned

**Next Scheduled Review:** *[Date]*

---

*Document generated by librarian v{{librarian_version}} from template `stakeholder-analysis`.*
