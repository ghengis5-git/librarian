# Librarian

Standalone document governance tool. Enforces naming conventions, tracks versions, manages cross-references, and produces tamper-evident manifests and audit trails.

Project-agnostic by design — works with any project that supplies a `REGISTRY.yaml`.

## Install

```bash
pip install -e .
```

## Quick Start

```bash
# Initialize a new registry from a preset
python -m librarian init --preset software

# Run a governance audit
python -m librarian --registry docs/REGISTRY.yaml audit

# Generate a portable manifest (JSON + SHA-256 hashes)
python -m librarian --registry docs/REGISTRY.yaml manifest -o manifest.json

# Generate an interactive dashboard
python -m librarian --registry docs/REGISTRY.yaml dashboard -o dashboard.html

# Generate a full static site
python -m librarian --registry docs/REGISTRY.yaml site --output site/
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `audit` | OODA governance audit (drift, naming, orphans, cross-refs) |
| `status` | Quick registry summary (counts by status) |
| `register` | Add a new document entry to the registry |
| `bump` | Version-bump an existing document |
| `manifest` | Generate portable JSON manifest with SHA-256 hashes |
| `evidence` | Generate tamper-evident IP evidence pack |
| `diff` | Compare two manifests |
| `log` | Read/filter the append-only operation log |
| `dashboard` | Render interactive HTML dashboard |
| `site` | Generate full static site with sidebar navigation |
| `init` | Scaffold a new REGISTRY.yaml from a preset |
| `config` | Show resolved config or list presets/templates |

## Naming Convention

All governed documents follow: `descriptive-name-YYYYMMDD-VX.Y.ext`

- Major (X) = rewrites or redesigns
- Minor (Y) = updates or fixes within same scope
- Configurable: separator, case, date format, version format, domain prefix

## Presets

9 built-in configuration presets: `software`, `business`, `accounting`, `government`, `scientific`, `finance`, `healthcare`, `legal`, `minimal`.

## Stack

- Python 3.13
- PyYAML
- Zero runtime dependencies beyond PyYAML (by design)

## Tests

```bash
python -m pytest tests/ -v
```

329 tests across 10 test files.

## License

All rights reserved. Open-source release planned for Phase F.
