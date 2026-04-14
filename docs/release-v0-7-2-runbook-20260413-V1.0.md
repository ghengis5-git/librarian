# Release Runbook — v0.7.2

**Date:** 2026-04-13
**Version:** V1.0
**Status:** Draft
**Target release:** v0.7.2 (patch — ships Session 49 install-path fixes)
**Executor:** Host terminal at `~/projects/librarian` (Cowork sandbox cannot git/build/upload)

---

## 0. Pre-flight context

What's already done in Cowork Session 50 (on `main`, uncommitted):

- `librarian/__init__.py` — `__version__ = "0.7.2"`
- `pyproject.toml` — `version = "0.7.2"`
- `.claude-plugin/plugin.json` — `"version": "0.7.2"`
- `.claude-plugin/marketplace.json` — `"version": "0.7.2"`
- `skills/librarian/SKILL.md` — frontmatter `metadata.version: "0.7.2"`
- `docs/release-notes-20260413-V2.0.md` — new v0.7.2 release notes (draft in registry)
- `docs/REGISTRY.yaml` — v0.7.1 notes promoted to active, v0.7.2 notes added as draft, totals 25→26 / active 17→18
- `CLAUDE.md` — Session 50 deliverables block added, Current State and Phase 7.3 bullet updated
- `docs/release-v0-7-2-runbook-20260413-V1.0.md` — this file

No git commits yet. No tags. No builds. No uploads. Nothing destructive.

---

## 1. Sanity check (host terminal)

```bash
cd ~/projects/librarian
source .venv/bin/activate
```

Confirm you're on `main` with a clean working tree except for the Session 50 edits:

```bash
git status
git branch --show-current
```

Expected: branch `main`, 7 modified files + 2 new files (release notes V2.0, runbook).

Run the full test suite — sandbox couldn't:

```bash
pytest -q
```

**Gate:** must print `681 passed`. If not, stop and investigate before tagging.

Sanity-check every version string landed:

```bash
grep -n '"0\.7\.2"\|^version = "0\.7\.2"\|__version__ = "0\.7\.2"' \
  librarian/__init__.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md
```

**Gate:** must return 5 matches (one per file). Zero v0.7.1 leftovers in those 5 files:

```bash
grep -n '0\.7\.1' \
  librarian/__init__.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md
```

**Gate:** must return nothing. (Historical refs in `CLAUDE.md`, old release notes, and session-history docs are expected and fine.)

Run the librarian's own audit on itself:

```bash
python -m librarian --registry docs/REGISTRY.yaml audit
```

**Gate:** 0 naming violations, 0 pending cross-refs, 0 missing files.

---

## 2. Commit the bump

Single commit, all 9 files:

```bash
git add \
  librarian/__init__.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md \
  docs/release-notes-20260413-V2.0.md \
  docs/release-v0-7-2-runbook-20260413-V1.0.md \
  docs/REGISTRY.yaml \
  CLAUDE.md

git commit -S -m "release: v0.7.2 — ship Session 49 install-path fixes

Pure re-release of main. No code changes. No test changes.
Bumps version strings in all 5 manifests, adds v0.7.2 release
notes, promotes v0.7.1 release notes from draft to active."
```

**Gate:** commit shows `gpg: Good signature` or the SSH-signed equivalent in
`git log --show-signature -1`. If signing fails, do not proceed — check
`~/.ssh/id_ed25519` and `git config user.signingkey`.

---

## 3. Tag

```bash
git tag -s v0.7.2 -m "Librarian v0.7.2 — patch release (plugin install-path fixes)"
git tag --list v0.7.2
git show v0.7.2 --stat | head -5
```

**Gate:** `git tag --verify v0.7.2` reports a good signature.

---

## 4. Build

Clean old artifacts and build fresh:

```bash
rm -rf dist/ build/ librarian_2026.egg-info/
python -m build
ls -lh dist/
```

Expected output: two files, `librarian_2026-0.7.2-py3-none-any.whl` and
`librarian_2026-0.7.2.tar.gz`, both in the 300–320 KB range.

**Gate:** twine's metadata check must pass:

```bash
twine check dist/*
```

---

## 5. TestPyPI dry-run

Always push to TestPyPI before PyPI — catches metadata typos before they
become permanent on the real index.

```bash
twine upload --repository testpypi dist/*
```

Verify the listing appears at https://test.pypi.org/project/librarian-2026/0.7.2/
and that `pip install --index-url https://test.pypi.org/simple/ librarian-2026==0.7.2`
works in a throwaway venv:

```bash
python -m venv /tmp/librarian-testpypi-check
source /tmp/librarian-testpypi-check/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  librarian-2026==0.7.2
python -c "import librarian; print(librarian.__version__)"
deactivate
rm -rf /tmp/librarian-testpypi-check
cd ~/projects/librarian
source .venv/bin/activate
```

**Gate:** the print must read `0.7.2`.

---

## 6. PyPI upload

```bash
twine upload dist/*
```

Verify at https://pypi.org/project/librarian-2026/0.7.2/ — description,
keywords, classifiers, license, author all correct.

**Gate:** a fresh install pulls v0.7.2 by default:

```bash
python -m venv /tmp/librarian-pypi-check
source /tmp/librarian-pypi-check/bin/activate
pip install librarian-2026
python -c "import librarian; print(librarian.__version__)"  # → 0.7.2
deactivate
rm -rf /tmp/librarian-pypi-check
cd ~/projects/librarian
source .venv/bin/activate
```

---

## 7. Push to GitHub

```bash
git push origin main
git push origin v0.7.2
```

**Gate:** both show up in the refs at https://github.com/ghengis5-git/librarian

---

## 8. GitHub release

Use the V2.0 release notes as the release body:

```bash
gh release create v0.7.2 \
  --title "Librarian v0.7.2 — patch release (plugin install-path fixes)" \
  --notes-file docs/release-notes-20260413-V2.0.md \
  dist/librarian_2026-0.7.2-py3-none-any.whl \
  dist/librarian_2026-0.7.2.tar.gz
```

Verify at https://github.com/ghengis5-git/librarian/releases/tag/v0.7.2

---

## 9. Marketplace refresh

The same `.claude-plugin/marketplace.json` that's now on `main` is what the
Claude Code plugin loader reads on every `marketplace update`. No separate
marketplace-repo step needed (we use the same-repo distribution path).

End-user refresh:

```bash
claude plugins marketplace update librarian-marketplace
claude plugins install librarian@librarian-marketplace   # auto-upgrades to 0.7.2
claude plugins list
```

**Gate:** `claude plugins list` shows `librarian@librarian-marketplace 0.7.2 ✔ enabled`.

For anyone stuck on the v0.7.1 broken-marketplace path, the fresh-install
recipe in the release notes works:

```bash
claude plugins marketplace remove librarian-marketplace
claude plugins marketplace add ghengis5-git/librarian
claude plugins install librarian@librarian-marketplace
```

---

## 10. Post-release cleanup

Promote the v0.7.2 release notes from draft → active in the registry:

```bash
python -m librarian --registry docs/REGISTRY.yaml bump \
  release-notes-20260413-V2.0.md --status active
```

Or edit `docs/REGISTRY.yaml` directly:

```yaml
- filename: release-notes-20260413-V2.0.md
  ...
  status: active    # was: draft
```

Regenerate the manifest + evidence pack so the v0.7.2 artifacts are
tamper-evidenced:

```bash
python -m librarian --registry docs/REGISTRY.yaml manifest \
  -o docs/librarian-manifest-20260413.json
python -m librarian --registry docs/REGISTRY.yaml evidence \
  -o docs/librarian-evidence-20260413.json
```

Commit the post-release state:

```bash
git add docs/REGISTRY.yaml docs/librarian-manifest-20260413.json docs/librarian-evidence-20260413.json
git commit -S -m "registry: activate v0.7.2 release notes + refresh manifest/evidence"
git push origin main
```

---

## 11. Announce (optional, deferrable)

If you're doing a public post for v0.7.2 — HN, r/programming, the Claude Code
community — the Phase 7.6 task covers it. For a patch release that's mostly
a plumbing fix, probably not worth a launch post on its own; bundle it with
Phase 7.1/7.2 work when those ship as v0.7.3.

---

## Rollback

If any step 1–9 fails:

- **Before `git push`:** `git reset --hard HEAD~1; git tag -d v0.7.2`.
  Nothing public happened.
- **After `git push` but before PyPI:** `git push origin :v0.7.2` deletes the
  remote tag; then reset locally and force-push main. Still recoverable.
- **After PyPI upload:** **you cannot delete a PyPI release**, only yank it
  via `pip install` (yank hides it from resolver but keeps it installable by
  exact version). The only forward path is v0.7.3. Don't panic — v0.7.2 ships
  only a versioned re-release of main, so the worst case is "broken patch
  release exists, fix in next patch."
- **After marketplace refresh:** the marketplace is just `marketplace.json`
  in git — revert the file, push, and end-users get the rolled-back version
  on next `marketplace update`.

## Success criteria

All green:

- [ ] `pytest -q` → 681 passed
- [ ] `librarian audit` → 0 violations
- [ ] `git tag --verify v0.7.2` → good signature
- [ ] `twine check dist/*` → PASSED
- [ ] TestPyPI install → `0.7.2`
- [ ] PyPI install → `0.7.2`
- [ ] `gh release create` → release page live
- [ ] `claude plugins list` → `librarian 0.7.2 ✔ enabled`
- [ ] CLAUDE.md and registry reflect the shipped state
