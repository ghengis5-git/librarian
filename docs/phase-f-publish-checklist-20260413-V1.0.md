# Phase F — Publish Checklist

**Date:** 2026-04-13
**Version:** V1.0
**Status:** Active
**Purpose:** Executable runbook for the host-terminal publish session. The Cowork sandbox cannot run `git`, `pytest`, or `rm` on tracked files, so the final publish must happen from `~/projects/librarian` in a host Claude Code conversation.

---

## Pre-flight

Run from `~/projects/librarian`:

```bash
cd ~/projects/librarian
source .venv/bin/activate
git status                          # expect clean tree after Session 47 edits are committed
python -m pytest tests/ -q          # expect 682/682
```

If anything fails, stop and investigate — do not proceed.

---

## F.a — Filesystem cleanup (sandbox couldn't remove these)

```bash
rm -rf dashboard/legacy
rm -rf skills/doc-librarian
rm -rf _site _site-* 2>/dev/null || true
```

Then re-run the former-project scrub to confirm zero regressions:

```bash
grep -riI 'prism' --exclude-dir=.venv --exclude-dir=.git --exclude-dir=__pycache__ \
  --exclude-dir=_site --exclude-dir='*.egg-info' . || echo "clean"
```

Expected: `clean`.

---

## F.a1 — Rewrite git history to the GitHub noreply address

**Why:** Prior commits in this repo carry real emails (`ghengis5@gmail.com`, one commit under `research+ai@brokenwire.org`) in the git author/committer fields. Those fields become public once pushed and are NOT hidden by GitHub's "Keep my email addresses private" setting, which only affects web UI actions. Rewriting before the first push is the only clean fix.

**Target email:** `272935920+ghengis5-git@users.noreply.github.com`

```bash
cd ~/projects/librarian

# Sanity: confirm we haven't pushed yet (remote should be empty or not yet set)
git remote -v
git log --format='%h %ae' | head -5   # see current author emails

# Rewrite every commit's author + committer to the noreply address
git filter-branch --env-filter '
  export GIT_AUTHOR_NAME="Chris Kahn"
  export GIT_AUTHOR_EMAIL="272935920+ghengis5-git@users.noreply.github.com"
  export GIT_COMMITTER_NAME="Chris Kahn"
  export GIT_COMMITTER_EMAIL="272935920+ghengis5-git@users.noreply.github.com"
' --tag-name-filter cat -- --all

# Re-sign all commits so the Verified badge sticks after rewrite
git rebase -r --root --exec 'git commit --amend --no-edit -S'

# Lock in noreply for all future commits in this repo
git config user.email "272935920+ghengis5-git@users.noreply.github.com"
git config user.name "Chris Kahn"

# Verify — every line should show the noreply address and a Good signature ('G')
git log --format='%h %ae %G?' | head -10
```

After this, clean up filter-branch refs:

```bash
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now
```

---

## F.b — Registry + manifest refresh

```bash
python -m librarian --registry docs/REGISTRY.yaml audit
python -m librarian --registry docs/REGISTRY.yaml manifest -o docs/librarian-manifest-$(date +%Y%m%d)-V1.0.json
python -m librarian --registry docs/REGISTRY.yaml evidence -o docs/librarian-evidence-$(date +%Y%m%d)-V1.0.json
```

Commit results:

```bash
git add docs/librarian-manifest-*.json docs/librarian-evidence-*.json docs/REGISTRY.yaml
git commit -S -m "docs: refresh manifest + evidence before publish"
# (repo-local config set in F.a1 means -c override no longer needed)
```

---

## F.c — Final sanity on publish-critical files

```bash
# Version consistency — all should say 0.7.1
grep '"version"' .claude-plugin/plugin.json marketplace.json
grep '__version__' librarian/__init__.py
grep '^version' pyproject.toml
grep 'version:' skills/librarian/SKILL.md | head -2

# Test count
grep '682 tests' README.md

# License + readme present
test -f LICENSE && test -f README.md && echo "present"
```

---

## F.d — GitHub repo creation

**Decision (Session 48): publish under `ghengis5-git/librarian`.** All repo metadata (plugin.json, marketplace.json, pyproject.toml, README install line) already points there. Move to an org later if the project attracts contributors.

**Pre-flight identity check** (do once before first push):
1. Sign in to github.com as `ghengis5`.
2. Settings → Emails → confirm both `ghengis5@gmail.com` and `research+ai@brokenwire.org` are verified.
3. If both are on the same account: commit `990e7d9` (currently authored as `research+ai@brokenwire.org`) will attribute correctly. No rewrite.
4. If `research+ai@brokenwire.org` is on a different account: `990e7d9` will show as a ghost author on the public repo. Cosmetic only. Optional one-shot fix before first push:
   ```bash
   git rebase -r --root --exec 'git commit --amend --no-edit \
     --author="Chris Kahn <ghengis5@gmail.com>"' HEAD
   ```

```bash
# Personal path (recommended):
gh repo create ghengis5-git/librarian --public --description "Document governance for projects with serious docs." \
  --source=. --remote=origin --push
```

If moving to a new org:
1. Update `.claude-plugin/plugin.json` `homepage` + `repository`
2. Update `marketplace.json` `plugins[0].source.repo`
3. Update `pyproject.toml` `[project.urls]` block
4. Update `README.md` `claude plugins add ghengis5-git/librarian` line

---

## F.e — First public push

```bash
# Assumes gh repo create --push above succeeded
git push -u origin main
git push origin --tags  # if any tags exist
gh release create v0.7.1 --title "Librarian v0.7.1" --notes "See docs/phase-f-plugin-and-release-20260413-V1.1.md for scope."
```

---

## F.f — PyPI publish

```bash
# Clean build artifacts from prior runs
rm -rf dist build *.egg-info
python -m pip install --upgrade build twine
python -m build

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*
# Verify in a fresh venv
python -m venv /tmp/lib-test && /tmp/lib-test/bin/pip install -i https://test.pypi.org/simple/ librarian-2026
/tmp/lib-test/bin/librarian --help

# Then production
python -m twine upload dist/*
```

Smoke-test the real install:

```bash
python -m venv /tmp/lib-prod && /tmp/lib-prod/bin/pip install librarian-2026
/tmp/lib-prod/bin/librarian init --preset minimal -o /tmp/test-reg.yaml --no-hook
cat /tmp/test-reg.yaml | head -20
```

---

## F.g — Marketplace submission

Two options for `marketplace.json`:

1. **Same repo** — the `marketplace.json` already sits at repo root. User installs via:
   ```bash
   claude plugins marketplace add ghengis5-git/librarian
   claude plugins add librarian@librarian-marketplace
   ```

2. **Dedicated marketplace repo** — create `ghengis5-git/librarian-marketplace` with just `marketplace.json` inside, if a multi-plugin marketplace grows.

For v1, **same-repo is correct**. Nothing to do.

---

## F.h — Announce + close Phase F

1. Tag the commit: `git tag -s v0.7.1-published -m "First public release"`.
2. Write `docs/release-notes-20260413-V1.0.md` (can use the `release-notes` template: `librarian scaffold --template release-notes --title "v0.7.1 first public release"`).
3. Update CLAUDE.md: mark Phase F complete, bump "Next Steps" priority list.
4. Move `phase-f-plugin-and-release-20260413-V1.1.md` and `phase-f-publish-checklist-20260413-V1.0.md` to `status: superseded` in the registry.
5. Open a Phase H (or next) plan for the remaining "Next Steps" items: review scheduling, pre-commit hook registry-sync bug, oplog prevention-mode (requires format approval).

---

## Rollback

If PyPI upload has a defect:

```bash
# PyPI does NOT allow re-uploading the same version — bump to 0.7.2 first
# Edit pyproject.toml + librarian/__init__.py + .claude-plugin/plugin.json + marketplace.json + skills/librarian/SKILL.md
# Then rebuild and re-upload
```

If the GitHub repo needs to come down:

```bash
gh repo delete ghengis5-git/librarian --yes   # nuclear, destructive — confirm with user first
```

Prefer `gh repo archive` to soft-delete.

---

## Appendix — Blocker resolution summary (from Session 47)

| Blocker | Resolution |
|---------|-----------|
| PyPI namespace | Keep `librarian-2026` (already in `pyproject.toml`) |
| Git history | Keep full — 21 commits all conventional-prefix, publication-quality |
| Hook default | Middle option shipped — disabled globally, project-gated via `enforce_naming_hook` |
| IP clearance | No patents on librarian — not a blocker |
| GitHub owner | **OPEN** — recommendation above is `ghengis5` personal for v1 |
