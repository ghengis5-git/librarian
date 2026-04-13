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
- **673 tests** across 13 test files
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
- Audit page: 17 (exists/title/sections/KPI/nav/data/JS/controls/seal/CLI/recs/OODA/oplog/CSS/search-index/global-search)
- Run: `python -m pytest tests/ -v --tb=short`
- **Always** run tests before any commit

---

## Current State
**Version:** 0.7.1
**Tests:** 673/673 PASS

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
- **PRISM scrub completed** (Session 34 carryover): All references to former consumer project removed across entire codebase
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
2. **Plugin packaging (Phase F):** Wrap as Claude Code plugin for marketplace distribution
3. **Review scheduling:** `next_review` date field in registry, surfaced as KPI on Audit page
4. **Open-source release:** GitHub public repo + PyPI + LICENSE + scrub pass
5. **Pre-commit hook registry sync bug:** Hook greps for full filepath but registry stores filename only — causes false "not found" warnings
6. **Remaining security items (LOW):** Oplog chain is detect-only (no write prevention); template for-loop only iterates list/tuple (silently drops dict_keys/set); no output size limit on template engine

---

## Buildout Plan
The authoritative buildout plan is at `docs/librarian-buildout-plan-20260411-V1.2.md`.
The Phase G plan (templates + recommendations) is at `docs/phase-g-templates-and-recommendations-20260412-V1.0.md`.

---

## Document Governance — Self-Governed
The librarian governs its own docs. `docs/REGISTRY.yaml` is the registry.
The `project_config` block in that file contains the librarian-specific rules.
The `doc-librarian` skill applies to this repo too.

### Naming Convention
`descriptive-name-YYYYMMDD-VX.Y.ext`
- Major (X) = rewrites/redesigns
- Minor (Y) = updates/fixes within same scope
- Infrastructure-exempt: REGISTRY.yaml, README.md, CLAUDE.md, .gitignore

---

## Git Identity
```bash
git -c user.name="Chris Kahn" -c user.email="ghengis5@gmail.com" commit ...
```
**Never write to git config.** Always pass identity via `-c` flags.
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
