---
template_id: regulatory-compliance-checklist
display_name: Regulatory Compliance Checklist
preset: legal
description: Comprehensive compliance requirements matrix and gap analysis for regulatory frameworks
suggested_tags: [compliance, regulatory, checklist]
suggested_folder: compliance/
typical_cross_refs: [legal-review, contract-summary]
recommended_with: [legal-review]
requires: []
sections:
  - Regulatory Framework
  - Compliance Requirements Matrix
  - Current Compliance Status
  - Gap Analysis
  - Remediation Plan
  - Audit Schedule
  - Responsible Parties
---

# Regulatory Compliance Checklist — {{title}}

**Date:** {{date}}  
**Author:** {{author}}  
**Version:** {{version}}  
**Classification:** {{classification}}  
**Compliance Scope:** *[e.g., Data Privacy, Financial Services, Healthcare, Environmental]*

---

## Regulatory Framework

### Applicable Regulations

| Regulation | Jurisdiction | Effective Date | Scope |
|-----------|--------------|----------------|-------|
| *[Reg 1]* | *[Country/State]* | *[Date]* | *[Coverage areas]* |
| *[Reg 2]* | *[Country/State]* | *[Date]* | *[Coverage areas]* |
| *[Reg 3]* | *[Country/State]* | *[Date]* | *[Coverage areas]* |

### Industry Standards & Best Practices

- *[Standard 1: [Issuing body, version, adoption status]]*
- *[Standard 2: [Issuing body, version, adoption status]]*
- *[Standard 3: [Issuing body, version, adoption status]]*

### Regulatory Body Contacts

| Body | Jurisdiction | Primary Contact | Reporting Frequency |
|------|--------------|-----------------|-------------------|
| *[Regulatory Agency 1]* | *[Location]* | *[Contact info]* | *[Annual/Quarterly/As triggered]* |
| *[Regulatory Agency 2]* | *[Location]* | *[Contact info]* | *[Annual/Quarterly/As triggered]* |

---

## Compliance Requirements Matrix

### Overview Checklist

*[Master list of all compliance obligations across applicable regulations. Each item maps to regulatory source and current status.]*

| Requirement ID | Requirement Description | Regulatory Source | Materiality | Status | Owner |
|---|---|---|---|---|---|
| *[REQ-001]* | *[Requirement summary]* | *[Regulation X, Section Y]* | Critical/High/Medium/Low | Compliant/Non-Compliant/Not Applicable | *[Owner]* |
| *[REQ-002]* | *[Requirement summary]* | *[Regulation X, Section Y]* | Critical/High/Medium/Low | Compliant/Non-Compliant/Not Applicable | *[Owner]* |
| *[REQ-003]* | *[Requirement summary]* | *[Regulation X, Section Y]* | Critical/High/Medium/Low | Compliant/Non-Compliant/Not Applicable | *[Owner]* |

{% if "hipaa" in compliance %}
### Healthcare Compliance (HIPAA)

#### Privacy Rule Requirements

| Requirement | Status | Evidence/Documentation |
|-----------|--------|--------------------------|
| Designate Privacy Officer | Compliant/Non-Compliant | *[Name, start date]* |
| Develop Privacy Policies & Procedures | Compliant/Non-Compliant | *[Policy version, approval date]* |
| Implement Access Controls | Compliant/Non-Compliant | *[Role-based access configuration]* |
| Provide Privacy Notice | Compliant/Non-Compliant | *[Distribution method, signed receipts]* |
| Establish Patient Rights Procedures | Compliant/Non-Compliant | *[Procedure for access requests, amendments]* |
| Restrict PHI Use & Disclosure | Compliant/Non-Compliant | *[Business Associate Agreements executed]* |
| Document Uses & Disclosures | Compliant/Non-Compliant | *[Accounting of disclosures system]* |

#### Security Rule Requirements

| Requirement | Status | Evidence/Documentation |
|-----------|--------|--------------------------|
| Designate Security Officer | Compliant/Non-Compliant | *[Name, start date]* |
| Conduct Security Risk Analysis | Compliant/Non-Compliant | *[Assessment date, findings]* |
| Implement Technical Safeguards | Compliant/Non-Compliant | *[Encryption, access logs, audit controls]* |
| Implement Physical Safeguards | Compliant/Non-Compliant | *[Facility access controls, video surveillance]* |
| Implement Administrative Safeguards | Compliant/Non-Compliant | *[Workforce security, training program]* |
| Establish Incident Response Plan | Compliant/Non-Compliant | *[Plan version, testing dates]* |
| Breach Notification Procedures | Compliant/Non-Compliant | *[Notification templates, state attorney tracking]* |

#### Breach Notification Requirements

| Trigger | Notification Timeline | Responsible Party | Status |
|---------|---------------------|-------------------|--------|
| **Breach affecting <500 individuals** | Without unreasonable delay | *[Internal]* | Documented |
| **Breach affecting >=500 individuals** | Without unreasonable delay + Media notice | *[Legal/Compliance]* | Documented |
| **HHS Notification** | If delay unwarranted | *[Compliance Officer]* | Procedure in place |

{% endif %}

{% if "iso_27001" in compliance %}
### Information Security Compliance (ISO 27001)

#### Asset Management (A.8)

| Control | Status | Evidence |
|---------|--------|----------|
| Inventory of assets maintained | Compliant/Non-Compliant | *[Asset register, last update]* |
| Information classification applied | Compliant/Non-Compliant | *[Classification scheme, applied to X% of assets]* |
| Labeling of information implemented | Compliant/Non-Compliant | *[Labels on X documents/systems]* |

#### Access Control (A.9)

| Control | Status | Evidence |
|---------|--------|----------|
| User access policies documented | Compliant/Non-Compliant | *[Policy version, approval date]* |
| Access rights provisioning/deprovisioning | Compliant/Non-Compliant | *[Process documentation, audit trail]* |
| Privileged access management in place | Compliant/Non-Compliant | *[PAM tool deployed, audit logs]* |
| Password policy enforced | Compliant/Non-Compliant | *[Policy specification, technical controls]* |

#### Cryptography (A.10)

| Control | Status | Evidence |
|---------|--------|----------|
| Encryption policy documented | Compliant/Non-Compliant | *[Policy version, scope]* |
| Encryption in transit (TLS/SSH) | Compliant/Non-Compliant | *[Systems audit, certificate inventory]* |
| Encryption at rest for sensitive data | Compliant/Non-Compliant | *[Database encryption, key management]* |
| Key management procedures in place | Compliant/Non-Compliant | *[Key rotation log, documented procedures]* |

#### Incident Management (A.16)

| Control | Status | Evidence |
|---------|--------|----------|
| Incident reporting procedure | Compliant/Non-Compliant | *[Procedure documented, communication templates]* |
| Incident response team identified | Compliant/Non-Compliant | *[Team roster, contact info, training records]* |
| Incident response plan tested | Compliant/Non-Compliant | *[Tabletop exercise dates, findings documented]* |

{% endif %}

{% if "sec_finra" in compliance %}
### Securities & Financial Compliance (SEC/FINRA)

#### Books & Records (SEC Rule 17a-3, 17a-4, FINRA 4511)

| Requirement | Status | Evidence |
|-----------|--------|----------|
| Customer account records maintained | Compliant/Non-Compliant | *[System audit, sampling results]* |
| Blotter/trade journal maintained | Compliant/Non-Compliant | *[System configuration, retention verified]* |
| General ledger & financial statements | Compliant/Non-Compliant | *[Financial audit, reconciliation sign-off]* |
| Communications archived (emails, calls) | Compliant/Non-Compliant | *[System monitoring, retention policy]* |
| Record retention per schedule | Compliant/Non-Compliant | *[Retention matrix, disposal audit]* |

#### Compliance Programs (SEC Rule 15c2-1, FINRA 4110)

| Requirement | Status | Evidence |
|-----------|--------|----------|
| Chief Compliance Officer designated | Compliant/Non-Compliant | *[Appointment letter, reporting line]* |
| Supervisory policies & procedures | Compliant/Non-Compliant | *[Manual version, approval date]* |
| Written supervisory procedures (WSPs) | Compliant/Non-Compliant | *[WSP manual, reviewer assignments]* |
| Compliance testing conducted | Compliant/Non-Compliant | *[Test schedule, results documented]* |
| Annual compliance certifications | Compliant/Non-Compliant | *[Certifications signed, filed with regulators]* |

#### Anti-Money Laundering (AML) — FINRA 2210, SEC Rule 17j-1

| Requirement | Status | Evidence |
|-----------|--------|----------|
| AML program established & tested | Compliant/Non-Compliant | *[Program documentation, annual audit]* |
| Customer identification (CIP) procedure | Compliant/Non-Compliant | *[KYC form usage, identity verification]* |
| Suspicious activity reporting (SAR) | Compliant/Non-Compliant | *[Escalation procedures, FinCEN filings]* |
| Transaction monitoring system | Compliant/Non-Compliant | *[Rules configured, alert review logs]* |

{% endif %}

{% if "dod_5200" in compliance %}
### Classified Information (DoD 5200.01 / NIST SP 800-171)

#### Information Sensitivity Classification

| Classification Level | Definition | Handling Requirements |
|---------------------|-----------|----------------------|
| **UNCLASSIFIED** | Non-sensitive information | Standard office procedures |
| **CUI (Controlled Unclassified Information)** | Unclassified but sensitive | Limited distribution, marked, tracked |
| **CONFIDENTIAL** | Disclosure could cause serious damage | Limited access, marked, secure storage |
| **SECRET** | Disclosure could cause grave damage | Cleared personnel only, safes, crypto |
| **TOP SECRET** | Disclosure could cause exceptionally grave damage | Need-to-know, vaults, highest security |

#### Classified Document Handling

| Control | Status | Evidence |
|---------|--------|----------|
| Classified markings applied | Compliant/Non-Compliant | *[Marking samples, staff training records]* |
| Secure storage facilities (Classified Material Control Areas) | Compliant/Non-Compliant | *[Facility inspection, vault certifications]* |
| Access control logging | Compliant/Non-Compliant | *[Sign-in/sign-out sheets, audit trails]* |
| Classification review schedule | Compliant/Non-Compliant | *[Declassification dates assigned, review log]* |
| Destruction procedures for classified material | Compliant/Non-Compliant | *[Shredding/incineration records, witness certification]* |

#### Personnel Security Clearances

| Control | Status | Evidence |
|---------|--------|----------|
| Clearance verification before access | Compliant/Non-Compliant | *[Clearance verification process, records]* |
| Periodic reinvestigations scheduled | Compliant/Non-Compliant | *[Reinvestigation dates, last reinvestigation]* |
| Personnel security briefings | Compliant/Non-Compliant | *[Briefing attendance sign-in, NOFORN briefing]* |
| Non-disclosure agreements signed | Compliant/Non-Compliant | *[SF-312 or equivalent on file]* |
| Counterintelligence training | Compliant/Non-Compliant | *[Annual training completion records]* |

{% endif %}

---

## Current Compliance Status

### Summary Dashboard

**Overall Compliance Status:** *[Green/Yellow/Red]*

| Category | Compliant | Non-Compliant | Pending | N/A |
|----------|-----------|---------------|---------|-----|
| *[Category 1]* | X | X | X | X |
| *[Category 2]* | X | X | X | X |
| *[Category 3]* | X | X | X | X |
| **TOTAL** | **X** | **X** | **X** | **X** |

### Critical Issues

*[List any high-priority, non-compliant items that present regulatory risk.]*

1. *[Issue 1: [Description] — Due: [Remediation date]]*
2. *[Issue 2: [Description] — Due: [Remediation date]]*

---

## Gap Analysis

### Non-Compliant Requirements

| Requirement ID | Description | Root Cause | Impact | Priority |
|---|---|---|---|---|
| *[REQ-XXX]* | *[What is missing]* | *[Why]* | *[Regulatory/Financial/Operational]* | Critical/High/Medium |
| *[REQ-YYY]* | *[What is missing]* | *[Why]* | *[Regulatory/Financial/Operational]* | Critical/High/Medium |

### Resource & Capability Gaps

*[Identify staffing, skills, tools, or budget constraints preventing compliance.]*

---

## Remediation Plan

### Corrective Actions

| Gap/Issue | Corrective Action | Target Date | Owner | Status |
|-----------|------------------|------------|-------|--------|
| *[Gap 1]* | *[Action]* | *[Date]* | *[Owner]* | Not Started/In Progress/Complete |
| *[Gap 2]* | *[Action]* | *[Date]* | *[Owner]* | Not Started/In Progress/Complete |

### Implementation Timeline

- **Phase 1 (Immediate):** *[Critical items, Days 1-30]*
- **Phase 2 (Short-term):** *[Important items, Weeks 6-12]*
- **Phase 3 (Medium-term):** *[Enhancement items, Months 4-6]*

---

## Audit Schedule

### Internal Audit Plan

| Audit Area | Frequency | Next Scheduled Date | Responsible Team |
|-----------|-----------|-------------------|------------------|
| *[Audit 1]* | *[Annual/Semi-Annual/Quarterly]* | *[Date]* | *[Internal Audit]* |
| *[Audit 2]* | *[Annual/Semi-Annual/Quarterly]* | *[Date]* | *[Internal Audit]* |

### External Audit & Inspection Schedule

| Regulatory Body | Audit Type | Last Audit | Expected Next | Findings Status |
|----------------|-----------|-----------|---------------|-----------------|
| *[Agency 1]* | *[Routine/Targeted/Complaint-driven]* | *[Date]* | *[Expected date]* | *[All resolved / Pending]* |
| *[Agency 2]* | *[Routine/Targeted/Complaint-driven]* | *[Date]* | *[Expected date]* | *[All resolved / Pending]* |

---

## Responsible Parties

### Compliance Leadership

| Role | Name | Title | Contact | Approval Authority |
|------|------|-------|---------|-------------------|
| **Compliance Sponsor** | *[Name]* | *[Title]* | *[Email/Phone]* | Executive / Board |
| **Compliance Officer** | *[Name]* | *[Title]* | *[Email/Phone]* | Yes |
| **Audit Lead** | *[Name]* | *[Title]* | *[Email/Phone]* | Internal/External |

### Functional Owners

| Function | Owner | Responsibilities |
|----------|-------|------------------|
| *[Function 1]* | *[Owner]* | *[Specific controls/monitoring]* |
| *[Function 2]* | *[Owner]* | *[Specific controls/monitoring]* |
| *[Function 3]* | *[Owner]* | *[Specific controls/monitoring]* |

---

## Document Control

**Distribution:** {{distribution_statement}}  
**Retention Period:** {{retention_period_days}} days  
**Review Frequency:** *[Quarterly / Semi-Annual / Annual]*  
**Next Review Date:** *[Date]*  

---

*Document generated by librarian v{{librarian_version}} from template \`regulatory-compliance-checklist\`.*
