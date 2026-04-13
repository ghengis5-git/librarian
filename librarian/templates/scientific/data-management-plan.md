---
template_id: data-management-plan
display_name: Data Management Plan
preset: scientific
description: Establishes data governance policies including collection, storage, security, organization, access, and preservation for research data.
suggested_tags: [data, management, governance]
suggested_folder: docs/
typical_cross_refs: [experiment-protocol, scientific-foundation]
requires: []
recommended_with: [experiment-protocol, scientific-foundation]
sections:
  - Data Description
  - Data Collection
  - Data Storage & Security
  - Data Organization
  - Quality Assurance
  - Access & Sharing
  - Preservation & Retention
  - Roles & Responsibilities
---

# {{title}}

| DMP Metadata |  |
|---|---|
| Plan ID | {{project_name}}-DMP-{{date}} |
| Version | {{version}} |
| Status | {{status}} |
| Data Steward | {{author}} |
| Last Updated | {{date}} |

---

## Data Description

### Dataset Overview

*[Describe all datasets generated or collected in this project. Include data type, format, volume, and scientific context.]*

| Dataset | Data Type | Format | Est. Size | Source |
|---|---|---|---|---|
| [Name] | [Type: numeric, text, image, etc.] | [CSV, JSON, DICOM, etc.] | [Size] | [Instrument/method] |
| | | | | |

### Data Standards & Metadata

*[Specify data standards, controlled vocabularies, or ontologies used (e.g., FAIR principles, domain-specific standards).]*

- Standard: [Standard name and version]
- Metadata schema: [Schema and required fields]

---

## Data Collection

### Collection Methods & Timeline

| Data Stream | Collection Method | Frequency | Start Date | End Date |
|---|---|---|---|---|
| [Dataset name] | [Instrument/protocol] | [Daily/weekly/etc.] | [Date] | [Date] |
| | | | | |

### Data Collection Points & Responsible Parties

*[Who collects data? At which locations or instruments? What training is required?]*

---

## Data Storage & Security

### Storage Infrastructure

*[Primary and backup storage locations, systems, and redundancy.]*

- **Primary storage**: [Location, system, capacity]
- **Backup storage**: [Location, system, frequency]
- **Archive storage**: [Long-term location if different]

### Data Access & Authentication

*[Describe access controls: who can access data, and how access is restricted.]*

- Authentication method: [Passwords, 2FA, SSH keys, etc.]
- Authorization level: [By role, project, dataset]
- Access logging: [How access is logged and monitored]

{% if "hipaa" in compliance %}
### PHI Data Security & De-Identification

- **Data Classification**: Research data containing PHI is classified as Sensitive
- **De-identification Method**: [HIPAA Safe Harbor method / Expert determination]
- **Identifier Separation**: Linkage keys stored separately from identifiers, encrypted
- **Encryption Standards**: All PHI at rest encrypted using AES-256; in transit via TLS 1.2+
- **Access Restrictions**: Only authorized personnel with HIPAA training can access PHI
- **Audit Trail**: All PHI access logged with timestamps and user IDs

{% endif %}

{% if "iso_27001" in compliance %}
### Information Security Controls (ISO 27001)

| Control Domain | Implementation | Responsibility |
|---|---|---|
| Access Control | [MFA, role-based access, VPN] | [IT/Data Steward] |
| Encryption | [AES-256 at rest, TLS 1.2+ in transit] | [IT] |
| Monitoring | [Log review, intrusion detection] | [IT] |
| Incident Response | [Breach notification, containment] | [Data Steward + IT] |

{% endif %}

{% if "dod_5200" in compliance %}
### Classified Data Handling (DoD 5200.01-M)

- **Classification Level**: [UNCLASSIFIED / CONTROLLED UNCLASSIFIED INFORMATION / CONFIDENTIAL / SECRET / TOP SECRET]
- **Marking Requirements**: All physical and digital documents marked with classification and handling caveats
- **Storage**: Classified data stored in secure facility or encrypted containers; unclassified working copies clearly marked
- **Personnel**: Only personnel with appropriate clearance level can access classified data
- **Disposition**: Classified data destroyed by approved method per retention schedule

{% endif %}

---

## Data Organization

### File Structure & Naming

*[Directory structure and file naming conventions for consistency and findability.]*

```
project/
├── raw/                    [Original, unmodified data]
│   ├── instrument_A/
│   └── instrument_B/
├── processed/              [Cleaned, transformed data]
│   ├── datasets/
│   └── derived/
└── metadata/               [Data dictionaries, codebooks]
    └── data-dictionary.csv
```

**File Naming Convention:**
`[dataset]-[version]-[date]-[description].[ext]`
Example: `metabolites-v2-20260413-filtered.csv`

### Data Dictionary & Codebook

*[For each variable/field, document: name, description, data type, units, acceptable values, missing value codes.]*

| Variable | Description | Type | Units | Valid Range | Missing Code |
|---|---|---|---|---|---|
| [VarName] | [What it measures] | [int/float/char] | [Units] | [Range] | [Code] |
| | | | | | |

---

## Quality Assurance

### Data Validation & Cleaning

*[Procedures to check data completeness, accuracy, consistency, and logical validity.]*

1. **Range checks**: Values outside [min, max] range flagged
2. **Consistency checks**: Cross-variable logical constraints verified
3. **Completeness**: Missing data documented and flagged
4. **Duplicate detection**: [Method for identifying and handling duplicates]

### Quality Metrics

- Target completeness: [%]
- Acceptable error rate: [%]
- Outlier detection threshold: [e.g., ±3 SD]

### Version Control

*[How updates and revisions are tracked. Version numbering, change logs, and approval workflows.]*

---

## Access & Sharing

### Data Access Policy

*[Who is permitted to access data? What restrictions apply?]*

| User Role | Access Level | Permitted Operations | Restrictions |
|---|---|---|---|
| [Role] | [Full/read-only/aggregated] | [Query/download/analyze] | [Confidentiality restrictions] |
| | | | |

### Data Sharing & Publication

*[Under what conditions may data be shared with collaborators, deposited in repositories, or published?]*

- **Internal sharing**: [Collaboration agreements, licensing]
- **External sharing**: [Institutional review, data use agreements required]
- **Publication timeline**: [When data becomes publicly available]
- **Repository**: [Where data will be deposited for long-term access]

---

## Preservation & Retention

### Data Retention Schedule

| Dataset | Retention Period | Justification | Disposition |
|---|---|---|---|
| [Name] | [Duration] | [Regulatory/scientific] | [Delete/archive] |

### Long-Term Preservation

*[Plan for maintaining data accessibility and usability over [X] years.]*

- **Format preservation**: [Archival formats, format migration plan]
- **Technology watch**: [How obsolescence is monitored and managed]
- **Metadata preservation**: [Ensuring metadata remains interpretable]

---

## Roles & Responsibilities

| Role | Responsibility |
|---|---|
| Data Steward | Overall DMP compliance, access approvals, retention enforcement |
| IT Administrator | Storage, backup, encryption, access logging |
| Researcher/Analyst | Data collection quality, documentation, validation |
| Project Manager | DMP updates, stakeholder communication |

---

*Document generated by librarian v{{librarian_version}} from template `data-management-plan`.*
