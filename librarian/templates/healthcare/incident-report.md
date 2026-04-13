---
template_id: incident-report
display_name: Incident Report
preset: healthcare
description: >-
  Healthcare incident/event report for patient safety events, near misses, and adverse
  occurrences. Covers event description, severity classification, contributing factors,
  immediate actions, root cause analysis, and corrective action plan. Supports Joint
  Commission sentinel event reporting and state DOH requirements.
suggested_tags: [incident, safety, event-report]
suggested_folder: incident-reports/
typical_cross_refs:
  - clinical-protocol
  - quality-improvement-plan
  - policy-document
recommended_with:
  - quality-improvement-plan
requires: []
sections:
  - Event Summary
  - Event Classification
  - Event Details
  - Contributing Factors
  - Immediate Actions Taken
  - Root Cause Analysis
  - Corrective Action Plan
  - Reporting Requirements
  - Follow-Up & Closure
---

# Incident Report: {{title}}

**Report ID:** *[IR-XXXX]*
**Date of Event:** *[YYYY-MM-DD]*
**Date of Report:** {{date}}
**Reporter:** {{author}}
**Status:** {{status}}
**Version:** {{version}}

---

## Event Summary

*[2–3 sentence factual summary of the event. What happened, to whom (no patient name — use MRN or de-identified reference), when, and where.]*

---

## Event Classification

| Attribute | Classification |
|-----------|---------------|
| **Event Type** | *[Adverse event / Near miss / No harm event / Sentinel event / Hazardous condition]* |
| **Severity** | *[1-Catastrophic / 2-Major / 3-Moderate / 4-Minor / 5-Insignificant]* |
| **Harm Level** | *[Death / Severe / Moderate / Mild / No harm / N/A (near miss)]* |
| **Category** | *[Medication / Fall / Procedure / Diagnostic / Device / Infection / Other]* |
| **Unit/Location** | *[Department, unit, room number]* |
| **Patient Population** | *[Adult / Pediatric / Neonatal / Obstetric / Behavioral health]* |

### Sentinel Event Determination
- **Meets Joint Commission sentinel event criteria?** *[Yes / No]*
- **Meets state mandatory reporting criteria?** *[Yes / No — cite regulation]*
- **Root Cause Analysis required?** *[Yes (sentinel/serious) / No (near miss — aggregate review)]*

---

## Event Details

### Timeline

| Time | Event |
|------|-------|
| *[HH:MM]* | *[What happened — factual, no attribution]* |
| *[HH:MM]* | *[Next event in sequence]* |
| *[HH:MM]* | *[Discovery / Recognition]* |
| *[HH:MM]* | *[Response initiated]* |

### Persons Involved

| Role | Present | Notified | Time Notified |
|------|---------|----------|---------------|
| *[Primary nurse]* | *[Yes/No]* | *[Yes]* | *[HH:MM]* |
| *[Attending physician]* | *[Yes/No]* | *[Yes]* | *[HH:MM]* |
| *[Charge nurse / Supervisor]* | *[Yes/No]* | *[Yes]* | *[HH:MM]* |
| *[Risk management]* | N/A | *[Yes]* | *[HH:MM]* |
| *[Patient/family]* | N/A | *[Yes/No]* | *[HH:MM / N/A]* |

{% if "hipaa" in compliance %}
### HIPAA Considerations
- **PHI in this report:** This report contains protected health information. Access is restricted to risk management, quality, legal, and individuals with a need to know.
- **Patient Identifiers:** Use MRN only. Do not include patient name in this report.
- **Disclosure:** If disclosed externally (state DOH, Joint Commission), follow minimum necessary standard.
{% endif %}

---

## Contributing Factors

| Factor Category | Description | Contributing? |
|----------------|-------------|---------------|
| **Communication** | *[Handoff gap, order ambiguity, language barrier]* | *[Yes/No/Unknown]* |
| **Staffing** | *[Ratio, skill mix, fatigue, float staff]* | *[Yes/No/Unknown]* |
| **Training** | *[Knowledge gap, competency, orientation]* | *[Yes/No/Unknown]* |
| **Equipment** | *[Malfunction, unavailable, unfamiliar device]* | *[Yes/No/Unknown]* |
| **Environment** | *[Lighting, noise, interruptions, layout]* | *[Yes/No/Unknown]* |
| **Process/Policy** | *[Unclear policy, workaround, missing protocol]* | *[Yes/No/Unknown]* |
| **Patient Factors** | *[Acuity, cognition, compliance, complexity]* | *[Yes/No/Unknown]* |

---

## Immediate Actions Taken

1. *[Action 1: e.g., "Patient assessed — vitals stable, no immediate harm"]*
2. *[Action 2: e.g., "Attending physician notified at HH:MM"]*
3. *[Action 3: e.g., "Patient/family informed of event per disclosure policy"]*
4. *[Action 4: e.g., "Equipment sequestered for biomedical inspection"]*
5. *[Action 5: e.g., "Risk management notified"]*

---

## Root Cause Analysis

### Method: *[5 Whys / Fishbone / FMEA / Comprehensive RCA]*

### Findings

| # | Root Cause | Category | Preventable |
|---|-----------|----------|------------|
| 1 | *[Root cause description]* | *[System / Process / Human / Equipment]* | *[Yes/No]* |
| 2 | *[Root cause description]* | *[Category]* | *[Yes/No]* |

### RCA Team

| Name | Role | Date of RCA |
|------|------|-------------|
| *[Name]* | *[Title]* | *[Date]* |

---

## Corrective Action Plan

| # | Action | Owner | Deadline | Status | Effectiveness Check |
|---|--------|-------|----------|--------|-------------------|
| 1 | *[Corrective action]* | *[Name]* | *[Date]* | *[Open/In progress/Complete]* | *[How verified]* |
| 2 | *[Corrective action]* | *[Name]* | *[Date]* | *[Status]* | *[How verified]* |

### Strength of Corrective Actions
- **Strong (system-level):** *[e.g., "Forcing function, automation, physical barrier"]*
- **Intermediate (process-level):** *[e.g., "Checklist, standardized protocol, redundancy"]*
- **Weak (individual-level):** *[e.g., "Education, counseling, policy reminder"]* — insufficient alone

---

## Reporting Requirements

| Regulatory Body | Required | Deadline | Filed |
|----------------|----------|----------|-------|
| State Department of Health | *[Yes/No]* | *[X hours/days]* | *[Yes/No/N/A]* |
| Joint Commission (sentinel event) | *[Yes/No]* | *[45 business days]* | *[Yes/No/N/A]* |
| CMS / Medicare | *[Yes/No]* | *[Per CoP]* | *[Yes/No/N/A]* |
| FDA (device/drug) | *[Yes/No]* | *[MedWatch]* | *[Yes/No/N/A]* |
| Malpractice carrier | *[Yes/No]* | *[Per policy]* | *[Yes/No/N/A]* |

---

## Follow-Up & Closure

### Patient Follow-Up
- **Clinical follow-up completed?** *[Yes/No — describe]*
- **Disclosure conversation with patient/family?** *[Yes/No — date, participants]*
- **Ongoing monitoring needed?** *[Yes/No — describe plan]*

### Report Closure
- **All corrective actions verified?** *[Yes/No]*
- **Effectiveness monitoring period:** *[X months post-implementation]*
- **Report closed by:** *[Name/Title]*  **Date:** *[Date]*

---

## Approval

- **Reporter (Name/Title):** ____________________  **Date:** __________
- **Risk Manager (Name/Title):** ____________________  **Date:** __________
- **Medical Director (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `incident-report`.*
