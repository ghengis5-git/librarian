# Release Runbook — v0.7.4

**Date:** 2026-04-14
**Version:** V1.0
**Status:** Draft
**Target release:** v0.7.4 (feature — Phase 7.5 oplog append-only detection + Phase 7.7 pre-commit framework integration)
**Executor:** Host terminal at `~/projects/librarian` (Cowork sandbox cannot git/build/upload)

---

## 0. Pre-flight context

What's already done in Cowork Session 51 (on `main`, uncommitted):

- `librarian/__init__.py` — `__version__ = "0.7.4"`
- `pyproject.toml` — `version = "0.7.4"`
- `.claude-plugin/plugin.json` — `"version": "0.7.4"`
- `.claude-plugin/marketplace.json` — `"version": "0.7.4"`
- `skills/librarian/SKILL.md` — frontmatter `metadata.version: "0.7.4"`
- `docs/release-notes-20260414-V4.0.md` — new v0.7.4 release notes (draft in registry)
- `docs/REGISTRY.yaml` — v0.7.3 artifacts stay active; 2026-04-14 V1.0 manifest + evidence marked superseded; new 2026-04-14 V2.0 manifest + evidence registered active; v0.7.4 notes + runbook added as draft; totals 31→35 / active 22 / draft 2→4 / superseded 7→9
- `docs/librarian-manifest-20260414-V2.0.json` — fresh manifest (31 registered, 31 hashed, 17 edges)
- `docs/librarian-evidence-20260414-V2.0.json` — fresh evidence pack, SSH-signed (parent commit `86568557`, DIRTY — expected pre-tag)
- `docs/librarian-manifest-20260414.json` — refreshed "latest" copy (mirrors V2.0)
- `docs/librarian-evidence-20260414.json` — refreshed "latest" copy (mirrors V2.0)
- `docs/release-v0-7-4-runbook-20260414-V1.0.md` — this file

**On main, already committed and pushed (pending this runbook):**
- `f296045` — Phase 7.5 oplog append-only detection
- `758e30e` — Session 51 CLAUDE.md/README updates
- `8656855` — Phase 7.7 pre-commit framework integration

No further git commits, tags, builds, or uploads have been made for v0.7.4. Nothing destructive has happened.

---

## 1. Sanity check the working tree

```bash
cd ~/projects/librarian
source .venv/bin/activate

git status --short
# Expected (Cowork-staged, not yet committed):
#  M .claude-plugin/marketplace.json
#  M .claude-plugin/plugin.json
#  M docs/REGISTRY.yaml
#  M docs/librarian-manifest-20260414-V1.0.json   (may show unchanged; updated: field only)
#  A docs/librarian-manifest-20260414-V2.0.json
#  M docs/librarian-manifest-20260414.json
#  M docs/librarian-evidence-20260414-V1.0.json   (may show unchanged; updated: field only)
#  A docs/librarian-evidence-20260414-V2.0.json
#  M docs/librarian-evidence-20260414.json
#  A docs/release-notes-20260414-V4.0.md
#  A docs/release-v0-7-4-runbook-20260414-V1.0.md
#  M librarian/__init__.py
#  M pyproject.toml
#  M skills/librarian/SKILL.md

pytest -q
# Expected: 796 passed
```

If pytest fails, stop and investigate. Do not proceed to tag.

---

## 2. Confirm no v0.7.4 work is missing from main

```bash
git log --oneline v0.7.3..HEAD
# Expected (3 commits, oldest-to-newest reading bottom-up):
#   8656855 feat: pre-commit framework integration (Phase 7.7)
#   758e30e docs: Session 51 — v0.7.3 shipped + Phase 7.5 on main (test count 774)
#   f296045 feat: oplog append-only detection + setup helper (Phase 7.5)
```

These three commits are what v0.7.4 ships (plus the bump commit you're about to make).

---

## 3. Commit the version bumps + release notes + runbook + refreshed artifacts

```bash
git add \
  librarian/__init__.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md \
  docs/release-notes-20260414-V4.0.md \
  docs/release-v0-7-4-runbook-20260414-V1.0.md \
  docs/REGISTRY.yaml \
  docs/librarian-manifest-20260414-V1.0.json \
  docs/librarian-manifest-20260414-V2.0.json \
  docs/librarian-manifest-20260414.json \
  docs/librarian-evidence-20260414-V1.0.json \
  docs/librarian-evidence-20260414-V2.0.json \
  docs/librarian-evidence-20260414.json

git status --short
# Every line should start with a staged indicator.

git commit -m "release: v0.7.4 — Phase 7.5 oplog lock + Phase 7.7 pre-commit framework integration"
```

Pre-commit hook will run naming + registry-sync + shell lint checks.

---

## 4. Tag the release

```bash
git tag -s v0.7.4 -m "v0.7.4 — Phase 7.5 oplog append-only detection + Phase 7.7 pre-commit framework integration"
git tag --list | grep 0.7
# Expected: v0.7.1-published, v0.7.2, v0.7.3, v0.7.4
```

---

## 5. Build sdist + wheel

```bash
rm -rf dist/ build/ *.egg-info

python -m build
# Expected: dist/librarian_2026-0.7.4-py3-none-any.whl + dist/librarian_2026-0.7.4.tar.gz
ls -la dist/
```

---

## 6. TestPyPI dry-run

```bash
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*

curl -s https://test.pypi.org/pypi/librarian-2026/json | python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.7.4
```

---

## 7. Real PyPI upload

```bash
python -m twine upload dist/*

curl -s https://pypi.org/pypi/librarian-2026/json | python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.7.4
```

⚠️ **PyPI uploads are immutable.** Once 0.7.4 is up, the only forward path if something's broken is 0.7.5.

---

## 8. Push commits + tag to GitHub

```bash
git push origin main
git push origin v0.7.4
```

---

## 9. GitHub release

```bash
gh release create v0.7.4 \
  --title "Librarian v0.7.4 — Oplog lock + pre-commit framework integration" \
  --notes-file docs/release-notes-20260414-V4.0.md \
  dist/librarian_2026-0.7.4.tar.gz \
  dist/librarian_2026-0.7.4-py3-none-any.whl

gh release view v0.7.4
```

---

## 10. Plugin marketplace refresh

```bash
claude plugins update librarian@librarian-marketplace
claude plugins list | grep -A2 librarian
# Expected: version 0.7.4, enabled
```

---

## 11. Post-release smoke test

```bash
python -m venv /tmp/lib-smoke-074
source /tmp/lib-smoke-074/bin/activate
cd /tmp
pip install --no-cache-dir librarian-2026==0.7.4
python -c "import librarian; print(librarian.__version__)"
# Expected: 0.7.4

# Phase 7.5 — oplog CLI
mkdir -p /tmp/lib074-test && cd /tmp/lib074-test
python -m librarian init --preset minimal --no-hook
python -m librarian oplog status
# Expected: "State: missing" or "State: unlocked" (depending on whether
# any librarian op has created the log yet)

# Phase 7.7 — pre-commit entry point
librarian-precommit docs/REGISTRY.yaml   # should exit 0 (REGISTRY.yaml is exempt)
echo "# smoke" > docs/bad-filename.md
librarian-precommit docs/bad-filename.md || echo "correctly flagged: exit $?"
# Expected: "FAIL" output + exit 1

# Cleanup
deactivate
rm -rf /tmp/lib-smoke-074 /tmp/lib074-test
cd ~/projects/librarian
```

---

## 12. Post-release housekeeping

Flip release-notes V4.0 and runbook V1.0 in `docs/REGISTRY.yaml` from `draft` to `active` now that v0.7.4 is live. Quick Python script:

```bash
python << 'PY'
from librarian.registry import Registry
reg = Registry.load("docs/REGISTRY.yaml")
flipped = []
for doc in reg.documents:
    if doc.get("filename") in ("release-notes-20260414-V4.0.md",
                                "release-v0-7-4-runbook-20260414-V1.0.md"):
        if doc.get("status") != "active":
            doc["status"] = "active"
            doc["updated"] = "2026-04-14"
            flipped.append(doc["filename"])
reg.update_meta()
reg.save()
print("Flipped to active:")
for f in flipped: print(" ", f)
m = reg.data["registry_meta"]
print(f"\nregistry_meta: total={m['total_documents']} active={m['active']} draft={m['draft']} superseded={m['superseded']}")
PY

git diff docs/REGISTRY.yaml | head -30
git add docs/REGISTRY.yaml
git commit -m "registry: activate v0.7.4 release notes + runbook"
git push origin main
```

Expected final counts: total=35, active=24, draft=2, superseded=9.

---

## Rollback

- **Between commit and tag:** `git reset --soft HEAD~1` to unstage; fix; re-commit.
- **Between tag and PyPI upload:** `git tag -d v0.7.4 && git push origin :refs/tags/v0.7.4` to remove; fix; retag.
- **After PyPI upload:** PyPI is immutable — must ship v0.7.5 with the fix.
- **After GitHub release:** `gh release delete v0.7.4` removes the release page; tag + PyPI entry persist.
- **After plugin marketplace refresh:** users who already pulled v0.7.4 keep it; fix forward in v0.7.5.

---

## Definition of done

- [ ] `pytest -q` → 796 passed
- [ ] `git tag --list` includes `v0.7.4`
- [ ] `pip index versions librarian-2026` shows 0.7.4 as latest
- [ ] `gh release view v0.7.4` shows the release page with both artifacts attached
- [ ] `claude plugins list` shows librarian @ 0.7.4 enabled
- [ ] Smoke-test venv: `pip install librarian-2026` pulls 0.7.4; `oplog status` runs; `librarian-precommit` rejects bad names

Once all six are green, the release is done. Step 12 (housekeeping) can be done immediately after or batched with the next session's work.
