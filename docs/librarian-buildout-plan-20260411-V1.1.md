---
title: Doc Librarian Buildout Plan
filename: librarian-buildout-plan-20260411-V1.1.md
version: 1.1
date: 2026-04-11
status: active
author: Christopher A. Kahn
classification: PERSONAL / INTERNAL USE ONLY
supersedes: librarian-buildout-plan-20260411-V1.0.md
---

# Doc Librarian Buildout Plan — V1.1

## Purpose

This document is the authoritative plan for evolving the `doc-librarian` skill from a project-specific tool into a **standalone, open-source-ready doc-governance project**. The generic librarian is NOT a skill folder inside the consumer project's repo. It is a separate project that happens to have the first consumer project as its first adoption target.

The buildout is driven by an explicit goal captured in Session 25 (2026-04-11):

> "Needs to be another project, standalone."

The librarian graduates from "a custom skill I use on my project" into a product that governs docs across multiple projects and, after IP protection is established, becomes part of a public startup plugin. This plan is the contract that keeps the scope honest across the phased execution.

## Background and rationale

Session 25 closed the OODA governance backlog and asked whether anything in the Claude Code / Cowork / Anthropic / MCP / docs-as-code ecosystem already does what the librarian does. Research found nothing covering more than a narrow slice: Antora, Sphinx+mike, MkDocs+mike, and Docusaurus versioning are publishing pipelines, not development-time governance layers. MCP Registry is server governance. Vale is prose linting. The librarian occupies a real gap — doc governance as a development skill, not a publishing pipeline.

The current skill implementation is approximately 70% generic by construction — it already reads a `project_config` block from REGISTRY.yaml with sensible defaults. The remaining coupling is (a) hardcoded fallback values, (b) project-specific examples in the body, (c) the assumption that `project_config` lives inside `REGISTRY.yaml` rather than as a standalone config file, and (d) the absence of multi-project testing. Phase A corrects all four — but does so **outside any consumer project's repo**, in a dedicated standalone project.

## Standalone architecture

**The generic librarian is its own project, not a subdirectory of any consumer project.**

Project name: `librarian` (renamed from working name `doc-librarian` in V1.1 on 2026-04-11).

Repository structure (destination, standalone):

```
librarian/                             # standalone project root
├── README.md
├── LICENSE                            # deferred until Phase F public release
├── skill/
│   └── SKILL.md                       # the generic skill
├── schema/
│   ├── project_config.schema.yaml     # authoritative config schema
│   ├── registry.schema.yaml           # REGISTRY.yaml schema
│   └── manifest.schema.json           # generated manifest format
├── scripts/                           # librarian runtime scripts
│   ├── librarian-manifest-generate-*.py
│   ├── librarian-audit-drift-*.py
│   ├── librarian-audit-diff-*.py
│   ├── librarian-audit-evidence-pack-*.py
│   └── librarian-pre-commit-hook-*.sh
├── dashboard/                         # web output (Phase D)
│   └── librarian-dashboard-template-*.html
├── site/                              # static site scaffold (Phase E)
├── examples/
│   ├── project_config.minimal.yaml
│   ├── project_config.full.yaml
│   └── project_config.example.yaml    # example consumer config as reference
├── tests/
│   ├── fixtures/
│   │   ├── sample-project-alpha/      # synthetic test project #1
│   │   └── sample-project-beta/       # synthetic test project #2
│   └── test_librarian.py
└── docs/                              # documentation of the librarian itself
    ├── REGISTRY.yaml                  # yes, the librarian governs its own docs
    ├── architecture-*.md
    └── buildout-plan-*.md             # this plan, copied over in Phase A
```

Each consumer project becomes a **user** of the librarian: the consumer's repo contains only a thin wrapper config pointing to the standalone librarian project. The consumer's config file tells Claude: "load the librarian skill from the standalone project and apply this project's settings."

**Why standalone matters:**

1. **Clean IP separation.** Consumer projects may carry trade-secret content. The librarian carries none of that. Keeping them in separate repos is the safest posture for eventual open-source release.
2. **Multi-project reuse.** A standalone project can be cloned or symlinked into any project. If the librarian lives inside a consumer project, any other project that wants to use it has to either (a) clone that consumer's repo (wrong for IP reasons) or (b) copy-paste the skill files (drift risk).
3. **Open-source path.** Standalone repo is already shaped for a public release. Phase F becomes "flip the visibility bit and add a LICENSE" rather than "extract from a private repo."
4. **Test fixtures.** Standalone tests can include synthetic test projects. Inside a consumer project those fixtures would either pollute the project's docs tree or require exclusions.
5. **Dependency direction is correct.** Consumer projects depend on the librarian, not the other way around. A file layout that makes a consumer project the parent of the librarian is backwards.

## Phase A routing decision (resolved)

Session 25 selected **Routing option 1 — additional Cowork mount** at `~/projects/librarian/` on the host Mac. The operator kickoff checklist for Session 26 is in the session log and includes `mkdir -p ~/projects/librarian && cd ~/projects/librarian && git init` as step 1, followed by adding the new directory as a Cowork mount (multi-mount or switch) before Phase A execution begins.

Routing options 2 (temp workspace + archive handoff) and 3 (temporary extraction folder) remain documented below as fallbacks in case the Cowork multi-mount workflow hits a blocker at Session 26 kickoff.

**Routing option 1 — additional Cowork mount.** The operator creates `~/projects/librarian/` on the host Mac and mounts it as an additional Cowork folder (if supported) or switches the mount. Claude writes directly into the new mount from day one. Cleanest. Requires Cowork multi-mount or a mount swap.

**Routing option 2 — scaffold in Claude's temp workspace, hand off as archive.** Claude builds the standalone project in its working directory. Not visible in the operator's Cowork file browser during the session. At end of Phase A, Claude produces a tarball or zip the operator can extract to wherever they want the real project to live. No mount changes required. Downside: the operator can't inspect files in real time through Cowork's native file UI.

**Routing option 3 — temporary extraction folder.** Claude scaffolds at a temporary location with a README marking it for imminent removal. The operator cuts the folder out to a new standalone location on the host. Claude deletes the extraction folder in the same commit that bootstraps the consumer project's new thin-wrapper config. Maintains Cowork file visibility. Downside: transient git churn in the consumer's history (one commit adds the extraction folder, another removes it, both touching the consumer's tree for reasons unrelated to its goals).

This plan is written environment-agnostic so none of the later phases depend on which routing option was chosen.

## Capability scope

Session 25 locked in the following capability targets. Each is treated as a product requirement, not a stretch goal.

### Manifest system (all four types)

1. **Portable JSON manifest.** Machine-readable export of REGISTRY.yaml in JSON. Enables external tools, CI pipelines, and future plugin consumption to read the librarian's state without parsing YAML.
2. **Cryptographic manifest (SHA-256).** Per-file hash of every registered document. Separate from git SHA-1 because SHA-1 is cryptographically weak and would not hold up as tamper evidence in an IP dispute; SHA-256 is the current legal standard. Cost: approximately 100 lines of Python, one `hashlib` import.
3. **Dependency manifest.** Cross-reference graph as explicit edges (doc A depends on doc B). Enables impact analysis and feeds the dashboard's cross-reference visualization.
4. **Plugin install manifest.** Deferred to Phase F — the plugin format expects a skill directory structure that isn't stable yet.
5. **Full indexed tracking.** Full-text search index (Lunr, Phase D), temporal index (Phase C), vector index (Phase F, deferred). Feeds dashboard search and duplicate detection.

### Audit system (all four types)

1. **Drift audit.** Reconciles REGISTRY.yaml against filesystem state. Flags naming violations, orphans, missing files, broken cross-references. Formalizes the existing OODA check into a command with exit codes.
2. **IP evidence pack.** Signed snapshot of manifest + commit hash + timestamp. Suitable for patent filings and trade-secret claims. Uses SHA-256 from the cryptographic manifest as its integrity anchor.
3. **Diff audit (since last session).** Delta report between two points in time. Uses the append-only operation log plus git.
4. **Operation log (append-only).** Every librarian action writes a timestamped line: who, what, when, files touched, commit hash. Backbone for the other three audit types.

### Web output

- **Extended dashboard (Phase D).** Take the current V2.1 HTML dashboard and add search, filter by type/status, timeline view, and cross-reference graph. Single-file HTML, self-contained. Consumes the manifest (not REGISTRY directly).
- **Static site scaffold (Phase E, deferred).** Multi-page MkDocs-style generator. Publishable to GitHub Pages. Deferred because it's prep for plugin conversion, not needed for initial functionality.

### Index types — use case reference

**Full-text (Lunr) — Phase D.** Exact and prefix-matching search across doc titles and bodies. Client-side, no server. Adds ~2MB to the dashboard payload. Zero new dependencies in the browser.

**Temporal — Phase C.** Time-series view of every version bump, archive, and cross-ref change. Enables history replay, velocity analysis, staleness detection, and IP timeline reconstruction. Essentially free — computed from git-log-per-doc plus the audit log.

**Vector (semantic) — deferred to Phase F.** Embeddings-based semantic search. Unlocks: find docs that talk about a concept even when the word isn't in them; duplicate-detection at authoring time; auto-discovery of cross-references; auto-clustering; cross-project prior-art search. Cost: ~80MB local model, `sentence-transformers` dependency, ~15s per full re-index on M5 Max. Deferred because its biggest value is cross-project search, which requires Phase F's multi-project deployment.

## Execution plan

Six phases. Each phase is approximately one focused session. Phases build on each other in a required order.

### Phase A — Foundation (next session after routing decision)

**Goal:** bootstrap the standalone `librarian` project. Extract generic logic from the current skill implementation. Make consumer projects adoptable via a thin wrapper config.

**Depends on:** routing decision (option 1 selected; 2 and 3 are fallbacks).

**Deliverables, in the standalone project:**
- Project scaffold per the directory structure above (README, LICENSE placeholder, empty dirs with `.gitkeep`)
- `skill/SKILL.md` — full generic librarian skill, all references to specific projects removed from normative content (retained in clearly marked examples only)
- `schema/project_config.schema.yaml` — authoritative schema for `project_config.yaml` files, with field descriptions and defaults
- `schema/registry.schema.yaml` — schema for REGISTRY.yaml
- `examples/project_config.example.yaml` — an example consumer config as a reference
- `docs/REGISTRY.yaml` — the standalone project's own registry, bootstrapped empty plus the buildout plan entry
- `docs/buildout-plan-*.md` — this plan, copied into the standalone project as its own governed document

**Deliverables, in consumer projects:**
- `skills/librarian/project_config.yaml` — the consumer's concrete config
- `skills/librarian/SKILL.md` — rewritten as ~50 line wrapper that documents the dependency on the standalone librarian project, loads the project_config, and points Claude at the generic skill
- `docs/librarian-buildout-plan-20260411-V1.1.md` may remain in the consumer as a record of the decision (not the authoritative copy — the authoritative copy lives in the standalone project)

**Regression check:** a librarian query against a consumer's current registry produces equivalent behavior before and after the fork. No consumer workflows break.

**Not in scope for Phase A:** manifest generation, audit log, dashboard changes, Python runtime scripts, CLI entry points. Phase A is pure scaffolding plus skill-file restructuring.

### Phase B — Manifest system

**Goal:** emit portable JSON manifest, cryptographic manifest, dependency manifest, and search index on demand, from the standalone project.

**Depends on:** Phase A complete.

**Deliverables (all in standalone project):**
- `scripts/librarian-manifest-generate-YYYYMMDD-V1.0.py` — producer
- `schema/manifest.schema.json` — JSON Schema for the manifest format
- First generated manifest for a consumer project, written to that project's `docs/manifests/` via the standalone script pointed at the consumer's `project_config.yaml`
- Deterministic output (sorted keys, stable hash ordering)

### Phase C — Audit system + temporal index

**Goal:** drift detection, change deltas, operation history, IP evidence packaging.

**Depends on:** Phase B (IP evidence pack needs the cryptographic manifest).

**Deliverables (standalone scripts, tested with consumer projects):**
- `scripts/librarian-audit-drift-YYYYMMDD-V1.0.py`
- `scripts/librarian-audit-diff-YYYYMMDD-V1.0.py`
- `scripts/librarian-audit-evidence-pack-YYYYMMDD-V1.0.py`
- `operator/librarian-audit.jsonl` format spec — written to wherever each consuming project's `project_config.audit_log_path` points
- Temporal index as a derived view on top of audit log + git log

### Phase D — Web output V1 (extended dashboard)

**Goal:** dashboard V3.0 with search, filter, timeline, cross-reference graph.

**Depends on:** Phase B (consumes manifest) and Phase C (consumes temporal data).

**Deliverables:**
- `dashboard/librarian-dashboard-template-YYYYMMDD-V3.0.html` — template in standalone project
- Generator script that renders the template against a consuming project's manifest
- Consumer projects receive rendered dashboards at their configured output location
- Client-side Lunr search, filter UI, timeline view, cytoscape.js or d3-force dependency graph
- Zero external dependencies, works offline, no data leaves the machine

### Phase E — Static site scaffold

**Goal:** multi-page publishable site generator consuming the manifest.

**Depends on:** Phase D. The dashboard proves the manifest is a sufficient data contract.

**Deliverables:** scaffold only. Generator writes a multi-page `_site/` tree from the manifest. MkDocs-like structure. Polish and GitHub Pages integration land in Phase F.

### Phase F — Plugin conversion + open-source release

**Goal:** repackage standalone `librarian` as a Claude Code plugin, publish open-source (after IP protection is established), add vector index, tie into the planned startup plugin bundle.

**Depends on:** Phases A–E plus IP posture clearance.

**Deliverables:**
- Plugin manifest in the Claude Code plugin format (exact schema TBD at phase start)
- Marketplace entry
- Public LICENSE (Apache 2.0 or MIT — TBD)
- Open-source repo — the standalone project flipped to public
- Vector index via `sentence-transformers/all-MiniLM-L6-v2`
- Scrub pass to ensure no project-specific content remains in generic examples or test fixtures
- Startup plugin bundle integration (details TBD)

## Risks and open questions

**Name collision risk.** `librarian` is a generic noun. PyPI, npm, and GitHub all have existing projects using that name. This is acceptable for a private repo; Phase F publication must confirm namespace availability and may require a prefix (e.g., `claude-librarian`, `doc-librarian` as the published PyPI package name while keeping `librarian` as the local project directory).

**Cowork visibility during standalone work.** If the operator picks routing option 2 (temp workspace), the standalone project is invisible in Cowork's file browser during Phase A. The operator must rely on Claude's verbal reports plus the final handoff archive. Option 1 (selected) and option 3 preserve visibility.

**Cross-repo sync during iteration.** As Phase B adds a manifest generator, consumer projects remain the first test targets. The standalone scripts need to read a consumer's `project_config.yaml` and write manifests into the consumer's repo. This cross-repo read/write must be explicit in every script's config (no hardcoded paths). Flagging this as a risk because it's a common drift source.

**SHA-1 vs SHA-256 double-hashing.** Session 25 chose SHA-256 for IP/legal reasons. Git stores SHA-1 per blob. The manifest carries both: git commit hash as the git-side anchor, SHA-256 as the standalone evidence anchor. Belt and suspenders. Cost is sub-second compute for typical document counts.

**The manifest becomes a governed document.** Once the manifest is generated, that file is registered and versioned. The librarian manages a manifest of everything, including the manifest. Phase B must handle the edge case of the manifest being modified during generation.

**Cross-project vector search requires multi-registry consolidation.** Deferred to Phase F. Architecture decision (central aggregator vs. federated) deferred.

**Dashboard V3.0 payload size.** Lunr + cytoscape.js + manifest JSON + full-text corpus in one HTML file — likely 3–10 MB. Acceptable for a governance dashboard. Flag for optimization if it exceeds 10 MB.

**Plugin spec drift.** Claude Code plugin format may evolve between now and Phase F. Phase F planning starts with a fresh read of the current plugin spec.

**Open-source scrubbing risk.** Consumer project content may contain trade secrets. Phase E should draft the scrub checklist so it's ready when Phase F executes.

## Success criteria

The buildout is complete when:

1. The standalone `librarian` project exists independently and has its own git history
2. The generic skill has no project-specific content in normative sections — examples may reference example projects but the skill works identically for any project supplying a valid `project_config.yaml`
3. Consumer projects consume the standalone skill via a thin wrapper config — if the standalone project is missing, the wrapper fails in an obvious way rather than continuing to work by accident
4. A manifest can be generated deterministically and contains all four sub-manifests
5. All four audit types can be run from the command line and produce machine-readable output
6. Dashboard V3.0 renders against the manifest with search, filter, timeline, and graph views
7. A synthetic second test project can adopt the generic skill by dropping in a `project_config.yaml` and running the bootstrap, with no generic-skill edits required
8. The standalone project passes its own test suite against the synthetic fixtures

## Out of scope

- Vector semantic search until Phase F
- Static site GitHub Pages publishing until Phase F
- Multi-project registry aggregation until Phase F
- Any changes to consumer project's core code (not related to governance) — this buildout is governance only
- Web UI edits to anything other than the librarian dashboard
- Changes to a consumer project's pre-commit hooks beyond what's required to support the config layer

## Cross-references

| Document | Affected in phase | Nature of update |
|---|---|---|
| skills/librarian/SKILL.md | Phase A | Rewritten as thin wrapper pointing at standalone |
| skills/librarian/project_config.yaml (new) | Phase A | Created — consumer project's concrete config |
| docs/REGISTRY.yaml | Phase A, B, C, D | Schema compatibility; manifest entries |
| docs/diagrams/librarian-dashboard-*.html | Phase D | Generated from standalone template |
| librarian/ (new standalone project) | Phase A–F | Created and iterated |

## Version history

| Version | Date | Author | Notes |
|---|---|---|---|
| V1.0 | 2026-04-11 | Christopher A. Kahn | Initial plan. Captures standalone architecture decision from Session 25. Routing between in-consumer and standalone was resolved in favor of standalone before this file was committed. |
| V1.1 | 2026-04-11 | Christopher A. Kahn | Renamed standalone project `doc-librarian` → `librarian`. Wrapper skill renamed to generic `librarian` (directory `skills/librarian/`). Phase A routing decision recorded as resolved (option 1 selected). Added name collision risk note for Phase F publication. No scope, phase, capability, or timeline changes. Generic dashboard naming `librarian-dashboard-*` replaces project-specific variants. |
