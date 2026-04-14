"""Tests for librarian.precommit (Phase 7.7).

The pre-commit framework entry point takes staged file paths as argv and
returns 0 (all pass / nothing to check) or 1 (naming violations). We test:

* Registry discovery (walk-up to docs/REGISTRY.yaml)
* Scope filtering (tracked_dirs, extensions, infrastructure_exempt)
* Valid-name acceptance
* Invalid-name rejection with useful error output
* Exit code contract
* Fallback when no REGISTRY.yaml is reachable
* CLI argument handling (no args, --strict, etc.)

These tests stand up a fresh temporary repo per test so the behaviour is
isolated from the librarian project's own registry.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from librarian.precommit import (
    _find_registry,
    _get_exempt,
    _load_project_config,
    _should_check,
    main,
)


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #


@pytest.fixture
def fresh_repo(tmp_path: Path) -> Path:
    """A throwaway project with the minimum structure precommit.py expects.

    Creates:
      - docs/ directory
      - docs/REGISTRY.yaml with a minimal project_config
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "REGISTRY.yaml").write_text(textwrap.dedent("""\
        project_config:
          project_name: test
          tracked_dirs:
          - docs/
          naming_rules:
            separator: '-'
            case: lowercase
            infrastructure_exempt:
            - README.md
            - REGISTRY.yaml
        documents: []
    """))
    return tmp_path


@pytest.fixture
def no_registry_repo(tmp_path: Path) -> Path:
    """A project tree with NO REGISTRY.yaml — tests graceful fallback."""
    (tmp_path / "docs").mkdir()
    return tmp_path


# --------------------------------------------------------------------------- #
# _find_registry                                                               #
# --------------------------------------------------------------------------- #


class TestFindRegistry:
    def test_finds_in_direct_parent(self, fresh_repo):
        f = fresh_repo / "docs" / "test.md"
        f.write_text("x")
        assert _find_registry(f) == (fresh_repo / "docs" / "REGISTRY.yaml")

    def test_walks_up_from_nested(self, fresh_repo):
        nested = fresh_repo / "docs" / "subdir"
        nested.mkdir()
        f = nested / "test.md"
        f.write_text("x")
        assert _find_registry(f) == (fresh_repo / "docs" / "REGISTRY.yaml")

    def test_returns_none_when_absent(self, no_registry_repo):
        f = no_registry_repo / "docs" / "test.md"
        f.write_text("x")
        assert _find_registry(f) is None

    def test_accepts_directory_path(self, fresh_repo):
        # When given a directory, we walk from that directory.
        assert _find_registry(fresh_repo / "docs") == (
            fresh_repo / "docs" / "REGISTRY.yaml"
        )


# --------------------------------------------------------------------------- #
# _load_project_config                                                         #
# --------------------------------------------------------------------------- #


class TestLoadProjectConfig:
    def test_loads_real_registry(self, fresh_repo):
        pc = _load_project_config(fresh_repo / "docs" / "REGISTRY.yaml")
        assert pc["project_name"] == "test"
        assert "docs/" in pc["tracked_dirs"]

    def test_returns_empty_on_missing_file(self, tmp_path):
        assert _load_project_config(tmp_path / "nope.yaml") == {}

    def test_returns_empty_on_invalid_yaml(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("this: is: not: valid: yaml: [[[")
        assert _load_project_config(bad) == {}

    def test_returns_empty_on_missing_project_config(self, tmp_path):
        reg = tmp_path / "REGISTRY.yaml"
        reg.write_text("documents: []\n")
        assert _load_project_config(reg) == {}


# --------------------------------------------------------------------------- #
# _should_check                                                                #
# --------------------------------------------------------------------------- #


class TestShouldCheck:
    def test_md_in_tracked_dir_is_checked(self, fresh_repo):
        f = fresh_repo / "docs" / "foo-20260414-V1.0.md"
        f.write_text("x")
        pc = _load_project_config(fresh_repo / "docs" / "REGISTRY.yaml")
        assert _should_check(f, fresh_repo / "docs" / "REGISTRY.yaml", pc) is True

    def test_non_governed_extension_skipped(self, fresh_repo):
        f = fresh_repo / "docs" / "something.xyz"
        f.write_text("x")
        pc = _load_project_config(fresh_repo / "docs" / "REGISTRY.yaml")
        assert _should_check(f, fresh_repo / "docs" / "REGISTRY.yaml", pc) is False

    def test_registry_yaml_itself_skipped(self, fresh_repo):
        # REGISTRY.yaml is always exempt — hard-coded in _should_check
        f = fresh_repo / "docs" / "REGISTRY.yaml"
        pc = _load_project_config(f)
        assert _should_check(f, f, pc) is False

    def test_infrastructure_exempt_skipped(self, fresh_repo):
        f = fresh_repo / "README.md"
        f.write_text("x")
        pc = _load_project_config(fresh_repo / "docs" / "REGISTRY.yaml")
        assert _should_check(f, fresh_repo / "docs" / "REGISTRY.yaml", pc) is False

    def test_file_outside_tracked_dirs_skipped(self, fresh_repo):
        # Non-exempt file living outside tracked_dirs should be skipped
        f = fresh_repo / "src" / "module.md"
        f.parent.mkdir()
        f.write_text("x")
        pc = _load_project_config(fresh_repo / "docs" / "REGISTRY.yaml")
        assert _should_check(f, fresh_repo / "docs" / "REGISTRY.yaml", pc) is False

    def test_no_registry_treats_as_in_scope(self, no_registry_repo):
        """When no registry is reachable, fall back to doc-extension check."""
        f = no_registry_repo / "docs" / "foo.md"
        f.write_text("x")
        # registry_path=None, project_config={}
        assert _should_check(f, None, {}) is True


# --------------------------------------------------------------------------- #
# main() — end-to-end CLI behavior                                             #
# --------------------------------------------------------------------------- #


class TestMainCLI:
    def test_no_files_returns_0(self):
        assert main([]) == 0

    def test_valid_filename_returns_0(self, fresh_repo, capsys, monkeypatch):
        monkeypatch.chdir(fresh_repo)
        f = fresh_repo / "docs" / "my-doc-20260414-V1.0.md"
        f.write_text("x")
        assert main([str(f)]) == 0
        out = capsys.readouterr().out
        assert "OK" in out
        assert "1 file(s)" in out

    def test_invalid_filename_returns_1(self, fresh_repo, capsys, monkeypatch):
        monkeypatch.chdir(fresh_repo)
        f = fresh_repo / "docs" / "BAD_NAME.md"
        f.write_text("x")
        assert main([str(f)]) == 1
        err = capsys.readouterr().err
        assert "FAIL" in err
        assert "BAD_NAME.md" in err

    def test_multiple_files_mixed_validity(self, fresh_repo, capsys, monkeypatch):
        monkeypatch.chdir(fresh_repo)
        ok = fresh_repo / "docs" / "good-doc-20260414-V1.0.md"
        bad = fresh_repo / "docs" / "BadFile.md"
        ok.write_text("x")
        bad.write_text("x")
        rc = main([str(ok), str(bad)])
        assert rc == 1  # one violation is enough
        err = capsys.readouterr().err
        assert "BadFile.md" in err
        assert "good-doc-20260414-V1.0.md" not in err  # not listed as failure

    def test_skipped_file_not_counted_as_violation(self, fresh_repo, capsys, monkeypatch):
        monkeypatch.chdir(fresh_repo)
        # File outside tracked_dirs but doc-extension
        outside = fresh_repo / "src" / "readme-like.md"
        outside.parent.mkdir()
        outside.write_text("x")
        rc = main([str(outside)])
        assert rc == 0

    def test_registry_yaml_skipped(self, fresh_repo, capsys, monkeypatch):
        monkeypatch.chdir(fresh_repo)
        rc = main([str(fresh_repo / "docs" / "REGISTRY.yaml")])
        assert rc == 0

    def test_no_registry_fallback_still_validates(
        self, no_registry_repo, capsys, monkeypatch
    ):
        """Without a registry, we should still reject clearly-invalid names."""
        monkeypatch.chdir(no_registry_repo)
        f = no_registry_repo / "docs" / "foo.md"
        f.write_text("x")
        rc = main([str(f)])
        # 'foo.md' lacks the date + version parts required by default naming
        assert rc == 1

    def test_non_governed_extension_never_fails(
        self, fresh_repo, capsys, monkeypatch
    ):
        monkeypatch.chdir(fresh_repo)
        f = fresh_repo / "docs" / "data.xyz"
        f.write_text("x")
        assert main([str(f)]) == 0


# --------------------------------------------------------------------------- #
# Phase 8.0 hardening — symlinks, root fallback, helper dedup, empty-argv     #
# --------------------------------------------------------------------------- #


class TestSymlinkContainment:
    """Phase 8.0 HIGH fix — ``_should_check`` no longer follows symlinks
    out of the repo when deciding in-scope. Prior behaviour: a symlink
    ``docs/good-20260414-V1.0.md -> /etc/passwd`` would resolve outside
    repo_root, raise ValueError, and be skipped from naming check
    entirely. Now we do a lexical containment check.
    """

    @pytest.fixture
    def outside_dir(self, tmp_path_factory):
        """A temp dir unrelated to ``fresh_repo`` so symlinks can
        legitimately point outside the repo tree."""
        return tmp_path_factory.mktemp("outside")

    def test_symlink_with_bad_name_rejected(
        self, fresh_repo, outside_dir, monkeypatch
    ):
        """Symlink inside tracked dir with INVALID filename must be
        checked (and fail). Prior implementation silently skipped it
        because resolve() escaped ``repo_root`` → ValueError → False.
        """
        target = outside_dir / "external-target.txt"
        target.write_text("outside")
        bad_link = fresh_repo / "docs" / "BadName.md"
        try:
            bad_link.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("Filesystem does not support symlinks")
        monkeypatch.chdir(fresh_repo)
        rc = main([str(bad_link)])
        # Phase 8.0: the file MUST now be in scope. Previously returned 0.
        assert rc == 1

    def test_symlink_with_good_name_still_passes(
        self, fresh_repo, outside_dir, monkeypatch
    ):
        """Symlink with VALID filename must be in scope and pass. We
        observe scope inclusion via the ``1 file(s)`` line in OK output.
        """
        target = outside_dir / "external-target.txt"
        target.write_text("outside")
        link = fresh_repo / "docs" / "good-doc-20260414-V1.0.md"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("Filesystem does not support symlinks")
        monkeypatch.chdir(fresh_repo)
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main([str(link)])
        assert rc == 0
        # ``1 file(s)`` appears in the OK path; ``0 file(s)`` would mean
        # the symlink was silently skipped (the old bug).
        assert "1 file(s)" in buf.getvalue()


class TestFilesystemRootRegistryRejected:
    """Phase 8.0 HIGH fix — ``_find_registry`` no longer accepts
    ``/docs/REGISTRY.yaml`` at the filesystem root. Prior behaviour
    would treat the whole filesystem as repo_root on systems where
    ``/docs/REGISTRY.yaml`` happens to exist.
    """

    def test_does_not_walk_past_filesystem_root(self, tmp_path, monkeypatch):
        """When no ``docs/REGISTRY.yaml`` exists anywhere up to root, the
        function must return None. Previously it would check the root
        one more time as a fallback."""
        # tmp_path is guaranteed not to contain a docs/ directory
        f = tmp_path / "somefile.md"
        f.write_text("x")
        assert _find_registry(f) is None

    def test_root_fallback_not_consulted(self, monkeypatch, tmp_path):
        """Even if /docs/REGISTRY.yaml were to exist, the function must
        not probe for it. We can't actually plant a file at /docs/ in
        tests, so we verify the code path by asserting the function
        returned None without is_file ever being called on a root-level
        path. Simpler proxy test: no root probe remains in the function
        source.
        """
        import inspect
        from librarian import precommit
        src = inspect.getsource(precommit._find_registry)
        # The post-fix function must not contain a reference to
        # ``filesystem_root / "docs"`` AFTER the while loop. The loop
        # itself uses ``current`` not ``filesystem_root``.
        # Simple regex-free substring test:
        lines_after_loop = src.split("while current != filesystem_root:")[-1]
        assert 'filesystem_root / "docs"' not in lines_after_loop


class TestGetExemptHelper:
    """Phase 8.0 MED fix — ``_get_exempt`` dedups two identical blocks."""

    def test_returns_frozenset_of_exempt_names(self):
        pc = {
            "naming_rules": {
                "infrastructure_exempt": ["README.md", "REGISTRY.yaml", ".gitignore"]
            }
        }
        exempt = _get_exempt(pc)
        assert isinstance(exempt, frozenset)
        assert exempt == {"README.md", "REGISTRY.yaml", ".gitignore"}

    def test_empty_config_returns_empty_frozenset(self):
        assert _get_exempt({}) == frozenset()

    def test_missing_naming_rules_returns_empty(self):
        assert _get_exempt({"project_name": "foo"}) == frozenset()

    def test_null_infrastructure_exempt_returns_empty(self):
        """YAML ``infrastructure_exempt: null`` must not crash."""
        pc = {"naming_rules": {"infrastructure_exempt": None}}
        assert _get_exempt(pc) == frozenset()


class TestEmptyArgvNote:
    """Phase 8.0 MED fix — empty argv now prints a trace to stdout."""

    def test_no_files_prints_note(self, capsys):
        assert main([]) == 0
        captured = capsys.readouterr()
        assert "no files to check" in captured.out.lower()
