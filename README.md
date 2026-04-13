# librarian

Document governance for projects that outgrow "just put it in docs/." Enforces naming conventions, tracks versions, manages cross-references between documents, and produces tamper-evident manifests — all from a single `REGISTRY.yaml` file.

**Zero external dependencies** beyond PyYAML. Runs offline. No data leaves your machine.

## Why

Projects with 15+ cross-referencing documents drift out of sync without enforcement. Versions get skipped, naming conventions break, addenda create promises of updates that never happen, and nobody can tell which `architecture-v2-final-FINAL.docx` is actually current. The librarian prevents that.

## Install

### As a Claude Code / Cowork Plugin

```bash
claude plugins add ghengis5/librarian
```

The plugin gives Claude the governance skill — it will automatically validate document names, manage your registry, and scaffold new documents from templates.

### As a CLI Tool (pip)

```bash
pip install librarian-2026
```

```bash
librarian --help
```

Both `librarian` and `python -m librarian` work as entry points.

## Quick Start

```bash
# Initialize a registry from a preset
librarian init --preset software

# Run a governance audit
librarian --registry docs/REGISTRY.yaml audit

# Scaffold a document from a template
librarian --registry docs/REGISTRY.yaml scaffold --template architecture-decision-record

# See what documents your project is missing
librarian --registry docs/REGISTRY.yaml audit --recommend

# Generate a portable manifest (JSON + SHA-256 hashes + dependency graph)
librarian --registry docs/REGISTRY.yaml manifest -o manifest.json

# Generate an interactive dashboard
librarian --registry docs/REGISTRY.yaml dashboard -o dashboard.html

# Generate a full static site
librarian --registry docs/REGISTRY.yaml site --output site/
```

## Naming Convention

All governed documents follow: `descriptive-name-YYYYMMDD-VX.Y.ext`

| Component | Rule |
|-----------|------|
| Descriptive name | Lowercase, hyphen-separated. No generic words (file, download, output). |
| Date | `YYYYMMDD` — date of creation or last major revision. |
| Version | `VX.Y` — major (X) for rewrites, minor (Y) for updates. |
| Extension | Must match actual format. |

Configurable: separator (`-`, `_`, `.`), case, date format, version format, domain prefix. Infrastructure files (README.md, REGISTRY.yaml, .gitignore) are exempt.

## CLI Commands

| Command | Description |
|---------|-------------|
| `audit` | OODA governance audit — drift, naming, orphans, cross-refs, folder density (`--recommend`, `--json`) |
| `scaffold` | Create a document from a template (`--list`, `--list-all`, `--dry-run`) |
| `status` | Quick registry summary (counts by status) |
| `register` | Add a new document to the registry |
| `bump` | Version-bump a document (`--minor`, `--major`) |
| `manifest` | Generate portable JSON manifest with SHA-256 hashes |
| `evidence` | Generate tamper-evident IP evidence pack |
| `diff` | Compare two manifests |
| `log` | Read/filter the append-only operation log |
| `dashboard` | Render interactive HTML dashboard |
| `site` | Generate full static site with sidebar navigation |
| `init` | Scaffold a new REGISTRY.yaml from a preset |
| `config` | Show resolved config or list presets/templates |

## Document Templates

57+ templates across 10 categories, organized by preset. Templates scaffold properly named, pre-sectioned files with tags and cross-references pre-wired.

```bash
librarian --registry docs/REGISTRY.yaml scaffold --list       # Templates for your preset
librarian --registry docs/REGISTRY.yaml scaffold --list-all   # All templates
librarian --registry docs/REGISTRY.yaml scaffold --template threat-model --dry-run  # Preview
```

Templates include compliance-conditional sections (HIPAA, DoD 5200, ISO 9001/27001, SEC/FINRA) that activate based on your project's compliance flags. Custom templates override built-ins.

## Presets

9 built-in configuration presets: `software`, `business`, `accounting`, `government`, `scientific`, `finance`, `healthcare`, `legal`, `minimal`.

```bash
librarian init --preset healthcare
librarian config --list-presets
```

## Setup

### Optional: Enable Naming Enforcement Hook

The plugin ships with a naming enforcement hook that is **disabled by default**. When enabled, it checks every file write against the naming convention and blocks non-compliant document names.

To enable:

1. Open `hooks/hooks.json` in the plugin directory.
2. Rename the `_PreToolUse` key to `PreToolUse` (remove the leading underscore).
3. Save the file.

To disable again, add the underscore back.

The hook only affects governed documents (files in tracked directories with document extensions). Source code, config files, and infrastructure-exempt files are not affected.

## Stack

- Python ≥ 3.10
- PyYAML (only runtime dependency)
- pytest (dev only)

## Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

578 tests across 13 test files.

## License

Apache 2.0 — see [LICENSE](LICENSE).
