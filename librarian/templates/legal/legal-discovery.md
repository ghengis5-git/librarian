---
template_id: legal-discovery
display_name: Legal Discovery Plan
preset: legal
description: Litigation discovery plan covering preservation, custodians, ESI collection, search terms, privilege review, production, and chain of custody
suggested_tags: [legal, discovery, litigation, ediscovery]
suggested_folder: legal/discovery/
typical_cross_refs: [legal-review, contract-summary, nda-tracker]
recommended_with: [legal-review, regulatory-compliance-checklist]
requires: []
sections:
  - Matter Summary
  - Litigation Hold & Preservation
  - Custodians & Data Sources
  - ESI Collection Plan
  - Search Terms & Culling Strategy
  - Privilege Review Protocol
  - Production Plan
  - Chain of Custody
  - Meet-and-Confer Record
  - Timeline & Milestones
  - Privilege Notice
---

# Legal Discovery Plan — {{title}}

**Date:** {{date}}  
**Author:** {{author}}  
**Version:** {{version}}  
**Classification:** {{classification}}  

---

## Matter Summary

*[Provide a 2-3 paragraph overview of the underlying matter: case caption, court, docket number, parties, claims, defenses, and the specific discovery obligations driving this plan. Reference the scheduling order or discovery cutoff if one has been entered.]*

- **Case Caption:** *[Plaintiff v. Defendant]*
- **Court / Forum:** *[Jurisdiction and court]*
- **Docket / Case No.:** *[Case number]*
- **Discovery Cutoff:** *[Date from scheduling order]*
- **Producing Party Role:** Plaintiff / Defendant / Third Party

---

## Litigation Hold & Preservation

### Hold Scope

*[Describe the triggering event (complaint filed, demand letter, regulatory inquiry, reasonable anticipation of litigation) and the date preservation obligations attached. Identify the universe of documents, communications, and data covered.]*

| Hold Element | Status | Owner | Date |
|--------------|--------|-------|------|
| Hold notice issued | *[Date]* | *[Custodian of record]* | *[Date]* |
| Affected systems identified | *[Status]* | *[IT / eDiscovery lead]* | *[Date]* |
| Auto-delete suspensions applied | *[Status]* | *[IT lead]* | *[Date]* |
| Backup tape rotation halted | *[Status]* | *[IT lead]* | *[Date]* |
| Hold acknowledgment collected | *[%]* | *[Legal ops]* | *[Date]* |

### Preservation Risks

*[Identify any systems, custodians, or data types where preservation is imperfect or contested. Document remediation steps and whether spoliation motions are anticipated.]*

---

## Custodians & Data Sources

### Key Custodians

| Custodian | Role | Business Unit | Hold Acknowledged | Interview Scheduled |
|-----------|------|---------------|-------------------|---------------------|
| *[Name]* | *[Title]* | *[Unit]* | Yes/No | *[Date]* |
| *[Name]* | *[Title]* | *[Unit]* | Yes/No | *[Date]* |
| *[Name]* | *[Title]* | *[Unit]* | Yes/No | *[Date]* |

### Data Source Inventory

| Source | Type | Custodian Scope | Est. Volume | Collection Method |
|--------|------|-----------------|-------------|-------------------|
| Email server | Mailbox | *[All / named]* | *[GB]* | *[Forensic image / targeted export]* |
| File shares | Unstructured | *[Paths]* | *[GB]* | *[Robocopy / forensic]* |
| Collaboration (Slack/Teams) | Chat | *[Channels / DMs]* | *[GB]* | *[Vendor export]* |
| Cloud storage (GDrive/OneDrive) | Unstructured | *[Accounts]* | *[GB]* | *[Admin console export]* |
| Mobile devices | Phone / tablet | *[Named custodians]* | *[N devices]* | *[Cellebrite / MDM]* |
| Structured databases | Relational / NoSQL | *[Tables / schemas]* | *[Rows]* | *[Query export]* |

---

## ESI Collection Plan

### Collection Methodology

*[Describe the collection approach: forensic imaging vs. targeted collection, live vs. offline, on-premise vs. cloud. Identify vendor(s), tooling, and hash algorithms used for verification.]*

- **Collection Vendor:** *[Name]*
- **Tools:** *[Relativity, Nuix, Cellebrite, native admin consoles, etc.]*
- **Hash Algorithm:** SHA-256
- **Verification Protocol:** *[Pre- and post-collection hash comparison]*

### Metadata Preservation

*[List the metadata fields that must be preserved through collection and processing: sender/recipient, date sent/received, custodian, file path, parent/child relationships, hash values, etc.]*

{% if "hipaa" in compliance %}
### Protected Health Information Handling

- **PHI Identification:** *[Protocol for flagging records containing protected health information]*
- **Minimum Necessary Standard:** *[How the collection scope is narrowed to comply with HIPAA's minimum necessary rule]*
- **Business Associate Agreements:** *[Confirm BAAs in place with all collection and review vendors]*
- **Encryption in Transit & at Rest:** AES-256 or equivalent
- **Access Logs:** *[Audit trail retention for all PHI access during review]*
{% endif %}

{% if "sec_finra" in compliance %}
### Securities Records Retention Interplay

- **SEC Rule 17a-4 Compliance:** *[Confirm WORM storage or equivalent for records subject to 17a-4]*
- **FINRA 4511 Retention:** *[Identify records subject to 3-year and 6-year retention rules]*
- **Restricted Period Considerations:** *[Document any blackout or restricted period affecting custodian access]*
{% endif %}

{% if "dod_5200" in compliance %}
### Classified Information Handling

- **Classification Review:** *[Protocol for identifying classified or controlled unclassified information (CUI) in the collection]*
- **Cleared Personnel:** *[Confirm all reviewers hold appropriate clearance]*
- **Classified Storage & Transmission:** *[SCIF, SIPRNet, or equivalent handling requirements]*
- **Declassification / Redaction:** *[Coordinate with original classification authority]*
{% endif %}

---

## Search Terms & Culling Strategy

### Proposed Search Terms

| Term / Phrase | Rationale | Est. Hit Count | Status |
|---------------|-----------|----------------|--------|
| *[Term 1]* | *[Why this term is reasonably calculated to find responsive ESI]* | *[N docs]* | Proposed / Agreed / Disputed |
| *[Term 2]* | *[Rationale]* | *[N docs]* | Proposed / Agreed / Disputed |
| *[Term 3]* | *[Rationale]* | *[N docs]* | Proposed / Agreed / Disputed |

### Culling Parameters

- **Date Range:** *[Start - End]*
- **File Type Exclusions:** *[Executables, system files, known-file-filter (NIST NSRL), etc.]*
- **De-duplication:** Global MD5 + SHA-256 across all custodians
- **Email Threading:** *[Most-inclusive threading applied before review]*
- **Technology-Assisted Review (TAR):** *[TAR 1.0 / TAR 2.0 / none. If used, describe seed set, validation, recall targets.]*

---

## Privilege Review Protocol

### Privilege Categories

- Attorney-Client Privilege
- Work Product Doctrine
- Joint Defense / Common Interest
- Self-Critical Analysis (jurisdiction-dependent)
- {% if "hipaa" in compliance %}Psychotherapist-Patient Privilege (where applicable){% endif %}

### Review Workflow

1. **First-Pass Review:** *[Contract reviewers or TAR flags potentially privileged docs]*
2. **Second-Pass (Privilege QC):** *[Supervising attorney confirms privilege calls]*
3. **Privilege Log Entry:** *[For every withheld or redacted doc: date, author, recipients, subject, privilege basis]*
4. **Clawback Protocol:** *[FRE 502(d) order or equivalent; procedure for inadvertent disclosure]*

### Privilege Log Template

| Bates Range | Date | Author | Recipients | Subject / Type | Privilege Basis |
|-------------|------|--------|------------|----------------|-----------------|
| *[LIT-000001 – LIT-000003]* | *[Date]* | *[Name]* | *[Names]* | *[Description]* | AC / WP |

---

## Production Plan

### Production Format

- **Image Format:** Single-page TIFF / multi-page PDF / native
- **Text:** Extracted text with OCR for image-only documents
- **Metadata Load File:** *[.dat, Concordance, Relativity-compatible]*
- **Bates Numbering:** *[Prefix-NNNNNN format, with confidentiality designation endorsements]*
- **Confidentiality Designations:** Public / Confidential / Attorneys' Eyes Only / Highly Confidential
- **Redaction Protocol:** *[Privilege, PII, trade secret, third-party confidentiality]*

### Production Schedule

| Production Volume | Scope | Est. Doc Count | Target Date |
|-------------------|-------|----------------|-------------|
| Vol. 001 | *[Initial production per protective order]* | *[N]* | *[Date]* |
| Vol. 002 | *[Rolling production]* | *[N]* | *[Date]* |
| Vol. 003 | *[Final production]* | *[N]* | *[Date]* |

---

## Chain of Custody

### Custody Log

| Date | Evidence Item | Transferred From | Transferred To | Hash (SHA-256) | Notes |
|------|---------------|------------------|----------------|----------------|-------|
| *[Date]* | *[Device / dataset]* | *[Custodian / IT]* | *[Collection vendor]* | *[Hash]* | *[Method / location]* |
| *[Date]* | *[Device / dataset]* | *[Vendor]* | *[Review platform]* | *[Hash]* | *[Ingest confirmation]* |

### Storage & Access Controls

- **Primary Storage:** *[Vendor-hosted review platform with access logs]*
- **Backup Copies:** *[Location, encryption, retention]*
- **Access Authorization:** *[Named individuals, role-based]*
- **Audit Trail Retention:** Duration of matter + *[N years post-resolution]*

---

## Meet-and-Confer Record

### Key Discussions

| Date | Participants | Topic | Outcome / Agreement |
|------|--------------|-------|---------------------|
| *[Date]* | *[Counsel for all parties]* | Scope of custodians | *[Stipulation or dispute]* |
| *[Date]* | *[Counsel for all parties]* | Search term negotiation | *[Agreed terms, disputed terms]* |
| *[Date]* | *[Counsel for all parties]* | Production format | *[Agreed protocol]* |
| *[Date]* | *[Counsel for all parties]* | Privilege / clawback | *[FRE 502(d) order draft status]* |

### Outstanding Disputes

*[List any discovery disputes heading toward motion practice: scope objections, relevance challenges, privilege disputes, cost-shifting arguments, etc. Note target motion deadlines and meet-and-confer continuations.]*

---

## Timeline & Milestones

| Milestone | Target Date | Responsible Party | Status |
|-----------|-------------|-------------------|--------|
| Litigation hold issued | *[Date]* | *[Lead counsel]* | Complete / In Progress / Pending |
| Custodian interviews complete | *[Date]* | *[Case team]* | Complete / In Progress / Pending |
| Collection complete | *[Date]* | *[Vendor]* | Complete / In Progress / Pending |
| Search-term agreement | *[Date]* | *[Opposing counsel]* | Complete / In Progress / Pending |
| First review pass complete | *[Date]* | *[Review team]* | Complete / In Progress / Pending |
| Privilege log delivered | *[Date]* | *[Privilege QC lead]* | Complete / In Progress / Pending |
| Initial production (Vol. 001) | *[Date]* | *[Case team]* | Complete / In Progress / Pending |
| Substantial completion | *[Date]* | *[Case team]* | Complete / In Progress / Pending |
| Discovery cutoff | *[Date per scheduling order]* | Court | *[Fixed]* |

---

## Privilege Notice

**ATTORNEY WORK PRODUCT — PREPARED IN ANTICIPATION OF LITIGATION**

This discovery plan is prepared by or at the direction of counsel in anticipation of litigation and contains attorney work product and attorney-client privileged communications protected under applicable law (including Fed. R. Civ. P. 26(b)(3) and the attorney-client privilege). This document reflects the mental impressions, conclusions, opinions, and legal theories of counsel and is not subject to discovery. This document is intended solely for the use of the addressee and the case team and may not be disclosed, copied, or distributed to any third party — including opposing counsel, the court, or any regulator — without the express written consent of lead counsel.

**Distribution:** {{distribution_statement}}

---

*Document generated by librarian v{{librarian_version}} from template \`legal-discovery\`.*
