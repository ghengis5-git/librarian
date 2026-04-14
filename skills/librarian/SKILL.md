---
name: librarian
description: >
  Document governance, version control, and registry management. Use this skill
  whenever: creating, updating, or version-bumping any project document; checking
  what documents exist and their current versions; processing cross-reference tables
  from addenda to identify affected documents; enforcing the naming convention
  (descriptive-name-YYYYMMDD-VX.Y.ext); maintaining the document registry
  (REGISTRY.yaml); generating document status reports; or any time someone says
  "update the docs", "what version is X", "bump the version", "catalog this",
  "what documents need updating", "registry", "document list", or "version history".
  Also triggers when any other skill produces a document — the librarian validates
  naming, updates the registry, and checks cross-references before the document
  is finalized.
metadata:
  version: "0.7.2"
---

# Document Librarian

A governance layer that maintains the authoritative catalog of project documentation. It enforces naming conventions, tracks versions, manages cross-references between documents, and ensures no document update orphans dependent files.

The librarian is **project-agnostic**. It reads project-specific rules from a `project_config` block in `REGISTRY.yaml`. When no config is present, it falls back to built-in defaults.

## Prerequisites

Install the CLI:

```bash
pip install librarian-2026
```

Verify:

```bash
librarian --help
```

## Quick Start

1. **Initialize** a registry from a preset:

```bash
librarian init --preset software
```

This creates `docs/REGISTRY.yaml` with sensible defaults for a software project.

2. **Audit** your documents:

```bash
librarian --registry docs/REGISTRY.yaml audit
```

3. **Scaffold** a new document from a template:

```bash
librarian --registry docs/REGISTRY.yaml scaffold --template architecture-decision-record
```

## First-Run Setup: Naming Enforcement Hook

The plugin ships a `PreToolUse` hook that can block file writes whose names violate the governed-document naming convention. **It is disabled by default** so the plugin is safe to install everywhere; you opt in per project.

When the user runs `librarian init` for the first time in a project, prompt them:

> *"Librarian can block writes to files whose names don't follow the convention `descriptive-name-YYYYMMDD-VX.Y.ext`. This catches drift early but adds a step to every write. Enable the naming-enforcement hook for this project? [y/N]"*

- **If yes** — set `project_config.enforce_naming_hook: true` in the new `REGISTRY.yaml`, and print the one-line edit needed in `<plugin>/hooks/hooks.json` (rename `_PreToolUse` → `PreToolUse`). The project flag means the hook only enforces when the project opts in; other projects stay unaffected.
- **If no** — set `project_config.enforce_naming_hook: false`. The hook remains disabled globally; `librarian audit` still flags violations on demand.

Users who skip the prompt can flip this later by editing the registry or re-running `librarian init --force --enable-hook`.

## Core Responsibilities

### 1. Registry Maintenance

Maintain `REGISTRY.yaml` as the single source of truth for all project documents. Every entry tracks: filename, title, version, date, status (draft/active/superseded/archived), author, classification, cross-references, and tags.

**CLI:** `librarian register`, `librarian status`, `librarian bump`

### 2. Naming Convention Enforcement

All governed documents follow: `descriptive-name-YYYYMMDD-VX.Y.ext`

- **Descriptive name:** lowercase, hyphen-separated. No generic words (file, download, output, document).
- **Date:** YYYYMMDD of creation or last major revision.
- **Version:** VX.Y where X = major rewrites, Y = minor updates.
- Infrastructure files (README.md, REGISTRY.yaml, .gitignore) are exempt.

When a document is created or renamed, validate against the convention. If it fails, suggest the correct name.

**CLI:** `librarian audit` flags violations. The optional naming enforcement hook (see Setup) blocks non-compliant writes automatically.

### 3. Version Bump Logic

- **Minor bump (Y):** Content updates within existing scope.
- **Major bump (X):** Structural rewrites, scope expansion, redesigns.
- **Date updates** whenever version bumps.

When bumping: rename the file, update the registry, update the version history inside the document, and check if other documents reference it by filename.

**CLI:** `librarian bump <filename> --minor` or `--major`

### 4. Cross-Reference Processing

When an addendum includes a cross-reference table listing affected documents and sections:

1. Parse the cross-reference table.
2. Check whether referenced sections exist in target documents.
3. Generate a checklist of required updates.
4. Execute approved updates (pointer approach by default — inline notes referencing the source).
5. Bump versions on all affected documents.

This is the most important function. Without it, addenda create promises of updates that never happen.

**CLI:** `librarian audit` flags pending cross-references.

### 5. Document Templates

57+ templates across 10 categories (universal, software, business, legal, scientific, healthcare, finance, government, security, compliance). Templates create properly named, pre-sectioned files with tags and cross-references pre-wired.

Compliance-conditional sections activate based on project flags (HIPAA, DoD 5200, ISO 9001/27001, SEC/FINRA).

**CLI:** `librarian scaffold --template <name>`, `--list`, `--list-all`, `--dry-run`

See `references/templates.md` for the full catalog.

### 6. Recommendations Engine

Deterministic gap analysis that detects missing documents based on four rules: preset baseline expectations, cross-reference pull, maturity progression (prerequisite chains), and compliance triggers.

**CLI:** `librarian audit --recommend`, `--json` for machine-readable output.

### 7. Manifests and Evidence

- **Portable manifest:** JSON export with SHA-256 file hashes and dependency graph.
- **IP evidence pack:** Tamper-evident snapshot (manifest + commit hash + timestamp) for patent filings and trade-secret claims.
- **Diff audit:** Delta report between two manifests.
- **Operation log:** Append-only JSONL with SHA-256 hash chaining.

**CLI:** `librarian manifest`, `evidence`, `diff`, `log`

### 8. Web Output

- **Interactive dashboard:** Single-file HTML with Lunr search, dependency graph, filter chips, and timeline.
- **Static site:** Multi-page HTML site with sidebar navigation, document pages, template catalog, and recommendations panel.

**CLI:** `librarian dashboard -o dashboard.html`, `librarian site --output site/`

## Configuration

The librarian reads `project_config` from `REGISTRY.yaml`. Minimal config:

```yaml
project_config:
  project_name: "My Project"
```

Everything else falls back to defaults. For full configuration options, see `references/config-presets.md`.

9 built-in presets: `software`, `business`, `accounting`, `government`, `scientific`, `finance`, `healthcare`, `legal`, `minimal`.

## Workflow Integration

### When Another Skill Produces a Document

1. Validate the filename against the naming convention.
2. Create or update the registry entry.
3. Check if the new document cross-references existing documents.
4. Flag any documents that may need version bumps.

### When Processing an Addendum

1. Parse all cross-reference tables.
2. Build a complete update checklist.
3. Present to the operator for review.
4. Execute approved updates.
5. Bump versions on all affected documents.
6. Update the registry.

### Session Manifest

At session end, when multiple documents were produced, generate a manifest listing every file with its final version and whether it is CURRENT or SUPERSEDED.

## CLI Reference

See `references/cli-reference.md` for the complete command reference with all flags and examples.
