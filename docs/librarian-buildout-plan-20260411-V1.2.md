---
title: Doc Librarian Buildout Plan
filename: librarian-buildout-plan-20260411-V1.2.md
version: 1.2
date: 2026-04-11
status: active
author: Christopher A. Kahn
classification: PERSONAL / INTERNAL USE ONLY
supersedes: librarian-buildout-plan-20260411-V1.1.md
---

# Doc Librarian Buildout Plan — V1.2

## Purpose

This document is the authoritative plan for evolving the `doc-librarian` skill from a project-specific tool into a **standalone, open-source-ready doc-governance project**. The generic librarian is NOT a skill folder inside the consumer project's repo. It is a separate project that happens to have a consumer project as its first user.

The buildout is driven by an explicit goal captured in Session 25 (2026-04-11):

> "Needs to be another project, standalone."

The librarian graduates from "a custom skill for a single project" into a product that governs docs across multiple projects and, after the consumer project's patents are filed, becomes part of a public startup plugin. This plan is the contract that keeps the scope honest across the phased execution.

## Background and rationale

Session 25 closed the OODA governance backlog and asked whether anything in the Claude Code / Cowork / Anthropic / MCP / docs-as-code ecosystem already does what the librarian does. Research found nothing covering more than a narrow slice: Antora, Sphinx+mike, MkDocs+mike, and Docusaurus versioning are publishing pipelines, not development-time governance layers. MCP Registry is server governance. Vale is prose linting. The librarian occupies a real gap — doc governance as a development skill, not a publishing pipeline.

The initial implementation is approximately 70% generic by construction — it already reads a `project_config` block from REGISTRY.yaml with fallback defaults. The remaining coupling is (a) hardcoded fallback values, (b) project-specific examples in the body, (c) the assumption that `project_config` lives inside `REGISTRY.yaml` rather than as a standalone config file, and (d) the absence of multi-project testing. Phase A corrects all four — but does so **in a dedicated standalone project**, not within the consumer project's repo.

## Standalone architecture

**The generic librarian is its own project, not a subdirectory of the consumer project.**

Project name: `librarian` (renamed from working name `doc-librarian` in V1.1 on 2026-04-11).

Repository structure (actual, after Phase A completion):

```
librarian/                             # standalone project root
├── README.md                          # placeholder (draft, registered)
├── pyproject.toml                     # setuptools backend, Python >=3.13
├── .python-version                    # pyenv 3.13.12
├── .gitignore
├── librarian/                         # pip-installable Python package (v0.1.0)
│   ├── __init__.py                    # public API exports
│   ├── __main__.py                    # CLI: audit, status, register, bump
│   ├── naming.py                      # naming convention parser + validator
│   ├── versioning.py                  # version bump logic
│   ├── registry.py                    # REGISTRY.yaml CRUD
│   └── audit.py                       # OODA audit engine + formatter
├── skill/
│   └── SKILL.md                       # generic skill definition (active)
├── scripts/
│   └── librarian-pre-commit-hook-20260411-V1.0.sh
├── tests/
│   ├── conftest.py                    # fixtures: temp_repo, temp_registry_path
│   ├── test_naming.py                 # 10 tests
│   ├── test_versioning.py             # 10 tests
│   ├── test_registry.py               # 10 tests
│   └── test_audit.py                  # 6 tests
└── docs/
    └── REGISTRY.yaml                  # self-bootstrapped, 2 entries
```

Planned but deferred from Phase A (moved to later phases):

```
├── LICENSE                            # deferred until Phase F
├── schema/                            # deferred — Python code IS the schema enforcement
│   ├── project_config.schema.yaml     # Phase B or later
│   ├── registry.schema.yaml           # Phase B or later
│   └── manifest.schema.json           # Phase B
├── examples/                          # deferred — example consumer config serves as reference
│   ├── project_config.minimal.yaml    # Phase B
│   ├── project_config.full.yaml       # Phase B
│   └── project_config.example.yaml    # Phase B
├── dashboard/                         # Phase D
├── site/                              # Phase E
└── docs/
    ├── architecture-*.md              # Phase B
    └── buildout-plan-*.md             # authoritative copy in librarian repo
```

A consumer project is a **user**: the consumer's `skills/doc-librarian/SKILL.md` (or equivalent) is a thin wrapper containing a condensed governance protocol and a CLI command table. Mechanical operations (audit, register, bump, status) delegate to the standalone Python CLI via `python -m librarian`. The consumer's REGISTRY.yaml `project_config` block remains the project-specific configuration source.

**Why standalone matters:**

1. **Clean IP separation.** A consumer project's repo may carry trade secrets. The librarian carries none of that. Keeping them in separate repos is the safest posture for eventual open-source release.
2. **Multi-project reuse.** A standalone project can be cloned or symlinked into any project. If the librarian lives inside one consumer's repo, any new project that wants to use it has to either (a) clone that repo (wrong for IP reasons) or (b) copy-paste the skill files (drift risk).
3. **Open-source path.** Standalone repo is already shaped for a public release. Phase F becomes "flip the visibility bit and add a LICENSE" rather than "extract from a private repo."
4. **Test fixtures.** Standalone tests can include synthetic test projects. Inside a consumer's repo those fixtures would either pollute its docs tree or require exclusions.
5. **Dependency direction is correct.** Consumer projects depend on the librarian, not the other way around. A file layout that makes a consumer the parent of the librarian is backwards.

## Phase A routing decision (resolved)

Session 25 selected **Routing option 1 — additional Cowork mount** at `~/projects/librarian/` on the host Mac. Session 26 executed via a **hybrid workflow**: Cowork for governance/docs/registry, Claude Code terminal for Python/tests/git. Files were staged in a temporary directory and copied to the librarian repo by the operator.

Key discovery: the Cowork sandbox Python resolves to an older system version. All Python execution (tests, CLI, pip install) must happen in Claude Code terminal with the librarian venv activated.

## Capability scope

Session 25 locked in the following capability targets. Each is treated as a product requirement, not a stretch goal.

### Manifest system (all four types)

1. **Portable JSON manifest.** Machine-readable export of REGISTRY.yaml in JSON. Enables external tools, CI pipelines, and future plugin consumption to read the librarian's state without parsing YAML.
2. **Cryptographic manifest (SHA-256).** Per-file hash of every registered document. Separate from git SHA-1 because SHA-1 is cryptographically weak and would not hold up as tamper evidence in an IP dispute; SHA-256 is the current legal standard. Cost: approximately 100 lines of Python, one `hashlib` import.
3. **Dependency manifest.** Cross-reference graph as explicit edges (doc A depends on doc B). Enables impact analysis and feeds the dashboard's cross-reference visualization.
4. **Plugin install manifest.** Deferred to Phase F — the plugin format expects a skill directory structure that isn't stable yet.
5. **Full indexed tracking.** Full-text search index (Lunr, Phase D), temporal index (Phase C), vector index (Phase F, deferred). Feeds dashboard search and duplicate detection.

### Audit system (all four types)

1. **Drift audit.** Reconciles REGISTRY.yaml against filesystem state. Flags naming violations, orphans, missing files, broken cross-references. **Phase A delivered this as `python -m librarian audit` — the OODA audit is now a CLI command with structured output.**
2. **IP evidence pack.** Signed snapshot of manifest + commit hash + timestamp. Suitable for patent filings and trade-secret claims. Uses SHA-256 from the cryptographic manifest as its integrity anchor.
3. **Diff audit (since last session).** Delta report between two points in time. Uses the append-only operation log plus git.
4. **Operation log (append-only).** Every librarian action writes a timestamped line: who, what, when, files touched, commit hash. Backbone for the other three audit types.

### Web output

- **Extended dashboard (Phase D).** Take the current V2.1 HTML dashboard and add search, filter by type/status, timeline view, and cross-reference graph. Single-file HTML, self-contained. Consumes the manifest (not REGISTRY directly).
- **Static site scaffold (Phase E, deferred).** Multi-page MkDocs-style generator. Publishable to GitHub Pages. Deferred because it's prep for plugin conversion.

### Index types — use case reference

**Full-text (Lunr) — Phase D.** Exact and prefix-matching search across doc titles and bodies. Client-side, no server. Adds ~2MB to the dashboard payload. Zero new dependencies in the browser.

**Temporal — Phase C.** Time-series view of every version bump, archive, and cross-ref change. Enables history replay, velocity analysis, staleness detection, and IP timeline reconstruction. Essentially free — computed from git-log-per-doc plus the audit log.

**Vector (semantic) — deferred to Phase F.** Embeddings-based semantic search. Unlocks: find docs that talk about a concept even when the word isn't in them; duplicate-detection at authoring time; auto-discovery of cross-references; auto-clustering; cross-project prior-art search. Cost: ~80MB local model, `sentence-transformers` dependency, ~15s per full re-index on M5 Max. Deferred because its biggest value is cross-project search, which requires Phase F's multi-project deployment.

## Execution plan

Six phases. Each phase is approximately one focused session. Phases build on each other in a required order.

### Phase A — Foundation ✅ COMPLETE (Sessions 26–27)

**Goal:** bootstrap the standalone `librarian` project. Extract generic logic from project-specific skill. Make projects consume it via a thin wrapper.

**Depends on:** routing decision (option 1 selected; hybrid workflow used).

**What V1.1 planned vs. what actually shipped:**

| V1.1 Planned | Actual Deliverable | Notes |
|---|---|---|
| Project scaffold with empty dirs + .gitkeep | Pip-installable Python package v0.1.0 | Exceeded plan: working CLI, not just scaffold |
| `skill/SKILL.md` — generic skill | `skill/SKILL.md` — generic skill | As planned |
| `schema/project_config.schema.yaml` | Deferred — Python code enforces schema | Python `Registry` class validates on load |
| `schema/registry.schema.yaml` | Deferred — Python code enforces schema | Same rationale |
| `examples/project_config.example.yaml` | Deferred — example config serves as reference | Low value until multi-project adoption |
| `docs/REGISTRY.yaml` — self-bootstrapped | `docs/REGISTRY.yaml` — self-bootstrapped (2 entries) | As planned, plus librarian governs itself from commit #1 |
| `docs/buildout-plan-*.md` — copy into standalone | Lives in standalone repo | Authoritative copy in standalone project |
| Not planned | `librarian/` Python package — 4 modules (naming, versioning, registry, audit) | Phase A overdelivered: working code, not just files |
| Not planned | `librarian/__main__.py` — CLI with 4 subcommands | audit, status, register, bump — all functional |
| Not planned | `tests/` — 36 pytest cases across 4 test files | 10 naming + 10 versioning + 10 registry + 6 audit |
| Not planned | `pyproject.toml` with pip-installable entry point | `pip install -e ~/projects/librarian` works |
| Not planned | `scripts/librarian-pre-commit-hook-20260411-V1.0.sh` | Pre-commit hook for document governance |
| Not planned | Consumer wrapper | 110 lines (CLI delegation) | Thin wrapper for consumer projects |
| Consumer config | Config stays in `docs/REGISTRY.yaml` `project_config` block | No separate config file needed — REGISTRY.yaml already has it |

**Commits:**
- `7d5fcab` (librarian) — Phase A inaugural: 20 files, 2,162 insertions
- Consumer project wrapper updated for librarian CLI delegation

**Test results:** 36/36 passing in 0.06s (librarian).

**Regression check:** `python -m librarian --registry docs/REGISTRY.yaml audit` produces consistent findings. Named documents registered, pre-convention files flagged as legacy naming violations.

### Phase B — Manifest system

**Goal:** emit portable JSON manifest, cryptographic manifest, dependency manifest, and search index on demand, from the standalone project.

**Depends on:** Phase A complete ✅.

**Deliverables (all in standalone project):**
- `librarian/manifest.py` — manifest generation module (portable JSON + SHA-256 + dependency graph)
- `schema/manifest.schema.json` — JSON Schema for the manifest format
- `schema/project_config.schema.yaml` and `schema/registry.schema.yaml` — deferred from Phase A
- `examples/` directory — minimal, full, and example reference configs
- `docs/architecture-*.md` — architecture document for the standalone librarian
- CLI subcommand: `python -m librarian manifest` — generates all three manifest types
- First generated manifest for a consumer project
- Deterministic output (sorted keys, stable hash ordering)
- New tests for manifest generation

**Updated scope note:** Phase A delivered the Python package foundation. Phase B builds on it by adding a `manifest` module and CLI subcommand rather than creating standalone scripts. The `scripts/librarian-manifest-generate-*.py` approach from V1.1 is superseded by the integrated CLI.

### Phase C — Audit system + temporal index

**Goal:** drift detection enhancements, change deltas, operation history, IP evidence packaging.

**Depends on:** Phase B (IP evidence pack needs the cryptographic manifest).

**Deliverables (integrated into the librarian package):**
- `librarian/evidence.py` — IP evidence pack generation (SHA-256 + commit hash + timestamp)
- `librarian/diffaudit.py` — delta report between two points in time
- `librarian/oplog.py` — append-only operation log
- CLI subcommands: `python -m librarian evidence`, `python -m librarian diff`
- Temporal index as a derived view on top of audit log + git log
- `operator/librarian-audit.jsonl` format spec

**Updated scope note:** The V1.1 standalone-scripts approach (`scripts/librarian-audit-drift-*.py`, etc.) is superseded by integrated CLI subcommands. The drift audit already ships as `python -m librarian audit` from Phase A — Phase C extends it with the remaining three audit types.

### Phase D — Web output V1 (extended dashboard)

**Goal:** dashboard V3.0 with search, filter, timeline, cross-reference graph.

**Depends on:** Phase B (consumes manifest) and Phase C (consumes temporal data).

**Deliverables:**
- `dashboard/librarian-dashboard-template-YYYYMMDD-V3.0.html` — template in standalone project
- CLI subcommand: `python -m librarian dashboard` — renders template against a project's manifest
- Consumer projects receive rendered copies with standardized dashboard filenames
- Client-side Lunr search, filter UI, timeline view, cytoscape.js or d3-force dependency graph
- Zero external dependencies, works offline, no data leaves the machine

### Phase E — Static site scaffold

**Goal:** multi-page publishable site generator consuming the manifest.

**Depends on:** Phase D. The dashboard proves the manifest is a sufficient data contract.

**Deliverables:** scaffold only. Generator writes a multi-page `_site/` tree from the manifest. MkDocs-like structure. Polish and GitHub Pages integration land in Phase F.

### Phase F — Plugin conversion + open-source release

**Goal:** repackage standalone `librarian` as a Claude Code plugin, publish open-source (after consumer project patents are filed), add vector index, tie into the planned startup plugin bundle.

**Depends on:** Phases A–E plus IP posture clearance (provisional patents on file).

**Deliverables:**
- Plugin manifest in the Claude Code plugin format (exact schema TBD at phase start)
- Marketplace entry
- Public LICENSE (Apache 2.0 or MIT — TBD)
- Open-source repo — the standalone project flipped to public
- Vector index via `sentence-transformers/all-MiniLM-L6-v2`
- Scrub pass to ensure no consumer-specific content remains in any example or test fixture
- Startup plugin bundle integration (details TBD)
- PyPI package name resolution (see name collision risk below)

## Risks and open questions

**Name collision risk.** `librarian` is a generic noun. PyPI, npm, and GitHub all have existing projects using that name. This is acceptable for a private repo; Phase F publication must confirm namespace availability and may require a prefix (e.g., `claude-librarian`, `doc-librarian` as the published PyPI package name while keeping `librarian` as the local project directory).

**Cowork sandbox limitations (discovered in Phase A).** The Cowork sandbox Python may resolve to an older system version. All Python execution must happen in Claude Code terminal. The standalone librarian may not be accessible from a consumer project's Cowork session (mount restrictions). This drove the CLI delegation wrapper design — the consumer wrapper keeps a condensed governance protocol inline rather than pointing Claude at the generic skill file it cannot read from within the consumer's session.

**Cross-repo sync during iteration.** As Phase B adds a manifest generator, a consumer project's registry serves as the first test target. The standalone scripts need to read that project's `project_config` and write manifests into its repo. This cross-repo read/write must be explicit in every script's config (no hardcoded paths). Flagging this as a risk because it's a common drift source.

**SHA-1 vs SHA-256 double-hashing.** Session 25 chose SHA-256 for IP/legal reasons. Git stores SHA-1 per blob. The manifest carries both: git commit hash as the git-side anchor, SHA-256 as the standalone evidence anchor. Belt and suspenders. Cost is sub-second compute for 38 docs.

**The manifest becomes a governed document.** Once the manifest is generated, that file is registered and versioned. The librarian manages a manifest of everything, including the manifest. Phase B must handle the edge case of the manifest being modified during generation.

**Cross-project vector search requires multi-registry consolidation.** Deferred to Phase F. Architecture decision (central aggregator vs. federated) deferred.

**Dashboard V3.0 payload size.** Lunr + cytoscape.js + manifest JSON + full-text corpus in one HTML file — likely 3–10 MB. Acceptable for a governance dashboard. Flag for optimization if it exceeds 10 MB.

**Plugin spec drift.** Claude Code plugin format may evolve between now and Phase F. Phase F planning starts with a fresh read of the current plugin spec.

**Open-source scrubbing risk.** Consumer project-specific content (proprietary algorithms, markers, findings, calibration data) is trade secret. Phase E should draft the scrub checklist so it's ready when Phase F executes.

**Consumer tracked_dirs gap.** A consumer project's `project_config.tracked_dirs` may not include all document locations. Files in certain directories may show as "missing" in audits because they are registered but live outside tracked dirs. Expanding `tracked_dirs` to include all document locations is a deferred consumer config fix, not a librarian code issue.

## Success criteria

The buildout is complete when:

1. The standalone `librarian` project exists as a separate repo and has its own git history ✅
2. The generic skill has no consumer-specific content in normative sections — examples may reference a sample consumer project but the skill works identically for any project supplying a valid `project_config` ✅
3. Consumer projects consume the standalone skill via a thin wrapper — if the standalone project is missing, the wrapper fails in an obvious way rather than continuing to work by accident ✅ (CLI delegation: `python -m librarian` fails if package not installed)
4. A manifest can be generated deterministically and contains all four sub-manifests (Phase B)
5. All four audit types can be run from the command line and produce machine-readable output (Phase A: drift audit ✅; Phases B–C: remaining three)
6. Dashboard V3.0 renders against the manifest with search, filter, timeline, and graph views (Phase D)
7. A synthetic second test project can adopt the generic skill by dropping in a `project_config` and running the bootstrap, with no generic-skill edits required (Phase B — pytest fixtures already demonstrate this with synthetic registries)
8. The standalone project passes its own test suite against the synthetic fixtures ✅ (36/36)

## Out of scope

- Vector semantic search until Phase F
- Static site GitHub Pages publishing until Phase F
- Multi-project registry aggregation until Phase F
- Any change to consumer module code — this buildout is governance only
- Web UI edits to anything other than the librarian dashboard
- Changes to the existing consumer pre-commit hook beyond what's required to support the config layer

## Cross-references

| Document | Affected in phase | Nature of update |
|---|---|---|
| Consumer skill wrapper | Phase A ✅ | Rewritten as 110-line CLI delegation wrapper |
| docs/REGISTRY.yaml (consumer) | Phase A ✅, B, C, D | Schema compatibility; manifest entries |
| Consumer dashboard | Phase D | Superseded by Phase D dashboard |
| librarian/ (standalone project) | Phase A ✅, B–F | Created and iterated |

## Version history

| Version | Date | Author | Notes |
|---|---|---|---|
| V1.0 | 2026-04-11 | Christopher A. Kahn | Initial plan. Captures standalone architecture decision from Session 25. Routing decision resolved in favor of standalone before this file was committed. |
| V1.1 | 2026-04-11 | Christopher A. Kahn | Renamed standalone project `doc-librarian` → `librarian`. Consumer wrapper skill renamed. Phase A routing decision recorded as resolved (option 1 selected). Added name collision risk note for Phase F publication. No scope, phase, capability, or timeline changes. Dashboard filenames standardized. |
| V1.2 | 2026-04-11 | Christopher A. Kahn | Reconciled spec with actual Phase A deliverables (Sessions 26–27). Phase A overdelivered: pip-installable Python package v0.1.0 with 4 CLI subcommands and 36 pytest cases instead of the planned file-only scaffold with YAML schemas and example configs. Consumer wrapper is 110-line CLI delegation wrapper instead of planned ~50-line pointer. Deferred items (schemas, examples, architecture doc) moved to Phase B scope. Phases B–D updated: standalone scripts replaced by integrated CLI subcommands. Added Cowork sandbox limitation and tracked_dirs gap to risks. Marked Phase A complete with commit hashes. Updated success criteria with Phase A checkmarks. Removed consumer-specific config references. Genericized project references. |
