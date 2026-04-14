# Release Runbook — v0.7.5

**Date:** 2026-04-14
**Version:** V1.0
**Status:** Draft
**Target release:** v0.7.5 (security patch — Phase 8.0 hardening + Phase 8.1 polish)
**Executor:** Host terminal at `~/projects/librarian` (Cowork sandbox cannot git/tag/build/upload)

---

## 0. Pre-flight context

What's already done in Cowork Session 52 (on `main`, uncommitted at the time
this runbook is read; becomes committed at step 3):

- `librarian/__init__.py` — `__version__ = "0.7.5"`
- `pyproject.toml` — `version = "0.7.5"`
- `.claude-plugin/plugin.json` — `"version": "0.7.5"`
- `.claude-plugin/marketplace.json` — `"version": "0.7.5"`
- `skills/librarian/SKILL.md` — frontmatter `metadata.version: "0.7.5"`
- `docs/release-notes-20260414-V5.0.md` — new v0.7.5 release notes (draft in registry)
- `docs/release-v0-7-5-runbook-20260414-V1.0.md` — this file (draft in registry)
- `docs/librarian-manifest-20260414-V3.0.json` — fresh manifest (37 registered, 36 hashed, 19 edges)
- `docs/librarian-evidence-20260414-V3.0.json` — fresh evidence pack, SSH-signed (parent commit `7a09b47b`, DIRTY — expected pre-tag)
- `docs/librarian-manifest-20260414.json` — refreshed "latest" copy (mirrors V3.0)
- `docs/librarian-evidence-20260414.json` — refreshed "latest" copy (mirrors V3.0)
- `docs/REGISTRY.yaml` — V2.0 manifest+evidence moved active → superseded; V3.0 pair registered active; v0.7.5 notes + runbook added as draft; totals 37→39 / active 24 / draft 2→4 / superseded 9→11

**On `origin/main`, already pushed (Session 52, three commits past `v0.7.4`):**
- `e00...` or similar — Phase 8.0 hardening (9 findings)
- `0ac...` — Phase 8.1 polish (warnings, exempts, folder-density override)
- `7a09b47` — docs typo fix in v0.7.2 runbook (unrelated surface)

Exact SHAs — run `git log --oneline v0.7.4..HEAD` to see yours. These three
commits are the substantive v0.7.5 payload; the commit you're about to make
(version bumps + release notes + manifest + evidence) is the fourth.

No git tags, builds, or uploads have been made for v0.7.5. Nothing
destructive has happened.

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
#  M docs/librarian-manifest-20260414.json
#  A docs/librarian-manifest-20260414-V3.0.json
#  M docs/librarian-evidence-20260414.json
#  A docs/librarian-evidence-20260414-V3.0.json
#  A docs/release-notes-20260414-V5.0.md
#  A docs/release-v0-7-5-runbook-20260414-V1.0.md
#  M librarian/__init__.py
#  M pyproject.toml
#  M skills/librarian/SKILL.md

pytest -q
# Expected: 814 passed
```

If pytest fails, stop and investigate. Do not proceed to tag.

---

## 2. Confirm v0.7.5 commits on `main`

```bash
git log --oneline v0.7.4..HEAD
# Expected (3 commits on origin/main already, plus the bump commit you're
# about to make):
#   7a09b47 docs: fix self-reference typo in v0.7.2 runbook
#   <SHA>   chore: Phase 8.1 polish (warnings, exempts, folder-density override)
#   <SHA>   fix: Phase 8.0 adversarial-review hardening (9 findings)
```

These three commits + the bump commit (step 3) are what v0.7.5 ships.

---

## 3. Commit the version bumps + release notes + runbook + refreshed artifacts

```bash
git add \
  librarian/__init__.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md \
  docs/release-notes-20260414-V5.0.md \
  docs/release-v0-7-5-runbook-20260414-V1.0.md \
  docs/REGISTRY.yaml \
  docs/librarian-manifest-20260414-V3.0.json \
  docs/librarian-manifest-20260414.json \
  docs/librarian-evidence-20260414-V3.0.json \
  docs/librarian-evidence-20260414.json

git status --short
# Every line should start with a staged indicator (no "M " unstaged lines).

git commit -m "release: v0.7.5 — Phase 8.0 adversarial-review hardening + Phase 8.1 polish"
```

Pre-commit hook will run naming + registry-sync + shell lint checks. All
should pass cleanly (v0.7.5 Phase 8.0 also fixed the shell-compat warnings
that Phase 8.1 surfaced).

---

## 4. Tag the release

```bash
git tag -s v0.7.5 -m "v0.7.5 — Phase 8.0 adversarial-review hardening (1 CRIT + 3 HIGH + 4 MED + 1 LOW) + Phase 8.1 polish"
git tag --list | grep 0.7
# Expected: v0.7.1-published, v0.7.2, v0.7.3, v0.7.4, v0.7.5
```

---

## 5. Build sdist + wheel

```bash
rm -rf dist/ build/ *.egg-info

python -m build
# Expected: dist/librarian_2026-0.7.5-py3-none-any.whl + dist/librarian_2026-0.7.5.tar.gz
ls -la dist/
```

---

## 6. TestPyPI dry-run

```bash
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*

sleep 30 && curl -s https://test.pypi.org/pypi/librarian-2026/json | \
  python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.7.5  (30-second sleep handles CDN propagation lag per
# reference_release_runbook_curl_lag auto-memory)
```

---

## 7. Real PyPI upload

```bash
python -m twine upload dist/*

sleep 30 && curl -s https://pypi.org/pypi/librarian-2026/json | \
  python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.7.5
```

⚠️ **PyPI uploads are immutable.** Once 0.7.5 is up, the only forward path
if something's broken is 0.7.6.

---

## 8. Push commit + tag to GitHub

```bash
git push origin main
git push origin v0.7.5
```

The three Phase 8.0/8.1/typo commits are already on `origin/main` (pushed
in Session 52). This push carries the bump commit and the new tag.

---

## 9. GitHub release

```bash
gh release create v0.7.5 \
  --title "Librarian v0.7.5 — Phase 8.0 security hardening + Phase 8.1 polish" \
  --notes-file docs/release-notes-20260414-V5.0.md \
  dist/librarian_2026-0.7.5.tar.gz \
  dist/librarian_2026-0.7.5-py3-none-any.whl

gh release view v0.7.5
```

---

## 10. Plugin marketplace refresh

```bash
claude plugins update librarian@librarian-marketplace
claude plugins list | grep -A2 librarian
# Expected: version 0.7.5, enabled
```

---

## 11. Post-release smoke test

```bash
python -m venv /tmp/lib-smoke-075
source /tmp/lib-smoke-075/bin/activate
cd /tmp
pip install --no-cache-dir librarian-2026==0.7.5
python -c "import librarian; print(librarian.__version__)"
# Expected: 0.7.5

# Phase 8.0 CRIT fix — shell-quoting
python -c "
from librarian.oplog_lock import lock_instructions
from unittest.mock import patch
import shlex
with patch('librarian.oplog_lock.platform_support', return_value='macos'):
    out = lock_instructions('/tmp/foo; rm -rf \$HOME')
# Path must be single-quoted so the semicolon is inert
assert \"'\" in out, f'Not quoted: {out}'
tokens = shlex.split(out)
assert tokens == ['chflags', 'uappend', '/tmp/foo; rm -rf \$HOME'], tokens
print('CRIT fix: shell-injection safe')
"

# Phase 8.1 — audit_config.folder_threshold knob
mkdir -p /tmp/lib075-test && cd /tmp/lib075-test
python -m librarian init --preset minimal --no-hook
# Should accept audit_config block in registry
python -c "
import yaml
with open('docs/REGISTRY.yaml') as f:
    reg = yaml.safe_load(f)
reg['project_config']['audit_config'] = {'folder_threshold': 50}
with open('docs/REGISTRY.yaml', 'w') as f:
    yaml.safe_dump(reg, f)
"
python -m librarian --registry docs/REGISTRY.yaml audit
# Should run cleanly — folder_threshold override honored

# Cleanup
deactivate
rm -rf /tmp/lib-smoke-075 /tmp/lib075-test
cd ~/projects/librarian
```

---

## 12. Post-release housekeeping

Flip release-notes V5.0 and runbook V1.0 in `docs/REGISTRY.yaml` from
`draft` to `active` now that v0.7.5 is live:

```bash
python << 'PY'
from librarian.registry import Registry
reg = Registry.load("docs/REGISTRY.yaml")
flipped = []
for doc in reg.documents:
    if doc.get("filename") in ("release-notes-20260414-V5.0.md",
                                "release-v0-7-5-runbook-20260414-V1.0.md"):
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
git commit -m "registry: activate v0.7.5 release notes + runbook"
git push origin main
```

Expected final counts: total=39, active=26, draft=2, superseded=11.

---

## Rollback

- **Between commit and tag:** `git reset --soft HEAD~1` to unstage; fix; re-commit.
- **Between tag and PyPI upload:** `git tag -d v0.7.5 && git push origin :refs/tags/v0.7.5` to remove; fix; retag.
- **After PyPI upload:** PyPI is immutable — must ship v0.7.6 with the fix.
- **After GitHub release:** `gh release delete v0.7.5` removes the release page; tag + PyPI entry persist.
- **After plugin marketplace refresh:** users who already pulled v0.7.5 keep it; fix forward in v0.7.6.

⚠️ **Extra caution on this release:** the CRIT fix changes the return
value of `lock_instructions` / `unlock_instructions` (now shell-quoted).
Any downstream caller that splits the string on whitespace will break.
If you get a bug report from a user doing this, the fix is to tell them
to use `shlex.split()` instead — not to revert the quoting.

---

## Definition of done

- [ ] `pytest -q` → 814 passed
- [ ] `git tag --list` includes `v0.7.5`
- [ ] `pip index versions librarian-2026` shows 0.7.5 as latest
- [ ] `gh release view v0.7.5` shows the release page with both artifacts attached
- [ ] `claude plugins list` shows librarian @ 0.7.5 enabled
- [ ] Smoke-test venv: `pip install librarian-2026` pulls 0.7.5; `lock_instructions` returns shell-quoted string; `audit_config.folder_threshold` is honored

Once all six are green, the release is done. Step 12 (housekeeping) can be
done immediately after or batched with the next session's work.
