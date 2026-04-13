---
template_id: experiment-protocol
display_name: Experiment Protocol
preset: scientific
description: Standard operating procedure for conducting a controlled scientific experiment. Includes objectives, hypothesis, methodology, and safety considerations.
suggested_tags: [experiment, protocol, methodology]
suggested_folder: docs/
typical_cross_refs: [scientific-foundation, data-management-plan, irb-application]
requires: []
recommended_with: [scientific-foundation, data-management-plan, irb-application]
sections:
  - Protocol Summary
  - Objectives
  - Hypothesis
  - Materials & Equipment
  - Methodology
  - Variables & Controls
  - Data Collection Procedures
  - Safety Considerations
  - Statistical Analysis Plan
  - Quality Assurance
---

# {{title}}

| Protocol Metadata |  |
|---|---|
| Protocol ID | {{project_name}}-PROTO-{{date}} |
| Version | {{version}} |
| Status | {{status}} |
| Principal Investigator | {{author}} |
| Approval Date | [Date approved by PI/IRB] |

---

## Protocol Summary

*[Executive overview of the experiment (100–150 words). Include the central hypothesis, primary outcome measure, sample size/units, and expected duration.]*

---

## Objectives

### Primary Objective

*[State the main goal in measurable terms. Example: "To determine the effect of [intervention] on [outcome] in [population].]*

### Secondary Objectives

*[List supporting objectives that may illuminate mechanisms or generalizability.]*

1. [Objective and measurement]
2. [Objective and measurement]

---

## Hypothesis

**Null Hypothesis (H₀):**
*[Null hypothesis statement: typically "no difference" or "no effect"]*

**Alternative Hypothesis (H₁):**
*[Research hypothesis statement and direction (one-tailed or two-tailed)]*

**Theoretical Justification:**
*[Brief explanation of why this hypothesis is predicted based on prior literature and theory.]*

---

## Materials & Equipment

### Reagents & Materials

| Item | Specification | Supplier | Catalog # | Qty | Storage |
|---|---|---|---|---|---|
| [Reagent/Material] | [Purity, grade, lot info] | [Supplier] | [Cat. #] | [Qty] | [Condition] |
| | | | | | |

### Equipment & Instruments

| Equipment | Model/Make | Serial # | Last Calibrated | Precision/Range |
|---|---|---|---|---|
| [Equipment name] | [Model] | [S/N] | [Date] | [Spec] |
| | | | | |

{% if "iso_9001" in compliance %}
**Equipment Validation & Calibration:**
- All equipment must be calibrated within [X] months of use
- Calibration certificate or logbook entry required
- Out-of-calibration equipment must not be used

{% endif %}

---

## Methodology

### Experimental Design

*[Describe the overall design (randomized controlled, within-subjects, factorial, observational, etc.). Specify key design features and control/treatment allocation.]*

### Sample Preparation

*[Detailed procedure for preparing biological samples, chemical solutions, or experimental units. Include concentrations, volumes, and storage conditions.]*

### Procedure Steps

*[Numbered, step-by-step protocol. Include timing, temperatures, volumes, and conditions.]*

1. [Step with timing and parameters]
2. [Step with timing and parameters]
3. [Step with timing and parameters]

*[Continue as needed; detailed protocols may reference SOPs.]*

---

## Variables & Controls

| Variable Type | Variable Name | Measurement Unit | Method |
|---|---|---|---|
| Independent | [Intervention/exposure] | [Unit] | [How applied/measured] |
| Dependent | [Primary outcome] | [Unit] | [How measured] |
| Confounding | [Known confounder] | [Unit] | [Control method] |

### Control Conditions

*[Describe positive controls, negative controls, and vehicle controls. Justify control selection.]*

---

## Data Collection Procedures

### Measurement Schedule

| Timepoint | Measurement | Method | Personnel | Notes |
|---|---|---|---|---|
| Baseline | [Outcome measure] | [Instrument] | [Who] | [Special handling] |
| [Time] | [Outcome measure] | [Instrument] | [Who] | [Special handling] |

### Data Recording

*[How and where data are recorded (electronic lab notebook, hardcopy logbook, database). Include backup procedures.]*

### Data Quality

*[Define criteria for valid measurements (e.g., missing data thresholds, outlier detection). When is a measurement repeated?]*

{% if "hipaa" in compliance %}
### PHI & Human Subjects Protection

- All human subject data collected under informed consent (see irb-application)
- Data recorded using subject ID only (no identifiable information)
- Separately maintained key linking IDs to identities
- De-identification procedures per HIPAA Safe Harbor method [or expert determination]

{% endif %}

---

## Safety Considerations

### Hazard Assessment

*[Identify chemical, biological, physical, or radiation hazards involved.]*

| Hazard | Exposure Route | Control Measure | PPE |
|---|---|---|---|
| [Hazard] | [Route] | [Engineering/administrative control] | [PPE required] |

### Emergency Procedures

*[Protocol in case of spill, exposure, injury, or equipment failure.]*

1. [Emergency procedure]
2. [Emergency procedure]

### Waste Disposal

*[Proper disposal of chemical waste, biological waste, sharps, or other materials. Reference institutional waste disposal policy.]*

---

## Statistical Analysis Plan

### Primary Analysis

*[Primary comparison(s), test statistic, significance level (α = [0.05]), and assumptions. Include sample size justification.]*

### Secondary Analyses

*[Sensitivity analyses, subgroup analyses, or exploratory comparisons.]*

### Handling of Missing Data

*[Intention-to-treat vs. per-protocol analysis; imputation method if applicable.]*

---

## Quality Assurance

### Blinding & Randomization

*[Describe who is blinded (subjects, operators, analysts). Explain randomization method if applicable.]*

### Reproducibility Measures

- [ ] Protocol documented and version-controlled
- [ ] All equipment calibrated
- [ ] Operator training completed (see attached training records)
- [ ] Positive/negative controls included in each run
- [ ] Data management plan in place

### Documentation & Record-Keeping

*[All raw data, calculations, and observations recorded contemporaneously. Electronic lab notebooks maintained per institutional policy.]*

---

*Document generated by librarian v{{librarian_version}} from template `experiment-protocol`.*
