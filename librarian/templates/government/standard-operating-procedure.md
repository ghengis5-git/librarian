---
template_id: standard-operating-procedure
display_name: Standard Operating Procedure
preset: government
description: >-
  Standard Operating Procedure (SOP) for government and military organizations.
  Covers step-by-step procedures, safety requirements, quality checks, and
  record-keeping. Formatted for controlled document environments.
suggested_tags: [sop, procedure, operations]
suggested_folder: procedures/
typical_cross_refs:
  - policy-directive
  - after-action-report
  - security-plan
recommended_with:
  - policy-directive
requires: []
sections:
  - Purpose
  - Scope
  - References
  - Definitions
  - Responsibilities
  - Safety & Precautions
  - Procedure
  - Quality Checks
  - Records & Documentation
  - Change History
---

# Standard Operating Procedure: {{title}}

**SOP Number:** *[SOP-XXXX]*
**Effective Date:** {{date}}
**Version:** {{version}}
**Author:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
{% endif %}

---

## Purpose

*[State the purpose of this SOP in 1–2 sentences. What process or task does it standardize?]*

---

## Scope

- **Applicable To:** *[Units, sections, offices]*
- **Personnel:** *[Roles that execute this procedure]*
- **Conditions:** *[When this SOP applies — routine operations, contingency, both]*
- **Exclusions:** *[What this SOP does not cover]*

---

## References

| Reference | Title | Relevance |
|-----------|-------|-----------|
| *[Directive #]* | *[Title]* | *[Governing policy]* |
| *[Regulation]* | *[Title]* | *[Regulatory requirement]* |
| *[Manual/TM]* | *[Title]* | *[Technical reference]* |

---

## Definitions

| Term | Definition |
|------|-----------|
| *[Term 1]* | *[Definition]* |
| *[Term 2]* | *[Definition]* |

---

## Responsibilities

| Role | Responsibility |
|------|---------------|
| *[Supervisor / OIC]* | *[Ensure compliance, authorize deviations, sign off]* |
| *[Operator / Technician]* | *[Execute procedure, document results, report anomalies]* |
| *[QA / Inspector]* | *[Verify completion, audit records, report findings]* |

---

## Safety & Precautions

### Personal Protective Equipment (PPE)
- *[PPE item 1 — when required]*
- *[PPE item 2 — when required]*

### Safety Warnings
- **WARNING:** *[Action or condition that could result in serious injury or death]*
- **CAUTION:** *[Action or condition that could result in minor injury or equipment damage]*
- **NOTE:** *[Essential information for safe/efficient procedure execution]*

### Emergency Procedures
*[If an emergency occurs during this procedure, execute the following:]*
1. *[Immediate action]*
2. *[Notification chain]*
3. *[Reference to emergency plan]*

---

## Procedure

### Pre-Procedure Checks

| # | Check | Standard | Verified |
|---|-------|----------|---------|
| 1 | *[Pre-check item]* | *[Acceptance criteria]* | ☐ |
| 2 | *[Pre-check item]* | *[Acceptance criteria]* | ☐ |

### Step-by-Step Procedure

**Step 1:** *[Action verb + specific instruction]*
- *[Sub-step or detail]*
- *[Expected result or indicator]*

**Step 2:** *[Action verb + specific instruction]*
- *[Sub-step or detail]*
- *[Expected result or indicator]*

**Step 3:** *[Action verb + specific instruction]*
- *[Sub-step or detail]*

**Step 4:** *[Action verb + specific instruction]*

**Step 5:** *[Action verb + specific instruction]*

{% if "dod_5200" in compliance %}
### Classified Material Handling Steps
If this procedure involves classified material:
1. Verify personnel clearances before granting access
2. Log classified material receipt/transfer on accountability register
3. Process in approved secure area only
4. Return classified material to approved storage upon completion
5. Document any spills, compromises, or anomalies per local security SOP
{% endif %}

### Post-Procedure Actions

| # | Action | Responsible | Complete |
|---|--------|-------------|---------|
| 1 | *[Clean-up / reset]* | *[Role]* | ☐ |
| 2 | *[Documentation]* | *[Role]* | ☐ |
| 3 | *[Notification / handoff]* | *[Role]* | ☐ |

---

## Quality Checks

| # | Checkpoint | Standard | Method | Frequency |
|---|-----------|----------|--------|-----------|
| 1 | *[Quality item]* | *[Acceptance criteria]* | *[Inspection / Test / Review]* | *[Each time / Daily / Weekly]* |
| 2 | *[Quality item]* | *[Acceptance criteria]* | *[Method]* | *[Frequency]* |

{% if "iso_9001" in compliance %}
### ISO 9001 Process Controls
This SOP is a controlled process document. Process metrics are tracked for continual improvement:
- **Process KPI:** *[Metric and target]*
- **Nonconformity handling:** Per corrective action procedure *[reference]*
- **Management review:** Process performance reviewed *[quarterly/annually]*
{% endif %}

---

## Records & Documentation

| Record | Location | Retention | Format |
|--------|----------|-----------|--------|
| *[Procedure log]* | *[System/file]* | *[X years]* | *[Electronic/Paper]* |
| *[Checklist (completed)]* | *[System/file]* | *[X years]* | *[Electronic/Paper]* |
| *[Exception/deviation report]* | *[System/file]* | *[X years]* | *[Electronic/Paper]* |

---

## Change History

| Version | Date | Author | Description of Change |
|---------|------|--------|----------------------|
| {{version}} | {{date}} | {{author}} | Initial release |

---

## Approval

- **Author (Name/Title):** ____________________  **Date:** __________
- **Supervisor / OIC (Name/Title):** ____________________  **Date:** __________
- **Approving Authority (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `standard-operating-procedure`.*
