---
template_id: incident-postmortem
display_name: Incident Postmortem
preset: software
description: Structured postmortem report for analyzing incidents, root causes, and preventing recurrence
suggested_tags:
  - incident
  - postmortem
  - operational
suggested_folder: docs/
typical_cross_refs:
  - runbook
  - security-assessment
requires: []
recommended_with:
  - runbook
  - security-assessment
sections:
  - Incident Summary
  - Timeline
  - Impact
  - Root Cause Analysis
  - Contributing Factors
  - Remediation Actions
  - Lessons Learned
  - Follow-Up Items
---

# Incident Postmortem: {{title}}

**Incident ID:** INC-[YYYY]-[XXX]  
**Date:** {{date}}  
**Severity:** [*P1 / P2 / P3 / P4*]  
**Status:** {{status}}  
**Facilitator:** {{author}}

---

## Incident Summary

[*Brief, factual description of what happened.*]

### Key Metrics

| Metric | Value |
|--------|-------|
| **Detection Time** | [*Time between occurrence and detection*] |
| **Time to Impact Awareness** | [*When users were first affected*] |
| **Time to Mitigation** | [*Time to implement fix*] |
| **Time to Resolution** | [*Total duration*] |
| **Customers Impacted** | [*Number or percentage*] |
| **Severity** | [*P1 (Critical) / P2 (High) / P3 (Medium) / P4 (Low)*] |

### Affected Services

- [*Service name*]
- [*Service name*]
- [*Service name*]

### Root Cause (Brief)

[*One sentence summary of why this happened.*]

---

## Timeline

[*Chronological sequence of events. Be specific with times. Include detection, communication, and resolution steps.*]

| Time (UTC) | Event | Owner |
|-----------|-------|-------|
| 2026-04-13 10:00 | [*Event: Database connection pool exhaustion detected in monitoring*] | [*Name*] |
| 10:05 | [*Event: PagerDuty alert fired, on-call engineer paged*] | [*System*] |
| 10:07 | [*Event: Engineer acknowledged alert*] | [*Name*] |
| 10:10 | [*Event: Initial diagnosis: service queuing requests, checking logs*] | [*Name*] |
| 10:15 | [*Event: Identified increased database load from new feature*] | [*Name*] |
| 10:20 | [*Event: Escalated to database team, confirmed lock contention*] | [*Name*] |
| 10:30 | [*Event: Disabled new feature flag to reduce load*] | [*Name*] |
| 10:35 | [*Event: Connection pool recovered, service latency normalized*] | [*Name*] |
| 10:50 | [*Event: Verified no data loss, post-incident review scheduled*] | [*Name*] |

---

## Impact

### Customer-Facing Impact

- **Duration:** [*10:00 - 10:35 UTC (35 minutes)*]
- **Services Affected:** [*List specific features/endpoints*]
- **User Impact:** [*Unable to place orders, view account, etc.*]
- **Customers Impacted:** [*X users, Y% of user base*]
- **Data Loss:** [*None / Minimal / Significant*]

### Internal Impact

- **Engineering:** [*How much time spent on incident response*]
- **Support:** [*Number of customer escalations, tickets filed*]
- **Finance:** [*Estimated revenue loss, if applicable*]

### Financial Impact

| Cost Category | Estimate |
|--------------|----------|
| Revenue Loss | [*$X*] |
| Customer Credits | [*$X*] |
| Engineering Hours | [*$X*] |
| **Total** | [*$X*] |

---

## Root Cause Analysis

[*Why did this happen? Dig deep. This section should explain the fundamental reason, not just the immediate trigger.*]

### Immediate Cause

[*The direct technical cause. Example: A newly deployed feature was inefficient at querying the database.*]

### Contributing Factors

[*What allowed this to happen? What defenses failed?*]

1. **Insufficient Load Testing:**
   - New feature was not load-tested before deployment
   - Expected 1,000 queries/sec, but actual was 50,000 queries/sec
   - Load test environment only simulated 100 concurrent users

2. **Missing Monitoring Alert:**
   - No alert on database connection pool utilization
   - Alert only triggered at 90% exhaustion (too late)

3. **No Gradual Rollout:**
   - Feature was deployed to 100% of users at once
   - No canary deployment or feature flag
   - No circuit breaker to degrade gracefully

4. **Code Review Gap:**
   - PR reviewer didn't catch the N+1 query problem
   - No database query performance review in code review checklist

### Why Prevention Failed

- [*What monitoring should have caught this?*]
- [*What process failed?*]
- [*What guardrail was missing?*]

---

## Contributing Factors

[*Not all factors are technical. List organizational and process factors.*]

- **Schedule Pressure:** [*Feature rush for deadline?*]
- **Communication:** [*Was the feature's impact communicated to ops?*]
- **Knowledge Gaps:** [*Did the engineer understand the codebase implications?*]
- **Tool Limitations:** [*Monitoring gaps? Logging issues? Dashboard limitations?*]
- **Documentation:** [*Was the new feature documented for ops?*]
- **Staffing:** [*On-call fatigue? Understaffed team?*]

---

## Remediation Actions

[*What are we doing to fix this and prevent recurrence? Prioritize by urgency.*]

### Immediate Fixes (Completed)

- [x] **Disabled problematic feature flag** — Instant mitigation (10:30 UTC)
  - Owner: [*Name*]
  - Completed: [*Date*]

### Short-Term (Next 2 weeks)

- [ ] **Optimize database queries** — Reduce query volume from 50k to 5k/sec
  - Owner: [*Name*]
  - Target: [*Date*]
  - Acceptance Criteria: Load test shows < 1000 queries/sec per user

- [ ] **Add connection pool monitoring alert** — Alert at 60% utilization
  - Owner: [*Name*]
  - Target: [*Date*]
  - Acceptance Criteria: Alert fires before connection pool exhaustion

### Medium-Term (Next 1-2 months)

- [ ] **Implement feature flags for all new features** — Gradual rollout strategy
  - Owner: [*Name*]
  - Target: [*Date*]
  - Acceptance Criteria: New features default to 10% → 50% → 100% rollout

- [ ] **Mandatory load testing in CI/CD pipeline** — Prevent performance regressions
  - Owner: [*Name*]
  - Target: [*Date*]
  - Acceptance Criteria: CI tests fail if latency increases > 10%

- [ ] **Database query review in code review checklist** — Catch N+1 queries
  - Owner: [*Name*]
  - Target: [*Date*]
  - Acceptance Criteria: All PRs checked for query efficiency

### Long-Term (Roadmap)

- [ ] **Circuit breaker for database client** — Degrade gracefully under load
  - Owner: [*Name*]
  - Target: [*Date*]
  - Design: [*Link to architecture decision*]

- [ ] **Chaos engineering tests** — Regular resilience testing
  - Owner: [*Name*]
  - Target: [*Date*]
  - Plan: Monthly tests of common failure modes

---

## Lessons Learned

[*What did we learn? What will we do differently?*]

### What Went Well

- [*Fast detection via monitoring alert*]
- [*Quick incident response and communication*]
- [*Clear escalation path*]
- [*Effective cross-team collaboration*]

### What We'll Improve

- [*"We will perform load testing before every feature deployment"*]
- [*"We need better monitoring on resource exhaustion metrics"*]
- [*"Feature flags should be standard practice for major features"*]
- [*"Database implications should be discussed in design phase"*]
- [*"On-call runbook for database issues needs expansion"*]

### Cultural Observations

- [*Was there time pressure that contributed?*]
- [*Did people feel safe speaking up?*]
- [*What communication worked well? What didn't?*]

---

## Follow-Up Items

[*Capture all action items and assign owners.*]

### Action Items

| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| Optimize queries for new feature | [*Name*] | 2026-04-20 | P0 |
| Add connection pool monitoring | [*Name*] | 2026-04-17 | P0 |
| Implement feature flag rollout | [*Name*] | 2026-05-01 | P1 |
| Add load testing to CI/CD | [*Name*] | 2026-05-15 | P1 |
| Design circuit breaker | [*Name*] | 2026-05-30 | P2 |
| Update on-call runbook | [*Name*] | 2026-04-20 | P1 |

### Stakeholder Notifications

- [x] **Customers:** Sent apology email + $X credit on 2026-04-13 14:00 UTC
- [x] **Executive Sponsor:** Notified of root cause and remediation plan
- [ ] **Board/Leadership:** Incident report (if required by policy)
- [ ] **Compliance/Audit:** Document for regulatory file (if applicable)

---

## Appendix: Supporting Materials

- **Incident Timeline Visualization:** [*Link to detailed timeline document*]
- **Log Excerpts:** [*Relevant logs from incident period*]
- **Metrics Graphs:** [*Dashboard screenshots showing degradation*]
- **Database Queries:** [*Slow query logs, execution plans*]
- **Related Documents:**
  - [*Link to Runbook: Database Troubleshooting*]
  - [*Link to Architecture Decision Record on feature flag strategy*]
  - [*Link to previous incident with similar symptoms*]

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Incident Commander | [*Name*] | [*Signature*] | {{date}} |
| Service Owner | [*Name*] | [*Signature*] | [*Date*] |
| Engineering Manager | [*Name*] | [*Signature*] | [*Date*] |

---

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 Draft | {{date}} | {{author}} | Initial postmortem |
| 1.0 Final | [*date*] | [*author*] | Approved after review |

---

*Document generated by librarian v{{librarian_version}} from template \`incident-postmortem\`.*
