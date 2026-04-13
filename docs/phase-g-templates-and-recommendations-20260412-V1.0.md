---
title: "Phase G — Document Templates & Recommendations Engine"
filename: phase-g-templates-and-recommendations-20260412-V1.0.md
version: 1.0
date: 2026-04-12
status: active
author: Christopher A. Kahn
classification: PERSONAL / INTERNAL USE ONLY
supersedes: null
---

# Phase G — Document Templates & Recommendations Engine

## Purpose

This plan adds two capabilities to the librarian:

1. **Document templates** — markdown skeletons for common document types, organized by preset.
   `python -m librarian scaffold --template strategic-plan` creates a properly named,
   pre-sectioned file and registers it in one step.

2. **Recommendations engine** — the audit command gains a `--recommend` flag that analyzes
   the current registry and suggests documents the project is missing. Not content
   generation — gap detection. "You have an architecture doc but no security assessment.
   Projects in the `software` preset typically have both."

The librarian does NOT write documents. It creates the container (structure, naming,
metadata, registry entry) and tells you what containers you're missing. Content generation
stays in the skill layer (doc-coauthoring, contract-review, etc.) or with the operator.

## Background

During development of the first consumer project, a natural constellation of documents
emerged: buildout plan, architecture, implementation plans, cost analysis, legal review,
patent review, competitor analysis, scientific foundation, strategic plan, project
management tracker. These were created ad hoc. The librarian governed them after the fact
but had no ability to (a) suggest that a project of that type needs them, or (b) scaffold
them with the right sections from the start.

Every preset already defines folder structures, tags, and document types. Templates are
the missing link between "here are the folders you should have" and "here's a document
with the right frontmatter, sections, and cross-references pre-wired."

## Architecture

### Template storage

```
librarian/
├── templates/                        # ships with the package
│   ├── __init__.py                   # template registry + loader
│   ├── _base.py                      # BaseTemplate dataclass + rendering engine
│   ├── universal/                    # available in all presets
│   │   ├── readme.md.j2
│   │   ├── project-plan.md.j2
│   │   ├── changelog.md.j2
│   │   └── meeting-notes.md.j2
│   ├── software/
│   │   ├── architecture-decision-record.md.j2
│   │   ├── technical-architecture.md.j2
│   │   ├── api-specification.md.j2
│   │   ├── runbook.md.j2
│   │   ├── security-assessment.md.j2
│   │   ├── incident-postmortem.md.j2
│   │   ├── test-plan.md.j2
│   │   └── release-notes.md.j2
│   ├── business/
│   │   ├── strategic-plan.md.j2
│   │   ├── cost-analysis.md.j2
│   │   ├── competitor-analysis.md.j2
│   │   ├── project-management-plan.md.j2
│   │   ├── business-case.md.j2
│   │   ├── risk-assessment.md.j2
│   │   ├── stakeholder-analysis.md.j2
│   │   └── executive-summary.md.j2
│   ├── legal/
│   │   ├── legal-review.md.j2
│   │   ├── patent-review.md.j2
│   │   ├── ip-landscape.md.j2
│   │   ├── contract-summary.md.j2
│   │   ├── regulatory-compliance-checklist.md.j2
│   │   └── nda-tracker.md.j2
│   ├── scientific/
│   │   ├── scientific-foundation.md.j2
│   │   ├── experiment-protocol.md.j2
│   │   ├── literature-review.md.j2
│   │   ├── data-management-plan.md.j2
│   │   ├── irb-application.md.j2
│   │   └── lab-notebook-entry.md.j2
│   ├── healthcare/
│   │   ├── clinical-protocol.md.j2
│   │   ├── hipaa-risk-assessment.md.j2
│   │   ├── quality-improvement-plan.md.j2
│   │   ├── policy-document.md.j2
│   │   ├── incident-report.md.j2
│   │   └── credentialing-checklist.md.j2
│   ├── finance/
│   │   ├── due-diligence-report.md.j2
│   │   ├── investment-memo.md.j2
│   │   ├── compliance-review.md.j2
│   │   ├── audit-finding.md.j2
│   │   ├── risk-assessment.md.j2
│   │   └── regulatory-filing-checklist.md.j2
│   ├── government/
│   │   ├── policy-directive.md.j2
│   │   ├── standard-operating-procedure.md.j2
│   │   ├── memorandum.md.j2
│   │   ├── acquisition-plan.md.j2
│   │   ├── security-plan.md.j2
│   │   └── after-action-report.md.j2
│   ├── security/                     # cross-cutting — available to any preset
│   │   ├── threat-model.md.j2
│   │   ├── vulnerability-assessment.md.j2
│   │   ├── penetration-test-report.md.j2
│   │   ├── security-architecture-review.md.j2
│   │   ├── incident-response-plan.md.j2
│   │   ├── access-control-matrix.md.j2
│   │   └── data-classification-policy.md.j2
│   └── compliance/                   # cross-cutting — available to any preset
│       ├── sox-controls-matrix.md.j2
│       ├── gdpr-dpia.md.j2
│       ├── pci-dss-checklist.md.j2
│       ├── iso27001-statement-of-applicability.md.j2
│       ├── audit-readiness-checklist.md.j2
│       └── vendor-risk-assessment.md.j2
```

### Template format

Templates are markdown files with YAML frontmatter and lightweight Jinja2-style variable
substitution. No Jinja2 dependency — the librarian uses `str.replace()` on a small set
of known variables. This preserves the zero-dependency constraint.

```markdown
---
template_id: strategic-plan
display_name: Strategic Plan
preset: business
description: Multi-year strategic plan with vision, objectives, and execution roadmap
suggested_tags: [strategy, planning, executive]
suggested_folder: executive/
typical_cross_refs: [cost-analysis, competitor-analysis, risk-assessment]
requires: []                          # templates that should exist first
recommended_with: [cost-analysis, competitor-analysis]
sections:
  - Executive Summary
  - Vision & Mission Alignment
  - Strategic Objectives (3-5 Year)
  - Market Analysis
  - Competitive Position
  - Resource Requirements
  - Risk Factors
  - Execution Roadmap
  - Success Metrics & KPIs
  - Review Cadence
---

# {{title}}

**Version:** {{version}} | **Date:** {{date}} | **Author:** {{author}}
**Classification:** {{classification}}
**Status:** {{status}}

---

## Executive Summary

*[Provide a 1-2 paragraph summary of the strategic direction, key decisions,
and expected outcomes. Write this section last.]*

## Vision & Mission Alignment

*[How does this plan connect to the organization's stated vision and mission?
What strategic gap does it address?]*

## Strategic Objectives (3–5 Year)

| # | Objective | Owner | Target Date | Success Metric |
|---|-----------|-------|-------------|----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Market Analysis

*[Current market conditions, trends, and forces shaping the opportunity.]*

## Competitive Position

*[Where the organization stands relative to competitors. Reference the
companion competitor-analysis document if one exists.]*

## Resource Requirements

| Resource Type | Current State | Required | Gap | Priority |
|--------------|---------------|----------|-----|----------|
| Personnel | | | | |
| Technology | | | | |
| Capital | | | | |

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| | | | |

## Execution Roadmap

### Phase 1: [Name] — Q1–Q2 {{year}}

*[Key milestones and deliverables]*

### Phase 2: [Name] — Q3–Q4 {{year}}

*[Key milestones and deliverables]*

## Success Metrics & KPIs

| KPI | Baseline | Target | Measurement Frequency |
|-----|----------|--------|-----------------------|
| | | | |

## Review Cadence

*[How often this plan is reviewed, by whom, and what triggers an off-cycle review.]*

---

*Document generated by librarian v{{librarian_version}} from template `strategic-plan`.*
```

### Variable substitution

The rendering engine replaces these tokens at scaffold time:

| Variable | Source |
|---|---|
| `{{title}}` | Derived from template display_name or operator override |
| `{{version}}` | Always `V1.0` for new documents |
| `{{date}}` | Today's date in project's configured format |
| `{{author}}` | `project_config.default_author` |
| `{{classification}}` | `project_config.default_classification` |
| `{{status}}` | `draft` (always for new scaffolds) |
| `{{year}}` | Current year |
| `{{project_name}}` | `project_config.project_name` |
| `{{librarian_version}}` | Package `__version__` |

### Custom templates

Projects can add their own templates by placing `.md.j2` files in a `templates/` directory
at the project root (sibling to `docs/`). These take priority over built-in templates
when names collide. The `project_config` block gains a new field:

```yaml
project_config:
  custom_templates_dir: "templates/"   # default: null (built-in only)
```

## CLI: `scaffold` command

```
python -m librarian --registry docs/REGISTRY.yaml scaffold [OPTIONS]

Options:
  --template NAME       Template ID (e.g., strategic-plan, threat-model)
  --title "My Title"    Override the document title
  --folder PATH         Override the suggested output folder
  --author "Name"       Override the default author
  --list                List all available templates for the project's preset
  --list-all            List every template across all presets
  --dry-run             Show what would be created without writing files
  --no-register         Create file but skip registry entry
```

**Behavior:**

1. Load project config (preset detection from `project_config` or explicit `--preset`)
2. Resolve template: check custom dir first, then preset dir, then universal dir,
   then cross-cutting dirs (security/, compliance/)
3. Render variables
4. Apply naming convention: `strategic-plan-20260412-V1.0.md`
5. Write file to suggested_folder (or `--folder` override)
6. Register in REGISTRY.yaml with suggested_tags and cross-references pre-wired
7. Print summary: filename, path, tags, cross-references, recommended companion docs

**Example session:**

```
$ python -m librarian --registry docs/REGISTRY.yaml scaffold --template strategic-plan

Created: executive/strategic-plan-20260412-V1.0.md
  Title:    Strategic Plan
  Status:   draft
  Tags:     strategy, planning, executive
  X-refs:   cost-analysis (not yet created), competitor-analysis (not yet created)

  Recommended companions (not yet in registry):
    - cost-analysis       "Cost Analysis"
    - competitor-analysis  "Competitor Analysis"
    - risk-assessment     "Risk Assessment"

  Run: python -m librarian scaffold --template cost-analysis
```

## CLI: `audit --recommend`

```
python -m librarian --registry docs/REGISTRY.yaml audit --recommend
```

The recommendations engine is an extension of the existing OODA audit cycle. After the
standard audit (drift, naming, orphans, cross-refs, folder density), it adds a
**Recommendations** section.

### How recommendations work

The engine does NOT use AI or heuristics. It uses a deterministic rule set based on the
preset's template catalog and the current registry state.

**Rule 1 — Preset baseline.**
Each preset defines a set of "expected" templates — documents that most projects using
that preset will eventually need. The engine compares the registry's document types/tags
against the expected set and flags gaps.

```python
PRESET_EXPECTATIONS = {
    "software": {
        "core": ["technical-architecture", "project-plan"],
        "recommended": ["security-assessment", "runbook", "test-plan",
                        "architecture-decision-record"],
        "if_public": ["readme", "changelog", "release-notes"],
    },
    "business": {
        "core": ["strategic-plan", "project-management-plan"],
        "recommended": ["cost-analysis", "risk-assessment",
                        "competitor-analysis", "stakeholder-analysis"],
        "if_ip": ["patent-review", "legal-review", "ip-landscape"],
    },
    # ...
}
```

**Rule 2 — Cross-reference pull.**
If document A exists and its template declares `typical_cross_refs: [B, C]`, and B
exists but C doesn't, the engine recommends C. This is how the system learns that a
strategic plan implies a cost analysis — not by guessing, but because the template
metadata says so.

**Rule 3 — Maturity progression.**
Templates declare a `requires` field. If a project has reached a certain document
maturity (e.g., has architecture + implementation plan), the engine suggests the next
logical documents (e.g., security assessment, test plan). This creates a natural
progression without prescribing a rigid sequence.

**Rule 4 — Compliance triggers.**
If the project_config has compliance flags set (via the Settings page compliance
toggles — DoD 5200.01, HIPAA, SEC/FINRA, etc.), the engine pulls in the corresponding
compliance/ and security/ templates as recommendations.

### Recommendation output format

```
═══════════════════════════════════════════════════════════
 RECOMMENDATIONS — Based on 'software' preset, 8 registered docs
═══════════════════════════════════════════════════════════

 CORE (expected for this preset, not yet created):
   ⚠  security-assessment    "Security Assessment"
      → Referenced by: technical-architecture, runbook
      → Run: python -m librarian scaffold --template security-assessment

 RECOMMENDED (common for this preset):
   ○  test-plan              "Test Plan"
   ○  incident-postmortem    "Incident Postmortem"  (template only)

 CROSS-REFERENCE GAPS:
   ○  cost-analysis          Referenced by strategic-plan but not in registry
   ○  risk-assessment        Referenced by strategic-plan but not in registry

 COMPLIANCE:
   (no compliance standards selected — configure via Settings or project_config)

═══════════════════════════════════════════════════════════
```

### Machine-readable output

`audit --recommend --json` produces a JSON array of recommendation objects:

```json
{
  "recommendations": [
    {
      "template_id": "security-assessment",
      "display_name": "Security Assessment",
      "priority": "core",
      "reason": "preset_baseline",
      "referenced_by": ["technical-architecture", "runbook"],
      "scaffold_command": "python -m librarian scaffold --template security-assessment"
    }
  ]
}
```

## Data model changes

### Template dataclass (new: `librarian/templates/_base.py`)

```python
@dataclass
class DocumentTemplate:
    template_id: str                    # unique slug: "strategic-plan"
    display_name: str                   # human-readable: "Strategic Plan"
    preset: str                         # "business", "universal", "security", etc.
    description: str
    suggested_tags: list[str]
    suggested_folder: str               # relative to docs root
    typical_cross_refs: list[str]       # template_ids this doc typically links to
    requires: list[str]                 # template_ids that should exist first
    recommended_with: list[str]         # template_ids commonly created alongside
    sections: list[str]                 # section headings in the skeleton
    body: str                           # raw markdown body with {{variables}}
```

### Config additions (`config.py`)

```python
# Added to DEFAULTS
"custom_templates_dir": None,
"recommendation_rules": {
    "enabled": True,
    "show_core": True,
    "show_recommended": True,
    "show_cross_ref_gaps": True,
    "show_compliance": True,
},
```

### Registry entry additions

No schema changes. Scaffolded documents use existing fields. The `tags` field gets
populated from the template's `suggested_tags`. Cross-references get populated from
`typical_cross_refs` where the target already exists in the registry.

## Implementation plan

### G.1 — Template infrastructure (1 session)

**Deliverables:**
- `librarian/templates/` package with `__init__.py` and `_base.py`
- `DocumentTemplate` dataclass with `from_file()` classmethod
- Variable substitution engine (no Jinja2 — `str.replace()` loop)
- Template discovery: scan built-in dirs + custom dir, deduplicate
- `universal/` templates: readme, project-plan, changelog, meeting-notes
- `scaffold` CLI subcommand (core flow: resolve → render → write → register)
- `scaffold --list` and `scaffold --list-all`
- Tests: template parsing, variable substitution, naming convention application,
  file creation, registry insertion, list output
- Target: ~25 tests

### G.2 — Preset template packs (1 session)

**Deliverables:**
- Template files for all 8 preset-specific directories (software through government)
- Cross-cutting templates: security/ (7 templates) and compliance/ (6 templates)
- Each template has realistic section structures, not just placeholder headings
- `PRESET_EXPECTATIONS` dict wired into each preset
- `scaffold --dry-run` support
- Tests: template count per preset, expected sections present, cross-ref validity
  (every `typical_cross_refs` target exists as a template_id somewhere)
- Target: ~20 tests

### G.3 — Recommendations engine (1 session)

**Deliverables:**
- `librarian/recommend.py` — recommendation logic (Rules 1-4)
- Integration with `audit.py` — `--recommend` flag adds recommendations section
- `audit --recommend --json` machine-readable output
- `PRESET_EXPECTATIONS` expanded with core/recommended/conditional sets
- Compliance trigger integration (reads compliance flags from project_config)
- Dashboard integration: recommendations as a card/section on the dashboard
- Site integration: recommendations page in the static site
- Tests: each rule independently, combined output, JSON format, edge cases
  (empty registry, all templates satisfied, unknown preset)
- Target: ~30 tests

### G.4 — Custom templates & polish (1 session)

**Deliverables:**
- Custom template directory support (`custom_templates_dir` config field)
- Template override: project template beats built-in when IDs collide
- `scaffold --template` tab-completion helper (outputs valid IDs)
- Settings page: template browser section — shows available templates,
  lets operator preview sections before scaffolding
- Scaffold command prints "recommended companions" after creating a doc
- Update SKILL.md with template guidance
- Update README.md with template examples
- Full regression: all existing 329 tests pass + ~20 new tests
- Target: ~20 new tests

### Total estimated new tests: ~95
### Total test target: ~424

## What this does NOT include

- **Content generation.** Templates provide structure, not prose. The librarian will
  never write "Based on market analysis, we recommend..." — that's the operator's job
  or a skill's job.
- **AI-powered recommendations.** The engine uses deterministic rules, not embeddings
  or LLM calls. If a project has a strategic plan template that says it typically
  cross-refs a cost analysis, and there's no cost analysis, the engine recommends one.
  No magic.
- **Workflow enforcement.** The engine suggests, it doesn't block. You can ignore every
  recommendation. There's no "you must create a security assessment before you can
  create a release." The `requires` field is advisory.
- **Blockchain anchoring.** Deferred. Architecturally compatible (the evidence module's
  single SHA-256 seal is the hook point), but adds an external dependency and is only
  valuable for legal/IP use cases. Recommend as a post-Phase G feature: `evidence
  --anchor opentimestamps` as a pluggable adapter.

## Relationship to orchestration and skills

The boundary is clean:

| Layer | Responsibility | Example |
|---|---|---|
| **Librarian templates** | Structure scaffolding | "A strategic plan has these 10 sections" |
| **Librarian recommendations** | Gap detection | "You have 8 docs but no security assessment" |
| **Skills** (doc-coauthoring, etc.) | Content guidance | "Here's how to write the Market Analysis section" |
| **Orchestrator skill** | Multi-doc workflow | "Starting a new product? Create these 6 docs in order" |

The orchestrator is the natural consumer of the recommendations engine. It can call
`audit --recommend --json`, get the gap list, and offer to scaffold the missing docs
in sequence — using the appropriate content skills to help fill them. But the librarian
itself stays governance-only.

## Dependencies

- Phase A–E complete ✅ (foundation, manifest, audit, dashboard, site)
- Phase F (plugin packaging) is NOT required. Templates ship with the Python package.
- No new external dependencies. Template rendering uses `str.replace()`, not Jinja2.

## Risks

**Template bloat.** ~70 template files across all presets. Adds ~200KB to the package.
Acceptable for a governance tool — these are documentation files, not code. Monitor
and prune unused templates based on adoption data after open-source release.

**Recommendation noise.** The engine might suggest 15 documents for a project that
only needs 3. Mitigation: the core/recommended/conditional tiering ensures only 2-3
"core" suggestions appear by default. The full list requires `--recommend --verbose`.

**Template drift from best practices.** Section structures in templates will age.
Mitigation: templates are versioned markdown files. Updates ship with package updates.
Custom templates override built-in ones, so projects aren't forced to adopt changes.

**Cross-preset template ID collisions.** Two presets might define `risk-assessment`
with different sections. Mitigation: template resolution order is explicit —
custom > preset-specific > cross-cutting > universal. The `--list` command shows
which file wins.

## Success criteria

1. `scaffold --list` shows all available templates for the project's preset
2. `scaffold --template strategic-plan` creates a correctly named, registered document
3. `audit --recommend` produces actionable gap analysis with zero false positives on
   a project that has all expected documents
4. Custom templates in a project's `templates/` directory override built-in ones
5. All existing 329 tests continue to pass
6. ~95 new tests cover template parsing, scaffolding, recommendations, and integration

## Cross-references

| Document | Relationship |
|---|---|
| librarian-buildout-plan-20260411-V1.2.md | Parent plan — Phase G extends the A–F roadmap |
| librarian-architecture-20260411-V1.0.md | Architecture doc — needs update for templates module |
| SKILL.md | Skill definition — needs template guidance section |
| README.md | Project README — needs template examples |

## Version history

| Version | Date | Author | Notes |
|---|---|---|---|
| V1.0 | 2026-04-12 | Christopher A. Kahn | Initial plan. Defines template system, scaffold CLI, recommendations engine, and 4-sub-phase implementation roadmap. |
