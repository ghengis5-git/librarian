# Release Runbook — v0.8.0

**Date:** 2026-04-22
**Version:** V1.0
**Status:** Draft
**Target release:** v0.8.0 (security fixes + Phase 8.2a hardening + Pass-4 adversarial-review fixes)
**Executor:** Host terminal at `~/projects/librarian` (Cowork sandbox cannot git/tag/build/upload).

---

## 0. Pre-flight context

**What's already on `main` locally (two commits ahead of `origin/main`, unpushed):**
- `5bc0b16` — `fix(security): evidence seal time-dependency + manifest basename collision (v0.8.0)`
- `283c242` — `feat: Phase 8.2a - legal-discovery template, friendly YAML errors, Windows UNC hardening`

Run `git log --oneline v0.7.5..HEAD` on the host to confirm. These are the two substantive v0.8.0 payload commits; the commit you are about to make (version bumps + Pass-4 fixes + release notes + runbook + manifest + evidence) is the third.

**What Cowork Session 53 has staged in the working tree (uncommitted at the time this runbook is read; becomes committed at step 3):**

Version bumps:
- `librarian/__init__.py` — `__version__ = "0.8.0"`
- `pyproject.toml` — `version = "0.8.0"`
- `.claude-plugin/plugin.json` — `"version": "0.8.0"`
- `.claude-plugin/marketplace.json` — `"version": "0.8.0"`
- `skills/librarian/SKILL.md` — frontmatter `metadata.version: "0.8.0"`

Pass-4 HIGH fixes (adversarial review):
- `librarian/yaml_errors.py` — `UnicodeDecodeError` catch in `load_yaml`; caret off-by-one fix
- `librarian/manifest.py` — `seen_rel_paths` duplicate-rel_path guard in both Type-2 branches
- `tests/test_yaml_errors.py` — 5 new `TestLoadYamlUnicodeDecodeError` tests + 1 caret-column regression
- `tests/test_manifest.py` — 4 new `TestDuplicateResolutionDetection` tests

Documentation:
- `CLAUDE.md` — Session 53 handoff updates + Pass-4 trail
- `docs/release-notes-20260422-V6.0.md` — new v0.8.0 release notes (draft in registry)
- `docs/release-v0-8-0-runbook-20260422-V1.0.md` — this file (draft in registry)
- `docs/phase-9-pypi-rename-migration-20260422-V1.0.md` — new planning doc (registered)
- `docs/REGISTRY.yaml` — Phase 9 plan registered + release notes/runbook added as drafts; V3.0 manifest+evidence will be moved active → superseded in step 5 below

To be generated in step 5:
- `docs/librarian-manifest-20260422-V4.0.json` — fresh manifest
- `docs/librarian-evidence-20260422-V4.0.json` — fresh evidence pack, SSH-signed
- `docs/librarian-manifest-20260422.json` — refreshed "latest" copy
- `docs/librarian-evidence-20260422.json` — refreshed "latest" copy

No git tags, builds, or uploads have been made for v0.8.0. Nothing destructive has happened.

---

## 1. Sanity check the working tree

```bash
cd ~/projects/librarian
source .venv/bin/activate

git status --short
# Expected (Cowork-staged, not yet committed):
#  M CLAUDE.md
#  M .claude-plugin/marketplace.json
#  M .claude-plugin/plugin.json
#  M docs/REGISTRY.yaml
#  A docs/phase-9-pypi-rename-migration-20260422-V1.0.md
#  A docs/release-notes-20260422-V6.0.md
#  A docs/release-v0-8-0-runbook-20260422-V1.0.md
#  M librarian/__init__.py
#  M librarian/manifest.py
#  M librarian/yaml_errors.py
#  M pyproject.toml
#  M skills/librarian/SKILL.md
#  M tests/test_manifest.py
#  M tests/test_yaml_errors.py

pytest -q
# Expected: 884 passed
```

If pytest fails, stop and investigate. Do not proceed to tag.

---

## 2. Confirm v0.8.0 commits on `main`

```bash
git log --oneline v0.7.5..HEAD
# Expected (2 commits local-ahead, plus the bump commit you're about to make):
#   283c242 feat: Phase 8.2a - legal-discovery template, friendly YAML errors, Windows UNC hardening
#   5bc0b16 fix(security): evidence seal time-dependency + manifest basename collision (v0.8.0)
```

These two commits + the bump commit (step 3) are what v0.8.0 ships.

---

## 3. Commit the version bumps + Pass-4 fixes + release notes + runbook

Stage everything except the manifest + evidence artifacts (those get generated in step 5 and committed in step 6).

```bash
git add \
  librarian/__init__.py \
  librarian/manifest.py \
  librarian/yaml_errors.py \
  pyproject.toml \
  .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json \
  skills/librarian/SKILL.md \
  tests/test_manifest.py \
  tests/test_yaml_errors.py \
  CLAUDE.md \
  docs/release-notes-20260422-V6.0.md \
  docs/release-v0-8-0-runbook-20260422-V1.0.md \
  docs/phase-9-pypi-rename-migration-20260422-V1.0.md \
  docs/REGISTRY.yaml

git status --short
# Every line should start with a staged indicator (no "M " unstaged lines
# for the files listed above).

git -c user.name="Chris Kahn" \
    -c user.email="272935920+ghengis5-git@users.noreply.github.com" \
    commit -m "release: v0.8.0 - Phase 8.2a hardening plus Pass-4 adversarial-review fixes"
```

Pre-commit hook will run naming + registry-sync + shell lint checks. All should pass cleanly. The message uses ASCII-only punctuation per the release-runbook-ascii-only feedback memory (hyphen not em-dash, no parens inside quoted strings, no `$` or backticks in nested quotes).

---

## 4. Tag the release

```bash
git tag -s v0.8.0 -m "v0.8.0 - evidence seal fixes plus Phase 8.2a plus Pass-4 hardening"
git tag --list | grep 0.
# Expected: v0.7.1-published, v0.7.2, v0.7.3, v0.7.4, v0.7.5, v0.8.0
```

---

## 5. Refresh manifest + evidence seal (V4.0 pair)

Move V3.0 active -> superseded, generate fresh V4.0 pair against the freshly-tagged `v0.8.0`, and register the new pair.

```bash
# Step A: flip V3.0 pair in the registry
python << 'PY'
from librarian.registry import Registry
reg = Registry.load("docs/REGISTRY.yaml")
flipped = []
for doc in reg.documents:
    if doc.get("filename") in ("librarian-manifest-20260414-V3.0.json",
                                "librarian-evidence-20260414-V3.0.json"):
        if doc.get("status") != "superseded":
            doc["status"] = "superseded"
            doc["superseded_by"] = doc["filename"].replace("20260414-V3.0", "20260422-V4.0")
            flipped.append(doc["filename"])
reg.update_meta()
reg.save()
print("Flipped to superseded:", flipped)
PY

# Step B: generate the V4.0 pair
python -m librarian --registry docs/REGISTRY.yaml manifest \
  -o docs/librarian-manifest-20260422-V4.0.json
cp docs/librarian-manifest-20260422-V4.0.json docs/librarian-manifest-20260422.json

python -m librarian --registry docs/REGISTRY.yaml evidence \
  -o docs/librarian-evidence-20260422-V4.0.json
cp docs/librarian-evidence-20260422-V4.0.json docs/librarian-evidence-20260422.json

# Step C: sanity-check evidence verification round-trips
python << 'PY'
import json
from librarian.evidence import verify_evidence
with open("docs/librarian-evidence-20260422-V4.0.json") as f:
    pack = json.load(f)
ok, reason = verify_evidence(pack)
print(f"Evidence verifies: {ok}")
if not ok:
    raise SystemExit(f"Evidence verify failed: {reason}")
PY

# Step D: sleep 2 seconds then verify seal is stable across time
# (regression test for the Track 1 HIGH-1 fix — seal must survive re-verify delay)
sleep 2
python << 'PY'
import json
from librarian.evidence import verify_evidence
with open("docs/librarian-evidence-20260422-V4.0.json") as f:
    pack = json.load(f)
ok, reason = verify_evidence(pack)
assert ok, f"Evidence seal unstable across time delay: {reason}"
print("Seal stable across time delay: OK")
PY

# Step E: register the V4.0 pair in REGISTRY.yaml as active
python << 'PY'
from librarian.registry import Registry
reg = Registry.load("docs/REGISTRY.yaml")
new_entries = [
    {
        "filename": "librarian-manifest-20260422-V4.0.json",
        "path": "docs/librarian-manifest-20260422-V4.0.json",
        "title": "Librarian Manifest V4.0",
        "description": "Manifest generated against v0.8.0 tag. 40+ registered documents, SHA-256 hashes, dependency graph.",
        "format": "json",
        "version": "4.0",
        "date": "2026-04-22",
        "status": "active",
        "author": "Chris Kahn",
        "classification": "PERSONAL / INTERNAL USE ONLY",
        "supersedes": "librarian-manifest-20260414-V3.0.json",
        "superseded_by": None,
        "infrastructure_exempt": False,
        "tags": ["manifest", "evidence"],
    },
    {
        "filename": "librarian-evidence-20260422-V4.0.json",
        "path": "docs/librarian-evidence-20260422-V4.0.json",
        "title": "Librarian Evidence Pack V4.0",
        "description": "Tamper-evident evidence pack, SSH-signed against v0.8.0 tag. Uses canonical manifest form (no generated_at) per Track 1 HIGH-1 fix.",
        "format": "json",
        "version": "4.0",
        "date": "2026-04-22",
        "status": "active",
        "author": "Chris Kahn",
        "classification": "PERSONAL / INTERNAL USE ONLY",
        "supersedes": "librarian-evidence-20260414-V3.0.json",
        "superseded_by": None,
        "infrastructure_exempt": False,
        "tags": ["evidence", "ssh-signed"],
    },
]
existing = {d.get("filename") for d in reg.documents}
for e in new_entries:
    if e["filename"] not in existing:
        reg.documents.append(e)
reg.update_meta()
reg.save()
m = reg.data["registry_meta"]
print(f"registry_meta: total={m['total_documents']} active={m['active']} draft={m['draft']} superseded={m['superseded']}")
PY
```

---

## 6. Commit the refreshed manifest + evidence pair + registry update

```bash
git add \
  docs/librarian-manifest-20260422-V4.0.json \
  docs/librarian-manifest-20260422.json \
  docs/librarian-evidence-20260422-V4.0.json \
  docs/librarian-evidence-20260422.json \
  docs/REGISTRY.yaml

git -c user.name="Chris Kahn" \
    -c user.email="272935920+ghengis5-git@users.noreply.github.com" \
    commit -m "registry: activate v0.8.0 manifest plus evidence V4.0"
```

---

## 7. Build sdist + wheel

```bash
rm -rf dist/ build/ *.egg-info

python -m build
# Expected: dist/librarian_2026-0.8.0-py3-none-any.whl + dist/librarian_2026-0.8.0.tar.gz
ls -la dist/
```

---

## 8. TestPyPI dry-run

```bash
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*

sleep 30 && curl -s https://test.pypi.org/pypi/librarian-2026/json | \
  python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.8.0  (30-second sleep handles CDN propagation lag per
# feedback_release_runbook_curl_lag auto-memory)
```

---

## 9. Real PyPI upload

```bash
python -m twine upload dist/*

sleep 30 && curl -s https://pypi.org/pypi/librarian-2026/json | \
  python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.8.0
```

**PyPI uploads are immutable.** Once 0.8.0 is up, the only forward path if something's broken is 0.8.1.

---

## 10. Push commits + tag to GitHub

```bash
git push origin main
git push origin v0.8.0
```

This push carries `5bc0b16`, `283c242`, the bump commit from step 3, and the registry-activate commit from step 6, plus the new tag.

---

## 11. GitHub release

```bash
gh release create v0.8.0 \
  --title "Librarian v0.8.0 - evidence-seal fixes, Phase 8.2a hardening, Pass-4 adversarial review" \
  --notes-file docs/release-notes-20260422-V6.0.md \
  dist/librarian_2026-0.8.0.tar.gz \
  dist/librarian_2026-0.8.0-py3-none-any.whl

gh release view v0.8.0
```

Title uses ASCII-only punctuation (hyphen not em-dash) per release-runbook-ascii-only feedback memory.

---

## 12. Plugin marketplace refresh

```bash
claude plugins update librarian@librarian-marketplace
claude plugins list | grep -A2 librarian
# Expected: version 0.8.0, enabled
```

---

## 13. Post-release smoke test

Verify both Pass-4 HIGH fixes and the Track 1 evidence-seal stability in a clean venv.

```bash
python -m venv /tmp/lib-smoke-080
source /tmp/lib-smoke-080/bin/activate
cd /tmp
pip install --no-cache-dir librarian-2026==0.8.0
python -c "import librarian; print(librarian.__version__)"
# Expected: 0.8.0

# Track 1 HIGH-1 - evidence seal stable across time delay
mkdir -p /tmp/lib080-test && cd /tmp/lib080-test
python -m librarian init --preset minimal --no-hook
python -m librarian --registry docs/REGISTRY.yaml manifest -o /tmp/m1.json
python -m librarian --registry docs/REGISTRY.yaml evidence -o /tmp/e1.json
sleep 2
python -c "
import json
from librarian.evidence import verify_evidence
with open('/tmp/e1.json') as f:
    ok, reason = verify_evidence(json.load(f))
assert ok, f'Seal unstable: {reason}'
print('HIGH-1 fix: seal stable across delay')
"

# Track 1 HIGH-2 + Pass-4 HIGH-2 - duplicate resolution now raises
python -c "
from librarian import ManifestError
from librarian.manifest import generate
from librarian.registry import Registry
import tempfile, pathlib, yaml
with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    (root / 'a').mkdir()
    (root / 'b').mkdir()
    (root / 'a' / 'same.md').write_text('x')
    (root / 'b' / 'same.md').write_text('y')
    reg_data = {
        'project_config': {
            'project_name': 'test',
            'tracked_dirs': ['a', 'b'],
            'naming_convention': 'any',
        },
        'documents': [
            {'filename': 'same.md', 'title': 't1', 'version': '1.0', 'date': '2026-01-01', 'status': 'active', 'format': 'md', 'author': 'x', 'classification': 'PUBLIC'},
            {'filename': 'same.md', 'title': 't2', 'version': '1.0', 'date': '2026-01-01', 'status': 'active', 'format': 'md', 'author': 'x', 'classification': 'PUBLIC'},
        ]
    }
    reg_path = root / 'REGISTRY.yaml'
    reg_path.write_text(yaml.safe_dump(reg_data))
    try:
        generate(Registry.load(str(reg_path)), repo_root=root)
        raise SystemExit('FAIL: duplicate resolution did not raise')
    except ManifestError as e:
        assert 'Duplicate' in str(e) or 'basename' in str(e).lower()
        print('HIGH-2 fix: duplicate resolution raises ManifestError')
"

# Pass-4 HIGH-1 - UnicodeDecodeError wrapped as YamlParseError
python -c "
from librarian import YamlParseError, load_yaml
import tempfile, pathlib
with tempfile.NamedTemporaryFile(mode='wb', suffix='.yaml', delete=False) as f:
    f.write(b'\xff\xfe' + 'foo: bar'.encode('utf-16-le'))
    path = pathlib.Path(f.name)
try:
    load_yaml(path)
    raise SystemExit('FAIL: bad UTF-8 did not raise YamlParseError')
except YamlParseError as e:
    msg = str(e)
    assert str(path) in msg
    assert 'UTF-8' in msg or 'utf-8' in msg.lower()
    print('Pass-4 HIGH-1 fix: UnicodeDecodeError -> YamlParseError with path + UTF-8 hint')
finally:
    path.unlink(missing_ok=True)
"

# Track 2 - legal-discovery template registered
python -c "
from librarian.templates import get_template
t = get_template('legal-discovery')
assert t is not None
assert 'legal-discovery' in t.id
print('Track 2: legal-discovery template loadable')
"

# Cleanup
deactivate
rm -rf /tmp/lib-smoke-080 /tmp/lib080-test /tmp/m1.json /tmp/e1.json
cd ~/projects/librarian
```

---

## 14. Post-release housekeeping

Flip release-notes V6.0 and runbook V1.0 in `docs/REGISTRY.yaml` from `draft` to `active` now that v0.8.0 is live.

```bash
python << 'PY'
from librarian.registry import Registry
reg = Registry.load("docs/REGISTRY.yaml")
flipped = []
for doc in reg.documents:
    if doc.get("filename") in ("release-notes-20260422-V6.0.md",
                                "release-v0-8-0-runbook-20260422-V1.0.md",
                                "phase-9-pypi-rename-migration-20260422-V1.0.md"):
        if doc.get("status") != "active":
            doc["status"] = "active"
            doc["updated"] = "2026-04-22"
            flipped.append(doc["filename"])
reg.update_meta()
reg.save()
print("Flipped to active:")
for f in flipped: print(" ", f)
m = reg.data["registry_meta"]
print(f"\nregistry_meta: total={m['total_documents']} active={m['active']} draft={m['draft']} superseded={m['superseded']}")
PY

git diff docs/REGISTRY.yaml | head -60
git add docs/REGISTRY.yaml
git -c user.name="Chris Kahn" \
    -c user.email="272935920+ghengis5-git@users.noreply.github.com" \
    commit -m "registry: activate v0.8.0 release notes plus runbook plus phase-9 plan"
git push origin main
```

---

## Rollback

- **Between commit and tag:** `git reset --soft HEAD~1` to unstage; fix; re-commit.
- **Between tag and PyPI upload:** `git tag -d v0.8.0 && git push origin :refs/tags/v0.8.0` to remove; fix; retag.
- **After PyPI upload:** PyPI is immutable - must ship v0.8.1 with the fix.
- **After GitHub release:** `gh release delete v0.8.0` removes the release page; tag + PyPI entry persist.
- **After plugin marketplace refresh:** users who already pulled v0.8.0 keep it; fix forward in v0.8.1.

**Extra caution on this release:** the manifest canonical form changed shape (no `generated_at` in sealed content). Existing evidence packs generated by v0.7.5 or earlier still verify against the original manifest JSON blob, but *regenerating* evidence under v0.8.0 produces a new seal value. If a downstream audit process pins to a specific seal hash, that process needs to be re-run against the V4.0 pair.

---

## Definition of done

- [ ] `pytest -q` shows 884 passed
- [ ] `git tag --list` includes `v0.8.0`
- [ ] `pip index versions librarian-2026` shows 0.8.0 as latest
- [ ] `gh release view v0.8.0` shows the release page with both artifacts attached
- [ ] `claude plugins list` shows librarian at 0.8.0 enabled
- [ ] Smoke-test venv: all four in-venv probes pass (evidence seal stable, duplicate resolution raises, UnicodeDecodeError wrapped, legal-discovery template loadable)
- [ ] V3.0 manifest+evidence pair shows status=superseded in REGISTRY.yaml; V4.0 pair shows status=active

Once all seven are green, the release is done. Step 14 (housekeeping) can be done immediately after or batched with the next session's work.
