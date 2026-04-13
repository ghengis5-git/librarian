---
template_id: penetration-test-report
display_name: Penetration Test Report
preset: security
description: >-
  Penetration test report documenting scope, methodology, findings, exploitation
  evidence, and remediation recommendations. Covers external, internal, web
  application, and social engineering tests.
suggested_tags: [security, pentest, offensive]
suggested_folder: docs/
typical_cross_refs:
  - vulnerability-assessment
  - threat-model
  - incident-response-plan
recommended_with:
  - vulnerability-assessment
requires: []
sections:
  - Executive Summary
  - Engagement Details
  - Methodology
  - Findings
  - Attack Narratives
  - Remediation Recommendations
  - Conclusion
---

# Penetration Test Report: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**Engagement Period:** *[Start]* — *[End]*

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
{% endif %}

---

## Executive Summary

*[1–2 paragraph overview for executive audience: scope, key findings, highest-impact vulnerabilities exploited, and overall security posture (Strong / Moderate / Weak).]*

### Key Metrics

| Metric | Value |
|--------|-------|
| Total vulnerabilities identified | *[X]* |
| Successfully exploited | *[X]* |
| Critical / High severity | *[X]* |
| Domain/root access achieved | *[Yes / No]* |
| Data exfiltration demonstrated | *[Yes / No]* |
| Social engineering success rate | *[X% — if tested]* |

---

## Engagement Details

| Attribute | Detail |
|-----------|--------|
| **Client** | *[Organization name]* |
| **Test Type** | *[External / Internal / Web App / Mobile / Social Engineering / Red Team]* |
| **Approach** | *[Black box / Grey box / White box]* |
| **Rules of Engagement** | *[Reference signed ROE document]* |
| **In-Scope Systems** | *[IP ranges, URLs, applications]* |
| **Out-of-Scope** | *[Excluded systems, techniques]* |
| **Testing Window** | *[Dates and hours]* |
| **Emergency Contact** | *[Client POC for issues]* |

### Testing Team

| Name | Role | Certification |
|------|------|-------------|
| *[Name]* | *[Lead tester]* | *[OSCP / GPEN / CEH / etc.]* |
| *[Name]* | *[Tester]* | *[Cert]* |

---

## Methodology

*[Describe the testing methodology used. Reference industry frameworks.]*

1. **Reconnaissance** — OSINT, DNS enumeration, port scanning
2. **Enumeration** — Service identification, version detection, directory brute-force
3. **Vulnerability Analysis** — Automated scanning + manual verification
4. **Exploitation** — Controlled exploitation of confirmed vulnerabilities
5. **Post-Exploitation** — Privilege escalation, lateral movement, data access
6. **Reporting** — Documentation of findings with evidence and remediation

---

## Findings

### Finding 1: *[Title]*

| Attribute | Detail |
|-----------|--------|
| **Severity** | *[Critical / High / Medium / Low]* |
| **CVSS** | *[X.X]* |
| **Type** | *[RCE / SQLi / XSS / Auth Bypass / PrivEsc / etc.]* |
| **Affected** | *[System / URL / Service]* |
| **Description** | *[Technical description of the vulnerability]* |
| **Evidence** | *[Screenshot, command output, or proof-of-concept reference]* |
| **Business Impact** | *[What an attacker could achieve in real-world terms]* |
| **Remediation** | *[Specific technical fix]* |

### Finding 2: *[Title]*
*[Follow same structure.]*

{% if "hipaa" in compliance %}
### PHI Exposure Findings
| Finding | PHI Accessible | Volume | HIPAA Impact |
|---------|---------------|--------|-------------|
| *[Finding ref]* | *[Yes — type of PHI]* | *[X records]* | *[Breach notification threshold]* |
{% endif %}

---

## Attack Narratives

### Narrative 1: *[Attack Chain Title]*

*[Step-by-step description of the most significant attack chain, from initial access to objective completion. Include timestamps and evidence.]*

1. **Initial Access:** *[How entry was gained]*
2. **Privilege Escalation:** *[How elevated access was obtained]*
3. **Lateral Movement:** *[How access was expanded]*
4. **Objective:** *[What was achieved — data access, admin control, etc.]*

---

## Remediation Recommendations

| Priority | Finding | Remediation | Effort | Owner |
|----------|---------|------------|--------|-------|
| P1 (Immediate) | *[Finding]* | *[Fix]* | *[Hours/Days]* | *[Team]* |
| P2 (Short-term) | *[Finding]* | *[Fix]* | *[Days/Weeks]* | *[Team]* |
| P3 (Medium-term) | *[Finding]* | *[Fix]* | *[Weeks/Months]* | *[Team]* |

### Strategic Recommendations
1. *[Broader security improvement recommendation]*
2. *[Process or architecture recommendation]*

---

## Conclusion

*[Overall assessment of security posture, comparison to previous tests if applicable, and recommended retest timeline.]*

**Retest Recommended:** *[Yes — after remediation of P1/P2 items, target date]*

---

## Approval

- **Lead Tester (Name):** ____________________  **Date:** __________
- **Client Security Lead (Name):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `penetration-test-report`.*
