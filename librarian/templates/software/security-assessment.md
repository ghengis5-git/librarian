---
template_id: security-assessment
display_name: Security Assessment
preset: software
description: Comprehensive security assessment covering threats, vulnerabilities, risk analysis, and compliance controls
suggested_tags:
  - security
  - assessment
  - compliance
suggested_folder: docs/
typical_cross_refs:
  - technical-architecture
  - runbook
requires: []
recommended_with:
  - technical-architecture
sections:
  - Executive Summary
  - Scope
  - Threat Model
  - Vulnerability Assessment
  - Risk Matrix
  - Remediation Plan
  - Compliance Mapping
---

# Security Assessment: {{title}}

**Project:** {{project_name}}  
**Assessment Date:** {{date}}  
**Version:** {{version}}  
**Classification:** {{classification}}  
**Assessor:** {{author}}

---

## Executive Summary

[*High-level overview of security posture, key findings, and overall risk rating.*]

### Risk Rating

| Category | Rating | Trend |
|----------|--------|-------|
| **Overall** | [*Critical / High / Medium / Low*] | [*↑ / → / ↓*] |
| **Authentication** | [*rating*] | [*trend*] |
| **Authorization** | [*rating*] | [*trend*] |
| **Encryption** | [*rating*] | [*trend*] |
| **Infrastructure** | [*rating*] | [*trend*] |
| **Data Protection** | [*rating*] | [*trend*] |

### Key Findings

- **Finding 1 (Critical):** [*Description of critical vulnerability*]
- **Finding 2 (High):** [*Description of high-severity issue*]
- **Finding 3 (Medium):** [*Improvement area*]

### Remediation Summary

- [*X critical items requiring immediate action*]
- [*Y high-priority items for next sprint*]
- [*Z medium-priority items for roadmap*]

---

## Scope

### In Scope

- [*Service/system being assessed*]
- [*Infrastructure components*]
- [*Third-party integrations*]
- [*Data types and flows*]

### Out of Scope

- [*Legacy systems/services*]
- [*Partner systems*]
- [*Future roadmap items*]

### Assessment Methodology

- **Standards:** [*NIST CSF / CIS / OWASP Top 10 / ISO 27001*]
- **Tools:** [*Vulnerability scanners, code review, penetration testing, interviews*]
- **Period:** [*Assessment dates*]

---

## Threat Model

[*What threats are we trying to protect against? Who are the attackers?*]

### Threat Actors

| Threat Actor | Capability | Motivation | Likelihood |
|--------------|-----------|-----------|------------|
| External Attackers | Medium-High | Financial gain / Disruption | High |
| Disgruntled Insider | High | Revenge / Financial | Medium |
| Competitors | Medium | Intellectual property theft | Low |
| Nation-State | Extreme | Political / Espionage | Low |

### Threat Scenarios

#### Scenario 1: Data Breach via SQL Injection

- **Attack Vector:** Malicious SQL in API input
- **Entry Point:** Public API endpoint
- **Impact:** Customer PII exposure
- **Likelihood:** Medium (without proper input validation)
- **Mitigation:** Parameterized queries, input validation, WAF rules

#### Scenario 2: Privilege Escalation

- **Attack Vector:** Insecure direct object reference (IDOR)
- **Entry Point:** Authenticated user API
- **Impact:** Access to unauthorized data
- **Likelihood:** Medium (if authorization checks weak)
- **Mitigation:** Proper access control checks, role-based permissions

#### Scenario 3: Infrastructure Compromise

- **Attack Vector:** Weak SSH credentials, unpatched server
- **Entry Point:** Admin interface
- **Impact:** Full system compromise
- **Likelihood:** Low (with MFA and patching)
- **Mitigation:** SSH key-only auth, automated patching, monitoring

---

## Vulnerability Assessment

### Application Security

| Vulnerability | Severity | Status | Remediation |
|---------------|----------|--------|-------------|
| Unvalidated Redirects | High | [*Open / In Progress / Resolved*] | [*Use allowlist for redirects*] |
| Broken Authentication | Critical | Open | [*Implement MFA, use OAuth*] |
| Sensitive Data Exposure | High | Open | [*Use HTTPS, encrypt at rest*] |
| Broken Access Control | Critical | Open | [*Implement RBAC, audit checks*] |
| Security Misconfiguration | Medium | Open | [*Harden configs, disable debug mode*] |
| Cross-Site Scripting (XSS) | Medium | [*status*] | [*Content Security Policy, sanitization*] |
| Insecure Serialization | High | [*status*] | [*Use safe serialization formats*] |
| Insufficient Logging | Medium | [*status*] | [*Implement security event logging*] |

### Infrastructure Security

- **Firewall Rules:** [*Review rules for overly permissive access*]
- **OS Patches:** [*Automated patching enabled? Update frequency?*]
- **Container Security:** [*Image scanning, runtime monitoring, network policies*]
- **Secrets Management:** [*Centralized KMS? Key rotation schedule?*]
- **SSL/TLS:** [*Protocol version, cipher suites, certificate management*]

### Dependencies & Supply Chain

```bash
# Audit for known vulnerabilities
npm audit
pip check
docker scout cves <image>
```

| Dependency | Version | CVE | Action |
|------------|---------|-----|--------|
| [*package*] | [*version*] | [*CVE-2026-XXXX*] | [*Update to X.Y.Z*] |

---

## Risk Matrix

[*Visual representation of likelihood vs. impact.*]

### Risk Ratings

| Risk | Likelihood | Impact | Priority | Owner |
|------|-----------|--------|----------|-------|
| **Critical Vulnerability 1** | High | Critical | P0 | [*Team/person*] |
| **High Issue 1** | Medium | High | P1 | [*Team/person*] |
| **Medium Issue 1** | Medium | Medium | P2 | [*Team/person*] |
| **Low Issue 1** | Low | Low | P3 | [*Team/person*] |

### Risk Acceptance

- [*Risk: [description], Accepted by: [name], Date: [date], Justification: [business reason]*]
- [*Risk: [description], Accepted by: [name], Date: [date], Justification: [business reason]*]

---

## Remediation Plan

### Immediate (0-30 days)

- [ ] **Critical Finding 1:** [*Description, assigned to [person], due [date]*]
  - Steps: [*1. step, 2. step, 3. step*]
  - Verification: [*How will we confirm this is fixed?*]

### Short-Term (1-3 months)

- [ ] **High Finding 1:** [*Description, assigned to [person], due [date]*]
- [ ] **High Finding 2:** [*Description, assigned to [person], due [date]*]

### Medium-Term (3-6 months)

- [ ] **Medium Finding 1:** [*Description, assigned to [person], due [date]*]
- [ ] **Infrastructure Hardening:** [*Specific improvement*]

### Long-Term (6-12 months)

- [ ] **Security Program Maturity:** [*Process improvement, training, etc.*]
- [ ] **Compliance Certification:** [*ISO 27001, SOC 2, etc.*]

---

{% if "iso_27001" in compliance %}

## ISO 27001 Compliance Mapping

### Control Assessment

| Annex A Control | Requirement | Current Status | Gap | Action |
|-----------------|-------------|---------------|----|--------|
| A.5.1 Management Direction | Policies for info security | [*Implemented / Planned / Not Started*] | [*None / Minor / Major*] | [*action*] |
| A.6.1 Organization | Roles and responsibilities | [*status*] | [*gap*] | [*action*] |
| A.6.2 Confidentiality | Confidentiality agreements | [*status*] | [*gap*] | [*action*] |
| A.7.1 Prior to Employment | Personnel screening | [*status*] | [*gap*] | [*action*] |
| A.7.2 During Employment | Awareness and training | [*status*] | [*gap*] | [*action*] |
| A.9.1 Access Control Policy | User access management | [*status*] | [*gap*] | [*action*] |
| A.10.1 Cryptography Policy | Use of encryption | [*status*] | [*gap*] | [*action*] |
| A.12.2 Encryption | Data encryption standards | [*status*] | [*gap*] | [*action*] |
| A.13.1 Network Security | Network architecture and segmentation | [*status*] | [*gap*] | [*action*] |
| A.14.1 Information Security | Incident handling process | [*status*] | [*gap*] | [*action*] |
| A.15.1 Compliance | Compliance with laws | [*status*] | [*gap*] | [*action*] |

### Certification Timeline

- **Current Status:** [*Pre-audit / In audit / Certified*]
- **Target Date:** [*Date for certification*]
- **Auditor:** [*Accredited audit firm*]

{% endif %}

{% if "hipaa" in compliance %}

## HIPAA Compliance - PHI Handling

**Protected Health Information (PHI) in Scope:**
- [*List types of PHI handled: medical records, lab results, billing info, etc.*]
- [*Storage locations: databases, backups, logs*]
- [*Transmission methods: APIs, email, reports*]

### Technical Safeguards

- **Encryption:** [*AES-256 at rest, TLS 1.3 in transit*]
- **Access Control:** [*Role-based access, audit logs*]
- **Audit Controls:** [*All PHI access logged and reviewed*]

### Administrative Safeguards

- **Privacy Officer:** [*Name, contact*]
- **Security Training:** [*Frequency, coverage*]
- **Incident Response Plan:** [*Link to HIPAA breach response procedure*]

### Business Associate Agreements

| Vendor | BAA Status | Signed | Renewal |
|--------|-----------|--------|---------|
| [*vendor*] | [*Executed / Pending*] | [*date*] | [*date*] |

{% endif %}

{% if "dod_5200" in compliance %}

## DoD 5200.01-M Classification Controls

**Classification Level:** {{classification}}

### Marking & Handling

- **Header:** [*Include classification and declassification instructions*]
- **Footer:** [*Distribution statement (A-F)*]
- **Media:** [*Marked with highest classification on label*]
- **Transmission:** [*Secure channels only (encrypted, courier, etc.)*]

### Storage & Access

- **Facility:** [*Physical access controls (badges, cameras, guards)*]
- **Digital:** [*Network segmentation, role-based access, MFA*]
- **Disposal:** [*Shred paper, DoD wipe for digital media*]

### Personnel

- **Clearances:** [*Required clearance level(s)*]
- **Need-to-Know:** [*Document justification for each access grant*]
- **Training:** [*Initial and annual classification training*]

### Audit & Compliance

- **Access Log:** [*All classified file access logged*]
- **Inspection:** [*Quarterly security spot-checks*]
- **Incident Report:** [*Any unauthorized access reported to FSO/CISO*]

{% endif %}

---

## Recommendations & Next Steps

1. [*Priority 1 recommendation*]
2. [*Priority 2 recommendation*]
3. [*Priority 3 recommendation*]

### Timeline

- **Week 1-2:** [*Quick wins and critical fixes*]
- **Month 1-2:** [*High-priority improvements*]
- **Month 3-6:** [*Comprehensive security program build-out*]
- **Ongoing:** [*Monitoring, testing, training*]

---

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | {{date}} | {{author}} | Initial assessment |

---

*Document generated by librarian v{{librarian_version}} from template \`security-assessment\`.*
