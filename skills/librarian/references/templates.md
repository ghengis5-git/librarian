# Document Template Catalog

57+ templates organized by category. Templates create properly named files with pre-wired sections, tags, and cross-references. They do NOT generate content — they scaffold the structure.

## Template Resolution Order

1. Custom templates directory (`project_config.custom_templates_dir`)
2. Preset-specific templates (e.g., `software/`)
3. Cross-cutting templates (`security/`, `compliance/`)
4. Universal templates (available to all presets)

Custom templates with matching IDs override built-in ones.

## Universal Templates (All Presets)

| ID | Name | Sections | Tags |
|----|------|----------|------|
| `readme` | README | 5 | infrastructure |
| `project-plan` | Project Plan | 8 | planning |
| `changelog` | Changelog | 4 | infrastructure |
| `meeting-notes` | Meeting Notes | 6 | operational |

## Software Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `architecture-decision-record` | ADR | 7 | — |
| `technical-architecture` | Technical Architecture | 10 | ISO 27001, DoD 5200 |
| `api-specification` | API Specification | 9 | — |
| `runbook` | Runbook | 8 | — |
| `security-assessment` | Security Assessment | 9 | ISO 27001, HIPAA, DoD 5200 |
| `incident-postmortem` | Incident Postmortem | 8 | — |
| `test-plan` | Test Plan | 7 | ISO 9001 |
| `release-notes` | Release Notes | 6 | — |

## Business Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `strategic-plan` | Strategic Plan | 9 | SEC/FINRA, ISO 9001 |
| `cost-analysis` | Cost Analysis | 8 | — |
| `competitor-analysis` | Competitor Analysis | 7 | — |
| `project-management-plan` | Project Management Plan | 10 | — |
| `business-case` | Business Case | 8 | — |
| `risk-assessment` | Risk Assessment | 8 | ISO 9001, ISO 27001 |
| `stakeholder-analysis` | Stakeholder Analysis | 6 | — |
| `executive-summary` | Executive Summary | 5 | — |

## Legal Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `legal-review` | Legal Review | 8 | HIPAA, SEC/FINRA |
| `patent-review` | Patent Review | 9 | — |
| `ip-landscape` | IP Landscape | 7 | — |
| `contract-summary` | Contract Summary | 7 | HIPAA, SEC/FINRA |
| `regulatory-compliance-checklist` | Regulatory Compliance | 8 | HIPAA, ISO 27001, SEC/FINRA, DoD 5200 |
| `nda-tracker` | NDA Tracker | 5 | — |

## Scientific Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `scientific-foundation` | Scientific Foundation | 10 | — |
| `experiment-protocol` | Experiment Protocol | 9 | HIPAA, ISO 9001 |
| `literature-review` | Literature Review | 7 | — |
| `data-management-plan` | Data Management Plan | 8 | HIPAA, ISO 27001, DoD 5200 |
| `irb-application` | IRB Application | 10 | — |
| `lab-notebook-entry` | Lab Notebook Entry | 6 | — |

## Healthcare Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `clinical-protocol` | Clinical Protocol | 10 | HIPAA, ISO 9001 |
| `hipaa-risk-assessment` | HIPAA Risk Assessment | 9 | HIPAA, ISO 27001 |
| `quality-improvement-plan` | Quality Improvement Plan | 8 | ISO 9001 |
| `policy-document` | Policy Document | 7 | HIPAA |
| `incident-report` | Incident Report | 8 | HIPAA |
| `credentialing-checklist` | Credentialing Checklist | 6 | — |

## Finance Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `due-diligence-report` | Due Diligence Report | 10 | SEC/FINRA |
| `investment-memo` | Investment Memo | 9 | SEC/FINRA |
| `compliance-review` | Compliance Review | 8 | SEC/FINRA, HIPAA |
| `audit-finding` | Audit Finding | 7 | — |
| `risk-assessment-finance` | Financial Risk Assessment | 8 | SEC/FINRA |
| `regulatory-filing-checklist` | Regulatory Filing Checklist | 6 | SEC/FINRA |

## Government Templates

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `policy-directive` | Policy Directive | 8 | DoD 5200, ISO 9001 |
| `standard-operating-procedure` | SOP | 9 | ISO 9001 |
| `memorandum` | Memorandum | 6 | — |
| `acquisition-plan` | Acquisition Plan | 9 | DoD 5200 |
| `security-plan` | Security Plan | 10 | DoD 5200, ISO 27001 |
| `after-action-report` | After Action Report | 7 | — |

## Security Templates (Cross-Cutting — All Presets)

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `threat-model` | Threat Model | 9 | HIPAA, DoD 5200, ISO 27001 |
| `vulnerability-assessment` | Vulnerability Assessment | 8 | — |
| `penetration-test-report` | Penetration Test Report | 9 | HIPAA |
| `security-architecture-review` | Security Architecture Review | 8 | ISO 27001, DoD 5200 |
| `incident-response-plan` | Incident Response Plan | 10 | HIPAA |
| `access-control-matrix` | Access Control Matrix | 7 | HIPAA, DoD 5200 |
| `data-classification-policy` | Data Classification Policy | 8 | DoD 5200, HIPAA, SEC/FINRA |

## Compliance Templates (Cross-Cutting — All Presets)

| ID | Name | Sections | Compliance |
|----|------|----------|------------|
| `sox-controls-matrix` | SOX Controls Matrix | 8 | SEC/FINRA |
| `gdpr-dpia` | GDPR DPIA | 9 | HIPAA |
| `pci-dss-checklist` | PCI DSS Checklist | 8 | — |
| `iso27001-statement-of-applicability` | ISO 27001 SoA | 7 | HIPAA |
| `audit-readiness-checklist` | Audit Readiness Checklist | 8 | ISO 9001, ISO 27001, HIPAA, SEC/FINRA, DoD 5200 |
| `vendor-risk-assessment` | Vendor Risk Assessment | 7 | HIPAA, SEC/FINRA |
