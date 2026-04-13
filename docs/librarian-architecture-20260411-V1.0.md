---
title: Librarian Architecture
filename: librarian-architecture-20260411-V1.0.md
version: 1.0
date: 2026-04-11
status: active
author: Christopher A. Kahn
classification: PERSONAL / INTERNAL USE ONLY
---

# Librarian Architecture — V1.0

## Overview

The librarian is a document governance system that enforces naming conventions, tracks versions, manages cross-references, and produces tamper-evident manifests. It operates as a Python package (`librarian`) consumed by project-specific skill wrappers in Claude Code / Cowork environments.

This document describes the system as of v0.2.0 (Phase B complete).

## Design principles

**Registry as single source of truth.** REGISTRY.yaml is the only authoritative catalog. Every other output (manifests, audit reports, dashboards) is derived from the registry plus the filesystem. There is no secondary database.

**Stateless modules.** Each module (naming, versioning, registry, audit, manifest) is stateless. Functions accept data in, return data out. No module writes to disk except through explicit `save()` or `write_manifest()` calls initiated by the CLI layer.

**Deterministic output.** Manifests use sorted keys, sorted hashes, and sorted edges. Two runs against the same registry and filesystem produce identical JSON (modulo the `generated_at` timestamp). This enables meaningful diffs between manifest versions.

**Project-agnostic core.** The `librarian` package has zero project-specific logic. All project customization comes from the `project_config` block in REGISTRY.yaml. When `project_config` is absent, built-in defaults are used so the librarian works standalone for ad hoc use.

**Convention over configuration.** The naming convention (`descriptive-name-YYYYMMDD-VX.Y.ext`) is hardcoded in the regex. Projects can customize the separator, case, forbidden words, and exempt files — but not the structural pattern. This is intentional: the pattern is the product's identity.

## Package structure

```
librarian/
├── __init__.py        # public API, version string
├── __main__.py        # CLI entry point (argparse)
├── naming.py          # naming convention parser and validator
├── versioning.py      # version bump logic
├── registry.py        # REGISTRY.yaml CRUD
├── audit.py           # OODA audit engine
└── manifest.py        # manifest generation (JSON + SHA-256 + graph)
```

## Module responsibilities

### naming.py

Parses filenames against the canonical regex `stem-YYYYMMDD-VX.Y.ext`. Validates date ranges (real calendar dates only), forbidden words, and case rules. Returns a `ParsedName` dataclass on success or a `ValidationResult` with error details on failure. Infrastructure-exempt files bypass the date-version check.

### versioning.py

Provides `Version` dataclass with `bump_minor()` and `bump_major()` methods. The `bump_filename()` function takes a current filename and produces the next version's filename with an updated date stamp. Major bumps reset the minor version to zero.

### registry.py

The `Registry` class loads REGISTRY.yaml into memory, provides document CRUD operations (get, add, supersede), and updates aggregate metadata on every mutation. Uses naive read-modify-write (no file locking) — safe for single-user single-process use. The `project_config` block is exposed as properties: `infrastructure_exempt`, `tracked_dirs`.

### audit.py

The `audit()` function walks tracked directories, compares on-disk files against registered entries, and produces an `AuditReport` with: unregistered files, missing files, naming violations, and pending cross-references. The `format_report()` function renders the report as a human-readable banner.

### manifest.py

The `generate()` function produces a `Manifest` containing three sub-manifests:

1. **Portable JSON snapshot** — the full REGISTRY.yaml content serialized as JSON. Enables external tools to consume registry state without YAML parsing.

2. **SHA-256 cryptographic hashes** — per-file hash of every registered document found on disk. The manifest also computes a tamper-evident seal: a single SHA-256 over the sorted `filename:hash` pairs. If any file changes, the seal changes.

3. **Dependency graph** — cross-reference edges extracted from three sources: `cross_references` entries (explicit section-level references), `supplements` lists (document supplements relationships), and `supersedes`/`superseded_by` chains (version history edges). Sorted by (source, target) for determinism.

The `write_manifest()` function writes the combined manifest to a JSON file, creating parent directories as needed.

## CLI design

The CLI uses argparse with global flags (`--repo`, `--registry`) that must precede the subcommand. Five subcommands:

| Command | Purpose | Exit code |
|---|---|---|
| `audit` | OODA audit — files vs registry | 0 if clean, 1 if findings |
| `status` | Registry counts summary | always 0 |
| `register` | Add a new document entry | 0 on success, 1 if duplicate |
| `bump` | Version-bump a document | 0 on success, 1 if not found |
| `manifest` | Generate combined manifest | always 0 |

The `manifest` subcommand accepts `--output` (file path), `--no-snapshot`, `--no-hashes`, and `--no-graph` flags. When `--output` is omitted, JSON is printed to stdout with summary stats on stderr (pipe-safe).

## Data flow

```
REGISTRY.yaml (on disk)
        │
        ▼
  Registry.load()
        │
        ├──► audit()      ──► AuditReport  ──► format_report() ──► stdout
        │
        ├──► generate()   ──► Manifest      ──► to_json()       ──► file/stdout
        │        │
        │        ├── _hash_file()      for each registered doc
        │        ├── _resolve_file_path()  locate on disk
        │        ├── _extract_edges()  parse cross_references/supplements/supersedes
        │        └── _compute_manifest_hash()  tamper-evident seal
        │
        ├──► add_document()  ──► save()  ──► REGISTRY.yaml (updated)
        │
        └──► supersede()     ──► save()  ──► REGISTRY.yaml (updated)
```

## File resolution strategy

When computing SHA-256 hashes, the manifest generator needs to locate each registered file on disk. Resolution order:

1. Check the explicit `path` field in the document entry (e.g., `docs/alpha-doc-20260101-V1.0.md`)
2. Search each `tracked_dir` for the filename
3. Recursively search subdirectories of each tracked dir (handles `docs/archive/`, `docs/diagrams/`)
4. Return `None` if not found — the file hash is recorded with `exists: false`

## SHA-256 design decisions

**Why SHA-256 instead of git's SHA-1:** Git uses SHA-1 for internal object hashing. SHA-1 is cryptographically broken (SHAttered attack, 2017). For document governance used in IP evidence and patent filings, SHA-256 is the current legal standard. The manifest carries both: git commit hash as the version-control anchor, SHA-256 as the standalone evidence anchor.

**Tamper-evident seal:** The `manifest_sha256` field is not just any hash — it's computed over the sorted canonical string `filename:sha256\n` for each existing file. This means: if any file is modified, added, or removed, the seal changes. The seal can be verified independently of the manifest file itself by re-computing it from the individual file hashes.

**Missing files are excluded from the seal:** Files registered but not on disk (e.g., superseded files that were archived) get `exists: false` and are excluded from the seal computation. This prevents a missing file from invalidating the seal for all other files.

## Consumer integration

The librarian is installed as an editable package (`pip install -e ~/projects/librarian`) in each consuming project's venv. The consuming project provides:

1. A `project_config` block in its REGISTRY.yaml
2. A thin skill wrapper (e.g., `skills/doc-librarian/SKILL.md`) that documents CLI commands and project-specific governance rules

The skill wrapper contains a condensed governance protocol (naming rules, version bump decision tree, cross-reference cascade) and delegates mechanical operations to the CLI. This split keeps the governance knowledge in the skill file (read by Claude) and the implementation in the Python package (run by the operator).

## Test architecture

Tests use pytest with fixtures defined in `conftest.py`. Each test module creates temporary repos with synthetic REGISTRY.yaml files, avoiding any dependency on real project data.

| Test file | Tests | Coverage |
|---|---|---|
| test_naming.py | 10 | Canonical parsing, validation, forbidden words, exemptions |
| test_versioning.py | 10 | Version bumps, filename mutations, error handling |
| test_registry.py | 10 | CRUD, supersession, metadata updates, round-trip |
| test_audit.py | 6 | Clean state, unregistered, missing, naming, exemptions |
| test_manifest.py | 26 | Hashing, edges, seal, integration, serialization, file resolution |

Total: 62 tests, ~0.10s execution time.

## Version history

| Version | Date | Notes |
|---|---|---|
| V1.0 | 2026-04-11 | Initial architecture document covering v0.2.0 (Phase B). |
