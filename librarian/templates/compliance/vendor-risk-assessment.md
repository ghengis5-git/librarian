---
template_id: vendor-risk-assessment
display_name: Vendor Risk Assessment
preset: compliance
description: >-
  Third-party vendor risk assessment covering information security, operational
  resilience, regulatory compliance, and contractual safeguards. Tracks vendor
  risk rating, due diligence findings, and ongoing monitoring requirements.
suggested_tags: [compliance, vendor, third-party-risk]
suggested_folder: docs/
typical_cross_refs:
  - audit-readiness-checklist
  - gdpr-dpia
recommended_with:
  - audit-readiness-checklist
requires: []
sections:
  - Vendor Overview
  - Risk Classification
  - Due Diligence Assessment
  - Security Assessment
  - Contractual Safeguards
  - Ongoing Monitoring
  - Risk Decision
---

# Vendor Risk Assessment: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}

---

## Vendor Overview

| Attribute | Detail |
|-----------|--------|
| **Vendor Name** | *[Legal entity name]* |
| **Service Provided** | *[Description of service/product]* |
| **Business Owner** | *[Internal owner/sponsor]* |
| **Contract Value** | *[$X / annual]* |
| **Data Access** | *[Yes — describe / No]* |
| **Data Types** | *[PII, PHI, financial, confidential, public]* |
| **System Access** | *[Yes — describe / No]* |
| **Sub-processors** | *[Yes — list / No / Unknown]* |

---

## Risk Classification

### Inherent Risk Tier

| Factor | Assessment | Score |
|--------|-----------|-------|
| Data sensitivity | *[None / Low / Medium / High / Critical]* | *[1–5]* |
| Data volume | *[None / Low / Medium / High]* | *[1–5]* |
| System access level | *[None / Read / Read-Write / Admin]* | *[1–5]* |
| Business criticality | *[Low / Medium / High / Critical]* | *[1–5]* |
| Replaceability | *[Easy / Moderate / Difficult / Sole source]* | *[1–5]* |
| **Inherent Risk Tier** | | **[Critical / High / Medium / Low]** |

### Due Diligence Required by Tier

| Tier | Assessment Level | Review Frequency |
|------|-----------------|-----------------|
| Critical | Full assessment + on-site (if applicable) | Annual |
| High | Full questionnaire + evidence review | Annual |
| Medium | Standard questionnaire | Biennial |
| Low | Self-attestation | Triennial |

---

## Due Diligence Assessment

### Information Security

| # | Control Area | Question | Response | Evidence | Rating |
|---|-------------|----------|----------|----------|--------|
| 1 | Encryption | Data encrypted at rest and in transit? | *[Yes/No/Partial]* | *[Cert/Policy ref]* | *[✓/⚠/✗]* |
| 2 | Access control | MFA implemented for admin access? | *[Y/N/P]* | *[Evidence]* | *[Rating]* |
| 3 | Vulnerability mgmt | Regular vulnerability scanning? | *[Y/N/P]* | *[Evidence]* | *[Rating]* |
| 4 | Incident response | Documented incident response plan? | *[Y/N/P]* | *[Evidence]* | *[Rating]* |
| 5 | Business continuity | BCP/DR plan tested annually? | *[Y/N/P]* | *[Evidence]* | *[Rating]* |

### Certifications & Audits

| Certification | Status | Expiration | Scope Covers Our Use |
|--------------|--------|-----------|---------------------|
| SOC 2 Type II | *[Current / Expired / None]* | *[Date]* | *[Yes / Partial / No]* |
| ISO 27001 | *[Current / Expired / None]* | *[Date]* | *[Yes / Partial / No]* |
| PCI-DSS | *[Current / Expired / None / N/A]* | *[Date]* | *[Yes / Partial / No]* |
| HITRUST | *[Current / Expired / None / N/A]* | *[Date]* | *[Yes / Partial / No]* |

{% if "hipaa" in compliance %}
### HIPAA Compliance
| Requirement | Status | Evidence |
|------------|--------|----------|
| BAA executed | *[Yes / No / In progress]* | *[Document ref]* |
| HIPAA risk assessment (vendor's) | *[Current / Outdated / None]* | *[Date]* |
| Breach notification provisions | *[In BAA / Separate agreement / None]* | *[Reference]* |
| Subcontractor BAAs | *[Confirmed / Unconfirmed]* | *[Evidence]* |
{% endif %}

{% if "sec_finra" in compliance %}
### Regulatory Compliance (Financial Services)
| Requirement | Status | Evidence |
|------------|--------|----------|
| SEC/FINRA vendor due diligence | *[Complete / Incomplete]* | *[Reference]* |
| Outsourcing notification (if required) | *[Filed / Not required]* | *[Reference]* |
| BCP covers vendor dependency | *[Yes / No]* | *[BCP section ref]* |
{% endif %}

---

## Security Assessment

### Risk Findings

| # | Finding | Severity | Remediation Required | Vendor Response |
|---|---------|----------|---------------------|----------------|
| 1 | *[Finding description]* | *[Critical / High / Medium / Low]* | *[Yes / Accepted risk]* | *[Vendor's response/timeline]* |

---

## Contractual Safeguards

| Safeguard | In Contract | Notes |
|-----------|-----------|-------|
| Data protection / security requirements | *[Yes / No]* | *[Clause ref]* |
| Breach notification SLA | *[Yes — X hours / No]* | *[Clause ref]* |
| Right to audit | *[Yes / No]* | *[Clause ref]* |
| Data return / destruction on termination | *[Yes / No]* | *[Clause ref]* |
| Insurance requirements (cyber liability) | *[Yes — $X / No]* | *[Clause ref]* |
| Sub-processor approval requirements | *[Yes / No]* | *[Clause ref]* |
| SLA with remedies | *[Yes / No]* | *[Clause ref]* |
| Indemnification for data breach | *[Yes / No]* | *[Clause ref]* |

---

## Ongoing Monitoring

| Activity | Frequency | Owner | Last Completed | Next Due |
|----------|-----------|-------|---------------|---------|
| Security questionnaire refresh | *[Annual]* | *[Vendor mgmt]* | *[Date]* | *[Date]* |
| SOC 2 / certification review | *[Annual]* | *[Security]* | *[Date]* | *[Date]* |
| Performance review (SLA metrics) | *[Quarterly]* | *[Business owner]* | *[Date]* | *[Date]* |
| Financial viability check | *[Annual]* | *[Procurement]* | *[Date]* | *[Date]* |

---

## Risk Decision

**Residual Risk Rating:** *[Critical / High / Medium / Low]*

**Decision:** *[Approve / Approve with Conditions / Reject]*

**Conditions (if applicable):**
1. *[Condition — e.g., "BAA must be executed before go-live"]*
2. *[Condition]*

---

## Approval

- **Assessor (Name/Title):** ____________________  **Date:** __________
- **Security / Compliance (Name/Title):** ____________________  **Date:** __________
- **Business Owner (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `vendor-risk-assessment`.*
