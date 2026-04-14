# Release Notes — v0.7.1

**Date:** 2026-04-13
**Version:** V1.0
**Status:** Active

## Overview

First public release of **Librarian** — a zero-dependency document governance tool for projects with serious documentation needs.

- **GitHub:** https://github.com/ghengis5-git/librarian
- **PyPI:** https://pypi.org/project/librarian-2026/0.7.1/
- **Plugin:** `claude plugins marketplace add ghengis5-git/librarian`
- **License:** Apache 2.0

## Highlights

- **22 CLI commands** — audit, scaffold, manifest, evidence, diff, log, dashboard, site, init, config, register, bump, status, and more
- **57+ document templates** across 10 categories (universal, software, scientific, business, legal, healthcare, finance, government, security, compliance)
- **9 built-in presets** — software, business, accounting, government, scientific, finance, healthcare, legal, minimal
- **24 compliance standards** surfaced in the Settings UI (HIPAA, DoD 5200, ISO 9001, ISO 27001, SEC/FINRA, GDPR, SOX, PCI-DSS, and more)
- **Tamper-evident evidence packs** with SHA-256 manifest seals and hash-chained operation log
- **Optional SSH/GPG commit signing** captured in evidence packs
- **Project-gated naming enforcement hook** — ships disabled, opt-in per project via `enforce_naming_hook` flag
- **Interactive static site** — Home, Manage, Audit, Tree, Graph, Templates, Settings pages, all generated from a single `REGISTRY.yaml`
- **Recommendations engine** — 4-rule deterministic gap analysis (baseline, cross-reference, maturity, compliance)
- **681 tests** passing across 13 test files

## Install

```bash
# As a CLI tool
pip install librarian-2026

# As a Claude Code / Cowork plugin
claude plugins marketplace add ghengis5-git/librarian
claude plugins add librarian@librarian-marketplace
```

## What's in the box

Everything runs offline. No data leaves your machine. Only runtime dependency is PyYAML.

## Known Issues

- Oplog chain is detect-only (integrity verification, not write prevention). Changing it to prevention mode requires an oplog-format change.
- Pre-commit hook greps for full filepath but registry stores filename only — harmless warnings possible.

## Credits

Built solo by Chris Kahn. Thanks to the Claude Code and Cowork teams for the agent tooling.
