# Release Notes — v0.7.2

**Date:** 2026-04-13
**Version:** V2.0
**Status:** Draft

## Overview

Patch release. Ships the Session 49 plugin-install fixes to any user who
`pip install`-ed or `claude plugins install`-ed Librarian during the brief
post-publish window when the marketplace path was broken.

No feature changes. No API changes. No template changes. No test-count changes.
If v0.7.1 installs and runs cleanly for you, you do not need v0.7.2.

- **GitHub:** https://github.com/ghengis5-git/librarian
- **PyPI:** https://pypi.org/project/librarian-2026/0.7.2/
- **Plugin:** `claude plugins marketplace add ghengis5-git/librarian`
- **License:** Apache 2.0

## What changed

The following fixes landed on `main` in Session 49 and are now formally tagged
and re-shipped so first-time installers get them:

- **Marketplace manifest path** — `marketplace.json` moved from the repo root
  to `.claude-plugin/marketplace.json`, where the Claude Code plugin loader
  actually looks. Users on v0.7.1 who tried `claude plugins marketplace add
  ghengis5-git/librarian` got a "no manifest" error; v0.7.2 resolves cleanly.
- **Hooks schema** — `hooks/hooks.json` now ships an empty `"hooks": {}` record
  (schema-valid, truly disabled). The naming-enforcement hook moved to
  `hooks/hooks.enabled.example.json`; users opt in by copying the example over
  the primary file and restarting Claude Code. The old `_PreToolUse` underscore
  trick failed the validator.
- **Marketplace owner email** — scrubbed a stray `ghengis5@gmail.com` from the
  `owner.email` field in `marketplace.json`; replaced with the GitHub noreply
  address. (The email still exists in the public git history on the Session 48
  add-commit; see the Known Issues list below.)
- **Release notes** — this document, so the v0.7.1 release notes don't have to
  carry v0.7.2 bullets.

No changes to:

- CLI commands, flags, or output format
- Manifest seal algorithm, oplog format, or evidence pack schema
- Templates, presets, naming conventions, or recommendations engine
- Test suite (681/681 still passing on main — v0.7.2 does not add or remove
  any test)

## Install

```bash
# As a CLI tool
pip install --upgrade librarian-2026

# As a Claude Code / Cowork plugin
claude plugins marketplace add ghengis5-git/librarian
claude plugins install librarian@librarian-marketplace
```

If you installed v0.7.1 via the plugin marketplace and hit the manifest error,
remove the broken entry first:

```bash
claude plugins marketplace remove librarian-marketplace
claude plugins marketplace add ghengis5-git/librarian
claude plugins install librarian@librarian-marketplace
```

## Known Issues

Unchanged from v0.7.1:

- Oplog chain is detect-only (integrity verified at audit time, not at append
  time). Prevention-mode oplog requires a format change and is tracked as
  Phase 7.5.
- Pre-commit hook greps for full filepath but registry stores filename only —
  emits harmless "not found" warnings on every governed-doc commit. Tracked as
  Phase 7.1.

New to v0.7.2:

- `ghengis5@gmail.com` still appears in the public git log on the Session 48
  `marketplace.json` add-commit. Cleaning the blob requires `git filter-repo
  --replace-text` + force-push; deferred to Phase 7.4 unless traffic warrants.

## Upgrade guidance

- **From v0.7.1:** `pip install --upgrade librarian-2026`. No migration steps,
  no registry changes, no template invalidation. Existing manifests, evidence
  packs, and generated sites remain valid.
- **Fresh install:** follow the Install section above.

## Credits

Built solo by Chris Kahn. Session 49 fixes discovered via live smoke-test with
the Cowork team's plugin loader.
