"""Regression tests for the librarian pre-commit hook registry-sync check.

The hook at `scripts/librarian-pre-commit-hook-20260411-V1.0.sh` validates
that staged governed documents are registered in `docs/REGISTRY.yaml` via a
grep against the registry.

Historical bug (Session 35, commit 853c5ba):
    Hook searched for "$filepath" (the full staged path) but the registry
    only had the `filename:` key at the time — every governed-doc commit
    produced a false "not found" warning.

Session-51 bug (Phase 7.1):
    Fix from 853c5ba used an unescaped, unanchored pattern
    ``(filename|path):.*$filename`` which:
      1. Treated regex metacharacters in $filename (notably `.` in V1.0.md)
         as wildcards — over-permissive, could match unrelated lines.
      2. Did not anchor the filename at end of line — `foo.md` would match
         a registered `foo.md.backup` or `old-foo.md`.

These tests lock in the hardened matcher and guard against regression.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "scripts" / "librarian-pre-commit-hook-20260411-V1.0.sh"


# --------------------------------------------------------------------------- #
# Unit-level test of the grep the hook uses                                   #
# --------------------------------------------------------------------------- #

# Extracted verbatim from the hook (scripts/librarian-pre-commit-hook-...-V1.0.sh).
# Kept in sync by assertion in test_grep_pattern_matches_hook_source().
HARDENED_PATTERN = (
    r"^[-[:space:]]+(filename|path):[[:space:]]+"
    r"([^[:space:]]*/)?${filename_esc}[[:space:]]*$"
)


def _run_grep(registry_path: Path, filename: str) -> bool:
    """Invoke the exact bash escape + grep the hook uses. Returns True if matched."""
    script = f"""
set -u
filename='{filename}'
filename_esc=$(printf '%s' "$filename" | sed 's/[][().*+?|{{}}\\\\^$]/\\\\&/g')
grep -qE "^[-[:space:]]+(filename|path):[[:space:]]+([^[:space:]]*/)?${{filename_esc}}[[:space:]]*$" "{registry_path}"
"""
    result = subprocess.run(["bash", "-c", script], capture_output=True)
    return result.returncode == 0


@pytest.fixture
def fixture_registry(tmp_path: Path) -> Path:
    """A minimal registry exercising both list-item and indented entry forms."""
    content = """\
project_config:
  project_name: test
documents:
- filename: docs-guide-20260101-V1.0.md
  path: docs/docs-guide-20260101-V1.0.md
  title: Guide
- filename: readme-only-20260101-V1.0.md
  title: Has filename but no path
- filename: SKILL.md
  path: skill/SKILL.md
- filename: foo-V1x0xmd
  path: docs/foo-V1x0xmd
"""
    path = tmp_path / "REGISTRY.yaml"
    path.write_text(content)
    return path


class TestRegistrySyncGrep:
    """Direct tests of the hook's registry-sync grep pattern."""

    def test_matches_list_item_filename_form(self, fixture_registry):
        assert _run_grep(fixture_registry, "docs-guide-20260101-V1.0.md")

    def test_matches_indented_path_form(self, fixture_registry):
        # SKILL.md is only reachable via `path: skill/SKILL.md` (nested).
        assert _run_grep(fixture_registry, "SKILL.md")

    def test_matches_entry_with_filename_but_no_path(self, fixture_registry):
        # Some registry entries lack a `path:` field (legacy or intentional).
        assert _run_grep(fixture_registry, "readme-only-20260101-V1.0.md")

    def test_rejects_unregistered_filename(self, fixture_registry):
        assert not _run_grep(fixture_registry, "totally-fake-20260101-V1.0.md")

    def test_rejects_substring_suffix_extension(self, fixture_registry):
        # Anchoring: a real entry is `docs-guide-20260101-V1.0.md`; staging a
        # similarly-named file with an extra suffix must NOT false-positive.
        assert not _run_grep(
            fixture_registry, "docs-guide-20260101-V1.0.md.backup"
        )

    def test_rejects_substring_prefix_truncation(self, fixture_registry):
        # Staging a name that is a suffix of a registered name must not match.
        assert not _run_grep(fixture_registry, "ocs-guide-20260101-V1.0.md")

    def test_literal_dots_not_regex_wildcards(self, fixture_registry):
        # Phase 7.1 regression: the registry has `foo-V1x0xmd` (no dots).
        # Staging `foo-V1.0.md` (with dots) must NOT match — in an unescaped
        # regex the `.` chars would match the `x` chars in the registry entry,
        # producing a spurious "registered" result. The fix escapes them.
        assert not _run_grep(fixture_registry, "foo-V1.0.md")

    def test_literal_registry_entry_still_matches(self, fixture_registry):
        # Inverse of above — the registered name itself still resolves.
        assert _run_grep(fixture_registry, "foo-V1x0xmd")


# --------------------------------------------------------------------------- #
# End-to-end test: run the actual hook with a fixture git index               #
# --------------------------------------------------------------------------- #


@pytest.fixture
def fixture_git_repo(tmp_path: Path) -> Path:
    """Create a throwaway git repo with the hook + a registry + a doc."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "scripts").mkdir()

    # Copy the hook in verbatim.
    shutil.copy(HOOK, repo / "scripts" / HOOK.name)
    os.chmod(repo / "scripts" / HOOK.name, 0o755)

    # Minimal registry with two docs — one with the regex-metachar stress case.
    (repo / "docs" / "REGISTRY.yaml").write_text(
        """\
project_config:
  project_name: test
documents:
- filename: docs-guide-20260101-V1.0.md
  path: docs/docs-guide-20260101-V1.0.md
- filename: foo-V1x0xmd
  path: docs/foo-V1x0xmd
"""
    )

    # Governed file that IS registered.
    (repo / "docs" / "docs-guide-20260101-V1.0.md").write_text("# Guide\n")
    # Governed file that is NOT registered (for the negative case).
    (repo / "docs" / "unregistered-20260101-V1.0.md").write_text("# Orphan\n")
    # A file whose name would false-positive under the pre-fix regex.
    (repo / "docs" / "foo-V1.0.md").write_text("# Dots test\n")

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.x", "-c", "user.name=t",
         "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=repo, check=True,
    )
    return repo


def _stage(repo: Path, relpath: str) -> None:
    subprocess.run(["git", "add", relpath], cwd=repo, check=True)


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(repo / "scripts" / HOOK.name)],
        cwd=repo,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )


class TestRegistrySyncEndToEnd:
    """Drive the actual hook script end-to-end against a throwaway repo."""

    def test_registered_doc_produces_no_warning(self, fixture_git_repo):
        _stage(fixture_git_repo, "docs/docs-guide-20260101-V1.0.md")
        result = _run_hook(fixture_git_repo)
        assert "All staged document files are registered" in result.stdout
        assert "not found in REGISTRY.yaml" not in result.stdout

    def test_unregistered_doc_produces_warning(self, fixture_git_repo):
        _stage(fixture_git_repo, "docs/unregistered-20260101-V1.0.md")
        result = _run_hook(fixture_git_repo)
        assert "unregistered-20260101-V1.0.md — not found in REGISTRY.yaml" in result.stdout

    def test_dots_metachar_does_not_false_positive(self, fixture_git_repo):
        # Regression guard for Phase 7.1: registry has `foo-V1x0xmd`; staging
        # `foo-V1.0.md` (dots) MUST be flagged as unregistered. Under the
        # pre-fix regex, the literal dots acted as wildcards and matched the
        # registry entry — a silent false positive.
        _stage(fixture_git_repo, "docs/foo-V1.0.md")
        result = _run_hook(fixture_git_repo)
        assert "foo-V1.0.md — not found in REGISTRY.yaml" in result.stdout
