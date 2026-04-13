---
template_id: irb-application
display_name: IRB Application
preset: scientific
description: Institutional Review Board application for human subjects research approval. Establishes ethical protections and regulatory compliance.
suggested_tags: [irb, ethics, human-subjects]
suggested_folder: docs/
typical_cross_refs: [experiment-protocol, data-management-plan]
requires: [experiment-protocol]
recommended_with: [experiment-protocol, data-management-plan]
sections:
  - Study Information
  - Principal Investigator
  - Study Purpose
  - Subject Population
  - Recruitment
  - Informed Consent
  - Risks & Benefits
  - Data Privacy
  - Monitoring Plan
---

# {{title}}

| IRB Application |  |
|---|---|
| Application ID | {{project_name}}-IRB-{{date}} |
| Institution | {{organization}} |
| Status | {{status}} |
| Submission Date | {{date}} |
| Review Type | [Expedited / Full Board / Exempt] |

---

## Study Information

### Study Title & Acronym

*{{title}}* — Acronym: [Acronym]

### Study Duration

- **Anticipated start date**: [Date]
- **Anticipated end date**: [Date]
- **Total duration**: [X months/years]

### Study Objectives

*[Restate primary and secondary research objectives in plain language suitable for IRB review.]*

---

## Principal Investigator

| Item | Information |
|---|---|
| Name | {{author}} |
| Title | [Title/Rank] |
| Credentials | [Degrees, certifications] |
| Institution | {{organization}} |
| Phone | [Contact number] |
| Email | [Email address] |
| CITI Training | [Completion date] |

### Research Team

*[List all co-investigators, study coordinators, and personnel with human subjects contact.]*

| Name | Role | Institution | CITI Training Date |
|---|---|---|---|
| [Name] | [Role] | [Institution] | [Date] |
| | | | |

---

## Study Purpose

### Background & Significance

*[Explain why this research is important. What gap in knowledge or clinical practice does it address?]*

### Study Design

*[Brief description of research design: randomized controlled trial, observational cohort, qualitative interviews, survey, etc.]*

---

## Subject Population

### Inclusion Criteria

*[Who is eligible for the study?]*

1. [Criterion]
2. [Criterion]
3. [Criterion]

### Exclusion Criteria

*[Who should not participate?]*

1. [Criterion]
2. [Criterion]

### Target Enrollment

- **Total subjects**: [Number]
- **Gender distribution**: [Expected breakdown]
- **Age range**: [From–To years]
- **Special populations**: [Any vulnerable populations? Pregnant women? Children? Prisoners?]

---

## Recruitment

### Recruitment Strategy

*[How will subjects be identified and approached? Where will recruitment occur?]*

### Recruitment Materials

*[Attach or describe flyers, advertisements, email solicitations, or other recruitment materials.]*

### Compensation

*[Will subjects be paid? If so, what amount and when?]*

- Payment: [Amount] [Currency]
- Timing: [Upon completion / As study proceeds / Other]
- Justification: [Why this amount is reasonable and not coercive]

---

## Informed Consent

### Consent Process

*[When and how will consent be obtained? Who will obtain it? Is written consent required or is verbal sufficient?]*

### Consent Form Components

*[The informed consent document must include:]*

- Study purpose and procedures
- Duration of subject participation
- Foreseeable risks and discomforts
- Potential benefits
- Alternative procedures or treatments (if applicable)
- Confidentiality and data privacy protections
- Right to withdraw without penalty
- Contact information for study team and IRB
- Signature line and date

### Special Consent Considerations

*[For minors: how will parental consent and child assent be obtained?]*
*[For cognitively impaired: how will decision-making capacity be assessed?]*

{% if "hipaa" in compliance %}
### HIPAA Authorization & PHI Disclosure

**Separate HIPAA Authorization Form Required**

This study will require subjects to authorize use and disclosure of Protected Health Information (PHI):

- **Information to be used**: [Describe medical records, lab results, etc.]
- **Authorized recipients**: [Research team members only; no commercial use]
- **Duration**: [Study period only; data retained for X years then destroyed]
- **Subject rights**: [Right to revoke authorization, no penalty for refusal]

De-identification Method: [HIPAA Safe Harbor / Expert Determination]

Linkage Key Storage: [Separate from de-identified data; encrypted; access restricted]

{% endif %}

---

## Risks & Benefits

### Reasonably Foreseeable Risks

*[What harms could subjects experience? Physical, psychological, social, economic, legal?]*

| Risk | Severity | Probability | Mitigation Strategy |
|---|---|---|---|
| [Risk] | [Low/Moderate/High] | [Low/Moderate/High] | [How minimized] |
| | | | |

### Potential Benefits

*[What direct benefits might subjects experience? What benefits to science or society?]*

- **Direct benefits**: [To subject, if any]
- **Societal benefits**: [To science, public health, policy, etc.]

### Risk-Benefit Assessment

*[Justify that risks are reasonable in relation to anticipated benefits. Explain why the research is worth doing despite risks.]*

---

## Data Privacy

### Data Collection & Recording

*[What data will be collected? How? On what schedule?]*

### De-identification Procedures

*[How will personally identifiable information (PII) be removed or separated from research data?]*

**Method**: [HIPAA Safe Harbor / Expert Determination / [Other]

**Safe Harbor Elements**:
- Names: [Removed]
- Dates: [Kept as [month-year only / ages only / removed]]
- Medical record numbers: [Removed]
- Identifiers: [All removed or replaced with code]

### Data Storage & Security

- **Primary storage**: [Encrypted [AES-256] on secure server]
- **Backup**: [Frequency and location]
- **Access control**: [Who can access; authentication method]
- **Retention**: [Duration; destruction method]

### Data Sharing & Future Use

*[Will data be shared with other researchers? Deposited in repositories? Retained for future research?]*

- **Sharing permitted?**: [Yes / No / Only with written consent per [condition]]
- **Repository**: [Name, if applicable]
- **Secondary use**: [Permitted for similar research? Other uses? Require new consent?]

---

## Monitoring Plan

### Data Safety Monitoring

*[How will safety be monitored? What is the plan for detecting and responding to adverse events?]*

### Adverse Event Reporting

*[What constitutes a reportable adverse event? How quickly must it be reported to the IRB?]*

- **Serious adverse events**: [Report within 24 hours]
- **Non-serious adverse events**: [Report within X days]
- **Reporting mechanism**: [Email, phone, web portal]

### Protocol Violations

*[What happens if the study protocol is deviated from? When must deviations be reported?]*

---

*Document generated by librarian v{{librarian_version}} from template `irb-application`.*
