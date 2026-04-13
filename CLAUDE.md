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
├── __main__.py             # CLI: audit, status, register, bump, manifest, evidence, diff, log, dashboard, site, init, config
├── config.py               # configuration system: defaults, presets, naming templates, merge logic
├── naming.py               # naming convention parser + validator (config-aware)
├── versioning.py           # version bump logic
├── registry.py             # REGISTRY.yaml CRUD
├── audit.py                # OODA audit engine + formatter + folder density analysis
├── manifest.py             # portable JSON + SHA-256 hashes + dependency graph
├── oplog.py                # append-only JSONL operation log
├── evidence.py             # tamper-evident IP evidence pack
├── diffaudit.py            # delta report between two manifests
├── dashboard.py            # dashboard template loader + manifest JSON injection
└── sitegen.py              # static site generator (sidebar tree, grouping, graph)
```

---

## CLI Reference
```
python -m librarian --registry <path> <command>

Commands:
  audit       OODA governance audit (drift, naming, orphans, cross-refs, folder suggestions)
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
- **329 tests** across 10 test files
- Phase A: 36 (naming 10, versioning 10, registry 10, audit 6)
- Config: 56 (presets 8, templates 6, loading 7, naming-config 10, configurable-naming 9, parse 4, CLI init 5, CLI config 3, merge 4)
- Phase B: 26 (manifest)
- Phase C: 66 (oplog 18, evidence 13, diffaudit 35)
- Phase D: 16 (dashboard)
- Phase E: 74 (sitegen 23 + sidebar/grouping 16 + markdown/content 27 + tree diagram 8)
- Settings page: 9 (compliance standards, preview panel, gear icon)
- Settings interactivity: 18 (onclick quoting, ID consistency, STANDARDS completeness, toggle/deselect, YAML export)
- Editable tags + new fields: 20 (tag CRUD, logo field, disclaimer dropdown, YAML export coverage)
- Folder suggestions: 8 (audit density analysis)
- Run: `python -m pytest tests/ -v --tb=short`
- **Always** run tests before any commit

---

## Current State
**Version:** 0.7.0
**Tests:** 329/329 PASS

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

### Next Steps (by priority)
1. **Plugin packaging (Phase F):** Wrap as Claude Code plugin for marketplace distribution
2. **Review scheduling:** `next_review` date field in registry, surfaced as KPI
3. **Open-source release:** GitHub public repo + PyPI + LICENSE + scrub pass

---

## Buildout Plan
The authoritative buildout plan is at `docs/librarian-buildout-plan-20260411-V1.2.md`.

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
git -c user.name="Chris Kahn" -c user.email="research+ai@brokenwire.org" commit ...
```
**Never write to git config.** Always pass identity via `-c` flags.

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
