# Release Notes — v0.7.5

**Date:** 2026-04-14
**Version:** V5.0
**Status:** Draft

## Overview

**Security patch release.** Bundles Phase 8.0 adversarial-review hardening
and Phase 8.1 polish. No breaking changes, no schema migrations, no
registry edits required.

**Recommended for all users on v0.7.4 or earlier.** One of the fixes
(shell-injection in oplog-lock instruction strings) is reachable through
the `librarian oplog status` CLI path if the repo directory contains
shell-metacharacters (`;`, `$()`, backticks, etc.). The risk is
social-engineering — the CLI prints a "copy-paste this command" string
that the shell could mis-parse — rather than direct code execution.
Still worth fast-patching.

- **GitHub:** https://github.com/ghengis5-git/librarian
- **PyPI:** https://pypi.org/project/librarian-2026/0.7.5/
- **Plugin:** `claude plugins marketplace add ghengis5-git/librarian`
- **License:** Apache 2.0

## What's in it

### Phase 8.0 — Adversarial-review hardening (9 findings)

Nine findings from a targeted adversarial review of the Phase 7.5 + 7.7
code that shipped in v0.7.4. All addressed in this release.

#### CRITICAL

- **Shell-quoting in `oplog_lock.lock_instructions` / `unlock_instructions`.**
  Prior versions interpolated paths directly into shell command strings
  (`f"chflags uappend {p}"`). A path containing `;`, `$(...)`, or
  backticks produced a copy-pasteable shell-injection vector — the CLI
  output looked like a single command but parsed as multiple. Fixed by
  wrapping the path in `shlex.quote()` at construction time. The single
  place the output is rendered (`librarian oplog status` stdout, and
  eventual audit-page copy-to-clipboard cards) now receives an
  always-safely-quoted string.

#### HIGH

- **Symlink traversal in `precommit._should_check`.** A symlink inside
  a tracked directory pointing outside the repo (e.g.,
  `docs/good-V1.0.md -> /etc/passwd`) would resolve out of `repo_root`,
  raise `ValueError` on `relative_to`, and be silently skipped from the
  naming check — even though the on-disk filename itself matched the
  governed-extension filter. Fixed by switching to a symlink-safe
  containment check: resolve the *parent* directory only (trusted, handles
  macOS `/var → /private/var`) and rebind the leaf name. The on-disk name
  is always validated, regardless of what the symlink points to.

- **`_find_registry` filesystem-root fallback removed.** The walk-up
  previously probed `/docs/REGISTRY.yaml` as a last resort. On systems
  where that path happens to exist (some container images, certain unix
  setups), the function would return it, set `repo_root = /`, and pull
  every file on the filesystem into the naming-check scope. Fallback
  removed; no root probe.

- **Shell-script stat failure no longer reports false "unlocked".**
  In `librarian-oplog-lock-20260414-V1.0.sh`, the macOS `is_locked()`
  check used `stat ... || echo 0` and derived lock state from the
  returned flags integer. A failing `stat` (permission denied, syscall
  error) would yield `0` → `flags & 4 == 0` → "unlocked" (a false
  all-clear). Now distinguishes stat-failure from stat-success-with-zero,
  and reports "unknown" on failure — consistent with the existing
  Linux-side handling.

#### MEDIUM

- **TOCTOU pre-check removed in `is_append_only`.** Dropped the
  up-front `p.exists()` check that opened a race window before the
  `os.stat()` / `subprocess.run(lsattr)` call. Missing-file detection
  now comes from the probe itself — `FileNotFoundError` on macOS,
  non-zero `lsattr` exit on Linux — and both paths still return `None`
  per the existing contract. No behavioral change for callers.

- **`_get_exempt()` helper extracted** from two near-identical inline
  blocks in `precommit._should_check` and `precommit._check_file`. Single
  source of truth for `infrastructure_exempt` parsing.

- **Empty-argv note.** `librarian-precommit` with no positional args
  now prints `"Librarian naming check — no files to check"` to stdout
  (exit code still `0`). Distinguishes legitimate framework-triggered
  "nothing to check" from CLI misconfiguration.

- **`LIBRARIAN_DEBUG=1` surfaces lsattr stderr.** Failed `lsattr` calls
  on Linux now emit the captured stderr to our stderr when the env var
  is set. Default behavior unchanged (silent).

#### LOW

- **Simplified `uname -s`** in the oplog-lock shell script. Dropped the
  `2>/dev/null || echo unknown` fallback — `uname` is POSIX-guaranteed;
  if it ever fails, we want the failure to surface rather than be
  relabeled.

### Phase 8.1 — Polish sweep

- **`sitegen.py` raw f-string.** The HTML/JS page generator at line 2154
  embeds JavaScript regex literals (`\d`, `\s`, `\.`) inside a
  triple-quoted f-string, producing `DeprecationWarning` on Python 3.11+
  (and `SyntaxWarning` on 3.12+). Converted to `rf"""..."""` — raw
  string passes backslashes through to the rendered output while
  preserving `{expression}` substitution and `{{`/`}}` literal-brace
  escapes.

- **Extended `infrastructure_exempt`.** The librarian's own registry
  now exempts `.pre-commit-hooks.yaml` and `cli-reference.md` from the
  naming convention (those are framework-dictated filenames, like
  `README.md` or `.gitignore`).

- **New `audit_config.folder_threshold` config knob.** The audit's
  folder-density check previously hard-coded a 15-documents-per-folder
  threshold. Projects with intentional self-documentation density (the
  librarian itself is one — 21 docs in `docs/`) can now override via
  `project_config.audit_config.folder_threshold: N` in their registry.
  Default remains 15 for all other projects.

## What changed (by file)

**Phase 8.0:**

- `librarian/oplog_lock.py` — `shlex.quote` in instruction strings;
  `p.exists()` pre-check removed; `LIBRARIAN_DEBUG` stderr surfacing.
- `librarian/precommit.py` — symlink-safe containment; filesystem-root
  fallback removed; `_get_exempt()` helper extracted; empty-argv note.
- `scripts/librarian-oplog-lock-20260414-V1.0.sh` — stat-failure
  distinguishes from stat-success-zero; `uname -s` simplified.

**Phase 8.1:**

- `librarian/sitegen.py` — raw f-string at the main page-shell builder.
- `librarian/__main__.py` — reads `audit_config.folder_threshold` from
  project_config and passes to `audit()`.
- `docs/REGISTRY.yaml` — `audit_config.folder_threshold: 30` override
  for the librarian's own audit; two new infrastructure-exempt entries.

**Test suite:**

- `tests/test_oplog_lock.py` — +9 regression tests (shell-quoting 4,
  TOCTOU 2, debug-stderr 3).
- `tests/test_precommit.py` — +9 regression tests (symlink 2, root
  fallback 2, `_get_exempt` 4, empty-argv 1).

## Test suite

**796 → 814 tests, all passing.**

## Install

```bash
# As a CLI tool
pip install --upgrade librarian-2026

# As a Claude Code / Cowork plugin
claude plugins marketplace update librarian-marketplace
# (or claude plugins install librarian@librarian-marketplace for first-time)

# As a pre-commit hook
pre-commit autoupdate  # bumps the rev to v0.7.5
```

## Known Issues

Unchanged from v0.7.4:

- `ghengis5@gmail.com` still appears in the public git log on the
  Session 48 `marketplace.json` add-commit. Cleaning the blob requires
  `git filter-repo --replace-text` + force-push; explicitly deferred in
  Session 51.
- Oplog append-only flag only applies to the single file on the single
  machine — doesn't protect against filesystem-level tampering
  (editing the raw block device, or restoring from a backup).

## Upgrade guidance

- **From v0.7.4:** `pip install --upgrade librarian-2026`. No migration
  steps, no registry changes.
- **If you subclass or call `lock_instructions` / `unlock_instructions`
  directly:** the returned string is now shell-quoted. If you were
  previously splitting it on whitespace assuming an unquoted path, update
  to use `shlex.split()` instead. Most callers just pipe the string
  verbatim to a shell and will be unaffected.
- **Pre-commit framework users:** bump the `rev:` in your
  `.pre-commit-config.yaml` to `v0.7.5`, or run `pre-commit autoupdate`.

## Credits

Built solo by Chris Kahn. Phase 8.0 + 8.1 shipped in Cowork Session 52
alongside v0.7.5.
