---
template_id: after-action-report
display_name: After Action Report
preset: government
description: >-
  After Action Report (AAR) for documenting operations, exercises, incidents,
  or significant events. Covers executive summary, timeline, observations,
  lessons learned, and corrective actions. Standard government AAR format
  supporting continuous organizational improvement.
suggested_tags: [aar, lessons-learned, operations]
suggested_folder: reports/
typical_cross_refs:
  - standard-operating-procedure
  - policy-directive
  - security-plan
recommended_with:
  - standard-operating-procedure
requires: []
sections:
  - Executive Summary
  - Event Overview
  - Timeline of Events
  - Observations
  - Lessons Learned
  - Corrective Action Plan
  - Best Practices
  - Recommendations
---

# After Action Report: {{title}}

**Report Number:** *[AAR-XXXX]*
**Date:** {{date}}
**Version:** {{version}}
**Author:** {{author}}
**Status:** {{status}}

{% if "dod_5200" in compliance %}
**Classification:** {{classification}}
{% endif %}

---

## Executive Summary

*[2–3 paragraph summary of the event/operation, overall assessment (Successful / Partially Successful / Unsuccessful), key observations, and critical corrective actions.]*

### Overall Assessment

| Area | Rating | Notes |
|------|--------|-------|
| Planning | *[Effective / Partially Effective / Ineffective]* | *[Key observation]* |
| Execution | *[Effective / Partially Effective / Ineffective]* | *[Key observation]* |
| Communication | *[Effective / Partially Effective / Ineffective]* | *[Key observation]* |
| Logistics | *[Effective / Partially Effective / Ineffective]* | *[Key observation]* |
| Outcome | *[Met objectives / Partially met / Did not meet]* | *[Key observation]* |

---

## Event Overview

| Attribute | Detail |
|-----------|--------|
| **Event Name** | *[Name/designation]* |
| **Event Type** | *[Operation / Exercise / Incident / Training / Inspection]* |
| **Date(s)** | *[Start — End]* |
| **Location** | *[Location(s)]* |
| **Participants** | *[Units, agencies, organizations]* |
| **Personnel Count** | *[Approximate number involved]* |
| **Objectives** | *[List primary objectives]* |
| **Authorizing Directive** | *[OPORD / FRAGORD / Memo / Directive #]* |

### Objectives Assessment

| # | Objective | Met | Notes |
|---|----------|-----|-------|
| 1 | *[Objective 1]* | *[Yes / Partial / No]* | *[Evidence/explanation]* |
| 2 | *[Objective 2]* | *[Yes / Partial / No]* | *[Evidence/explanation]* |
| 3 | *[Objective 3]* | *[Yes / Partial / No]* | *[Evidence/explanation]* |

---

## Timeline of Events

| Date/Time | Event | Key Decision/Action | Impact |
|-----------|-------|-------------------|--------|
| *[DTG or date/time]* | *[Event description]* | *[Decision made or action taken]* | *[Positive / Negative / Neutral]* |
| *[DTG]* | *[Event]* | *[Decision/Action]* | *[Impact]* |
| *[DTG]* | *[Event]* | *[Decision/Action]* | *[Impact]* |

---

## Observations

### Observation 1: *[Title]*

| Attribute | Detail |
|-----------|--------|
| **Area** | *[Planning / Execution / Communication / Logistics / Other]* |
| **Type** | *[Sustain (strength) / Improve (weakness)]* |
| **Discussion** | *[Factual description of what was observed]* |
| **Impact** | *[How this observation affected the outcome]* |
| **Root Cause** | *[If weakness — what caused it]* |

### Observation 2: *[Title]*
*[Follow same structure.]*

### Observation 3: *[Title]*
*[Follow same structure.]*

{% if "dod_5200" in compliance %}
### Security Observations
| Observation | Classification Impact | Recommendation |
|------------|---------------------|---------------|
| *[Security-related observation]* | *[Compromise risk / Handling deficiency / None]* | *[Action]* |
{% endif %}

---

## Lessons Learned

| # | Lesson | Category | Priority | Applicability |
|---|--------|----------|----------|---------------|
| 1 | *[Lesson description — actionable, specific]* | *[Tactics / Procedures / Training / Equipment / Policy]* | *[High / Medium / Low]* | *[Unit-level / Organization-wide / Community of interest]* |
| 2 | *[Lesson]* | *[Category]* | *[Priority]* | *[Applicability]* |
| 3 | *[Lesson]* | *[Category]* | *[Priority]* | *[Applicability]* |

---

## Corrective Action Plan

| # | Observation | Corrective Action | OPR | OCR | Deadline | Status |
|---|-----------|-------------------|-----|-----|----------|--------|
| 1 | *[Observation ref]* | *[Specific action]* | *[Office of Primary Responsibility]* | *[Office of Coordinating Responsibility]* | *[Date]* | *[Open / In Progress / Complete]* |
| 2 | *[Observation ref]* | *[Action]* | *[OPR]* | *[OCR]* | *[Date]* | *[Status]* |

### Tracking & Follow-Up
- **Tracking Mechanism:** *[System / spreadsheet / memo for record]*
- **Review Frequency:** *[Monthly / Quarterly until all actions complete]*
- **Responsible for Close-Out:** *[Name/Title]*

---

## Best Practices

*[Document what worked well that should be sustained or adopted by other organizations.]*

| # | Best Practice | Why It Worked | Recommended For |
|---|-------------|---------------|----------------|
| 1 | *[Practice description]* | *[Explanation]* | *[Who should adopt]* |
| 2 | *[Practice]* | *[Explanation]* | *[Who]* |

---

## Recommendations

1. *[Recommendation 1 — specific, actionable, tied to observations]*
2. *[Recommendation 2]*
3. *[Recommendation 3]*

---

## Approval

- **Author (Name/Title):** ____________________  **Date:** __________
- **Reviewing Official (Name/Title):** ____________________  **Date:** __________
- **Approving Authority (Name/Title):** ____________________  **Date:** __________

---

*Document generated by librarian v{{librarian_version}} from template `after-action-report`.*
