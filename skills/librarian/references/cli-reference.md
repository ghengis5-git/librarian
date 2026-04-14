# CLI Reference

All commands accept `--registry <path>` to specify the REGISTRY.yaml location. Default: `docs/REGISTRY.yaml`.

Both `librarian` and `python -m librarian` work as entry points.

## Commands

### audit

Run an OODA governance audit: drift detection, naming violations, orphans, missing files, broken cross-references, folder density analysis.

```bash
librarian --registry docs/REGISTRY.yaml audit
librarian --registry docs/REGISTRY.yaml audit --recommend   # Include gap analysis
librarian --registry docs/REGISTRY.yaml audit --json         # Machine-readable output
librarian --registry docs/REGISTRY.yaml audit --recommend --json  # Both
```

**Flags:**
- `--recommend` — Append document recommendations (preset baseline gaps, cross-ref pull, maturity progression, compliance triggers).
- `--json` — Output structured JSON instead of human-readable text.

### scaffold

Create a new document from a template. Applies naming convention, registers in REGISTRY.yaml, and logs the operation.

```bash
librarian --registry docs/REGISTRY.yaml scaffold --template strategic-plan
librarian --registry docs/REGISTRY.yaml scaffold --template runbook --title "Deployment Runbook" --folder ops/
librarian --registry docs/REGISTRY.yaml scaffold --list        # List templates for active preset
librarian --registry docs/REGISTRY.yaml scaffold --list-all    # List all templates across all presets
librarian --registry docs/REGISTRY.yaml scaffold --template threat-model --dry-run  # Preview only
```

**Flags:**
- `--template <id>` — Template ID (e.g., `strategic-plan`, `threat-model`).
- `--title <text>` — Override the default title.
- `--folder <path>` — Output directory (default: `docs/`).
- `--author <name>` — Override author.
- `--preset <name>` — Override preset for template resolution.
- `--list` — List available templates for the active preset.
- `--list-all` — List all templates across all presets.
- `--dry-run` — Preview rendered output without writing.
- `--no-register` — Skip registry and oplog updates.

### status

Quick registry summary showing document counts by status.

```bash
librarian --registry docs/REGISTRY.yaml status
```

### register

Add a new document entry to the registry.

```bash
librarian --registry docs/REGISTRY.yaml register <filename>
librarian --registry docs/REGISTRY.yaml register <filename> --review-by 2026-12-31
```

The optional `--review-by YYYY-MM-DD` flag stores a `next_review` deadline.
Past deadlines are surfaced in `audit` output and on the Audit page's
"Overdue Reviews" KPI card. See [`review`](#review) for editing later.

### bump

Version-bump an existing document.

```bash
librarian --registry docs/REGISTRY.yaml bump <filename> --minor
librarian --registry docs/REGISTRY.yaml bump <filename> --major
librarian --registry docs/REGISTRY.yaml bump <filename> --review-by 2027-06-30
librarian --registry docs/REGISTRY.yaml bump <filename> --clear-review
```

The new version inherits `next_review` from the predecessor by default.
Use `--review-by` to override or `--clear-review` to drop the deadline.
The two flags are mutually exclusive.

### review

Manage per-document review deadlines (the optional `next_review` field).

```bash
librarian --registry docs/REGISTRY.yaml review set <filename> --by 2026-12-31
librarian --registry docs/REGISTRY.yaml review clear <filename>
librarian --registry docs/REGISTRY.yaml review list                   # all docs with deadlines
librarian --registry docs/REGISTRY.yaml review list --overdue         # past-due only
librarian --registry docs/REGISTRY.yaml review list --upcoming        # next 30 days
librarian --registry docs/REGISTRY.yaml review list --upcoming --within-days 90
```

Dates are absolute ISO 8601 (`YYYY-MM-DD`). Superseded and archived
documents are excluded from overdue calculations. Overdue findings
have **warn** severity — they appear in audit output but do not flip
the audit exit code (matches how folder suggestions behave).

### manifest

Generate a portable JSON manifest with SHA-256 file hashes and dependency graph.

```bash
librarian --registry docs/REGISTRY.yaml manifest -o manifest.json
librarian --registry docs/REGISTRY.yaml manifest --no-hashes   # Skip SHA-256
librarian --registry docs/REGISTRY.yaml manifest --no-graph    # Skip dependency graph
librarian --registry docs/REGISTRY.yaml manifest --no-snapshot # Skip registry snapshot
```

### evidence

Generate a tamper-evident IP evidence pack (manifest + git commit + timestamp + optional signature).

```bash
librarian --registry docs/REGISTRY.yaml evidence -o evidence.json
```

Evidence signing is configurable via `project_config.evidence_signing`: `off` (default), `gpg`, or `ssh`.

### diff

Compare two manifests and produce a delta report.

```bash
librarian diff old-manifest.json new-manifest.json
librarian diff old-manifest.json new-manifest.json --json
```

### log

Read and filter the append-only operation log.

```bash
librarian --registry docs/REGISTRY.yaml log
librarian --registry docs/REGISTRY.yaml log --last 10
librarian --registry docs/REGISTRY.yaml log --since 2026-04-01
```

### dashboard

Render an interactive HTML dashboard from the manifest.

```bash
librarian --registry docs/REGISTRY.yaml dashboard -o dashboard.html
```

### site

Generate a full static site with sidebar navigation, document pages, template catalog, and dependency graph.

```bash
librarian --registry docs/REGISTRY.yaml site --output site/
```

### init

Scaffold a new REGISTRY.yaml from a preset.

```bash
librarian init --preset software
librarian init --preset healthcare --naming-template healthcare
librarian init --preset government --create-folders
```

**Flags:**
- `--preset <name>` — Configuration preset (software, business, accounting, government, scientific, finance, healthcare, legal, minimal).
- `--naming-template <name>` — Naming template (default, legal, engineering, corporate, dateless, scientific, healthcare, finance).
- `--create-folders` — Create the directory structure defined by the preset.

### config

Show resolved configuration or list available presets and templates.

```bash
librarian --registry docs/REGISTRY.yaml config
librarian config --list-presets
librarian config --list-templates
librarian config --preset software
```
