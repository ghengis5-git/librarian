---
template_id: nda-tracker
display_name: NDA Tracker
preset: legal
description: Operational tracking register for non-disclosure agreements with key terms and obligation management
suggested_tags: [nda, confidentiality, tracking]
suggested_folder: legal/
typical_cross_refs: [contract-summary, legal-review]
recommended_with: [contract-summary]
requires: []
sections:
  - NDA Register
  - Active NDAs
  - Expiring NDAs
  - Key Terms Summary
  - Obligation Tracking
  - Breach Protocol
  - Review Schedule
---

# NDA Tracker — {{title}}

**Date:** {{date}}  
**Author:** {{author}}  
**Version:** {{version}}  
**Classification:** {{classification}}  
**Tracking Period:** *[Start date – End date]*

---

## NDA Register

### Register Overview

*[This tracker maintains a consolidated register of all non-disclosure agreements governing the protection of confidential information. Updates should be made within 5 business days of NDA execution, renewal, or expiration.]*

**Register Statistics**

| Status | Count | Trend |
|--------|-------|-------|
| **Active NDAs** | *[Number]* | ▲/▼/— |
| **Expiring within 90 days** | *[Number]* | ▲/▼/— |
| **Expired (Archive)** | *[Number]* | ▲/▼/— |
| **Total Managed** | *[Number]* | — |

---

## Active NDAs

### Current NDA Register

| ID | Counterparty | Executed Date | Expiration Date | Type | Status | Renewal Action |
|----|--------------|---------------|-----------------|------|--------|-----------------|
| **NDA-001** | *[Company name]* | *[MM/DD/YYYY]* | *[MM/DD/YYYY]* | *[Mutual/One-way]* | Active | None / Renew by *[date]* |
| **NDA-002** | *[Company name]* | *[MM/DD/YYYY]* | *[MM/DD/YYYY]* | *[Mutual/One-way]* | Active | None / Renew by *[date]* |
| **NDA-003** | *[Company name]* | *[MM/DD/YYYY]* | *[MM/DD/YYYY]* | *[Mutual/One-way]* | Active | None / Renew by *[date]* |
| **NDA-004** | *[Company name]* | *[MM/DD/YYYY]* | *[MM/DD/YYYY]* | *[Mutual/One-way]* | Active | None / Renew by *[date]* |
| **NDA-005** | *[Company name]* | *[MM/DD/YYYY]* | *[MM/DD/YYYY]* | *[Mutual/One-way]* | Active | None / Renew by *[date]* |

### Adding New NDAs

**When to register:**
- Upon execution of a new NDA (within 5 business days)
- Upon material amendment or restatement
- When adding a counterparty through a successor agreement

**Required metadata:**
- Counterparty legal entity name (exact as signed)
- Executed date (date both parties signed)
- Term length and expiration date
- Mutual vs. one-way (or asymmetrical if different obligations each direction)
- Signatory names and titles (for verification)
- File location (repository path or SharePoint link)

---

## Expiring NDAs

### 90-Day Expiration Window

*[NDAs approaching expiration within 90 days. Action required to determine renewal, replacement, or sunset approach.]*

| ID | Counterparty | Days Until Expiration | Expiration Date | Renewal Timeline | Owner |
|----|--------------|----------------------|-----------------|-----------------|-------|
| **NDA-XXX** | *[Name]* | **45** | *[MM/DD/YYYY]* | Renew by *[date]* | *[Owner]* |
| **NDA-YYY** | *[Name]* | **60** | *[MM/DD/YYYY]* | Renew by *[date]* | *[Owner]* |
| **NDA-ZZZ** | *[Name]* | **75** | *[MM/DD/YYYY]* | Renew by *[date]* | *[Owner]* |

### Renewal Decision Matrix

| Counterparty | Renewal Decision | Rationale | Action Required | Target Signature |
|--------------|-----------------|-----------|-----------------|-----------------|
| *[Name]* | **Renew** | *[Ongoing relationship, active projects]* | Draft amendment or execute new NDA | *[Date]* |
| *[Name]* | **Let Expire** | *[Relationship inactive, no current/planned disclosures]* | Send closure notice 30 days before expiration | *[Date]* |
| *[Name]* | **Replace** | *[Update terms, expand scope, change duration]* | Negotiate revised agreement | *[Date]* |
| *[Name]* | **Pending** | *[Decision deferred, gathering requirements]* | Schedule decision meeting | *[Date]* |

---

## Key Terms Summary

### Standard NDA Terms

*[Reference summary of standard contractual provisions across the NDA portfolio. Highlight any material deviations or non-standard language.]*

| Term Category | Our Standard | Notes |
|---------------|-------------|-------|
| **Term** | *[X years]* | *[Range: X-Y years depending on relationship]* |
| **Definition of Confidential** | *[Technical/Business information marked or identified as confidential]* | *[Include: Oral disclosures, documents, meetings]* |
| **Permitted Uses** | *[Evaluation of potential business relationship]* | *[May expand: Performance of contract, regulatory compliance]* |
| **Unauthorized Disclosure** | *[Prohibited except to employees with need-to-know]* | *[Attorney/accountant exceptions per law]* |
| **Return/Destruction** | *[Upon request or contract termination]* | *[30/60/90-day destruction window typical]* |
| **Standard of Care** | *[Reasonable security safeguards]* | *[Best-of-class may require 'industry-standard' or specific technical controls]* |
| **Exceptions** | *[Publicly available, independent development, required by law]* | *[Always include "required by law" exception with notice requirement]* |
| **Survival** | *[3 years post-termination]* | *[Industry norm: 2-5 years]* |

### Deviations & Special Provisions

*[Document any NDA-specific provisions or non-standard terms that deviate from company template.]*

| NDA ID | Counterparty | Deviation | Reason | Risk Level |
|--------|--------------|-----------|--------|------------|
| *[ID]* | *[Name]* | *[Custom provision]* | *[Negotiated for X reason]* | Low/Medium/High |
| *[ID]* | *[Name]* | *[Custom provision]* | *[Negotiated for X reason]* | Low/Medium/High |

---

## Obligation Tracking

### Confidentiality Obligations Matrix

*[Track specific obligations and restrictions imposed by each NDA. Use to manage day-to-day confidentiality activities.]*

| NDA ID | Counterparty | Key Obligation | Responsible Team | Monitoring Method | Status |
|--------|--------------|----------------|-----------------|------------------|--------|
| **NDA-001** | *[Company]* | *[Do not disclose technical specifications to third parties without consent]* | Engineering | Monthly disclosure register review | On Track |
| **NDA-002** | *[Company]* | *[Limit access to C-level and board members only]* | Legal/Business Dev | Quarterly access audit | On Track |
| **NDA-003** | *[Company]* | *[Segregate physical documents in locked cabinet]* | Operations | Quarterly facility walk-through | On Track |
| **NDA-004** | *[Company]* | *[Encrypt electronic copies; destroy after product launch]* | IT/Operations | Quarterly system audit + retention compliance check | At Risk |

### Disclosure Log

*[Maintain a log of any authorized disclosures made under NDA terms. Track timing, scope, and recipient approval.]*

| Date | NDA ID | Counterparty | Disclosure Scope | Authorized By | Recipient | Purpose |
|------|--------|--------------|------------------|---------------|-----------|---------|
| *[MM/DD/YYYY]* | *[ID]* | *[Company]* | *[Technical architecture white paper]* | *[Exec name]* | *[Individual name]* | *[Product evaluation]* |
| *[MM/DD/YYYY]* | *[ID]* | *[Company]* | *[Business plan and financial projections]* | *[Exec name]* | *[Individual name]* | *[Strategic partnership discussion]* |

---

## Breach Protocol

### Breach Definition

*[An unauthorized disclosure of information protected under an NDA, including accidental loss, theft, system compromise, or unauthorized sharing.]*

### Breach Response Checklist

Upon discovery of a suspected breach:

- [ ] **STOP dissemination:** Immediately cease any further disclosure and retrieve materials if possible
- [ ] **Document incident:** Note date, time, scope, affected information, counterparty(ies), and circumstances
- [ ] **Assess impact:** Determine if breach is material or minor
- [ ] **Notify Legal:** Escalate to General Counsel within **24 hours**
- [ ] **Evaluate NDA requirement:** Check specific breach notification clause (typically 10-30 days)
- [ ] **Prepare notification letter:** Draft formal disclosure to counterparty
- [ ] **Mitigation plan:** Develop steps to prevent recurrence
- [ ] **Deliver notification:** Send notice by certified mail and email as required
- [ ] **Document remediation:** Record all corrective actions taken
- [ ] **Close-out:** Obtain written acknowledgment from counterparty if applicable

### Breach Notification Template

```
[Counterparty Legal Name]
[Counterparty Address]

Date: [YYYY-MM-DD]
Subject: Notice of Confidential Information Disclosure

Dear [Counterparty Contact]:

We are writing to inform you that on [date], [description of how information was disclosed] 
resulted in the unauthorized disclosure of confidential information provided to us under the 
[date] Non-Disclosure Agreement between our companies.

Affected Information: [Specific description of disclosed information]
Date of Disclosure: [Date]
Recipient of Disclosure: [To whom information was disclosed]

Remediation Steps Taken:
1. [Action 1]
2. [Action 2]
3. [Action 3]

We are implementing the following measures to prevent future occurrences:
[Describe preventive controls]

We sincerely regret this incident and remain committed to protecting your confidential information.

Sincerely,
[Name, Title]
```

### Incident Tracking

| Date | Counterparty | Incident Description | Severity | Resolution Status | Notes |
|------|--------------|---------------------|----------|-------------------|-------|
| *[Date]* | *[Name]* | *[Brief description]* | Minor/Major/Critical | Resolved/Pending | *[Outcome]* |

---

## Review Schedule

### Quarterly Review Calendar

| Quarter | Review Date | Responsible Party | Checklist Items |
|---------|------------|-------------------|-----------------|
| **Q1** | *[MM/DD]* | *[Owner name]* | NDAs expiring in next 90 days; new executions; breach log |
| **Q2** | *[MM/DD]* | *[Owner name]* | Renewal decisions; disclosure log review; obligation compliance |
| **Q3** | *[MM/DD]* | *[Owner name]* | Expired NDA archival; inactive counterparty status update |
| **Q4** | *[MM/DD]* | *[Owner name]* | Annual register audit; training refresher; policy updates |

### Annual Audit

**Scope:** Full register audit, counterparty contact verification, compliance testing

**Frequency:** Annually in *[Month]*

**Lead:** *[Compliance Officer name]*

**Deliverable:** Annual NDA Audit Report with findings and recommendations

### Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| *[Update NDA register with new executions]* | *[Legal]* | *[Date]* | Pending |
| *[Renew expiring NDAs]* | *[Business Lead]* | *[Date]* | In Progress |
| *[Schedule renewal meetings with counterparties]* | *[BD]* | *[Date]* | Pending |
| *[Complete quarterly obligation compliance audit]* | *[Compliance]* | *[Date]* | Pending |
| *[Archive expired NDAs]* | *[Legal]* | *[Date]* | Pending |

---

## Document Control

**Distribution:** {{distribution_statement}}  
**Retention Period:** {{retention_period_days}} days  
**Last Updated:** {{date}}  
**Next Review Date:** *[Date]*  

---

*Document generated by librarian v{{librarian_version}} from template \`nda-tracker\`.*
