# Release Runbook — v0.7.3

**Date:** 2026-04-14
**Version:** V1.0
**Status:** Draft
**Target release:** v0.7.3 (feature + fix — Phase 7.1 hook hardening + Phase 7.2 review deadlines)
**Executor:** Host terminal at `~/projects/librarian` (Cowork sandbox cannot git/build/upload)

---

## 0. Pre-flight context

What's already done in Cowork Session 51 (on `main`, uncommitted):

- `librarian/__init__.py` — `__version__ = "0.7.3"`
- `pyproject.toml` — `version = "0.7.3"`
- `.claude-plugin/plugin.json` — `"version": "0.7.3"`
- `.claude-plugin/marketplace.json` — `"version": "0.7.3"`
- `skills/librarian/SKILL.md` — frontmatter `metadata.version: "0.7.3"`
- `docs/release-notes-20260414-V3.0.md` — new v0.7.3 release notes (draft in registry)
- `docs/REGISTRY.yaml` — v0.7.2 notes + runbook promoted to `active`, v0.7.3 notes added as `draft`, old 2026-04-13 manifest + evidence marked superseded, new 2026-04-14 manifest + evidence registered, totals 28→30 / active 20 / draft 3 / superseded 5→7, `last_updated: 2026-04-14`
- `docs/librarian-manifest-20260414-V1.0.json` — fresh manifest seal (28 registered / 28 hashed / 15 edges)
- `docs/librarian-evidence-20260414-V1.0.json` — fresh evidence pack, SSH-signed (parent commit `4283c437`, DIRTY — expected pre-tag)
- `docs/librarian-manifest-20260414.json` — unversioned "latest" copy
- `docs/librarian-evidence-20260414.json` — unversioned "latest" copy
- `docs/librarian-manifest-20260413.json` — removed (replaced by 0414 version)
- `docs/librarian-evidence-20260413.json` — removed (replaced by 0414 version)
- `docs/release-v0-7-3-runbook-20260414-V1.0.md` — this file

**On main, already committed and pushed:**
- `425180e` — Phase 7.1 hook hardening
- `c92875a` — Phase 7.2 next_review + review CLI + Audit KPI
- `4283c43` — Session 51 docs update (CLAUDE.md + README.md)

No further git commits, tags, builds, or uploads have been made. Nothing destructive has happened.

---

## 1. Sanity check the working tree

```bash
cd ~/projects/librarian
source .venv/bin/activate

git status --short
# Expected — all Cowork-staged, not yet committed:
#  M .claude-plugin/marketplace.json
#  M .claude-plugin/plugin.json
#  M docs/REGISTRY.yaml
#  D docs/librarian-evidence-20260413.json
#  M docs/librarian-manifest-20260413-V1.0.json   (may show as unchanged if timestamps match)
#  D docs/librarian-manifest-20260413.json
#  A docs/librarian-evidence-20260414-V1.0.json
#  A docs/librarian-evidence-20260414.json
#  A docs/librarian-manifest-20260414-V1.0.json
#  A docs/librarian-manifest-20260414.json
#  A docs/release-notes-20260414-V3.0.md
#  A docs/release-v0-7-3-runbook-20260414-V1.0.md
#  M librarian/__init__.py
#  M pyproject.toml
#  M skills/librarian/SKILL.md

pytest -q
# Expected: 743 passed
```

If pytest fails, stop and investigate. Do not proceed to tag.

---

## 2. Confirm no v0.7.3 work is missing from main

```bash
git log --oneline v0.7.2..HEAD
# Expected (3 commits, oldest-to-newest reading bottom-up):
#   4283c43 docs: Session 51 deliverables — Phase 7.1 + 7.2 on main unreleased
#   c92875a feat: next_review field + review CLI + Audit page KPI (Phase 7.2)
#   425180e fix: harden pre-commit hook registry-sync grep (Phase 7.1)
```

These three commits are what v0.7.3 ships (plus the bump commit you're about to make).

---

## 3. Commit the version bumps + release notes + runbook + refreshed artifacts

```bash
git add \
  librarian/__init__.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md \
  docs/release-notes-20260414-V3.0.md \
  docs/release-v0-7-3-runbook-20260414-V1.0.md \
  docs/REGISTRY.yaml \
  docs/librarian-manifest-20260414-V1.0.json \
  docs/librarian-manifest-20260414.json \
  docs/librarian-evidence-20260414-V1.0.json \
  docs/librarian-evidence-20260414.json

# The two deletions still need to be explicitly staged:
git rm docs/librarian-manifest-20260413.json docs/librarian-evidence-20260413.json

git status --short
# Every line should start with a staged indicator. The 2026-04-13 V1.0
# files MAY show as modified — that's the `updated:` field bump in their
# registry entries; commit it.
# (If docs/librarian-manifest-20260413-V1.0.json or the evidence pair show
#  as modified, stage those too — they get `updated: 2026-04-14` edits
#  from the registry supersede step.)

git commit -m "release: v0.7.3 — Phase 7.1 hook hardening + Phase 7.2 review deadlines"
```

Pre-commit hook will run naming + registry-sync + shell lint checks. Expected: all pass.

If the hook fails on a governed-doc filename or registry-sync lookup, **investigate** — do not `--no-verify` bypass. One legit exception: the pre-commit hook may warn on the unversioned `librarian-manifest-20260414.json` / `librarian-evidence-20260414.json` copies (same behaviour as v0.7.2 publish); those are intentionally unregistered.

---

## 4. Tag the release

```bash
git tag -s v0.7.3 -m "v0.7.3 — Phase 7.1 hook hardening + Phase 7.2 review deadlines"
git tag --list | grep 0.7
# Expected: v0.7.1, v0.7.1-published, v0.7.2, v0.7.3
```

SSH-sign the tag (`-s` uses your configured SSH signing key). If `-s` errors, verify:
```bash
git config --get gpg.format              # ssh
git config --get user.signingkey         # ~/.ssh/id_ed25519 (or path)
```

---

## 5. Build sdist + wheel

```bash
# Clean previous build artifacts so we don't upload stale wheels
rm -rf dist/ build/ *.egg-info

python -m build
# Expected: dist/librarian_2026-0.7.3-py3-none-any.whl + dist/librarian_2026-0.7.3.tar.gz
ls -la dist/
```

If `python -m build` is missing:
```bash
pip install --upgrade build
```

---

## 6. TestPyPI dry-run (optional but recommended)

```bash
python -m twine check dist/*
# Expected: both files PASSED

python -m twine upload --repository testpypi dist/*
# Enter TestPyPI API token (prefix "pypi-" — same as last time)

# Verify it appears
curl -s https://test.pypi.org/pypi/librarian-2026/json | python -c "import json,sys; d=json.load(sys.stdin); print(d['info']['version'])"
# Expected: 0.7.3
```

If TestPyPI upload fails with a file-exists error, the package was already uploaded to TestPyPI under this version — skip.

---

## 7. Real PyPI upload

```bash
python -m twine upload dist/*
# Enter PyPI API token (prefix "pypi-")
```

Verify:
```bash
curl -s https://pypi.org/pypi/librarian-2026/json | python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.7.3

pip index versions librarian-2026 2>&1 | head -3
# Expected: 0.7.3 in the "Available versions" line
```

---

## 8. Push commits + tag to GitHub

```bash
git push origin main
git push origin v0.7.3
```

---

## 9. GitHub release

```bash
gh release create v0.7.3 \
  --title "Librarian v0.7.3 — Review deadlines + hook hardening" \
  --notes-file docs/release-notes-20260414-V3.0.md \
  dist/librarian_2026-0.7.3.tar.gz \
  dist/librarian_2026-0.7.3-py3-none-any.whl
```

Verify:
```bash
gh release view v0.7.3
```

---

## 10. Plugin marketplace refresh

```bash
# If you have the plugin installed locally, refresh to pull v0.7.3
claude plugins update librarian@librarian-marketplace

# Or for a clean new install:
claude plugins marketplace refresh librarian-marketplace
claude plugins list | grep -A2 librarian
# Expected: version 0.7.3, enabled
```

---

## 11. Post-release smoke test

```bash
# Brand new venv — simulates a first-time user
python -m venv /tmp/lib-smoke
source /tmp/lib-smoke/bin/activate
pip install librarian-2026
python -c "import librarian; print(librarian.__version__)"
# Expected: 0.7.3

# Exercise the new review CLI
cd /tmp
mkdir lib-smoke-test && cd lib-smoke-test
python -m librarian init --preset minimal --no-hook
echo "# smoke" > docs/smoke-20260414-V1.0.md
python -m librarian register docs/smoke-20260414-V1.0.md --review-by 2027-01-01
python -m librarian review list
python -m librarian audit
# Expected: smoke-20260414-V1.0.md listed with next_review deadline

# Cleanup
deactivate
rm -rf /tmp/lib-smoke /tmp/lib-smoke-test
```

---

## 12. Post-release housekeeping (Cowork session)

In a new Cowork session, flip release-notes V3.0 status `draft` → `active` in the registry. That commit lives on its own so the release tag remains "notes in draft at time of tag" (mirrors how v0.7.1 and v0.7.2 were handled).

---

## Rollback (if something breaks mid-release)

- **Between commit and tag:** `git reset --soft HEAD~1` to unstage the bump commit; fix the issue; re-commit.
- **Between tag and PyPI upload:** `git tag -d v0.7.3 && git push origin :refs/tags/v0.7.3` to remove the tag (not yet uploaded); fix and retag.
- **After PyPI upload:** PyPI does NOT allow re-uploading a version. If v0.7.3 is broken on PyPI, you must publish v0.7.4 with the fix. DO NOT attempt to delete or re-upload.
- **After GitHub release:** `gh release delete v0.7.3` removes the release page; tag + PyPI entry persist.
- **After plugin marketplace refresh:** users who already pulled v0.7.3 will keep it; no remote rollback mechanism. Fix in v0.7.4.

---

## Definition of done

- [ ] `pytest -q` → 743 passed (all test files)
- [ ] `git tag --list` includes `v0.7.3`
- [ ] `pip index versions librarian-2026` shows 0.7.3 as latest
- [ ] `gh release view v0.7.3` shows the release page with both artifacts attached
- [ ] `claude plugins list` shows librarian @ 0.7.3 enabled
- [ ] Smoke-test venv: `pip install librarian-2026` pulls 0.7.3 and `review list` runs cleanly

Once all six are green, the release is done. Return to Cowork (or continue in host) to flip the registry-meta `release-notes-20260414-V3.0.md` status from `draft` to `active`, commit as `registry: activate v0.7.3 release notes`, and push.
