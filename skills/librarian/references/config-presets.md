# Configuration & Presets Reference

## project_config Schema

The `project_config` block in `REGISTRY.yaml` controls all librarian behavior. Every field is optional — unset fields fall back to built-in defaults.

```yaml
project_config:
  # Identity
  project_name: "My Project"           # Human-readable project name
  default_author: "Your Name"          # Default author for new documents
  default_classification: "CONFIDENTIAL"

  # Naming convention
  naming_convention: "descriptive-name-YYYYMMDD-VX.Y.ext"
  naming_rules:
    separator: "-"                     # Word separator: - | _ | .
    case: "lowercase"                  # lowercase | mixed | upper
    date_format: "YYYYMMDD"           # YYYYMMDD | YYYY-MM-DD | off
    version_format: "VX.Y"            # VX.Y | vX.Y | X.Y
    domain_prefix: null               # Optional prefix: "ENG-", "FIN-", etc.
    category_strictness: "soft"        # soft (warn) | hard (reject)
    forbidden_words:
      - "file"
      - "download"
      - "output"
      - "document"
    infrastructure_exempt:
      - "SKILL.md"
      - "REGISTRY.yaml"
      - "CLAUDE.md"
      - "README.md"
      - ".gitignore"

  # Paths
  tracked_dirs:
    - "docs/"
  docs_path: "docs/"
  archive_path: "docs/archive/"

  # Classification levels
  classification_levels:
    - "PUBLIC"
    - "INTERNAL"
    - "CONFIDENTIAL"

  # Tags taxonomy
  tags_taxonomy:
    domain: [architecture, planning, operations]
    type: [report, spec, plan, addendum]
    status_indicators: [needs-update, pending-review]

  # Compliance flags (activate conditional template sections)
  compliance_standards:
    hipaa: false
    dod_5200: false
    iso_9001: false
    iso_27001: false
    sec_finra: false

  # Custom templates directory (overrides built-in templates with matching IDs)
  custom_templates_dir: "templates/"

  # Evidence signing: off | gpg | ssh
  evidence_signing: "off"

  # Staleness threshold
  staleness_threshold_days: 90

  # Git (for commit-based workflows)
  git_author_name: "Your Name"
  git_author_email: "you@example.com"
  git_commit_prefixes:
    docs: "docs:"
    registry: "registry:"
    infra: "infra:"

  # Document header/footer (for generated output)
  header:
    organization: ""
    classification_banner: true
    logo_url: ""
  footer:
    disclaimer: ""
    custom_text: ""
  metadata_requirements:
    require_author: true
    require_classification: true
    require_date: true
```

## Built-in Presets

Presets provide pre-configured `project_config` defaults tuned for specific industries.

| Preset | Naming Template | Compliance Focus | Core Templates |
|--------|----------------|-----------------|----------------|
| `software` | default | ISO 27001 | ADR, technical-architecture, api-spec, runbook, test-plan, release-notes |
| `business` | corporate | SEC/FINRA, ISO 9001 | strategic-plan, cost-analysis, competitor-analysis, business-case, risk-assessment |
| `legal` | legal | SEC/FINRA, HIPAA | legal-review, patent-review, contract-summary, nda-tracker, regulatory-compliance |
| `scientific` | scientific | ISO 9001 | scientific-foundation, experiment-protocol, literature-review, data-management-plan |
| `healthcare` | healthcare | HIPAA, ISO 9001 | clinical-protocol, hipaa-risk-assessment, quality-improvement-plan, policy-document |
| `finance` | finance | SEC/FINRA | due-diligence-report, investment-memo, compliance-review, audit-finding |
| `government` | default | DoD 5200, ISO 9001 | policy-directive, SOP, memorandum, acquisition-plan, security-plan |
| `accounting` | finance | SEC/FINRA | (inherits from finance with accounting-specific tags) |
| `minimal` | default | None | (bare minimum — universal templates only) |

## Naming Templates

| Template | Pattern | Example |
|----------|---------|---------|
| `default` | `name-YYYYMMDD-VX.Y.ext` | `architecture-20260413-V1.0.md` |
| `legal` | `name-YYYYMMDD-VX.Y.ext` | `patent-review-20260413-V1.0.docx` |
| `engineering` | `name-YYYYMMDD-VX.Y.ext` | `api-spec-20260413-V2.1.md` |
| `corporate` | `name-YYYYMMDD-VX.Y.ext` | `strategic-plan-20260413-V1.0.pptx` |
| `dateless` | `name-VX.Y.ext` | `readme-V1.0.md` |
| `scientific` | `name-YYYYMMDD-VX.Y.ext` | `experiment-protocol-20260413-V1.0.md` |
| `healthcare` | `name-YYYYMMDD-VX.Y.ext` | `clinical-protocol-20260413-V1.0.docx` |
| `finance` | `name-YYYYMMDD-VX.Y.ext` | `due-diligence-20260413-V1.0.xlsx` |

All templates support configurable separators (`-`, `_`, `.`), case rules, and optional domain prefixes.

## Fallback Defaults

When `project_config` is absent or a key is missing, these defaults apply:

| Key | Default |
|-----|---------|
| `project_name` | "Untitled Project" |
| `naming_convention` | `descriptive-name-YYYYMMDD-VX.Y.ext` |
| `separator` | `-` |
| `case` | `lowercase` |
| `forbidden_words` | file, download, output, document |
| `default_classification` | CONFIDENTIAL |
| `staleness_threshold_days` | 90 |
| `docs_path` | `docs/` |
| `evidence_signing` | `off` |
