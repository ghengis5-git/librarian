---
template_id: data-classification-policy
display_name: Data Classification Policy
preset: security
description: >-
  Data classification policy defining sensitivity levels, handling requirements,
  labeling standards, and lifecycle management. Foundation for access control,
  encryption, and data loss prevention decisions.
suggested_tags: [security, data, classification, policy]
suggested_folder: docs/
typical_cross_refs:
  - access-control-matrix
  - security-architecture-review
  - threat-model
recommended_with:
  - access-control-matrix
requires: []
sections:
  - Purpose & Scope
  - Classification Levels
  - Classification Criteria
  - Handling Requirements
  - Labeling Standards
  - Data Lifecycle
  - Roles & Responsibilities
  - Exceptions
---

# Data Classification Policy: {{title}}

**Document ID:** {{title}} / {{version}}
**Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}

---

## Purpose & Scope

*[State the purpose of this policy: establish a framework for classifying data by sensitivity level, and define handling, storage, transmission, and disposal requirements for each level.]*

**Applies to:** All data created, received, maintained, or transmitted by the organization, in any format (electronic, paper, verbal).

---

## Classification Levels

| Level | Label | Description | Examples |
|-------|-------|------------|---------|
| **4 — Restricted** | RESTRICTED | Highest sensitivity. Unauthorized disclosure causes severe harm. | *[Trade secrets, encryption keys, M&A plans]* |
| **3 — Confidential** | CONFIDENTIAL | Sensitive business or personal data. Disclosure causes significant harm. | *[Financial records, employee PII, customer data]* |
| **2 — Internal** | INTERNAL USE ONLY | Not for public release but low harm if disclosed. | *[Internal memos, policies, org charts]* |
| **1 — Public** | PUBLIC | Approved for public release. No harm from disclosure. | *[Marketing materials, public website content]* |

{% if "dod_5200" in compliance %}
### DoD Classification Overlay
This policy maps to DoD 5200.01 classification levels:

| Organization Level | DoD Equivalent | Handling Standard |
|-------------------|---------------|-------------------|
| Restricted | TOP SECRET / SECRET | Per NISPOM Chapter 5 |
| Confidential | CONFIDENTIAL / CUI | Per 32 CFR Part 2002 |
| Internal | CUI / FOUO | Per agency CUI registry |
| Public | UNCLASSIFIED | Standard handling |
{% endif %}

{% if "hipaa" in compliance %}
### HIPAA Data Classification
| Data Type | Classification | HIPAA Category |
|-----------|---------------|---------------|
| PHI (identifiable health information) | Restricted | Protected Health Information |
| De-identified health data | Internal | Not subject to HIPAA Privacy Rule |
| Limited data set | Confidential | Requires Data Use Agreement |
{% endif %}

---

## Classification Criteria

### Decision Tree

1. Does the data contain personally identifiable information (PII)? → **Confidential minimum**
2. Is the data subject to regulatory requirements (HIPAA, SOX, GDPR, ITAR)? → **Classification per regulation**
3. Could disclosure cause competitive harm? → **Confidential or Restricted**
4. Is the data approved for public release? → **Public**
5. Default: **Internal Use Only**

### Regulatory Drivers

| Regulation | Data Type | Minimum Classification |
|-----------|-----------|----------------------|
| HIPAA | PHI / ePHI | Restricted |
| PCI-DSS | Cardholder data | Restricted |
| GDPR | EU personal data | Confidential |
| SOX | Financial controls data | Confidential |
| ITAR/EAR | Export-controlled technical data | Restricted |

{% if "sec_finra" in compliance %}
### SEC/FINRA Data Classification
| Data Type | Classification | Regulatory Basis |
|-----------|---------------|-----------------|
| Material non-public information (MNPI) | Restricted | SEC Rule 10b-5 |
| Client account information | Confidential | Reg S-P |
| Trading records | Confidential | SEC Rule 17a-4 |
| Research reports (pre-publication) | Restricted | FINRA Rule 2241 |
{% endif %}

---

## Handling Requirements

| Requirement | Public | Internal | Confidential | Restricted |
|------------|--------|----------|-------------|-----------|
| **Encryption at rest** | Optional | Optional | Required | Required (AES-256) |
| **Encryption in transit** | Optional | TLS | TLS 1.2+ | TLS 1.3 |
| **Access control** | None | Authentication | RBAC + need-to-know | RBAC + MFA + approval |
| **Storage** | Any | Approved systems | Approved + encrypted | Approved + encrypted + audited |
| **Sharing (internal)** | Unrestricted | Authenticated users | Need-to-know | Named recipients + NDA |
| **Sharing (external)** | Unrestricted | With approval | NDA + encryption | Legal approval + encryption |
| **Printing** | Unrestricted | Standard | Classified printer, collect immediately | Prohibited or secure print |
| **Mobile devices** | Allowed | Allowed (MDM) | MDM + encryption | Prohibited unless approved |
| **Cloud storage** | Approved services | Approved services | Approved + encrypted | Prohibited unless FedRAMP/approved |
| **Disposal** | Standard delete | Secure delete | Crypto-erase / NIST 800-88 | Crypto-erase + certificate |
| **Retention** | Per policy | Per policy | Per regulation or 7 years | Per regulation or 7 years |

---

## Labeling Standards

### Electronic Documents
- **Header/footer:** Classification label on every page
- **Email:** Subject line prefix: `[CLASSIFICATION]`
- **File naming:** Include classification in metadata or filename where feasible
- **Databases:** Classification column in data dictionary

### Physical Documents
- **Header/footer marking:** Top and bottom of every page
- **Cover sheet:** Classification label prominently displayed
- **Storage:** Locked cabinet (Confidential), safe (Restricted)

---

## Data Lifecycle

| Phase | Public | Internal | Confidential | Restricted |
|-------|--------|----------|-------------|-----------|
| **Creation** | No restrictions | Standard systems | Approved systems only | Approved + logged |
| **Storage** | Any | Approved | Encrypted | Encrypted + access-logged |
| **Use** | Unrestricted | Internal only | Need-to-know | Named users + MFA |
| **Sharing** | Open | Internal | NDA | Legal approval |
| **Archival** | Standard | Standard | Encrypted archive | Encrypted + access audit |
| **Destruction** | Delete | Secure delete | Crypto-erase | Crypto-erase + certificate |

---

## Roles & Responsibilities

| Role | Responsibility |
|------|---------------|
| **Data Owner** | Classify data, authorize access, review classification annually |
| **Data Custodian** | Implement controls per classification, manage storage/backup |
| **Data User** | Handle data per classification, report mishandling |
| **Security Team** | Define controls, audit compliance, respond to incidents |
| **Compliance** | Regulatory alignment, audit support, policy updates |

---

## Exceptions

- **Exception authority:** *[CISO / Security Committee]*
- **Request process:** Written request with risk assessment and compensating controls
- **Duration:** Maximum *[12 months]*, renewable with re-review
- **Documentation:** All exceptions logged in *[exception register]*

---

## Approval

- **Author (Name/Title):** ____________________  **Date:** __________
- **CISO (Name/Title):** ____________________  **Date:** __________
- **Executive Sponsor (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `data-classification-policy`.*
