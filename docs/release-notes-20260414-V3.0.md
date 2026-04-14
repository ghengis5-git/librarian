# Release Notes — v0.7.3

**Date:** 2026-04-14
**Version:** V3.0
**Status:** Draft

## Overview

Feature + fix release. Adds optional per-document review deadlines with a new
`review` CLI subcommand and an Audit-page KPI card. Hardens the pre-commit
hook's registry-sync grep against two latent false-positive cases.

Backwards compatible — no schema migrations, no registry edits required to
upgrade. Existing registries continue to load and audit cleanly.

- **GitHub:** https://github.com/ghengis5-git/librarian
- **PyPI:** https://pypi.org/project/librarian-2026/0.7.3/
- **Plugin:** `claude plugins marketplace add ghengis5-git/librarian`
- **License:** Apache 2.0

## What's new

### `next_review` field + `review` CLI subcommand

Documents can now carry an optional review deadline. Past deadlines surface
as a warning in `audit` output and as a new KPI card on the Audit page of the
generated site. Useful for compliance-heavy presets — HIPAA SOPs, SOC 2
policies, regulatory filings — where stale documents are a finding.

```bash
# Set deadlines at creation time
librarian register docs/sop-20260414-V1.0.md --review-by 2027-04-14
librarian scaffold --template policy-document --review-by 2027-04-14

# Carry or change deadlines across version bumps
librarian bump sop-20260414-V1.0.md                       # inherits
librarian bump sop-20260414-V1.0.md --review-by 2028-01-01  # override
librarian bump sop-20260414-V1.0.md --clear-review           # drop

# Dedicated subcommand for existing docs
librarian review set sop-20260414-V1.0.md --by 2027-04-14
librarian review clear sop-20260414-V1.0.md
librarian review list                       # all with deadlines
librarian review list --overdue             # past-due only
librarian review list --upcoming --within-days 90
```

**Design decisions locked in for this release:**

- Absolute ISO 8601 dates only (`YYYY-MM-DD`). Relative forms (`+6mo`) can layer
  on later without breaking the stored format.
- Explicit-only. Presets do not auto-apply default cadences — whatever the user
  sets is what sticks. Predictable, no hidden behavior across presets.
- Superseded and archived documents are excluded from overdue calculations.
- Overdue findings are **warn** severity — they appear in audit output but do
  **not** flip `AuditReport.clean` or the `audit` exit code. This preserves
  the contract for existing CI automation that relies on `audit` returning 0
  for compliant repos.

### Audit page — "Overdue Reviews" KPI + findings table

- New KPI card on `audit.html` showing the overdue count (green when 0, amber
  when > 0).
- New section inside OODA findings listing each overdue doc with filename,
  deadline, and days-overdue.
- New CLI quick-card advertising `librarian review list --overdue`.

### Pre-commit hook registry-sync hardening

The hook's registry-sync check now escapes regex metacharacters in the staged
filename and anchors the match at end of line. Before the fix, two latent
false-positives were possible:

1. Literal dots in version suffixes (`V1.0.md`) were treated as regex
   wildcards. A staged `foo-V1.0.md` could false-positive match a registered
   `foo-V1x0xmd`.
2. A staged `foo.md` would substring-match a registered `foo.md.backup` or
   `old-foo.md`.

The fixed grep accepts both YAML entry forms (`- filename: x` list-item and
`  path: dir/x` indented) and pins the filename to end of line.

## What changed (by file)

- `librarian/review.py` — new module: `parse_review_date`, `format_review_date`,
  `compute_overdue`, `compute_upcoming`, `OverdueReview` dataclass,
  `ReviewDateError`.
- `librarian/audit.py` — `AuditReport.overdue_reviews` populated automatically;
  `format_report` emits an "Overdue reviews" section.
- `librarian/__main__.py` — `review` subcommand; `--review-by` on `register`,
  `bump`, `scaffold`; `--clear-review` on `bump`; `overdue_reviews` in
  `audit --json` output.
- `librarian/sitegen.py` — Audit page KPI card, OODA-section overdue table,
  new CLI quick-card.
- `scripts/librarian-pre-commit-hook-20260411-V1.0.sh` — hardened registry-sync
  grep (Phase 7.1).
- `schema/registry.schema.yaml` — documents the new `next_review` field.
- `skills/librarian/references/cli-reference.md` — full CLI docs updated.

## Test suite

**681 → 743 tests, all passing.**

- `tests/test_precommit_hook.py` — new, 11 tests (8 grep unit, 3 end-to-end).
- `tests/test_review.py` — new, 49 tests across 8 classes (date parsing,
  overdue/upcoming computation, audit integration, all CLI surfaces).
- `tests/test_sitegen.py` — +2 tests, +1 updated for the new KPI card and CLI
  quick-card.

## Install

```bash
# As a CLI tool
pip install --upgrade librarian-2026

# As a Claude Code / Cowork plugin
claude plugins marketplace add ghengis5-git/librarian
claude plugins install librarian@librarian-marketplace
```

## Known Issues

- `ghengis5@gmail.com` still appears in the public git log on the Session 48
  `marketplace.json` add-commit. Cleaning the blob requires
  `git filter-repo --replace-text` + force-push; deferred to Phase 7.4 unless
  traffic warrants.
- Oplog chain is detect-only (integrity verified at audit time, not at append
  time). Prevention-mode oplog requires a format change and is tracked as
  Phase 7.5.

## Upgrade guidance

- **From v0.7.2:** `pip install --upgrade librarian-2026`. No migration steps,
  no registry changes. Existing manifests, evidence packs, and generated sites
  remain valid. The `next_review` field is optional — your registry works
  unchanged.
- **First use of `review` CLI:** no REGISTRY.yaml mutation is needed. Run
  `librarian review set <doc> --by YYYY-MM-DD` on whichever documents you want
  to track.
- **Updating the pre-commit hook:** no action. The hook auto-updates via the
  symlink (`.git/hooks/pre-commit` → `scripts/librarian-pre-commit-hook-20260411-V1.0.sh`).

## Credits

Built solo by Chris Kahn. Phase 7.1 and Phase 7.2 shipped in Cowork Session 51.
