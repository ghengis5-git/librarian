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
librarian/                  # pip-installable Python package (v0.3.0)
├── __init__.py             # public API exports + __version__
├── __main__.py             # CLI: audit, status, register, bump, manifest, evidence, diff, log
├── naming.py               # naming convention parser + validator
├── versioning.py           # version bump logic
├── registry.py             # REGISTRY.yaml CRUD
├── audit.py                # OODA audit engine + formatter
├── manifest.py             # portable JSON + SHA-256 hashes + dependency graph
├── oplog.py                # append-only JSONL operation log
├── evidence.py             # tamper-evident IP evidence pack
└── diffaudit.py            # delta report between two manifests
```

---

## CLI Reference
```
python -m librarian --registry <path> <command>

Commands:
  audit       OODA governance audit (drift, naming, orphans, cross-refs)
  status      Quick registry summary (counts by status)
  register    Add a new document entry to the registry
  bump        Version-bump an existing document
  manifest    Generate portable JSON manifest (--no-snapshot, --no-hashes, --no-graph)
  evidence    Generate tamper-evident IP evidence pack (-o output.json)
  diff        Compare two manifests (old.json new.json --json)
  log         Read/filter operation log (--since, --last N)
```

---

## Test Suite
- **128 tests** across 7 test files
- Phase A: 36 (naming 10, versioning 10, registry 10, audit 6)
- Phase B: 26 (manifest)
- Phase C: 66 (oplog 18, evidence 13, diffaudit 35)
- Run: `python -m pytest tests/ -v --tb=short`
- **Always** run tests before any commit

---

## Current State
**Version:** 0.3.0 (Phase C complete)
**Tests:** 128/128 PASS
**Last commit:** `db37d4f` — Phase C (oplog, evidence, diffaudit)

### Completed Phases
- **Phase A** (Sessions 26–27): Foundation — Python package, 4 CLI subcommands, pre-commit hook
- **Phase B** (Session 28): Manifest system — portable JSON + SHA-256 + dependency graph
- **Phase C** (Session 28): Audit extensions — operation log, evidence pack, diff audit

### Next Phase
- **Phase D:** Web output V1 — extended dashboard with search, filter, timeline, cross-reference graph
  - Template: `dashboard/librarian-dashboard-template-YYYYMMDD-V3.0.html`
  - CLI: `python -m librarian dashboard` — renders template against manifest
  - Client-side Lunr search, filter UI, timeline view, d3-force or cytoscape.js graph
  - Zero external dependencies, works offline
  - Supersedes legacy PRISM dashboards (`doc-librarian-dashboard-*`)

### Future Phases
- **Phase E:** Static site scaffold (MkDocs-like generator)
- **Phase F:** Plugin conversion + open-source release + vector index

---

## Buildout Plan
The authoritative buildout plan lives in PRISM at:
`~/projects/prism/docs/librarian-buildout-plan-20260411-V1.2.md`

A copy should be brought into this repo at `docs/` during Phase D.

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

---

## Stack
- Python 3.13 (pyenv)
- PyYAML
- pytest
- No other runtime dependencies (by design — zero-dep governance tool)

---

## When to Stop and Ask
- Any change to the manifest seal algorithm requires explicit approval
- Any change to the oplog format (JSONL schema) requires approval
- Never self-initiate architectural changes — wait for instruction
