---
template_id: credentialing-checklist
display_name: Credentialing Checklist
preset: healthcare
description: >-
  Provider credentialing and privileging checklist for medical staff appointments.
  Covers application requirements, primary source verification, committee review,
  and reappointment tracking. Aligns with Joint Commission MS standards and CMS CoP.
suggested_tags: [credentialing, medical-staff, privileging]
suggested_folder: credentialing/
typical_cross_refs:
  - policy-document
  - clinical-protocol
recommended_with:
  - policy-document
requires: []
sections:
  - Applicant Information
  - Application Checklist
  - Primary Source Verification
  - Query & Background Checks
  - Committee Review
  - Privilege Delineation
  - Reappointment Tracking
---

# Credentialing Checklist: {{title}}

**Applicant:** *[Provider Name, Degree]*
**Application Date:** {{date}}
**Credentialing Coordinator:** {{author}}
**Status:** {{status}}
**Version:** {{version}}

---

## Applicant Information

| Field | Value |
|-------|-------|
| Full Legal Name | *[Last, First, Middle]* |
| Degree(s) | *[MD / DO / DPM / DDS / PhD / NP / PA / CRNA / etc.]* |
| Specialty | *[Primary specialty]* |
| Sub-specialty | *[If applicable]* |
| NPI | *[10-digit NPI]* |
| DEA Number | *[If applicable]* |
| State License # | *[License number, state, expiration]* |
| Board Certification | *[Board, certification status, expiration]* |
| Requested Category | *[Active / Courtesy / Consulting / Allied Health / Telemedicine]* |

---

## Application Checklist

| # | Item | Required | Received | Date | Notes |
|---|------|----------|----------|------|-------|
| 1 | Completed application form (signed) | Yes | ☐ | | |
| 2 | Curriculum vitae (current) | Yes | ☐ | | |
| 3 | Copy of medical degree/diploma | Yes | ☐ | | |
| 4 | Copy of current state license(s) | Yes | ☐ | | |
| 5 | DEA certificate (if prescribing) | *[Yes/N/A]* | ☐ | | |
| 6 | Board certification documentation | Yes | ☐ | | |
| 7 | Malpractice insurance face sheet | Yes | ☐ | | Min: $*[X]*/$*[Y]* |
| 8 | Malpractice claims history (5 yr) | Yes | ☐ | | |
| 9 | Privilege request form (completed) | Yes | ☐ | | |
| 10 | Professional references (3 minimum) | Yes | ☐ | | |
| 11 | Photo ID (government-issued) | Yes | ☐ | | |
| 12 | Work history (5 yr, no gaps > 6 mo) | Yes | ☐ | | |
| 13 | Attestation questions (signed) | Yes | ☐ | | |
| 14 | HIPAA confidentiality agreement | Yes | ☐ | | |
| 15 | Conflict of interest disclosure | Yes | ☐ | | |

---

## Primary Source Verification

| # | Verification Item | Source | Status | Date Verified | Verifier |
|---|-------------------|--------|--------|--------------|----------|
| 1 | Medical education | *[ECFMG / School registrar]* | ☐ Complete | | |
| 2 | Residency/fellowship | *[Training program]* | ☐ Complete | | |
| 3 | State medical license | *[State board website]* | ☐ Complete | | |
| 4 | Board certification | *[ABMS / AOA / specialty board]* | ☐ Complete | | |
| 5 | DEA registration | *[NTIS / DEA]* | ☐ Complete | | |
| 6 | Hospital affiliations (5 yr) | *[Each hospital]* | ☐ Complete | | |
| 7 | Professional references | *[Direct contact]* | ☐ Complete | | |
| 8 | Work history verification | *[Employer]* | ☐ Complete | | |

{% if "hipaa" in compliance %}
### HIPAA Verification
- [ ] HIPAA training certificate on file (current year)
- [ ] Signed confidentiality/non-disclosure agreement
- [ ] ePHI access role assignment appropriate to privileges
{% endif %}

---

## Query & Background Checks

| # | Query | Status | Date | Result | Notes |
|---|-------|--------|------|--------|-------|
| 1 | NPDB (National Practitioner Data Bank) | ☐ Complete | | *[No reports / Reports found — see attachment]* | |
| 2 | OIG Exclusion List (LEIE) | ☐ Complete | | *[Not excluded / Excluded — STOP]* | |
| 3 | SAM.gov (System for Award Mgmt) | ☐ Complete | | *[Clear / Debarred — STOP]* | |
| 4 | State Medicaid exclusion list | ☐ Complete | | *[Clear / Excluded]* | |
| 5 | State license disciplinary check | ☐ Complete | | *[Clean / Actions found]* | |
| 6 | Criminal background check | ☐ Complete | | *[Clear / Findings — review required]* | |
| 7 | CMS Medicare opt-out check | ☐ Complete | | *[Not opted out / Opted out]* | |
| 8 | Sex offender registry | ☐ Complete | | *[Clear / Match — STOP]* | |

**Red Flag Items:** *[Any item marked "found" or "excluded" requires immediate escalation to Medical Staff Office Director and Legal.]*

---

## Committee Review

| Committee | Date Reviewed | Action | Chair Signature |
|-----------|-------------|--------|----------------|
| Department Chair review | *[Date]* | *[Recommend / Defer / Deny]* | ________________ |
| Credentials Committee | *[Date]* | *[Recommend / Defer / Deny]* | ________________ |
| Medical Executive Committee | *[Date]* | *[Approve / Defer / Deny]* | ________________ |
| Board of Directors/Trustees | *[Date]* | *[Approve / Deny]* | ________________ |

### Provisional Period
- **Start Date:** *[Date]*
- **End Date:** *[Date — typically 12–24 months]*
- **Proctoring Required:** *[Yes — X cases / No]*
- **Proctor Assigned:** *[Name, if applicable]*

---

## Privilege Delineation

### Core Privileges Granted

| Privilege Category | Granted | Conditions/Limitations |
|-------------------|---------|----------------------|
| *[Category 1: e.g., "General Internal Medicine"]* | ☐ | *[None / Specific limitations]* |
| *[Category 2: e.g., "Critical Care"]* | ☐ | *[Proctoring for first X cases]* |
| *[Category 3: e.g., "Moderate Sedation"]* | ☐ | *[Current ACLS required]* |

### Special Privileges Requested

| Privilege | Case Volume Required | Evidence Submitted | Approved |
|-----------|---------------------|-------------------|----------|
| *[Special privilege 1]* | *[X cases/yr]* | *[Log / Letter]* | ☐ |

---

## Reappointment Tracking

| Field | Value |
|-------|-------|
| Initial appointment date | *[Date]* |
| Current appointment expires | *[Date]* |
| Reappointment cycle | *[2 years / per bylaws]* |
| Next reappointment due | *[Date — 120 days before expiration]* |
| OPPE reviews completed | *[Dates of ongoing professional practice evaluations]* |
| FPPE completed | *[Date — focused professional practice evaluation for provisional]* |

### Expiring Items Monitor

| Item | Expiration Date | Renewal Reminder | Renewed |
|------|----------------|-----------------|---------|
| State license | *[Date]* | *[90 days prior]* | ☐ |
| DEA | *[Date]* | *[90 days prior]* | ☐ |
| Board certification | *[Date]* | *[180 days prior]* | ☐ |
| Malpractice insurance | *[Date]* | *[60 days prior]* | ☐ |
| BLS/ACLS/PALS | *[Date]* | *[90 days prior]* | ☐ |

---

## Credentialing File Completion

- **File complete?** *[Yes / No — list missing items]*
- **Credential verification organization (CVO) used?** *[Yes — name / No — in-house]*
- **File reviewed by:** *[Name/Title]*  **Date:** *[Date]*

---

*Document generated by librarian v{{librarian_version}} from template `credentialing-checklist`.*
