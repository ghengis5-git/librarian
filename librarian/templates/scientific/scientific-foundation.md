---
template_id: scientific-foundation
display_name: Scientific Foundation Document
preset: scientific
description: Establishes research framework, theoretical foundation, and research questions for a scientific inquiry. Suitable for research proposals, thesis foundations, and grant applications.
suggested_tags: [research, foundation, scientific]
suggested_folder: docs/
typical_cross_refs: [literature-review, experiment-protocol, data-management-plan]
requires: []
recommended_with: [literature-review, experiment-protocol, data-management-plan]
sections:
  - Abstract
  - Background & Motivation
  - Theoretical Framework
  - Key Principles
  - Current State of Knowledge
  - Research Questions
  - Methodology Overview
  - Expected Contributions
  - References
---

# {{title}}

{% if "iso_9001" in compliance %}
| Document Control |  |
|---|---|
| Document ID | {{project_name}}-FOUNDATION-{{date}} |
| Status | {{status}} |
| Classification | {{classification}} |
| Last Revised | {{date}} |
| Next Review | [{{review_cycle_days}} days] |

{% endif %}

## Abstract

*[Provide a concise summary (150–250 words) of the research problem, theoretical contribution, and expected findings. This section should stand alone and be comprehensible to a reader unfamiliar with the field.]*

---

## Background & Motivation

### Historical Context

*[Describe the historical development of this area of inquiry. What gaps or limitations prompted this research? Reference key milestone discoveries or paradigm shifts.]*

### Current Problem Statement

*[Define the specific problem or gap in knowledge this research addresses. Why is this problem important to the scientific community and broader society?]*

### Significance of the Research

*[Explain the potential impact of findings on theory, practice, or policy. Consider academic significance, industry applications, and societal benefit.]*

---

## Theoretical Framework

### Core Theoretical Foundation

*[Describe the primary theoretical model(s) underpinning this research. Include key assumptions, postulates, and limitations of these frameworks.]*

| Theoretical Model | Key Assumption | Scope | Applicability |
|---|---|---|---|
| [Model Name] | [Core assumption] | [Scope of validity] | [Where applicable] |
| | | | |

### Related Theories

*[Discuss how this work relates to competing or complementary theoretical perspectives. How does it build on or challenge existing theory?]*

---

## Key Principles

### Operational Definitions

*[Define core concepts with precision. Include mathematical or empirical definitions where applicable.]*

- **[Term]**: [Definition and scope]
- **[Term]**: [Definition and scope]

### Underlying Assumptions

*[List explicit assumptions about physical phenomena, human behavior, measurement validity, or system behavior.]*

1. [Assumption and justification]
2. [Assumption and justification]

---

## Current State of Knowledge

### Published Literature Synthesis

*[Summarize the current consensus on this topic. Reference landmark papers and recent developments.]*

| Author(s) | Year | Key Finding | Relevance to This Work |
|---|---|---|---|
| [Citation] | [Year] | [Finding] | [Connection to framework] |
| | | | |

### Identified Gaps

*[What questions remain unanswered? What methodologies are underdeveloped? Where are the inconsistencies in existing work?]*

1. [Gap and justification]
2. [Gap and justification]

---

## Research Questions

*[State the primary and secondary research questions. Frame them as testable hypotheses or exploratory inquiries.]*

**Primary Research Question:**
- [Question in precise, measurable form]

**Secondary Research Questions:**
1. [Question]
2. [Question]
3. [Question]

---

## Methodology Overview

### Research Design Type

*[Brief description of quantitative, qualitative, mixed-methods, experimental, observational, or theoretical approach.]*

### Data Sources & Collection Strategy

*[Outline the primary sources of data and general collection procedures. (Detailed protocols belong in experiment-protocol document.)]*

### Analytical Approach

*[Describe the statistical, computational, or interpretive methods that will be applied.]*

---

## Expected Contributions

### Theoretical Contributions

*[How will this research advance theory in the field? What new models, frameworks, or concepts may emerge?]*

### Methodological Contributions

*[Does this work introduce novel measurement tools, experimental designs, or analytical techniques?]*

### Practical Implications

*[What are the actionable insights for practitioners, policymakers, or industry?]*

{% if "hipaa" in compliance %}
### Data Privacy & Research Ethics Contribution

*[This research advances ethical data handling and privacy protection standards. See irb-application document for human subjects protections.]*

{% endif %}

---

## References

*[Alphabetical list of cited literature. Use standard citation format for your discipline.]*

1. [Author(s)]. [Year]. [Title]. *[Journal/Publisher]*, [Volume(Issue)], [Pages].
2. [Author(s)]. [Year]. [Title]. *[Journal/Publisher]*, [Volume(Issue)], [Pages].

---

*Document generated by librarian v{{librarian_version}} from template `scientific-foundation`.*
