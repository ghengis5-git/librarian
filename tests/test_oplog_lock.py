"""Tests for librarian.oplog_lock (Phase 7.5).

Covers detection semantics (macOS stat flag, Linux lsattr parsing,
unsupported-platform paths), instruction strings, audit integration,
and the `librarian oplog status` CLI.

macOS and Linux code paths are covered via mocking rather than by
actually setting the append-only flag — doing so in a sandbox / CI
environment requires sudo on Linux and isn't worth the test flakiness.
We test the *logic* (platform branching, parse correctness, graceful
failure on missing tools) in isolation.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from librarian.oplog_lock import (
    is_append_only,
    lock_instructions,
    platform_support,
    unlock_instructions,
    _is_append_only_linux,
    _is_append_only_macos,
)


_REPO_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# platform_support                                                             #
# --------------------------------------------------------------------------- #


class TestPlatformSupport:
    def test_returns_one_of_known_values(self):
        assert platform_support() in {"macos", "linux", "unsupported"}

    @pytest.mark.parametrize("sysname,expected", [
        ("Darwin", "macos"),
        ("Linux", "linux"),
        ("Windows", "unsupported"),
        ("FreeBSD", "unsupported"),
        ("", "unsupported"),
    ])
    def test_maps_platform_system(self, sysname, expected):
        with patch("librarian.oplog_lock.platform.system", return_value=sysname):
            assert platform_support() == expected


# --------------------------------------------------------------------------- #
# is_append_only — top-level dispatch                                          #
# --------------------------------------------------------------------------- #


class TestIsAppendOnlyDispatch:
    def test_missing_file_returns_none(self, tmp_path):
        assert is_append_only(tmp_path / "does-not-exist") is None

    def test_unsupported_platform_returns_none(self, tmp_path):
        f = tmp_path / "file"
        f.write_text("")
        with patch("librarian.oplog_lock.platform_support", return_value="unsupported"):
            assert is_append_only(f) is None


# --------------------------------------------------------------------------- #
# macOS stat-flag parsing                                                      #
# --------------------------------------------------------------------------- #


class TestMacOSDetection:
    def test_flag_set_returns_true(self, tmp_path):
        f = tmp_path / "locked"
        f.write_text("x")

        class FakeStat:
            st_flags = 0x04  # UF_APPEND

        with patch("librarian.oplog_lock.os.stat", return_value=FakeStat()):
            assert _is_append_only_macos(f) is True

    def test_flag_unset_returns_false(self, tmp_path):
        f = tmp_path / "unlocked"
        f.write_text("x")

        class FakeStat:
            st_flags = 0x00

        with patch("librarian.oplog_lock.os.stat", return_value=FakeStat()):
            assert _is_append_only_macos(f) is False

    def test_other_flags_set_no_uappend(self, tmp_path):
        f = tmp_path / "locked-other"
        f.write_text("x")

        class FakeStat:
            st_flags = 0x02 | 0x08 | 0x10  # various non-UF_APPEND bits

        with patch("librarian.oplog_lock.os.stat", return_value=FakeStat()):
            assert _is_append_only_macos(f) is False

    def test_oserror_returns_none(self, tmp_path):
        f = tmp_path / "errfile"
        f.write_text("x")
        with patch("librarian.oplog_lock.os.stat", side_effect=OSError("boom")):
            assert _is_append_only_macos(f) is None

    def test_no_stflags_attr_returns_none(self, tmp_path):
        """On a Linux Python that somehow runs _is_append_only_macos
        (e.g., imported directly), st_flags is absent. Fall through to None."""
        f = tmp_path / "nostflags"
        f.write_text("x")

        class FakeStat:
            pass  # no st_flags

        with patch("librarian.oplog_lock.os.stat", return_value=FakeStat()):
            assert _is_append_only_macos(f) is None


# --------------------------------------------------------------------------- #
# Linux lsattr parsing                                                         #
# --------------------------------------------------------------------------- #


class TestLinuxDetection:
    def _fake_run(self, stdout: str, returncode: int = 0):
        """Build a subprocess.CompletedProcess stand-in."""
        return subprocess.CompletedProcess(
            args=["lsattr", "-d", "/x"],
            returncode=returncode,
            stdout=stdout,
            stderr="",
        )

    def _run(self, f, stdout, returncode=0, which="/usr/bin/lsattr"):
        with patch("librarian.oplog_lock.shutil.which", return_value=which):
            with patch("librarian.oplog_lock.subprocess.run",
                       return_value=self._fake_run(stdout, returncode)):
                return _is_append_only_linux(f)

    def test_append_flag_detected(self, tmp_path):
        f = tmp_path / "f"; f.write_text("x")
        # Standard lsattr -d output; 'a' is the append-only bit
        out = "-----a-------e------- /tmp/f\n"
        assert self._run(f, out) is True

    def test_append_flag_absent(self, tmp_path):
        f = tmp_path / "f"; f.write_text("x")
        out = "-------------e------- /tmp/f\n"
        assert self._run(f, out) is False

    def test_lsattr_missing_returns_none(self, tmp_path):
        f = tmp_path / "f"; f.write_text("x")
        # shutil.which returns None -> lsattr not on PATH
        assert self._run(f, "", which=None) is None

    def test_lsattr_nonzero_exit_returns_none(self, tmp_path):
        """Overlayfs / unsupported fs returns a non-zero exit; treat as undetectable."""
        f = tmp_path / "f"; f.write_text("x")
        assert self._run(f, "", returncode=1) is None

    def test_lsattr_oserror_returns_none(self, tmp_path):
        f = tmp_path / "f"; f.write_text("x")
        with patch("librarian.oplog_lock.shutil.which", return_value="/usr/bin/lsattr"):
            with patch("librarian.oplog_lock.subprocess.run",
                       side_effect=OSError("broken")):
                assert _is_append_only_linux(f) is None

    def test_lsattr_timeout_returns_none(self, tmp_path):
        f = tmp_path / "f"; f.write_text("x")
        with patch("librarian.oplog_lock.shutil.which", return_value="/usr/bin/lsattr"):
            with patch("librarian.oplog_lock.subprocess.run",
                       side_effect=subprocess.TimeoutExpired(cmd="lsattr", timeout=5)):
                assert _is_append_only_linux(f) is None

    def test_empty_output_returns_none(self, tmp_path):
        f = tmp_path / "f"; f.write_text("x")
        assert self._run(f, "\n\n") is None


# --------------------------------------------------------------------------- #
# Instruction strings                                                          #
# --------------------------------------------------------------------------- #


class TestInstructions:
    def test_lock_macos(self, tmp_path):
        with patch("librarian.oplog_lock.platform_support", return_value="macos"):
            assert lock_instructions(tmp_path / "f").startswith("chflags uappend ")

    def test_lock_linux(self, tmp_path):
        with patch("librarian.oplog_lock.platform_support", return_value="linux"):
            assert lock_instructions(tmp_path / "f").startswith("sudo chattr +a ")

    def test_lock_unsupported(self, tmp_path):
        with patch("librarian.oplog_lock.platform_support", return_value="unsupported"):
            assert "not supported" in lock_instructions(tmp_path / "f")

    def test_unlock_macos(self, tmp_path):
        with patch("librarian.oplog_lock.platform_support", return_value="macos"):
            assert "nouappend" in unlock_instructions(tmp_path / "f")

    def test_unlock_linux(self, tmp_path):
        with patch("librarian.oplog_lock.platform_support", return_value="linux"):
            assert unlock_instructions(tmp_path / "f").startswith("sudo chattr -a ")


# --------------------------------------------------------------------------- #
# Audit report integration                                                     #
# --------------------------------------------------------------------------- #


class TestAuditIntegration:
    def test_auditreport_has_oplog_fields(self):
        from librarian.audit import AuditReport
        r = AuditReport()
        assert hasattr(r, "oplog_locked")
        assert hasattr(r, "oplog_path")
        assert r.oplog_locked is None
        assert r.oplog_path == ""

    def test_audit_populates_oplog_fields(self, tmp_path):
        """A full audit run should always set oplog_path and try to detect state."""
        import yaml
        from librarian.audit import audit
        from librarian.registry import Registry
        (tmp_path / "docs").mkdir()
        reg_path = tmp_path / "docs" / "REGISTRY.yaml"
        reg_path.write_text(yaml.safe_dump({
            "project_config": {"project_name": "t", "tracked_dirs": ["docs/"]},
            "documents": [],
        }))
        reg = Registry.load(reg_path)
        report = audit(reg, tmp_path)
        # oplog_path always populated — matches expected default location
        assert report.oplog_path.endswith("operator/librarian-audit.jsonl")
        # oplog_locked is None when the file doesn't exist (common in tests)
        assert report.oplog_locked in (None, True, False)

    def test_format_report_silent_when_undetectable(self, tmp_path):
        """audit text output stays clean when oplog_locked is None."""
        from librarian.audit import AuditReport, format_report
        r = AuditReport()
        r.oplog_locked = None
        out = format_report(r)
        assert "Oplog lock" not in out

    def test_format_report_shows_enabled(self):
        from librarian.audit import AuditReport, format_report
        r = AuditReport()
        r.oplog_locked = True
        out = format_report(r)
        assert "Oplog lock: ENABLED" in out

    def test_format_report_shows_disabled_with_hint(self):
        from librarian.audit import AuditReport, format_report
        r = AuditReport()
        r.oplog_locked = False
        out = format_report(r)
        assert "Oplog lock: disabled" in out
        assert "librarian-oplog-lock" in out  # actionable hint present


# --------------------------------------------------------------------------- #
# Phase 8.0 hardening — shell-quoting, TOCTOU, debug surfacing                 #
# --------------------------------------------------------------------------- #


class TestShellInjectionQuoting:
    """Phase 8.0 CRITICAL fix — paths are shell-quoted in lock/unlock
    instruction strings. Prior versions interpolated unquoted paths,
    producing copy-pasteable shell-injection vectors.
    """

    def test_lock_macos_quotes_space_path(self, tmp_path):
        evil = tmp_path / "my docs"
        evil.mkdir()
        log = evil / "librarian-audit.jsonl"
        with patch("librarian.oplog_lock.platform_support", return_value="macos"):
            out = lock_instructions(log)
        # The path must be single-quoted; unquoted spaces would make the
        # command parse as multiple tokens.
        assert "'" in out
        assert str(log.resolve()) in out

    def test_lock_macos_quotes_semicolon_path(self, tmp_path):
        """A path with a semicolon must NOT produce a multi-command string."""
        evil = tmp_path / "foo; rm -rf ~"
        evil.mkdir()
        log = evil / "librarian-audit.jsonl"
        with patch("librarian.oplog_lock.platform_support", return_value="macos"):
            out = lock_instructions(log)
        # shlex.quote wraps in single quotes and escapes internal single quotes
        assert "'" in out
        # The semicolon should be INSIDE single quotes, making it inert
        # to shell parsing. A quick sanity check: the literal ``; rm -rf``
        # substring must appear inside a quoted region (between a pair of
        # single quotes).
        import shlex
        # Re-tokenize the instruction and confirm it parses as exactly
        # three args: ``chflags``, ``uappend``, and the path.
        tokens = shlex.split(out)
        assert tokens[0] == "chflags"
        assert tokens[1] == "uappend"
        assert tokens[2] == str(log.resolve())

    def test_lock_linux_quotes_command_substitution(self, tmp_path):
        """Path containing $(...) must be inert after quoting."""
        evil = tmp_path / "pwnd-$(id)"
        evil.mkdir()
        log = evil / "librarian-audit.jsonl"
        with patch("librarian.oplog_lock.platform_support", return_value="linux"):
            out = lock_instructions(log)
        import shlex
        tokens = shlex.split(out)
        # sudo chattr +a <path>
        assert tokens[:3] == ["sudo", "chattr", "+a"]
        assert tokens[3] == str(log.resolve())

    def test_unlock_macos_quotes_backtick_path(self, tmp_path):
        evil = tmp_path / "weird`hostname`"
        evil.mkdir()
        log = evil / "librarian-audit.jsonl"
        with patch("librarian.oplog_lock.platform_support", return_value="macos"):
            out = unlock_instructions(log)
        import shlex
        tokens = shlex.split(out)
        assert tokens[:2] == ["chflags", "nouappend"]
        assert tokens[2] == str(log.resolve())


class TestTOCTOURemoval:
    """Phase 8.0 MED fix — removed pre-stat ``p.exists()`` check.
    Missing-file detection now comes from the probe itself. This
    preserves the None contract without opening a TOCTOU window.
    """

    def test_missing_file_still_returns_none_macos(self, tmp_path):
        """On macOS, os.stat on a nonexistent file raises FileNotFoundError
        (an OSError subclass). The macOS path must catch it and return None
        WITHOUT relying on a prior exists() check."""
        missing = tmp_path / "does-not-exist.jsonl"
        with patch("librarian.oplog_lock.platform_support", return_value="macos"):
            # No patching of os.stat — we actually stat a missing file.
            assert is_append_only(missing) is None

    def test_missing_file_still_returns_none_linux(self, tmp_path):
        """On Linux, lsattr returns non-zero exit for a missing file.
        The Linux path must treat that as None without relying on a
        prior exists() check."""
        missing = tmp_path / "does-not-exist.jsonl"
        with patch("librarian.oplog_lock.platform_support", return_value="linux"):
            # Only patches platform dispatch — lsattr probe runs for real
            # (or returns None if lsattr is absent, which is fine).
            result = is_append_only(missing)
            assert result is None


class TestLibrarianDebugStderr:
    """Phase 8.0 MED fix — lsattr failures surface under LIBRARIAN_DEBUG=1."""

    def test_lsattr_nonzero_silent_by_default(self, tmp_path, capsys, monkeypatch):
        """Default behavior: lsattr errors don't pollute stderr."""
        monkeypatch.delenv("LIBRARIAN_DEBUG", raising=False)
        import subprocess as sp
        fake = sp.CompletedProcess(
            args=["lsattr"], returncode=1, stdout="", stderr="permission denied\n"
        )
        with patch("librarian.oplog_lock.shutil.which", return_value="/usr/bin/lsattr"):
            with patch("librarian.oplog_lock.subprocess.run", return_value=fake):
                result = _is_append_only_linux(tmp_path / "f")
        assert result is None
        captured = capsys.readouterr()
        assert "permission denied" not in captured.err

    def test_lsattr_nonzero_surfaces_stderr_with_debug(
        self, tmp_path, capsys, monkeypatch
    ):
        """With LIBRARIAN_DEBUG=1, lsattr stderr reaches our stderr."""
        monkeypatch.setenv("LIBRARIAN_DEBUG", "1")
        import subprocess as sp
        fake = sp.CompletedProcess(
            args=["lsattr"], returncode=1, stdout="", stderr="permission denied\n"
        )
        with patch("librarian.oplog_lock.shutil.which", return_value="/usr/bin/lsattr"):
            with patch("librarian.oplog_lock.subprocess.run", return_value=fake):
                result = _is_append_only_linux(tmp_path / "f")
        assert result is None
        captured = capsys.readouterr()
        assert "permission denied" in captured.err
        assert "rc=1" in captured.err

    def test_lsattr_oserror_surfaces_with_debug(
        self, tmp_path, capsys, monkeypatch
    ):
        """OSError from subprocess.run also surfaces under debug."""
        monkeypatch.setenv("LIBRARIAN_DEBUG", "1")
        with patch("librarian.oplog_lock.shutil.which", return_value="/usr/bin/lsattr"):
            with patch(
                "librarian.oplog_lock.subprocess.run",
                side_effect=OSError("exec format error"),
            ):
                result = _is_append_only_linux(tmp_path / "f")
        assert result is None
        captured = capsys.readouterr()
        assert "exec format error" in captured.err
