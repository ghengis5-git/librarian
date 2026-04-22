---
name: package-structure
description: Full Librarian Python package structure including all 57+ document templates across 10 subdirectories. Extracted from CLAUDE.md during v0.8.0 slimming pass so the main handoff doc stays compact.
type: reference
version: V1.0
date: 2026-04-22
superseded_by: null
---

> **This file is the archive of CLAUDE.md's full package tree.** CLAUDE.md itself now carries only a top-level directory list plus a pointer to this file. Read this file when you need the exhaustive list of modules or templates — e.g. when adding a new template, renaming a module, or auditing template coverage across presets. Keep this file in sync with reality: if you add/rename/remove a module or template, update this file and bump its version.

## Package Tree

```
librarian/                  # pip-installable Python package (v0.8.0 local, v0.7.5 published)
├── __init__.py             # public API exports + __version__
├── __main__.py             # CLI: audit (--recommend --json), status, register, bump, manifest, evidence, diff, log, dashboard, site, init, config, scaffold, review, oplog
├── config.py               # configuration system: defaults, presets, naming templates, merge logic
├── naming.py               # naming convention parser + validator (config-aware)
├── versioning.py           # version bump logic
├── registry.py             # REGISTRY.yaml CRUD
├── audit.py                # OODA audit engine + formatter + folder density analysis
├── recommend.py            # recommendations engine: 4 deterministic rules, PRESET_EXPECTATIONS, COMPLIANCE_TEMPLATES
├── manifest.py             # portable JSON + SHA-256 hashes + dependency graph
├── oplog.py                # append-only JSONL operation log
├── oplog_lock.py           # Phase 7.5 — OS-level append-only flag detection (macOS chflags / Linux chattr)
├── evidence.py             # tamper-evident IP evidence pack
├── diffaudit.py            # delta report between two manifests
├── dashboard.py            # dashboard template loader + manifest JSON injection
├── sitegen.py              # static site generator (sidebar tree, grouping, graph)
├── precommit.py            # Phase 7.7 — pre-commit framework native Python entry point (Windows/UNC hardened Session 53)
├── review.py               # Phase 7.2 — next_review field, overdue/upcoming calc, review CLI
├── yaml_errors.py          # Session 53 — friendly YAML parse errors with caret preview
└── templates/              # Phase G — document template system
    ├── __init__.py         # template registry, discovery, resolution, context builder
    ├── _base.py            # DocumentTemplate dataclass + zero-dep mini template engine
    ├── universal/          # templates available to all presets (4)
    │   ├── readme.md
    │   ├── project-plan.md
    │   ├── changelog.md
    │   └── meeting-notes.md
    ├── software/           # software preset templates (8)
    │   ├── architecture-decision-record.md
    │   ├── technical-architecture.md
    │   ├── api-specification.md
    │   ├── runbook.md
    │   ├── security-assessment.md
    │   ├── incident-postmortem.md
    │   ├── test-plan.md
    │   └── release-notes.md
    ├── scientific/         # scientific preset templates (6)
    │   ├── scientific-foundation.md
    │   ├── experiment-protocol.md
    │   ├── literature-review.md
    │   ├── data-management-plan.md
    │   ├── irb-application.md
    │   └── lab-notebook-entry.md
    ├── business/           # business preset templates (8)
    │   ├── strategic-plan.md
    │   ├── cost-analysis.md
    │   ├── competitor-analysis.md
    │   ├── project-management-plan.md
    │   ├── business-case.md
    │   ├── risk-assessment.md
    │   ├── stakeholder-analysis.md
    │   └── executive-summary.md
    ├── legal/              # legal preset templates (7)
    │   ├── legal-review.md
    │   ├── legal-discovery.md                # Session 53 addition
    │   ├── patent-review.md
    │   ├── ip-landscape.md
    │   ├── contract-summary.md
    │   ├── regulatory-compliance-checklist.md
    │   └── nda-tracker.md
    ├── healthcare/         # healthcare preset templates (6)
    │   ├── clinical-protocol.md
    │   ├── hipaa-risk-assessment.md
    │   ├── quality-improvement-plan.md
    │   ├── policy-document.md
    │   ├── incident-report.md
    │   └── credentialing-checklist.md
    ├── finance/            # finance preset templates (6)
    │   ├── due-diligence-report.md
    │   ├── investment-memo.md
    │   ├── compliance-review.md
    │   ├── audit-finding.md
    │   ├── risk-assessment-finance.md
    │   └── regulatory-filing-checklist.md
    ├── government/         # government preset templates (6)
    │   ├── policy-directive.md
    │   ├── standard-operating-procedure.md
    │   ├── memorandum.md
    │   ├── acquisition-plan.md
    │   ├── security-plan.md
    │   └── after-action-report.md
    ├── security/           # cross-cutting security templates (7)
    │   ├── threat-model.md
    │   ├── vulnerability-assessment.md
    │   ├── penetration-test-report.md
    │   ├── security-architecture-review.md
    │   ├── incident-response-plan.md
    │   ├── access-control-matrix.md
    │   └── data-classification-policy.md
    └── compliance/         # cross-cutting compliance templates (6)
        ├── sox-controls-matrix.md
        ├── gdpr-dpia.md
        ├── pci-dss-checklist.md
        ├── iso27001-statement-of-applicability.md
        ├── audit-readiness-checklist.md
        └── vendor-risk-assessment.md
```

## Template Counts by Preset

| Preset       | Dedicated | + Universal | + Cross-cutting (security+compliance) | Total visible |
|--------------|-----------|-------------|---------------------------------------|---------------|
| software     | 8         | 4           | 13                                    | 25            |
| scientific   | 6         | 4           | 13                                    | 23            |
| business     | 8         | 4           | 13                                    | 25            |
| legal        | 7         | 4           | 13                                    | 24            |
| healthcare   | 6         | 4           | 13                                    | 23            |
| finance      | 6         | 4           | 13                                    | 23            |
| government   | 6         | 4           | 13                                    | 23            |

Cross-cutting `security/` (7) and `compliance/` (6) directories are auto-loaded for every preset via the `CROSS_CUTTING` tuple in `templates/__init__.py`. Custom templates (from `project_config.custom_templates_dir`) override any built-in on ID collision.

## Test Files (`tests/`)

Test suite currently at **849 tests across 17 test files** (see CLAUDE.md Test Suite section for the full phase-by-phase breakdown). Files under `tests/`:

- `test_naming.py`, `test_versioning.py`, `test_registry.py`, `test_audit.py` (Phase A foundation)
- `test_config.py`, `test_config_merge.py`, `test_naming_config.py`, `test_cli_init.py`, `test_cli_config.py` (config system)
- `test_manifest.py`, `test_oplog.py`, `test_evidence.py`, `test_diffaudit.py` (Phase B/C)
- `test_dashboard.py`, `test_sitegen.py` (Phase D/E)
- `test_templates.py` (Phase G template infrastructure + all preset templates)
- `test_recommend.py` (Phase G.3 recommendations engine)
- `test_precommit_hook.py`, `test_precommit.py` (Phase 7.1 shell hook + Phase 7.7 Python entry point)
- `test_review.py` (Phase 7.2 next_review)
- `test_oplog_lock.py` (Phase 7.5 append-only detection)
- `test_yaml_errors.py` (Session 53)

See also:

- `docs/session-history-20260422-V1.0.md` — archived Session 31-52 Deliverables (the *why* behind each template directory and module).
- `CLAUDE.md` — current live handoff doc. Session 53+ deliverables live there.
