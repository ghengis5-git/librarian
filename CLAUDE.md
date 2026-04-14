# Librarian — Claude Code Instructions

## Project Overview
Standalone document governance tool. Enforces naming conventions, tracks versions,
manages cross-references, produces tamper-evident manifests and audit trails.
Project-agnostic by design — works with any project that supplies a REGISTRY.yaml.

**Solo development — local only.**

---

## Execution Environment
- **Always** activate the virtual environment first: `source .venv/bin/activate`
- **Always** run scripts from project root: `~/projects/librarian`
- Run Python as: `python` (not `python3`)
- Do not use `sudo`
- Never use `nano` or other interactive editors — use file tools instead

---

## Package Structure
```
librarian/                  # pip-installable Python package (v0.7.0)
├── __init__.py             # public API exports + __version__
├── __main__.py             # CLI: audit (--recommend --json), status, register, bump, manifest, evidence, diff, log, dashboard, site, init, config, scaffold
├── config.py               # configuration system: defaults, presets, naming templates, merge logic
├── naming.py               # naming convention parser + validator (config-aware)
├── versioning.py           # version bump logic
├── registry.py             # REGISTRY.yaml CRUD
├── audit.py                # OODA audit engine + formatter + folder density analysis
├── recommend.py            # recommendations engine: 4 deterministic rules, PRESET_EXPECTATIONS, COMPLIANCE_TEMPLATES
├── manifest.py             # portable JSON + SHA-256 hashes + dependency graph
├── oplog.py                # append-only JSONL operation log
├── evidence.py             # tamper-evident IP evidence pack
├── diffaudit.py            # delta report between two manifests
├── dashboard.py            # dashboard template loader + manifest JSON injection
├── sitegen.py              # static site generator (sidebar tree, grouping, graph)
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
    ├── legal/              # legal preset templates (6)
    │   ├── legal-review.md
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

---

## CLI Reference
```
python -m librarian --registry <path> <command>

Commands:
  audit       OODA governance audit (drift, naming, orphans, cross-refs, folder suggestions, --recommend, --json)
  scaffold    Create a new document from a template (--list, --list-all, --dry-run, --no-register)
  status      Quick registry summary (counts by status)
  register    Add a new document entry to the registry
  bump        Version-bump an existing document
  manifest    Generate portable JSON manifest (--no-snapshot, --no-hashes, --no-graph)
  evidence    Generate tamper-evident IP evidence pack (-o output.json)
  diff        Compare two manifests (old.json new.json --json)
  log         Read/filter operation log (--since, --last N)
  dashboard   Render interactive HTML dashboard from manifest
  site        Generate full static site with sidebar tree navigation
  init        Scaffold a new REGISTRY.yaml from a preset (--preset, --naming-template, --create-folders)
  config      Show resolved config or list presets/templates (--list-presets, --list-templates, --preset)
```

---

## Test Suite
- **774 tests** across 16 test files
- Phase A: 36 (naming 10, versioning 10, registry 10, audit 6)
- Config: 56 (presets 8, templates 6, loading 7, naming-config 10, configurable-naming 9, parse 4, CLI init 5, CLI config 3, merge 4)
- Phase B: 26 (manifest)
- Phase C: 90 (oplog 31, evidence 24, diffaudit 35)
- Phase D: 16 (dashboard)
- Phase E: 74 (sitegen 23 + sidebar/grouping 16 + markdown/content 27 + tree diagram 8)
- Settings page: 9 (compliance standards, preview panel, gear icon)
- Settings interactivity: 18 (onclick quoting, ID consistency, STANDARDS completeness, toggle/deselect, YAML export)
- Editable tags + new fields: 20 (tag CRUD, logo field, disclaimer dropdown, YAML export coverage)
- Folder suggestions: 8 (audit density analysis)
- Phase G.1 Templates: 56 (engine 20, dataclass 3, frontmatter 2, discovery 7, context 5, scaffold CLI 11, condition eval 4, security 4)
- Phase G.2a Software+Scientific: 17 (software count/ids/sections/tags/xrefs/conditionals 8, scientific count/ids/sections/xrefs/conditionals/requires 9)
- Phase G.2b Business+Legal: 15 (business count/ids/sections/tags/xrefs/conditionals/isolation 8, legal count/ids/sections/xrefs/conditionals 7)
- Phase G.2c Healthcare+Finance+Government: 24 (healthcare count/ids/sections/tags/xrefs/conditionals/isolation 8, finance count/ids/sections/xrefs/conditionals/isolation 8, government count/ids/sections/xrefs/conditionals/isolation 8)
- Phase G.2d Security+Compliance cross-cutting: 28 (security count/ids/sections/xrefs/conditionals 7, compliance count/ids/sections/xrefs/conditionals 7, cross-cutting resolution parametrized 14)
- Phase G.3 Recommendations: 39 (preset expectations 4, compliance templates 2, rule 1 baseline 8, rule 2 cross-ref 3, rule 3 maturity 3, rule 4 compliance 5, dedup 2, report 3, formatter 6, CLI integration 3)
- Phase G.4 Templates page + integration: 32 (catalog page 12, nav links 4, index recommendations 5, dashboard overlay 1, CSS 2, settings template browser 3, custom template override 5)
- Security hardening: 20 (XSS safe_url 10, manifest path traversal 3, template recursion depth 1, script breakout 3, sitegen path traversal 3)
- Oplog hash chaining: 12 (genesis/linking/three-entry/compat/v1-json/passthrough 6, verify chain 5, format indicator 1)
- Evidence signing: 12 (default off 2, signing config 8, verify returns 1, signed pack mock 1)
- Folders Only fix: 1 (branch expansion)
- Manage page: 16 (exists/title/sections/nav/data/forms/JS/search/CSS/index)
- Audit page: 21 (exists/title/sections/KPI/nav/data/JS/controls/seal/CLI/recs/OODA/oplog/CSS/search-index/global-search + Phase 7.2 overdue KPI + overdue CLI card + Phase 7.5 oplog KPI + oplog CLI cards)
- Phase 7.1 Pre-commit hook: 11 (grep unit 8 + end-to-end 3 — list-item/indented YAML, filename-only entries, substring suffix/prefix rejection, dots-metachar exploit)
- Phase 7.2 Review deadlines: 49 (parse 9, format 2, compute_overdue 9, compute_upcoming 4, audit integration 3, CLI register 3, CLI bump 4, CLI review subcommand 9, CLI audit JSON 1, + 5 infrastructure)
- Phase 7.5 Oplog append-only: 30 (platform support 6, dispatch 2, macOS stat-flag 5, Linux lsattr parsing 7, instruction strings 5, audit integration 5)
- Run: `python -m pytest tests/ -v --tb=short`
- **Always** run tests before any commit

---

## Current State
**Version:** 0.7.3 released (tag `v0.7.3`, PyPI https://pypi.org/project/librarian-2026/0.7.3/, GitHub release). `HEAD` on main is ahead of the tag with Phase 7.5 (oplog append-only lock) unreleased work; manifests still read `0.7.3`. Next release target is v0.7.4.
**Tests:** 774/774 PASS (681 pre-session + 11 Phase 7.1 + 51 Phase 7.2 + 31 Phase 7.5)

### Completed Phases
- **Phase A** (Sessions 26–27): Foundation — Python package, 4 CLI subcommands, pre-commit hook
- **Phase B** (Session 28): Manifest system — portable JSON + SHA-256 + dependency graph
- **Phase C** (Session 28): Audit extensions — operation log, evidence pack, diff audit
- **Phase D** (Session 29): Interactive dashboard — Lunr search, cytoscape.js graph, filter chips, timeline
- **Phase E** (Session 29): Static site generator — multi-page HTML, per-doc pages, graph page
- **Sidebar + grouping** (Session 30): Collapsible tree nav with status/tag/path grouping modes
- **Folder suggestions** (Session 30): Audit auto-detects crowded directories/tags, suggests reorganization
- **Design refresh** (Session 30): Unified design tokens across sitegen + dashboard template
- **Website completion** (Session 31): Doc page content rendering, search/filter, tree page, dashboard nav, bug fixes

### Session 31 Deliverables
- Zero-dep markdown→HTML converter (`_md_to_html`) — headings, code blocks, lists, tables, blockquotes
- Doc pages render real file content (prose for .md, syntax blocks for .yaml/.json/.sh)
- Index page: client-side text search + status filter chips (All/Active/Draft/Superseded)
- Folder structure page (`tree.html`) — directory cards with file tables
- Dashboard nav overlay — floating frosted-glass bar injected into standalone dashboard
- Replaced `<base>` tag with explicit `path_prefix` pattern for correct relative links
- Cytoscape.js loading hardened — graceful fallback, case-insensitive extraction, PermissionError handling
- Sidebar JS escaping fix (`\\x27` instead of `\'`)
- 27 new tests (markdown, content rendering, search/filter, doc page content, tree page)
- Site generates 14 pages (index, tree, graph, dashboard, 10 doc pages)

### Session 32 Deliverables
- Interactive folder-tree diagram on tree.html — expandable/collapsible, click-to-scroll, status dots
- Configuration system (`config.py`) with layered merge: defaults → preset → project_config overrides
- 9 preset packs: software, business, accounting, government, scientific, finance, healthcare, legal, minimal
- 8 naming templates: default, legal, engineering, corporate, dateless, scientific, healthcare, finance
- Configurable naming: separator (-/_/.), case (lower/mixed/upper), date (YYYYMMDD/YYYY-MM-DD/off), version (VX.Y/vX.Y/X.Y), domain prefix
- Configurable category strictness: soft (warn) or hard (reject) mode
- `init` CLI command: scaffold REGISTRY.yaml from preset + naming template, optionally create folders
- `config` CLI command: show resolved config, list presets, list naming templates
- Updated naming.py: fully config-aware parser and validator, backward-compatible with default behavior
- Interactive Settings page — gear icon (far right, tooltip-only), form inputs for all config, live naming preview, YAML export
- Document header/footer/metadata config: organization, classification banner, doc-id, distribution, retention, copyright
- Government/military preset: DoD 5200.01 classification markings (UNCLASSIFIED through TOP SECRET), CUI support
- HeaderConfig, FooterConfig, MetadataRequirements dataclasses in config.py
- Settings page sections for Document Header/Footer and Required Metadata fields
- Gear icon refactored to `_gear_link()` helper, positioned far right after seal in header flex layout
- Dashboard overlay nav uses gear icon instead of text Settings link
- Compliance Standards toggles: DoD 5200.01, ISO 9001, HIPAA, SEC/FINRA, Research/Academic, Legal
- Live preview panel: sticky sidebar showing filename, header, footer, metadata previews in real-time
- Compliance buttons auto-apply naming, header/footer, and metadata rules from industry standards
- 56 config tests + 8 tree diagram tests + 9 settings page tests = 73 new tests (291 total)

### Session 33 Deliverables
- **Critical JS fix:** All `onclick` handlers used `\x27` (literal text) instead of `'` (actual quote) — `\x27` is only valid inside JS string literals, not HTML attributes. Every button/toggle silently failed. Replaced all 19 HTML-context `\x27` with `'`.
- **Compliance toggle-off:** Clicking an already-selected compliance button now deselects it and restores project defaults. Added `captureDefaults()` (snapshots form state on page load), `applyFields()` (shared setter), and `wasActive` toggle logic.
- **Compliance active state:** Solid accent background + white text/icons when selected (was nearly invisible border ring before).
- **Missing org field:** `applyStandard()` now sets `cfg-hdr-org` from STANDARDS object.
- 18 new comprehensive interactivity tests (309 total): onclick quoting, ID consistency, STANDARDS completeness, toggle/deselect, YAML export coverage, preview opacity behavior.

### Session 34 Deliverables
- **Editable tag lists:** Forbidden words, exempt files, and tags taxonomy now have add/remove UI (`addTag()`, `removeTag()`, `getTagValues()` JS helpers, `×` remove buttons on each tag)
- **Company logo URL field:** `cfg-hdr-logo` input in Document Header section, wired into captureDefaults, applyFields, all 6 STANDARDS entries, YAML export (`logo_url:`), and live preview (shows filename indicator)
- **Legal disclaimer presets:** `cfg-ftr-disclaimer` dropdown with 7 industry options (general, HIPAA, financial, legal, government, academic, technology). `DISCLAIMERS` object with full text, `applyDisclaimer()` sets footer custom text.
- **YAML export extended:** `generateYaml()` now exports forbidden_words, exempt_files, and tags_taxonomy lists via `getTagValues()`
- **CSS additions:** `.tag-remove`, `.settings-tag-add`, `.settings-disclaimer-select` styles for editable tags and disclaimer dropdown
- **Safe HTML escaping:** `escHtml()` uses DOM `createTextNode` pattern; `renderLines()` replaces raw `.innerHTML`
- 20 new tests (329 total): editable tag CRUD functions, logo field presence/preview/YAML/standards, disclaimer dropdown/object/options, YAML export coverage for new fields

### Session 35 Deliverables
- **Phase G plan:** `docs/phase-g-templates-and-recommendations-20260412-V1.0.md` — document templates and recommendations engine
- **Former-project scrub completed** (Session 34 carryover): All references to the former consumer project removed across entire codebase (re-verified Session 47)
- **Registry cleanup** (Session 34 carryover): 17 documents registered (14 active, 1 draft, 2 superseded), 0 naming violations, 0 pending cross-refs
- **Pre-commit hook hardened**: Removed `py` from DOC_EXTENSIONS, added source dirs to SKIP_DIRS, warnings pass in non-interactive mode
- **Audit false positive fix**: `audit.py` now checks registered `path` for files outside `tracked_dirs`

### Session 36 Deliverables (Phase G.1 — Template infrastructure)
- **Mini template engine** (`_base.py`, ~260 lines): Zero-dependency engine with `{{variable}}` substitution, `{% if %}` / `{% elif %}` / `{% else %}` / `{% endif %}` conditionals, `{% for %}` / `{% endfor %}` iteration. Supports truthiness, `==`, `!=`, `in` membership, `and`, `or`, `not` operators. No arbitrary Python eval.
- **DocumentTemplate dataclass**: `from_string()`, `from_file()`, `render()` — parses YAML frontmatter + markdown body, renders with context dict
- **Template registry** (`templates/__init__.py`): `discover_templates()`, `load_template()`, `list_templates()`, `build_context()` — scans built-in dirs + custom dir with resolution priority: custom > preset > cross-cutting > universal
- **4 universal templates**: `readme`, `project-plan`, `changelog`, `meeting-notes` — each with YAML frontmatter (template_id, display_name, suggested_tags, cross-refs, sections) and conditional blocks for compliance standards
- **`scaffold` CLI subcommand**: `--template`, `--title`, `--folder`, `--author`, `--preset`, `--list`, `--list-all`, `--dry-run`, `--no-register`. Creates properly named file, registers in REGISTRY.yaml with tags/cross-refs, logs operation, prints recommended companions.
- **Context builder**: Reads `project_config` (preset, compliance flags, naming rules, header/footer config) and builds the dict that feeds the engine
- **56 new tests** (385 total): engine variable substitution (5), conditionals (11), for loops (4), condition eval (4), DocumentTemplate (3), frontmatter (2), discovery (7), context builder (5), scaffold CLI (11), security hardening (4)

### Session 37 Deliverables (Phase G.2a — Software + Scientific templates)
- **8 software templates**: architecture-decision-record, technical-architecture, api-specification, runbook, security-assessment, incident-postmortem, test-plan, release-notes
- **6 scientific templates**: scientific-foundation, experiment-protocol, literature-review, data-management-plan, irb-application, lab-notebook-entry
- **Compliance conditionals**: security-assessment has ISO 27001 + HIPAA + DoD 5200 conditional blocks; data-management-plan has HIPAA + ISO 27001 + DoD 5200; experiment-protocol has HIPAA + ISO 9001; test-plan has ISO 9001; technical-architecture has ISO 27001 + DoD 5200
- **Cross-reference integrity**: all cross-refs resolve within each preset's template set
- **IRB requires field**: irb-application declares `requires: [experiment-protocol]` — first use of prerequisite chain
- **17 new tests** (402 total): template counts, ID verification, section counts, tag counts, cross-ref validity, conditional rendering (ISO 27001, HIPAA), prerequisite chains, preset isolation

### Session 38 Deliverables (Phase G.2b — Business + Legal templates)
- **8 business templates**: strategic-plan, cost-analysis, competitor-analysis, project-management-plan, business-case, risk-assessment, stakeholder-analysis, executive-summary
- **6 legal templates**: legal-review, patent-review, ip-landscape, contract-summary, regulatory-compliance-checklist, nda-tracker
- **Compliance conditionals**: strategic-plan has SEC/FINRA + ISO 9001; risk-assessment has ISO 9001 + ISO 27001; regulatory-compliance-checklist has HIPAA + ISO 27001 + SEC/FINRA + DoD 5200; contract-summary has HIPAA (BAA) + SEC/FINRA; legal-review has HIPAA + SEC/FINRA
- **Cross-reference integrity**: all cross-refs resolve within each preset's template set + universal
- **Preset isolation**: business templates don't leak into scientific, legal don't leak into software
- **15 new tests** (417 total): business count/ids/sections/tags/xrefs/conditionals/isolation (8), legal count/ids/sections/xrefs/conditionals (7)

### Session 39 Deliverables (Phase G.2c — Healthcare + Finance + Government templates)
- **6 healthcare templates**: clinical-protocol, hipaa-risk-assessment, quality-improvement-plan, policy-document, incident-report, credentialing-checklist
- **6 finance templates**: due-diligence-report, investment-memo, compliance-review, audit-finding, risk-assessment-finance, regulatory-filing-checklist
- **6 government templates**: policy-directive, standard-operating-procedure, memorandum, acquisition-plan, security-plan, after-action-report
- **Compliance conditionals**: healthcare templates use HIPAA + ISO 27001 + ISO 9001; finance templates use SEC/FINRA + HIPAA; government templates use DoD 5200 + ISO 9001
- **Cross-reference integrity**: all cross-refs resolve within each preset's template set + universal
- **Preset isolation**: healthcare/finance/government templates don't leak across presets
- **Template ID collision avoidance**: finance risk-assessment uses `risk-assessment-finance` to avoid collision with business `risk-assessment`
- **24 new tests** (441 total): healthcare 8, finance 8, government 8 — each covering count/ids/sections/tags/xrefs/conditionals/isolation

### Session 40 Deliverables (Phase G.2d — Cross-cutting Security + Compliance templates)
- **7 security templates** (cross-cutting — available to all presets): threat-model, vulnerability-assessment, penetration-test-report, security-architecture-review, incident-response-plan, access-control-matrix, data-classification-policy
- **6 compliance templates** (cross-cutting — available to all presets): sox-controls-matrix, gdpr-dpia, pci-dss-checklist, iso27001-statement-of-applicability, audit-readiness-checklist, vendor-risk-assessment
- **Cross-cutting resolution**: security/ and compliance/ directories auto-loaded for every preset via `CROSS_CUTTING` tuple in `templates/__init__.py` — no code changes needed
- **Compliance conditionals**: threat-model (HIPAA + DoD 5200 + ISO 27001), data-classification-policy (DoD 5200 + HIPAA + SEC/FINRA), audit-readiness-checklist (5 compliance blocks: ISO 9001/27001 + HIPAA + SEC/FINRA + DoD 5200), vendor-risk-assessment (HIPAA + SEC/FINRA), gdpr-dpia (HIPAA), iso27001-statement-of-applicability (HIPAA), penetration-test-report (HIPAA), incident-response-plan (HIPAA), access-control-matrix (HIPAA + DoD 5200), security-architecture-review (ISO 27001 + DoD 5200), sox-controls-matrix (SEC/FINRA)
- **Cross-reference integrity**: all cross-refs resolve within security + compliance cross-cutting sets
- **28 new tests** (469 total): TestSecurityTemplates (7), TestComplianceTemplates (7), TestCrossCuttingResolution (14 parametrized — 7 presets × 2 cross-cutting dirs)

### Session 41 Deliverables (Phase G.3 — Recommendations engine)
- **`librarian/recommend.py`** (~230 lines): Deterministic gap analysis engine with 4 rules
  - Rule 1 (Preset baseline): `PRESET_EXPECTATIONS` dict with core/recommended template sets for all 7 presets (software, business, legal, scientific, healthcare, finance, government)
  - Rule 2 (Cross-reference pull): Scans `typical_cross_refs` from present docs, flags missing targets with `referenced_by` attribution
  - Rule 3 (Maturity progression): Checks template `requires` fields; recommends templates when all prerequisites are present
  - Rule 4 (Compliance triggers): `COMPLIANCE_TEMPLATES` maps 5 flags (hipaa, dod_5200, iso_9001, iso_27001, sec_finra) to security/compliance template IDs
- **Deduplication**: Each template_id appears at most once; earlier rules take priority (core > recommended > cross_ref > maturity > compliance)
- **CLI integration**: `audit --recommend` appends formatted recommendations after standard OODA audit; `audit --json` produces machine-readable JSON (works with or without `--recommend`)
- **`Recommendation` + `RecommendationReport` dataclasses**: `.to_dict()` for JSON serialization, category properties (`.core`, `.recommended`, `.cross_ref_gaps`, `.maturity`, `.compliance`)
- **`format_recommendations()`**: Human-readable formatter matching the plan's output format (CORE/RECOMMENDED/CROSS-REFERENCE GAPS/MATURITY PROGRESSION/COMPLIANCE sections)
- **39 new tests** (508 total): preset expectations structure (4), compliance templates structure (2), Rule 1 (8), Rule 2 (3), Rule 3 (3), Rule 4 (5), deduplication (2), report dataclass (3), formatter (6), CLI integration (3)

### Session 42 Deliverables (Phase G.4 — Templates catalog page + site integration)
- **Template Catalog page** (`templates.html`): New page in the static site with a filterable card grid of all available templates
  - Preset switcher dropdown to browse templates across all 7 presets
  - Source filter (Universal, Security, Compliance, Custom, or per-preset)
  - Compliance filter (HIPAA, DoD 5200, ISO 9001, ISO 27001, SEC/FINRA)
  - Cards display: template name, description, section count, tag count, cross-ref count, source badge
  - Click-to-expand: full section list, cross-ref links, compliance conditionals, requires/recommended-with, scaffold command
  - Cross-ref links between template cards (click scrolls to target card)
  - Source badges with distinct colors: universal (blue), security (red), compliance (gold), custom (green)
  - Client-side filtering via JSON template data — no server round-trips
- **Navigation integration**: "Templates" link added to all site nav bars (header nav, sidebar pages, dashboard overlay nav)
- **Recommendations on index page**: Index page now renders a recommendations panel below the document table, showing core/recommended/cross-ref/maturity/compliance gaps with priority color coding
- **`_build_recommendations_html()` helper**: Reusable function that generates recommendations HTML from any manifest, returns empty string if no gaps
- **CSS additions**: 30+ new CSS classes for template cards (`.tmpl-*`) and recommendations panel (`.rec-*`), following existing design token system
- **24 new tests** (532 total): templates catalog page (12), navigation links (4), index recommendations (5), dashboard overlay (1), CSS presence (2)

### Session 42b Deliverables (Phase G.4 completion)
- **Settings page template browser**: "Available Templates" section with scrollable table listing all templates for the active preset, click-to-copy scaffold command, auto-refreshes when preset dropdown changes
- **Custom templates dir support**: `custom_templates_dir` config field wired through settings page, scaffold CLI, and site generator; custom templates override built-in when IDs collide
- **SKILL.md updated** (V1.1): Added Document Templates section covering scaffold command, template organization table, custom templates, compliance conditionals, recommendations engine
- **README.md updated**: Added scaffold to CLI commands table, new Document Templates section with usage examples, updated test count to 540
- **8 new tests** (540 total): settings template browser (3), custom template override/add/none/nonexistent/scaffold-cli (5)

### Session 43 Deliverables (Security hardening + oplog chaining + evidence signing)
- **Security review document**: `docs/security-review-20260413-V1.0.md` — 8-item finding catalog with severity/effort/remediation
- **XSS prevention** (`sitegen.py`): `_safe_url()` blocks javascript:/data: URIs in links and images; `esc()` JS function escapes single quotes with `&#39;`; tree page onclick handlers use `&#39;` instead of `\x27`
- **Path traversal prevention** (`manifest.py`): `.resolve()` + `.relative_to()` on explicit `path` fields; TOCTOU fix replacing `is_file()` with try/except
- **Template recursion guard** (`templates/_base.py`): `_MAX_CONDITION_DEPTH = 20` prevents stack overflow from deeply nested conditionals
- **Custom template path hardening** (`templates/__init__.py`): `.resolve()` before loading custom template directories
- **Oplog hash chaining** (`oplog.py`): SHA-256 chain with `prev_hash` field, genesis sentinel, `fcntl.flock()` write exclusivity, `verify_chain()` integrity checker, backward-compatible with v1 logs, chain indicator (⛓) in formatted output
- **Evidence signing feature flag** (`evidence.py`): `evidence_signing: off|gpg|ssh` in `project_config`. Captures git commit signature via `git log --format=%G?|%GS|%GK|%GT`. `SigningError` with setup instructions. No network calls.
- **SSH signing parser fix** (`evidence.py`): Pipe-delimited format without `--show-signature` (which mixed banner text into stdout). Takes last non-empty line.
- **`setup-signing.sh`**: Automated GPG/SSH signing configuration script; fixed macOS BSD sed compatibility
- **Config update**: `evidence_signing: "off"` added to DEFAULTS; `evidence_signing: ssh` set in project REGISTRY.yaml
- **Updated exports** (`__init__.py`): `SigningError`, `verify_chain` added to public API
- **38 new tests** (578 total): XSS safe_url (10), path traversal (3), recursion depth (1), oplog chaining (6), verify chain (5), format indicator (1), evidence signing config (8), default off (2), verify signature (1), signed pack mock (1)

### Session 44 Deliverables (Website improvements + wizard + settings UX)
- **Header redesign**: Removed seal hash from top, removed diamond bullet, added SVG logo mark, Playfair Display serif font for brand title, brass/gold gear icon (22px, `--gear-color: #b07d2e`)
- **Dashboard removed from site**: Index + Graph + Tree cover all features; standalone `librarian dashboard` CLI preserved for portable single-file export
- **Nav updates**: "Index" renamed to "Home", Dashboard link removed
- **Tree page Folders Only mode**: Collapse All / Expand All / Folders Only toggle buttons with `toggleFoldersOnly()` JS
- **24 compliance standards**: Expanded from 6 to 24 across all touchpoints (Settings buttons, STANDARDS JS object, COMPLIANCE_TEMPLATES in recommend.py, disclaimer dropdown). Two-tier layout with industry filter dropdown.
- **Setup wizard** (`wizard.html`): 5-step questionnaire — use case (Personal/Business/Both) → industry → compliance → formality (Minimal/Standard/Strict) → org details. Generates ready-to-paste `project_config` YAML block.
- **Settings Basic/Advanced toggle**: BASIC view as default showing only Project Basics + Compliance Standards. Advanced reveals all settings sections. `data-view` attributes control visibility.
- **Settings search bar**: Search icon + input field in settings topbar. Searches section headers, field labels, and hints. Auto-switches to Advanced view on search. Highlights matching rows, dims non-matching sections, scrolls to first match.
- **Template catalog search**: Search input added to templates page filter bar. Searches template id, name, description, tags, and section names. Works alongside preset/source/compliance dropdowns.
- **Compliance filter fix**: Template compliance detection expanded from 5 flags to 22 (now catches `gdpr` and `sox`). Compliance dropdown dynamically trimmed to only show flags with actual template content (8 options instead of 23 dead-end options).
- **36 new tests** (614 total): wizard page (12), settings view toggle (10), settings search bar (4), template search input (4), compliance filter accuracy (6)

### Session 45 Deliverables (Manage page + Audit page + bug fixes)
- **Folders Only fix** (tree.html): `toggleFoldersOnly()` now expands all collapsed branches before hiding files, showing full nested hierarchy instead of just top-level folders
- **Settings template browser fix**: `renderSettingsTemplates()` now shows all templates when no preset is selected (was filtering for empty string)
- **Project Manager page** (`manage.html`): Full document management page with 4 collapsible sections:
  - Unregistered Files — shows files on disk not in registry, one-click `quickRegister()` buttons
  - Register Existing File — form with filename, path, status, description, tags → generates `librarian register` CLI command
  - Create Folder — path input → generates `mkdir -p` command
  - Scaffold from Template — preset/template/title/folder/author → generates `librarian scaffold` command
  - Shared: sticky command output panel, section collapse, shell quoting, datalist autocomplete, scaffold live preview
- **Audit & Verify page** (`audit.html`): Unified governance health dashboard with 6 sections:
  - KPI cards: Registered, Unregistered, Missing, Naming Issues, Chain Integrity
  - OODA Audit: unregistered/missing/naming/cross-ref/folder findings with severity coloring
  - File Integrity: SHA-256 hash table with search filter and full-hash toggle
  - Operation Log: last 20 oplog entries with operation badges and chain status
  - Manifest Seal: full SHA-256 seal display with copy button and explanation
  - Recommendations: grouped by category (core/recommended/cross-ref/maturity/compliance)
  - CLI Commands: 6 copy-to-clipboard cards for forensic commands
  - Runs actual audit at site-gen time; reads real oplog and chain verification
- **Nav bar updated**: Added Manage and Audit links (Home → Manage → Audit → Tree → Graph → Templates)
- **60+ CSS classes**: `.mgr-*` for Manage page, `.aud-*` for Audit page, `.kpi-ok/warn/err` status colors
- **Adversarial security review**: Found and fixed 2 vulnerability classes:
  - CRITICAL: `</script>` breakout in all JSON data embedded in `<script>` tags — `_json_safe()` helper escapes `</` → `<\/` in 17 call sites across all pages
  - HIGH: Path traversal in `_render_file_content()` — added `.resolve()` + `.relative_to()` guard, blocks `../` and symlink escapes
  - Template engine confirmed safe (no code execution, no builtin access, depth guard works)
  - Oplog chain integrity verified (detect-only by design, not prevention)
- **40 new tests** (673 total): Manage page (16), Audit page (17), Folders Only fix (1), script breakout (3), path traversal (3)

### Session 46 Deliverables (Phase F kickoff + security residuals)
- **Phase F plan corrected to V1.1** (`docs/phase-f-plugin-and-release-20260413-V1.1.md`): `doc-librarian` → `librarian` project name corrected throughout; PyPI namespace treated as unresolved open question (current pyproject uses `librarian-2026` fallback); session plan renumbered to 46/47; V1.0 marked superseded with banner and registry entry updated (`status: superseded`, `superseded_by: V1.1`).
- **Version bumps**: `librarian/__init__.py`, `pyproject.toml`, `.claude-plugin/plugin.json` → 0.7.1.
- **Marketplace scaffolding**: `marketplace.json` created at repo root — self-contained marketplace manifest for `librarian@librarian-marketplace` install path; ready for separate-repo or same-repo submission.
- **Registry updated**: `phase-f-plugin-and-release-20260413-V1.1.md` registered as draft; V1.0 moved to superseded with forward pointer.
- **Scrub partial**: `skills/librarian/` created as rename target. Cowork sandbox blocks `rm` on tracked files so `skills/doc-librarian/` coexists temporarily — must be removed in host terminal during Session 47 publish prep. Other `doc-librarian` residuals catalogued in V1.1 §Scrub pass (legacy dashboard filenames under `dashboard/legacy/`, one example manifest).
- **README updated**: test count 578 → 673.
- **Security residuals addressed** (2 of 3 remaining LOW items from Session 45):
  - **Template for-loop iterator coverage** (`librarian/templates/_base.py`): now accepts any iterable (set, dict_keys, generators, custom iterables) via `list(iterable)` unpacking; rejects str/bytes to avoid accidental character-iteration. Empty/falsy iterables still skip cleanly.
  - **Template engine output size guard** (`librarian/templates/_base.py`): new `_MAX_RENDER_BYTES = 4 MB` cap and `TemplateRenderError` exception raised when `render_template()` output exceeds cap. Prevents resource exhaustion from hostile templates. Exported from `librarian.templates` and top-level `librarian` package.
  - **Remaining**: oplog chain is still detect-only; changing it to prevention-mode requires oplog-format approval (CLAUDE.md §When to Stop and Ask).
- **8 new tests** (681 total; confirmed in host Session 48): for-loop over set/dict_keys/generator (3), for-loop rejects str/bytes (2), output size under limit (1), over limit raises (1), `_MAX_RENDER_BYTES` sanity (1), plus the existing `test_empty_list` still passes under the new logic.
- **Open Phase F blockers** (need user decision before Session 47 publish): (1) PyPI namespace (`librarian-docs` / keep `librarian-2026` / new name); (2) git history strategy (squash vs. full); (3) GitHub org vs. personal; (4) hook ship-enabled vs. opt-in; (5) IP clearance.

### Session 47 Deliverables (Phase F blocker resolution — scrub, hook, decisions)
- **Former-project (PRISM) scrub — verified clean**: grep for `prism` case-insensitive across entire repo → **0 matches**. Residuals cleaned: (1) polluted `examples/manifests/example-manifest-20260411-V1.0.json` (216 PRISM hits) replaced with generic minimal example manifest; (2) `dashboard/legacy/*.{html,jsx}` (88 combined hits) replaced with tombstone stubs pointing at the active `librarian-dashboard-template-20260412-V3.0.html`; (3) Phase F V1.0 + V1.1 plans cleaned — 10 PRISM mentions rewritten as "former-project references"; (4) CLAUDE.md Session 35 deliverable line rephrased. Sandbox blocks `rm` on tracked files, so `dashboard/legacy/*` stubs remain in tree and must be removed in host terminal before publish.
- **Git log reviewed** (21 commits on main): all messages use conventional prefixes (`feat:`/`fix:`/`docs:`/`infra:`/`registry:`), no WIP, no leaked secrets, no profanity. **Recommendation: keep full history** (no squash). One commit message `1dda1ec docs: remove all PRISM references` is itself a self-referential mention but is historically accurate and fine to leave.
- **Hook middle-option implemented** (ship disabled + project-gated opt-in):
  - `hooks/hooks.json` — hook key remains `_PreToolUse` (shipped disabled). Prompt rewritten to: (a) walk up from the target file to find nearest `REGISTRY.yaml`, (b) read `project_config.enforce_naming_hook`, (c) approve unconditionally if the flag is absent or false, (d) only then validate the filename against the naming convention. Users who globally enable the hook (`_PreToolUse` → `PreToolUse`) still won't get enforcement on projects that haven't opted in.
  - `cmd_init` — added interactive prompt ("Enable naming-enforcement hook for this project? [y/N]"), plus non-interactive `--enable-hook` and `--no-hook` flags. Writes `project_config.enforce_naming_hook: <bool>` into the generated REGISTRY.yaml. Post-init status line reports hook state and the `_PreToolUse` → `PreToolUse` rename needed to activate globally.
  - `skills/librarian/SKILL.md` — new §First-Run Setup section explaining the hook opt-in; metadata version bumped 0.7.0 → 0.7.1. End-to-end sanity check passed: `python -m librarian init --no-hook` writes `enforce_naming_hook: false` and prints the disabled status message.
- **IP clearance — resolved**: user confirmed no patents being filed on librarian. Removed as a publish blocker.
- **Remaining Phase F blockers**: (1) PyPI namespace — user kept `librarian-2026` (already in `pyproject.toml`); (2) git history — keep full (recommended above, awaiting confirmation); (3) GitHub org vs. personal — open.
- **Host-terminal cleanup still required before publish**: (a) `rm -rf dashboard/legacy/` (stubs present but tracked); (b) `rm -rf skills/doc-librarian/` (coexists with `skills/librarian/`); (c) `rm -rf _site*` scratch dirs; (d) run `pytest` to confirm 681/681 (sandbox has no pytest). ✅ Confirmed 681/681 in Session 48.

### Session 48 Deliverables (Phase F publish — shipped)
- **Git history rewritten** via `git filter-repo` — all 24 commits now authored/committed as `Chris Kahn <272935920+ghengis5-git@users.noreply.github.com>`; all re-signed with SSH key; filter-branch backup refs gc'd.
- **GitHub repo published**: https://github.com/ghengis5-git/librarian (public, Apache 2.0, 704 KiB pack, 411 objects). Initial push via `gh repo create --public --source=. --push`.
- **GitHub release**: `v0.7.1` — "Librarian v0.7.1 — First public release" with full release notes covering 22 CLI commands, 57+ templates, 9 presets, 24 compliance standards, tamper-evident evidence packs, 681 tests. Also anchored with `v0.7.1-published` tag.
- **PyPI published**: https://pypi.org/project/librarian-2026/0.7.1/ — wheel (316 KB) + sdist (305 KB). Install path `pip install librarian-2026`. Dry-run on TestPyPI succeeded first. Also pushed to TestPyPI: https://test.pypi.org/project/librarian-2026/0.7.1/
- **Plugin marketplace**: `marketplace.json` at repo root (same-repo distribution path, no separate marketplace repo needed). Install: `claude plugins marketplace add ghengis5-git/librarian` → `claude plugins add librarian@librarian-marketplace`.
- **pyproject.toml cleanup**: dropped obsolete `License :: OSI Approved :: Apache Software License` classifier (PEP 639 now requires SPDX-only `license = "Apache-2.0"`); author email switched from `ghengis5@gmail.com` to the GitHub noreply address to hide it from PyPI metadata.
- **Test count corrected**: 682 → 681 across CLAUDE.md, README.md, and publish checklist. Session 46 docs overcounted template-engine hardening tests by one (actual: 8 new, not 9).
- **example-manifest**, **librarian-manifest-20260413**, **librarian-evidence-20260413** registered in REGISTRY.yaml; audit reports 24/24 clean.
- **7 publish commits on main** (all SSH-signed, all noreply-authored):
  - `b772777` feat: template engine hardening — iterator coverage + output size guard
  - `987d3ed` docs: Phase F prep — hook opt-in, ghengis5-git owner, noreply identity
  - `fbd47e1` chore: remove legacy dashboard stubs and old skill dir pre-publish
  - `8ae7ded` docs: correct test count to 681
  - `acd369f` docs: refresh manifest + evidence before publish
  - (pyproject fix commit) chore: drop obsolete license classifier (PEP 639) + hide author email
  - (release-notes + Phase F close commit — in progress)

### Session 49 Deliverables (Post-publish plugin-install fixes)
- **Phase F plan docs marked superseded** in `docs/REGISTRY.yaml` — both `phase-f-plugin-and-release-20260413-V1.1.md` and `phase-f-publish-checklist-20260413-V1.0.md` now `status: superseded` (both plans fully executed in Session 48).
- **Release notes scaffolded and committed**: `docs/release-notes-20260413-V1.0.md` (V1.0). Scaffold required `--preset software` override because project registry's preset doesn't include the `release-notes` template by default. Body covers 22 CLI commands, 57+ templates, 9 presets, 24 compliance standards, evidence packs, 681 tests, install paths, known issues.
- **Plugin marketplace install path fixes** (3 issues discovered by live smoke test):
  1. **`marketplace.json` wrong location** — Claude Code looks at `.claude-plugin/marketplace.json`, not repo root. Moved via `git mv`.
  2. **Real email leak in marketplace.json** — `owner.email: ghengis5@gmail.com` was still in the file; scrubbed to noreply. **Caveat**: the leak persists in public git history on the original Session 48 `marketplace.json` add commit. User opted to leave the history untouched (low-traffic repo, email derivable from GitHub profile anyway). To scrub later: `git filter-repo --replace-text` + force-push.
  3. **hooks.json schema mismatch** — Claude Code's validator requires a top-level `hooks: {}` record; our "ship-disabled via `_PreToolUse` underscore prefix" trick failed validation with `Invalid input: expected record, received undefined`. Fixed by shipping `hooks/hooks.json` with `"hooks": {}` (empty, truly disabled) and moving the real hook into `hooks/hooks.enabled.example.json`. Users enable by copying the example over the primary file.
- **README Gate 1 updated** to reflect the new enable procedure (copy `hooks.enabled.example.json` over `hooks.json`, restart Claude Code).
- **SSH host key** — `ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts` required on user's machine to allow plugin's secondary clone (first `install` failed with `No ED25519 host key is known`). This is a per-machine setup issue, not a plugin bug.
- **CLI verb correction**: install command is `claude plugins install`, not `claude plugins add`. README install line was already correct; only affected the Session 48 CLAUDE.md snippet.
- **Verified install path end-to-end**: plugin now reports `Status: ✔ enabled` in `claude plugins list`. Marketplace path: `claude plugins marketplace add ghengis5-git/librarian` → `claude plugins install librarian@librarian-marketplace`.
- **3 post-publish commits on main**:
  - `4347ca4` fix: move marketplace.json to .claude-plugin/ for Claude Code discovery
  - `bb8ea34` fix: scrub real email from marketplace.json owner field
  - `7d27353` fix(plugin): hooks.json schema — ship empty hooks record, move real hook to .enabled.example
- **Phase F truly complete** — all four distribution channels (GitHub, PyPI, plugin marketplace install path, release notes) verified working in the wild.

### Session 50 Deliverables (Phase 7.3 prep — v0.7.2 patch release)
- **Scope decision**: Phase 7.3 only (patch release). Phase 7.1 (pre-commit hook registry-sync bug) and 7.2 (next_review field + Audit KPI) deferred to v0.7.3. v0.7.2 is a pure re-release of `main` — it ships the Session 49 install-path fixes to anyone who installed during the broken window. No code changes, no test changes, no API changes.
- **Version strings bumped 0.7.1 → 0.7.2** in 5 manifests:
  - `librarian/__init__.py` (`__version__`)
  - `pyproject.toml` (`[project] version`)
  - `.claude-plugin/plugin.json` (`version`)
  - `.claude-plugin/marketplace.json` (`plugins[0].version`)
  - `skills/librarian/SKILL.md` (frontmatter `metadata.version`)
- **Release notes drafted**: `docs/release-notes-20260413-V2.0.md` — documents what changed in Session 49 (marketplace.json path, hooks.json schema, owner email scrub), explicitly calls out no-op areas (CLI, manifest, oplog, evidence, templates, tests), includes "remove the broken marketplace entry first" guidance for users stuck on v0.7.1 plugin install. Treated as a new document rather than a revision of V1.0 (each release notes file = one release).
- **Registry updated**:
  - v0.7.1 release notes promoted `draft` → `active` (they describe a live release).
  - v0.7.2 release notes added as new `draft` entry (V2.0, patch-tagged).
  - `registry_meta`: total 25 → 26, active 17 → 18.
- **Runbook produced** for host terminal: `docs/release-v0-7-2-runbook-20260413-V1.0.md` — step-by-step commands to execute the release (pytest sanity → commit version bumps → tag → build → TestPyPI dry-run → PyPI upload → gh release create → marketplace refresh → plugin smoke test). Nothing destructive or irreversible happens in Cowork; all git/build/upload steps live in the runbook.
- **Cowork sandbox limits hit as expected**: can't run `pytest`, `git tag`, `python -m build`, `twine upload`, or `gh release create`. These are the entire "execute the release" surface. All execution steps moved to the host runbook per user direction.
- **Phase 7.3 — EXECUTED** in host terminal between Sessions 50 and 51. Runbook ran clean: tag `v0.7.2` pushed, sdist + wheel uploaded to PyPI (`librarian-2026==0.7.2`), GitHub release created, marketplace refreshed, plugin smoke test passed. `82103c9 release: v0.7.2` and `ebfe7a7 registry: activate v0.7.2 release notes` landed on main. No Session 50.5 log because the host commits *are* the log.

### Session 51 Deliverables (Phase 7.1 + 7.2 + 7.3-next release + 7.5 — most unreleased, v0.7.3 shipped mid-session)

#### Phase 7.1 — Pre-commit hook registry-sync hardening (`425180e`)
- **Diagnosis correction**: CLAUDE.md's Phase 7.1 entry described the bug as "hook greps for full filepath but registry stores filename only". That bug was actually fixed in `853c5ba` (Session 35, while working on Phase G.1 prep). Tested against all 27 real registry entries → zero false negatives.
- **Real latent bugs found and fixed**:
  1. **Unescaped regex metacharacters** — `$filename` was interpolated verbatim into an extended regex. Literal dots in version suffixes (`V1.0.md`) were treated as wildcards; a staged `foo-V1.0.md` could spuriously match a registered `foo-V1x0xmd`. Demonstrated with a fixture registry.
  2. **No end-of-line anchor** — a staged `foo.md` would substring-match a registered `foo.md.backup` or `old-foo.md`.
- **Fix** (`scripts/librarian-pre-commit-hook-20260411-V1.0.sh`): escape regex metachars via `sed 's/[][().*+?|{}\\^$]/\\&/g'`, then anchor with `^[-[:space:]]+(filename|path):[[:space:]]+([^[:space:]]*/)?${filename_esc}[[:space:]]*$`. Accepts both list-item (`- filename: x`) and indented-path (`  path: dir/x`) YAML forms; filename must be at end of line.
- **11 regression tests** in `tests/test_precommit_hook.py` — 8 grep-level unit tests + 3 end-to-end tests that stage files into a fixture git repo and run the real hook script.
- **Hook self-tested on its own commit** — passed cleanly.

#### Phase 7.2 — `next_review` field + `review` CLI + Audit page KPI (`c92875a`)
- **Scope (user-chosen A3 + B1 + C1 + D1)**:
  - A3 — both flag-on-existing-command AND dedicated subcommand
  - B1 — explicit-only (presets do NOT auto-apply default cadences)
  - C1 — absolute ISO 8601 dates only; no relative parsing (`+6mo`, `+1y`) this pass
  - D1 — overdue = warn severity; `AuditReport.clean` deliberately unaffected to preserve the existing exit-code contract for downstream automation
- **New module** `librarian/review.py` (~210 lines): `parse_review_date`, `format_review_date`, `compute_overdue`, `compute_upcoming`, `OverdueReview` dataclass, `ReviewDateError`. Status-aware — superseded/archived docs excluded from overdue calc. Most-overdue-first sort.
- **Schema**: optional `next_review: YYYY-MM-DD|null` on each document entry (`schema/registry.schema.yaml`). Backwards compatible — every existing entry remains valid without it.
- **CLI surface**:
  - `librarian register --review-by YYYY-MM-DD`
  - `librarian bump --review-by YYYY-MM-DD` and `librarian bump --clear-review` (mutually exclusive; default = inherit from predecessor)
  - `librarian scaffold --review-by YYYY-MM-DD`
  - `librarian review set <filename> --by YYYY-MM-DD`
  - `librarian review clear <filename>`
  - `librarian review list [--overdue | --upcoming [--within-days N]]`
- **Audit integration**: `AuditReport.overdue_reviews: list[OverdueReview]` populated automatically; `format_report` emits an "Overdue reviews" section; `audit --json` includes `overdue_reviews` in the payload.
- **Audit page** (`sitegen.py`): new "Overdue Reviews" KPI card (kpi-warn when > 0); new OODA-section table with filename / deadline / days-overdue; new "List Overdue Reviews" CLI quick-card.
- **Docs**: `skills/librarian/references/cli-reference.md` updated with all new flags + the `review` subcommand.
- **51 new tests** (692 → 743) — `tests/test_review.py` (49 tests across 8 classes) and `tests/test_sitegen.py` (+2, +1 updated).
- **Smoke test on real registry**: set deadline on `librarian-architecture-20260411-V1.0.md` → audit detected (468 days overdue) → `review list --overdue` listed it → cleared back out → `git checkout` reverted stray writes.

#### Phase 7.3-next — v0.7.3 release (shipped mid-session)
- Commits on main leading up to tag: `425180e` (7.1), `c92875a` (7.2), `4283c43` (Session 51 docs), `62d3086` (release: version bumps + notes + runbook + manifest/evidence), `e8d866d` (post-release: activate release-notes V3.0 + runbook in registry).
- All 12 runbook steps executed clean: pytest 743 passed → `git tag -s v0.7.3` → `python -m build` (wheel 311 KB, sdist 306 KB) → TestPyPI dry-run → real PyPI upload → `git push origin main && git push origin v0.7.3` → `gh release create v0.7.3` with wheel + sdist attached → marketplace refreshed (plugin went 0.7.2 → 0.7.3).
- **Post-release smoke test** in a fresh `/tmp/lib-smoke` venv: `pip install librarian-2026==0.7.3` + `librarian register --review-by 2027-01-01` + `librarian review list` + `librarian audit` all worked end-to-end. PyPI CDN had a brief propagation lag (first install pulled 0.7.2); resolved on retry with `--no-cache-dir`.
- v0.7.3 release notes promoted draft → active in post-release housekeeping commit `e8d866d` (mirrors how v0.7.1 and v0.7.2 were handled).
- **Phase 7.4 explicitly skipped** mid-session — email-in-history scrub deferred indefinitely; user opted not to rewrite the Session 48 blob even though traffic could warrant it later.

#### Phase 7.5 — Oplog append-only detection + setup helper (`f296045`)
- **Scope pivot**: the original Phase 7.5 description in CLAUDE.md said "oplog prevention mode — requires oplog-format change — needs explicit approval." Session 51 chose **Option A** of the three scoped alternatives: OS-level append-only flag. **Zero oplog format change** — the JSONL schema stays identical, so the §When to Stop and Ask rule on oplog format changes was not triggered.
- **Mechanism**: kernel-enforced append-only via `chflags uappend` (macOS, UF_APPEND bit 0x04) or `chattr +a` (Linux, requires CAP_LINUX_IMMUTABLE / sudo). The existing `oplog.append()` already opens with `"a"` (`O_APPEND`), so normal operation is unaffected once the flag is set. Attackers with write access can no longer truncate or rewrite past entries — kernel returns EPERM.
- **New module** `librarian/oplog_lock.py` (~162 lines): `is_append_only(path) -> bool | None` (True/False/None with graceful degradation on unsupported platforms, missing tools, overlay/network filesystems); `platform_support() -> "macos" | "linux" | "unsupported"`; `lock_instructions(path)` / `unlock_instructions(path)` build human-readable shell commands. Never raises.
- **Setup helper** `scripts/librarian-oplog-lock-20260414-V1.0.sh` (~185 lines): `status | lock | unlock` subcommands, auto-detects OS. Applying the flag lives outside Python because Linux requires sudo — didn't want to gate library calls on that. Treats non-zero `lsattr` exit as "unknown" rather than silently reporting "unlocked" (bug caught + fixed mid-build during smoke test).
- **CLI**: new `librarian oplog status` subcommand (inspect-only; apply/remove routes through the shell script).
- **Audit integration**: `AuditReport.oplog_locked: bool | None` + `AuditReport.oplog_path: str` fields; `format_report` adds a one-line status (silent when `None`); `audit --json` includes both fields in payload; `report.clean` deliberately unaffected (preserves the existing CI-contract; advisory like folder suggestions and overdue reviews).
- **Audit page** (`sitegen.py`): new "Oplog Lock" KPI card (✓ when locked, ✗ when unlocked, – when undetectable); two new CLI quick-cards for status + enable. Audit page test count bumped 19 → 21.
- **Docs**: `skills/librarian/references/cli-reference.md` updated with full `oplog` section covering states (locked/unlocked/undetectable/missing), apply/remove instructions, and cross-platform semantics.
- **31 new tests** (743 → 774) — `tests/test_oplog_lock.py` (30 tests: platform dispatch 6, macOS stat-flag 5, Linux lsattr parsing 7 with mocked subprocess, instruction strings 5, audit integration 5) + `tests/test_sitegen.py` (+1 KPI assertion, +1 new CLI quick-cards test). macOS and Linux detection paths are covered via mocking rather than actually setting the flag (requires sudo on Linux, not worth the test flakiness).
- **End-to-end smoke test** in overlayfs sandbox: Python CLI, shell script, audit text output, and `audit --json` all agree on "undetectable" state — matches the graceful-degradation contract documented in `oplog_lock.py`. Expected path: on a real ext4/macOS filesystem the detection would succeed.

### Next Steps (by priority)
1. **Phase G — Document templates & recommendations engine** ✅ COMPLETE:
   - ~~G.1: Template infrastructure~~ ✅ (Session 36)
   - ~~G.2a: Software + Scientific templates~~ ✅ (Session 37)
   - ~~G.2b: Business + Legal templates~~ ✅ (Session 38)
   - ~~G.2c: Healthcare + Finance + Government templates~~ ✅ (Session 39)
   - ~~G.2d: Cross-cutting Security + Compliance templates~~ ✅ (Session 40)
   - ~~G.3: Recommendations engine~~ ✅ (Session 41)
   - ~~G.4: Templates catalog page, site/dashboard integration, custom templates, settings browser, docs~~ ✅ (Session 42/42b)
   - See `docs/phase-g-templates-and-recommendations-20260412-V1.0.md` for full plan
2. **Phase F — Plugin packaging + open-source release** ✅ COMPLETE (Session 48, install path fixes Session 49):
   - GitHub: https://github.com/ghengis5-git/librarian (public, v0.7.1 + v0.7.1-published tag)
   - PyPI: https://pypi.org/project/librarian-2026/0.7.1/
   - Marketplace: `.claude-plugin/marketplace.json`; install via `claude plugins marketplace add ghengis5-git/librarian` → `claude plugins install librarian@librarian-marketplace`
   - Git history rewritten via `git filter-repo` to use GitHub noreply email (`272935920+ghengis5-git@users.noreply.github.com`) — zero real-email leakage in public author/committer fields
   - **Deferred cleanup**: `ghengis5@gmail.com` still appears in the public `marketplace.json` blob history (Session 48 add commit). User opted to leave history untouched; can scrub later with `git filter-repo --replace-text` + force-push if traffic warrants
   - All commits SSH-signed
3. **Phase 7 — Post-publish polish + releases**:
   - **Phase 7.1** — Pre-commit hook registry-sync hardening. ✅ DONE + SHIPPED (Session 51 commit `425180e`, in v0.7.3). 11 regression tests.
   - **Phase 7.2** — `next_review` field + `review` CLI + Audit page KPI. ✅ DONE + SHIPPED (Session 51 commit `c92875a`, in v0.7.3). Scope A3+B1+C1+D1. 51 new tests.
   - **Phase 7.3** — v0.7.2 patch release. ✅ DONE (Session 50 prep + host execution between Sessions 50 and 51). Shipped Session 49 install-path fixes only.
   - **Phase 7.3-next** — v0.7.3 release. ✅ DONE (Session 51, release commit `62d3086` + housekeeping `e8d866d`). Tag `v0.7.3` live; PyPI 0.7.3 live; GitHub release with wheel + sdist; marketplace refreshed; plugin updated to 0.7.3.
   - **Phase 7.4** — Email-in-history scrub. 🟡 EXPLICITLY SKIPPED Session 51. User opted to leave `ghengis5@gmail.com` in the Session 48 `marketplace.json` blob history rather than rewrite + force-push. Can revisit later if traffic warrants.
   - **Phase 7.5** — Oplog append-only detection (prevention mode via OS flag). ✅ DONE (Session 51, commit `f296045`). **Unreleased — sitting on main past v0.7.3 tag.** Chose Option A (OS-level append-only flag) from the three scoped alternatives — zero oplog format change, so §When to Stop and Ask rule was not triggered. Detection module + setup helper + CLI subcommand + audit integration + Audit page KPI. 31 new tests.
   - **Phase 7.7** — Pre-commit framework native extension. 🔴 NOT STARTED. Convert current shell hook into a `pre-commit-hooks.yaml` entry for the `pre-commit` framework — broader reach beyond Claude Code. ~2 hr.
   - **Phase 7.4-next** — v0.7.4 release. 🔴 NOT STARTED. Aggregator for Phase 7.5 + 7.7 (if shipped together). Bumps 5 manifests 0.7.3 → 0.7.4, drafts release notes, tags `v0.7.4`, builds + uploads, refreshes marketplace. ~30 min host execute.
   - **Phase 7.6** — Community signals. Launch announcement (HN / r/programming / Claude Code community), first external-user outreach, short blog on naming convention + evidence-pack design. Gated on having 7.7 shipped so the pre-commit-framework install surface is live before announcement.
   - **Phase 7.8** — VSCode extension / LSP. Surface audit findings inline in the editor. Large scope; gated on external adoption.

**Security items (LOW):** Template for-loop iterator coverage ✅ fixed Session 46. Template engine output size limit ✅ fixed Session 46 (`_MAX_RENDER_BYTES = 4 MB`, `TemplateRenderError`). Oplog prevention mode rolls up into Phase 7.5.

4. **Phase 8 — Post-v0.7.4 roadmap** (proposed Session 51; nothing started):
   - **Phase 8.0** — Adversarial-review hardening pass. 🔴 NOT STARTED. Nine findings from Session 51 adversarial review of Phase 7.5 + 7.7 code:
     1 CRITICAL (shell-injection surface in `oplog_lock.lock_instructions/unlock_instructions` — fix with `shlex.quote()`),
     3 HIGH (symlink traversal in `precommit._should_check`; registry walk accepts filesystem-root `/docs/REGISTRY.yaml`; unquoted `lsattr` parsing in `librarian-oplog-lock-20260414-V1.0.sh`),
     4 MEDIUM (duplicate `infrastructure_exempt` parsing; TOCTOU in `is_append_only`; silent exit on empty argv; `chflags`/`chattr` failures swallow stderr),
     1 LOW (`uname -s` redirect). All localized, single hardening commit closes all nine. ~1.5 hr.
   - **Phase 8.1** — Polish sweep. 🔴 NOT STARTED. Bundle of small items: (a) `sitegen.py` SyntaxWarnings from unraw'd triple-quoted f-strings around line 2382-2386, (b) add `.pre-commit-hooks.yaml` + `cli-reference.md` to `naming_rules.infrastructure_exempt` so the hook stops nagging, (c) CLAUDE.md continuation block reflecting Phase 7.7 + v0.7.4 (not added in `758e30e`), (d) resolve the librarian's own audit folder-density warning (`docs/` has 17 docs past the threshold). ~45 min.
   - **Phase 8.2** — Adoption helpers. 🔴 NOT STARTED. Four features that reduce the "I have to learn 12 commands" overhead for the non-programmer audience:
     (a) `librarian archive <filename>` — moves superseded docs to `docs/archive/`, updates `path` field, leaves crumb. ~1.5 hr.
     (b) `librarian doctor` — single-shot diagnostic command: registry parses, all referenced files exist, hook installed, signing key configured, no orphans, no broken cross-refs. ~2 hr.
     (c) GitHub Actions workflow — ship a reusable `.github/workflows/librarian-audit.yml` running `librarian audit` + `librarian-precommit` on every PR. ~1 hr.
     (d) `librarian register --all` — scan tracked_dirs, batch-register anything unregistered. Adoption helper for existing projects. ~30 min.
     Total: ~5 hr.
   - **Phase 8.3** — Audit power-ups. 🔴 NOT STARTED. Four features that extend the audit's surface:
     (a) Cross-reference auto-resolution — flip `pending` → `resolved` when a matching doc lands in the registry. ~1 hr.
     (b) Tag taxonomy validator — warn if a doc uses `tags:` values not in `project_config.tags_taxonomy`. ~30 min.
     (c) Content-based duplicate detection — SHA-256 of body content (separate from file-hash manifest); flag suspected duplicates across the registry. ~1.5 hr.
     (d) Schema validation on registry load — hard-validate against `registry.schema.yaml`, fail cleanly instead of raising downstream `KeyError`s. ~1 hr.
     Total: ~4 hr.
   - **Phase 8.4** — Larger features (deferred). 🔴 NOT STARTED. Listed for completeness, not recommended until there's a concrete driver: approval workflow (`status=pending_approval` + approver field), multi-author support, concurrent-write protection via filelock, custom statuses per project, encryption-at-rest for evidence packs. No effort estimate — each is multi-hour, some multi-day.

   Recommended execution order: 8.0 → 8.1 → 8.2 → 8.3 → defer 8.4. Phases 8.0 + 8.1 are housekeeping and remove existing noise. 8.2 builds on the adoption surface opened by Phase 7.7 (pre-commit framework). 8.3 makes the audit do more of what it already promises. 8.4 waits for a real use case.

---

## Buildout Plan
The authoritative buildout plan is at `docs/librarian-buildout-plan-20260411-V1.2.md`.
The Phase G plan (templates + recommendations) is at `docs/phase-g-templates-and-recommendations-20260412-V1.0.md`.

---

## Document Governance — Self-Governed
The librarian governs its own docs. `docs/REGISTRY.yaml` is the registry.
The `project_config` block in that file contains the librarian-specific rules.
The `librarian` skill applies to this repo too.

**Project name:** `librarian` (renamed from working name `doc-librarian` in buildout plan V1.1,
2026-04-11). Any doc or code still referencing `doc-librarian` as the *project* name is stale
and should be updated during the Phase F scrub pass. The skill directory `skills/doc-librarian/`
is a known residual and will be renamed to `skills/librarian/` before publish.

### Naming Convention
`descriptive-name-YYYYMMDD-VX.Y.ext`
- Major (X) = rewrites/redesigns
- Minor (Y) = updates/fixes within same scope
- Infrastructure-exempt: REGISTRY.yaml, README.md, CLAUDE.md, .gitignore

---

## Git Identity
```bash
git -c user.name="Chris Kahn" \
    -c user.email="272935920+ghengis5-git@users.noreply.github.com" \
    commit ...
```
**GitHub account:** `ghengis5-git` (URL slug). Verified emails on the account: `ghengis5@gmail.com`, `research+ai@brokenwire.org`. Both are marked Private; **public commits must use the noreply address** `272935920+ghengis5-git@users.noreply.github.com` so the gmail/brokenwire addresses never enter the public git log.

Once Phase F publish prep runs the history rewrite (see `docs/phase-f-publish-checklist-20260413-V1.0.md` §F.a1), the repo's local config is set to the noreply email and the `-c` override is no longer strictly required, but passing it remains a safe belt-and-suspenders default.
**SSH commit signing** is configured locally (`gpg.format=ssh`, `user.signingkey=~/.ssh/id_ed25519`).
Commits should be signed automatically. If not, pass `-S` flag explicitly.

### Commit Prefixes
- `feat:` — new modules or capabilities
- `docs:` — documentation, registry, schemas
- `test:` — test additions or fixes
- `fix:` — bug fixes
- `infra:` — build tooling, CI, pre-commit hooks

---

## Key Constraints
- No external service calls — everything runs locally
- SHA-256 for all cryptographic operations (not SHA-1)
- Deterministic output: sorted keys in JSON, sorted hashes, sorted edges
- Append-only operation log — never delete entries
- Evidence packs are tamper-evident — changing any file invalidates the seal
- Python source files are NOT governed documents (no YYYYMMDD-VX.Y naming)
- Pre-commit hook validates governed document names, not code files
- Cowork sandbox: .git/index.lock cannot be removed — all git ops in host terminal

---

## Stack
- Python 3.13 (pyenv)
- PyYAML
- pytest
- No other runtime dependencies (by design — zero-dep governance tool)

---

## Session Efficiency
- Keep sessions to ONE feature — commit, start fresh
- This CLAUDE.md is the handoff doc; update it at session end
- Avoid reading the dashboard template (~500KB) — modify surgically
- Use subagents for parallel isolated work

---

## When to Stop and Ask
- Any change to the manifest seal algorithm requires explicit approval
- Any change to the oplog format (JSONL schema) requires approval
- Never self-initiate architectural changes — wait for instruction
