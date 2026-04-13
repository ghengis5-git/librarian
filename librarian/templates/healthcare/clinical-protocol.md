---
template_id: clinical-protocol
display_name: Clinical Protocol
preset: healthcare
description: >-
  Standardized clinical protocol for patient care procedures, treatment guidelines,
  and clinical decision-making. Covers indications, contraindications, procedure steps,
  monitoring requirements, and documentation standards.
suggested_tags: [clinical, protocol, patient-care]
suggested_folder: clinical-protocols/
typical_cross_refs:
  - policy-document
  - quality-improvement-plan
  - incident-report
recommended_with:
  - policy-document
  - credentialing-checklist
requires: []
sections:
  - Purpose & Scope
  - Clinical Indications
  - Contraindications & Precautions
  - Required Qualifications
  - Equipment & Supplies
  - Procedure Steps
  - Monitoring & Assessment
  - Documentation Requirements
  - Complications & Emergency Response
  - References & Evidence Base
---

# Clinical Protocol: {{title}}

**Document ID:** {{title}} / {{version}}
**Effective Date:** {{date}}
**Author:** {{author}}
**Status:** {{status}}
**Review Cycle:** Annual

---

## Purpose & Scope

*[Define the clinical purpose of this protocol and the patient populations, settings, and staff to whom it applies.]*

- **Applicable Settings:** *[Inpatient / Outpatient / ED / OR / ICU / All]*
- **Target Population:** *[Age range, diagnosis, acuity level]*
- **Responsible Departments:** *[List departments with implementation responsibility]*

---

## Clinical Indications

*[List the clinical conditions, diagnoses, or situations in which this protocol should be initiated.]*

| Indication | ICD-10 Code | Notes |
|-----------|-------------|-------|
| *[Indication 1]* | *[Code]* | *[Inclusion/exclusion criteria]* |
| *[Indication 2]* | *[Code]* | *[Inclusion/exclusion criteria]* |

---

## Contraindications & Precautions

### Absolute Contraindications
- *[Contraindication 1]*
- *[Contraindication 2]*

### Relative Contraindications / Precautions
- *[Precaution 1 — describe risk-benefit considerations]*
- *[Precaution 2]*

---

## Required Qualifications

| Role | Minimum Credential | Supervision Required |
|------|-------------------|---------------------|
| *[Primary provider]* | *[MD/DO/NP/PA]* | *[Yes/No — describe]* |
| *[Assisting staff]* | *[RN/LPN/MA/RT]* | *[Yes/No — describe]* |

{% if "hipaa" in compliance %}
### HIPAA Workforce Requirements
All staff executing this protocol must have current HIPAA training and signed confidentiality agreements. PHI access is limited to minimum necessary for clinical care.

- **PHI Access Level:** *[Full chart / Limited to procedure record / De-identified]*
- **Minimum Necessary Standard:** *[Define what PHI elements are required]*
{% endif %}

---

## Equipment & Supplies

| Item | Specification | Quantity | Location |
|------|--------------|----------|----------|
| *[Equipment 1]* | *[Model/spec]* | *[X]* | *[Storage location]* |
| *[Supply 1]* | *[Spec/size]* | *[X per procedure]* | *[Par location]* |

---

## Procedure Steps

### Pre-Procedure
1. Verify patient identity using two identifiers (name + DOB or MRN)
2. Confirm informed consent is signed and in the chart
3. Perform time-out (patient, procedure, site verification)
4. *[Additional pre-procedure steps]*

### Procedure
1. *[Step 1 — include specific parameters, dosages, or settings]*
2. *[Step 2]*
3. *[Step 3]*
4. *[Step 4]*

### Post-Procedure
1. *[Monitoring parameters and frequency]*
2. *[Documentation requirements]*
3. *[Patient education and discharge criteria]*

---

## Monitoring & Assessment

| Parameter | Frequency | Acceptable Range | Escalation Trigger |
|-----------|-----------|-----------------|-------------------|
| *[Vital signs]* | *[Q15 min x 1hr]* | *[Define range]* | *[Define threshold]* |
| *[Lab value]* | *[At baseline + 4hr]* | *[Define range]* | *[Define threshold]* |

---

## Documentation Requirements

- [ ] Informed consent signed and scanned
- [ ] Time-out documented
- [ ] Procedure note completed within *[X hours]*
- [ ] Post-procedure assessment documented
- [ ] Patient/family education documented
- [ ] Complications (if any) documented per incident reporting policy

{% if "hipaa" in compliance %}
### PHI Documentation Standards
- All documentation must comply with HIPAA minimum necessary standard
- Electronic records must be entered in the designated EHR module
- Paper records (if any) must be stored in locked cabinets and scanned within 24 hours
- Access audit logs are maintained per HIPAA Security Rule requirements
{% endif %}

{% if "iso_9001" in compliance %}
### ISO 9001 Document Control (§ 7.5)
This protocol is a controlled document. Changes require approval through the document control process. Obsolete versions must be removed from clinical areas within 48 hours of new version release.

| Control | Requirement | Status |
|---------|-------------|--------|
| Approval Authority | *[Medical Director / Department Chief]* | |
| Review Cycle | Annual or after sentinel event | |
| Distribution | Controlled — clinical area heads | |
{% endif %}

---

## Complications & Emergency Response

| Complication | Signs/Symptoms | Immediate Action | Escalation |
|-------------|---------------|-----------------|------------|
| *[Complication 1]* | *[Signs]* | *[Action]* | *[Call RRT / Code Blue / etc.]* |
| *[Complication 2]* | *[Signs]* | *[Action]* | *[Notification chain]* |

**Emergency Contact:** *[Attending physician / On-call specialist / Rapid Response Team]*

---

## References & Evidence Base

1. *[Clinical guideline or journal citation]*
2. *[Professional society recommendation]*
3. *[Regulatory requirement (CMS, Joint Commission, state DOH)]*
4. *[Internal policy reference]*

**Evidence Level:** *[I / II / III / IV / V — describe evidence grading system used]*

---

## Approval & Sign-Off

- **Author (Name/Title):** ____________________  **Date:** __________
- **Medical Director (Name/Title):** ____________________  **Date:** __________
- **Quality/Compliance (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `clinical-protocol`.*
