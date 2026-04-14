# Release Notes — v0.7.4

**Date:** 2026-04-14
**Version:** V4.0
**Status:** Draft

## Overview

Feature release. Two additions on top of v0.7.3:

- **Oplog append-only detection** (Phase 7.5) — promotes the detect-only
  SHA-256 hash chain to prevention-mode by adding OS-level append-only
  flag support (`chflags uappend` on macOS, `chattr +a` on Linux).
- **Pre-commit framework integration** (Phase 7.7) — librarian's naming
  convention is now installable via
  [pre-commit](https://pre-commit.com) with a 3-line `.pre-commit-config.yaml`
  addition. Runs on Windows/macOS/Linux.

Backwards compatible — no schema migrations, no registry edits required.
Existing registries continue to load and audit cleanly. The
`next_review` field and `review` CLI from v0.7.3 are unchanged.

- **GitHub:** https://github.com/ghengis5-git/librarian
- **PyPI:** https://pypi.org/project/librarian-2026/0.7.4/
- **Plugin:** `claude plugins marketplace add ghengis5-git/librarian`
- **License:** Apache 2.0

## What's new

### Oplog append-only flag (Phase 7.5)

The oplog stores plaintext JSON entries with a SHA-256 hash chain. Before
v0.7.4, that chain was **detect-only**: an attacker with write access to
the log file could modify any entry and recompute the chain forward. The
audit would still accept the log as internally consistent.

v0.7.4 adds detection for the OS-level append-only flag, which closes
that gap when set:

- **macOS:** `chflags uappend <oplog>` — BSD UF_APPEND flag (0x04).
  No sudo required (owner-only).
- **Linux:** `sudo chattr +a <oplog>` — requires `CAP_LINUX_IMMUTABLE`.

Once set, the kernel rejects any open that isn't `O_APPEND`. Truncation
and random-offset writes return `EPERM`. The librarian's existing
`oplog.append()` already uses `open(path, "a")`, so normal operation is
unaffected.

**Cross-platform detection.** The CLI and audit report surface the lock
state as True/False/None (undetectable), gracefully degrading on Windows,
overlay filesystems, and any environment where attribute probes are
restricted.

**New CLI:**

```bash
librarian oplog status
# Shows: locked / unlocked / undetectable / missing, plus apply instructions
```

**New setup helper** (outside Python because Linux needs sudo):

```bash
scripts/librarian-oplog-lock-20260414-V1.0.sh status
scripts/librarian-oplog-lock-20260414-V1.0.sh lock
scripts/librarian-oplog-lock-20260414-V1.0.sh unlock
```

**Audit integration.** `AuditReport.oplog_locked` + `AuditReport.oplog_path`
fields populated automatically. `format_report` adds a one-line status
(silent when undetectable). `audit --json` includes both fields.
`report.clean` is **deliberately unaffected** — advisory, like folder
suggestions and overdue reviews. Preserves the existing exit-code contract
for CI automation.

**Audit page.** New "Oplog Lock" KPI card (✓ locked / ✗ unlocked /
– undetectable) and two new CLI quick-cards on `audit.html`.

### Pre-commit framework integration (Phase 7.7)

Python projects that already use the [pre-commit framework](https://pre-commit.com)
can now install librarian's naming convention with a 3-line addition to
their `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/ghengis5-git/librarian
    rev: v0.7.4
    hooks:
      - id: librarian-naming
      # or, to treat warnings as errors:
      # - id: librarian-naming-strict
```

Then install the hook:

```bash
pre-commit install
```

The new `librarian-precommit` entry point walks up from each staged file
to find the nearest `docs/REGISTRY.yaml`, reads `project_config.naming_rules`
and `tracked_dirs`, skips infrastructure-exempt files, and validates
filenames via `librarian.naming.validate`.

**Relationship to the existing shell hook.** The bash hook at
`scripts/librarian-pre-commit-hook-20260411-V1.0.sh` keeps working as-is
for direct git pre-commit symlink installs. The new Python entry point is
for pre-commit-framework installs. Both share the same rules via
`librarian.naming` so behavior is consistent.

**Why Python, not a wrapper around the shell script?**
- Runs on Windows (shell hook's bash-isms don't).
- Reuses `librarian.naming.validate` directly — no double-maintenance of
  the naming logic.
- Pre-commit framework's file-passing model is a better fit for a Python
  entry point than for a shell script that does its own `git diff`.

## What changed (by file)

**Phase 7.5 — Oplog append-only:**

- `librarian/oplog_lock.py` — new module; `is_append_only`,
  `platform_support`, `lock_instructions`, `unlock_instructions`.
- `librarian/audit.py` — `AuditReport.oplog_locked` + `.oplog_path`
  fields; `format_report` status line; populated in `audit()`.
- `librarian/__main__.py` — new `librarian oplog status` subcommand.
- `librarian/sitegen.py` — "Oplog Lock" KPI card, two new CLI quick-cards.
- `scripts/librarian-oplog-lock-20260414-V1.0.sh` — setup helper.

**Phase 7.7 — Pre-commit framework integration:**

- `librarian/precommit.py` — new module; `main()` entry point.
- `.pre-commit-hooks.yaml` — new file at repo root; two hook entries
  (`librarian-naming`, `librarian-naming-strict`).
- `pyproject.toml` — new `[project.scripts]` entry:
  `librarian-precommit = "librarian.precommit:main"`

## Test suite

**743 → 796 tests, all passing.**

- `tests/test_oplog_lock.py` — new, 30 tests (platform dispatch 6,
  macOS stat-flag parsing 5, Linux lsattr parsing 7, instruction strings 5,
  audit integration 5).
- `tests/test_precommit.py` — new, 22 tests (registry walk-up 4, config
  loader 4, scope filtering 6, end-to-end CLI 8).
- `tests/test_sitegen.py` — +2 updated for Phase 7.5 KPI + CLI cards.

## Install

```bash
# As a CLI tool
pip install --upgrade librarian-2026

# As a Claude Code / Cowork plugin
claude plugins marketplace add ghengis5-git/librarian
claude plugins install librarian@librarian-marketplace

# As a pre-commit hook (new in v0.7.4 — see .pre-commit-config.yaml
# snippet above)
pre-commit install
```

## Known Issues

Unchanged from v0.7.3:

- `ghengis5@gmail.com` still appears in the public git log on the Session 48
  `marketplace.json` add-commit. Cleaning the blob requires
  `git filter-repo --replace-text` + force-push; explicitly deferred in
  Session 51.
- Oplog append-only flag only applies to the single file on the single
  machine — doesn't protect against filesystem-level tampering (e.g.,
  editing the raw block device, or restoring from a backup).

## Upgrade guidance

- **From v0.7.3:** `pip install --upgrade librarian-2026`. No migration
  steps, no registry changes.
- **Enabling oplog lock:** run
  `scripts/librarian-oplog-lock-20260414-V1.0.sh lock` after updating.
  Already-generated evidence packs remain valid.
- **Adopting pre-commit:** add the `.pre-commit-config.yaml` snippet above
  to any project that wants librarian naming enforcement without relying
  on Claude Code. Existing Claude Code hook installations remain valid
  and are unaffected.

## Credits

Built solo by Chris Kahn. Phase 7.5 and Phase 7.7 shipped in Cowork
Session 51 alongside v0.7.3.
