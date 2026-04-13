---
template_id: incident-response-plan
display_name: Incident Response Plan
preset: security
description: >-
  Cybersecurity incident response plan covering preparation, detection, analysis,
  containment, eradication, recovery, and post-incident activities. Aligns with
  NIST SP 800-61 framework.
suggested_tags: [security, incident-response, plan]
suggested_folder: docs/
typical_cross_refs:
  - threat-model
  - vulnerability-assessment
  - data-classification-policy
recommended_with:
  - threat-model
requires: []
sections:
  - Plan Overview
  - Roles & Responsibilities
  - Incident Classification
  - Detection & Analysis
  - Containment Strategy
  - Eradication & Recovery
  - Post-Incident Activities
  - Communication Plan
  - Testing & Maintenance
---

# Incident Response Plan: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
{% endif %}

---

## Plan Overview

### Purpose
*[State the purpose: establish procedures for detecting, responding to, and recovering from cybersecurity incidents.]*

### Scope
- **Applies to:** *[All information systems, networks, and data / Specific systems]*
- **Personnel:** *[All employees, contractors, and third-party vendors]*
- **Incident types covered:** *[Malware, unauthorized access, data breach, DDoS, insider threat, social engineering, physical security]*

---

## Roles & Responsibilities

| Role | Name | Responsibility | Contact |
|------|------|---------------|---------|
| Incident Commander | *[Name]* | Overall incident management, escalation decisions | *[Phone/Email]* |
| Security Lead | *[Name]* | Technical analysis, containment, forensics | *[Phone/Email]* |
| Communications Lead | *[Name]* | Internal/external communications, media | *[Phone/Email]* |
| Legal Counsel | *[Name]* | Legal obligations, regulatory notification | *[Phone/Email]* |
| System Administrators | *[Name/Team]* | System isolation, recovery, log preservation | *[Phone/Email]* |
| Executive Sponsor | *[Name]* | Resource authorization, final decisions | *[Phone/Email]* |

{% if "hipaa" in compliance %}
### HIPAA-Specific Roles
| Role | Name | Responsibility |
|------|------|---------------|
| Privacy Officer | *[Name]* | PHI breach determination, HHS notification |
| Security Officer | *[Name]* | ePHI security incident investigation |
{% endif %}

---

## Incident Classification

| Severity | Definition | Response Time | Examples |
|----------|-----------|---------------|---------|
| **Critical (S1)** | Active exploitation, data exfiltration, critical system down | *[15 min]* | Ransomware, active APT, mass data breach |
| **High (S2)** | Confirmed compromise, no active exfiltration | *[1 hour]* | Compromised credentials, malware on server |
| **Medium (S3)** | Suspicious activity, potential incident | *[4 hours]* | Anomalous traffic, phishing campaign |
| **Low (S4)** | Policy violation, minor security event | *[24 hours]* | Single failed login, misconfiguration |

---

## Detection & Analysis

### Detection Sources

| Source | Monitor | Alert Owner |
|--------|---------|------------|
| SIEM / Log aggregation | *[24/7 / Business hours]* | *[SOC / IT]* |
| EDR / Endpoint alerts | *[24/7]* | *[SOC / Security]* |
| IDS/IPS | *[24/7]* | *[Network team]* |
| User reports | *[Business hours]* | *[Help desk]* |
| Threat intelligence feeds | *[Automated]* | *[Security team]* |

### Initial Analysis Checklist
- [ ] Confirm the event is a real incident (not false positive)
- [ ] Determine severity classification
- [ ] Identify affected systems and data
- [ ] Preserve initial evidence (logs, screenshots, memory dumps)
- [ ] Activate incident response team if S1/S2

{% if "hipaa" in compliance %}
### PHI Breach Determination
If incident may involve PHI:
- [ ] Determine if PHI was accessed, acquired, used, or disclosed
- [ ] Assess whether unauthorized access compromised PHI security/privacy
- [ ] Apply the 4-factor breach risk assessment (45 CFR § 164.402)
- [ ] Document breach determination rationale
{% endif %}

---

## Containment Strategy

### Short-Term Containment (Stop the Bleeding)

| Action | When | Owner |
|--------|------|-------|
| Isolate affected systems from network | Immediately upon S1/S2 | System Admin |
| Block malicious IPs/domains at firewall | Immediately | Network team |
| Disable compromised accounts | Immediately | Identity team |
| Preserve forensic evidence before changes | Before any remediation | Security Lead |

### Long-Term Containment (Stabilize)

| Action | When | Owner |
|--------|------|-------|
| Apply temporary patches/workarounds | Within 24 hours | System Admin |
| Implement enhanced monitoring on affected systems | Within 24 hours | SOC |
| Rotate credentials for affected scope | Within 24 hours | Identity team |

---

## Eradication & Recovery

### Eradication
1. Identify and remove all instances of the threat (malware, backdoors, unauthorized accounts)
2. Patch vulnerabilities that enabled the incident
3. Verify eradication with scans and manual review

### Recovery
1. Restore systems from known-good backups
2. Rebuild compromised systems if integrity cannot be verified
3. Gradually restore services with enhanced monitoring
4. Verify normal operations before full reconnection

### Recovery Verification
- [ ] All malicious artifacts removed
- [ ] Vulnerabilities patched
- [ ] Systems restored and functional
- [ ] Enhanced monitoring in place for *[30/60/90 days]*
- [ ] No indicators of re-compromise after *[X days]*

---

## Post-Incident Activities

### Lessons Learned Meeting
- **When:** Within *[5 business days]* of incident closure
- **Attendees:** All IR team members + affected system owners
- **Output:** Post-incident report with timeline, root cause, and improvement actions

### Post-Incident Report Contents
1. Incident timeline (detection → containment → eradication → recovery)
2. Root cause analysis
3. What worked well
4. What needs improvement
5. Action items with owners and deadlines

### Metrics to Track

| Metric | This Incident | Target |
|--------|-------------|--------|
| Time to detect | *[X hours]* | *[<1 hour]* |
| Time to contain | *[X hours]* | *[<4 hours]* |
| Time to eradicate | *[X days]* | *[<3 days]* |
| Time to recover | *[X days]* | *[<7 days]* |

---

## Communication Plan

### Internal Notifications

| Audience | Notify When | Method | Owner |
|----------|-----------|--------|-------|
| Executive team | S1/S2 confirmed | Phone + email | Incident Commander |
| Legal | Any potential data breach | Phone | Incident Commander |
| HR | Insider threat involvement | Phone | Security Lead |
| All staff | If awareness needed | Email / Intranet | Communications Lead |

### External Notifications

| Audience | Regulatory Basis | Deadline | Owner |
|----------|-----------------|----------|-------|
| *[Affected individuals]* | *[State breach notification laws]* | *[30–60 days]* | Legal |
| *[Regulators]* | *[HIPAA / SEC / State AG]* | *[Per regulation]* | Legal / Compliance |
| *[Law enforcement]* | *[If criminal activity suspected]* | *[ASAP]* | Legal |

{% if "hipaa" in compliance %}
### HIPAA Breach Notification Requirements
- **HHS OCR:** Within 60 days of discovery (>500 individuals: immediate)
- **Affected individuals:** Without unreasonable delay, no later than 60 days
- **Media:** If >500 residents of a state/jurisdiction affected
{% endif %}

---

## Testing & Maintenance

### Plan Testing

| Exercise Type | Frequency | Last Conducted | Next Scheduled |
|--------------|-----------|---------------|---------------|
| Tabletop exercise | *[Annual]* | *[Date]* | *[Date]* |
| Simulation / Drill | *[Semi-annual]* | *[Date]* | *[Date]* |
| Full-scale exercise | *[Biennial]* | *[Date]* | *[Date]* |

### Plan Maintenance
- **Review cycle:** *[Annual or after any S1/S2 incident]*
- **Contact list update:** *[Quarterly]*
- **Next scheduled review:** *[Date]*

---

## Approval

- **Author (Name/Title):** ____________________  **Date:** __________
- **CISO / Security Director (Name/Title):** ____________________  **Date:** __________
- **Executive Sponsor (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `incident-response-plan`.*
