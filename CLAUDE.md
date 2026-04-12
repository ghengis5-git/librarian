# Librarian — Claude Code Instructions

## Project Overview
Standalone document governance tool. Enforces naming conventions, tracks versions,
manages cross-references, produces tamper-evident manifests and audit trails.
Project-agnostic by design — PRISM (`~/projects/prism`) is the first consumer.

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
librarian/                  # pip-installable Python package (v0.5.0)
├── __init__.py             # public API exports + __version__
├── __main__.py             # CLI: audit, status, register, bump, manifest, evidence, diff, log, dashboard, site
├── naming.py               # naming convention parser + validator
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
```

---

## Test Suite
- **191 tests** across 9 test files
- Phase A: 36 (naming 10, versioning 10, registry 10, audit 6)
- Phase B: 26 (manifest)
- Phase C: 66 (oplog 18, evidence 13, diffaudit 35)
- Phase D: 16 (dashboard)
- Phase E: 39 (sitegen 23 + sidebar/grouping 16)
- Folder suggestions: 8 (audit density analysis)
- Run: `python -m pytest tests/ -v --tb=short`
- **Always** run tests before any commit

---

## Current State
**Version:** 0.5.0
**Tests:** 191/191 PASS

### Completed Phases
- **Phase A** (Sessions 26–27): Foundation — Python package, 4 CLI subcommands, pre-commit hook
- **Phase B** (Session 28): Manifest system — portable JSON + SHA-256 + dependency graph
- **Phase C** (Session 28): Audit extensions — operation log, evidence pack, diff audit
- **Phase D** (Session 29): Interactive dashboard — Lunr search, cytoscape.js graph, filter chips, timeline
- **Phase E** (Session 29): Static site generator — multi-page HTML, per-doc pages, graph page
- **Sidebar + grouping** (Session 30): Collapsible tree nav with status/tag/path grouping modes
- **Folder suggestions** (Session 30): Audit auto-detects crowded directories/tags, suggests reorganization
- **Design refresh** (Session 30): Unified design tokens across sitegen + dashboard template

### Next Steps (by priority)
1. **Plugin packaging (Phase F):** Wrap as Claude Code plugin for marketplace distribution
2. **Review scheduling:** `next_review` date field in registry, surfaced as KPI
3. **Open-source release:** GitHub public repo + PyPI + LICENSE + scrub pass

---

## Buildout Plan
The authoritative buildout plan lives in PRISM at:
`~/projects/prism/docs/librarian-buildout-plan-20260411-V1.2.md`

A local copy is at `docs/librarian-buildout-plan-20260411-V1.2.md`.

---

## Document Governance — Self-Governed
The librarian governs its own docs. `docs/REGISTRY.yaml` is the registry.
The `project_config` block in that file contains the librarian-specific rules.
The `prism-doc-librarian` skill (or equivalent) applies to this repo too.

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

## Dependency on PRISM
PRISM is a consumer of this project, not a dependency. The librarian must never
import anything from PRISM. PRISM installs the librarian as an editable package:
`pip install -e ~/projects/librarian`

When testing the librarian against PRISM's registry:
```bash
python -m librarian --registry ~/projects/prism/docs/REGISTRY.yaml audit
```

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
