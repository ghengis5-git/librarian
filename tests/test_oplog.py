"""Tests for librarian.oplog — append-only operation log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from librarian.oplog import (
    OpLogEntry,
    append,
    log_operation,
    read_log,
    read_log_since,
    format_log,
)


# ------------------------------------------------------------------ OpLogEntry


class TestOpLogEntry:
    def test_roundtrip_json_line(self) -> None:
        entry = OpLogEntry(
            timestamp="2026-04-11T12:00:00Z",
            operation="register",
            actor="librarian-cli",
            files=["alpha-doc-20260411-V1.0.md"],
            details={"version": "V1.0", "status": "draft"},
            commit_hash="abc1234",
        )
        line = entry.to_json_line()
        restored = OpLogEntry.from_json_line(line)
        assert restored.timestamp == entry.timestamp
        assert restored.operation == entry.operation
        assert restored.actor == entry.actor
        assert restored.files == entry.files
        assert restored.details == entry.details
        assert restored.commit_hash == entry.commit_hash

    def test_to_json_line_is_single_line(self) -> None:
        entry = OpLogEntry(
            timestamp="2026-04-11T12:00:00Z",
            operation="audit",
            actor="test",
        )
        line = entry.to_json_line()
        assert "\n" not in line

    def test_to_json_line_is_valid_json(self) -> None:
        entry = OpLogEntry(
            timestamp="2026-04-11T12:00:00Z",
            operation="bump",
            actor="test",
            files=["a.md", "b.md"],
            details={"major": True},
        )
        parsed = json.loads(entry.to_json_line())
        assert parsed["operation"] == "bump"
        assert parsed["files"] == ["a.md", "b.md"]

    def test_default_fields(self) -> None:
        entry = OpLogEntry(
            timestamp="2026-04-11T12:00:00Z",
            operation="audit",
            actor="test",
        )
        assert entry.files == []
        assert entry.details == {}
        assert entry.commit_hash == ""

    def test_from_json_line_strips_whitespace(self) -> None:
        entry = OpLogEntry(
            timestamp="2026-04-11T12:00:00Z",
            operation="test",
            actor="test",
        )
        line = "  " + entry.to_json_line() + "  \n"
        restored = OpLogEntry.from_json_line(line)
        assert restored.operation == "test"


# ------------------------------------------------------------------ append


class TestAppend:
    def test_creates_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(
            timestamp="2026-04-11T12:00:00Z",
            operation="register",
            actor="test",
        )
        result = append(entry, log_path=log_file)
        assert log_file.exists()
        assert result == log_file.resolve()

    def test_appends_not_overwrites(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        e1 = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="first", actor="a")
        e2 = OpLogEntry(timestamp="2026-04-11T12:01:00Z", operation="second", actor="b")
        append(e1, log_path=log_file)
        append(e2, log_path=log_file)
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["operation"] == "first"
        assert json.loads(lines[1])["operation"] == "second"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        log_file = tmp_path / "deep" / "nested" / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        append(entry, log_path=log_file)
        assert log_file.exists()

    def test_uses_default_path_from_repo_root(self, tmp_path: Path) -> None:
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        result = append(entry, repo_root=tmp_path)
        expected = tmp_path / "operator" / "librarian-audit.jsonl"
        assert expected.exists()
        assert result == expected.resolve()

    def test_raises_without_path_or_root(self) -> None:
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        with pytest.raises(ValueError, match="either log_path or repo_root"):
            append(entry)


# ------------------------------------------------------------------ log_operation


class TestLogOperation:
    def test_creates_entry_and_appends(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entry = log_operation(
            "register",
            actor="test-actor",
            files=["doc.md"],
            details={"version": "V1.0"},
            log_path=log_file,
        )
        assert entry.operation == "register"
        assert entry.actor == "test-actor"
        assert entry.timestamp != ""
        assert log_file.exists()

    def test_default_actor(self, tmp_path: Path) -> None:
        entry = log_operation("audit", log_path=tmp_path / "audit.jsonl")
        assert entry.actor == "librarian-cli"

    def test_timestamp_is_utc_iso(self, tmp_path: Path) -> None:
        entry = log_operation("test", log_path=tmp_path / "audit.jsonl")
        # Format: YYYY-MM-DDTHH:MM:SSZ
        assert entry.timestamp.endswith("Z")
        assert "T" in entry.timestamp
        assert len(entry.timestamp) == 20


# ------------------------------------------------------------------ read_log


class TestReadLog:
    def test_reads_all_entries(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        for i in range(5):
            log_operation(f"op{i}", log_path=log_file)
        entries = read_log(log_file)
        assert len(entries) == 5
        assert entries[0].operation == "op0"
        assert entries[4].operation == "op4"

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        entries = read_log(tmp_path / "nonexistent.jsonl")
        assert entries == []

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        log_file.write_text(entry.to_json_line() + "\n\n\n" + entry.to_json_line() + "\n")
        entries = read_log(log_file)
        assert len(entries) == 2

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        log_file.write_text(
            entry.to_json_line() + "\n"
            + "NOT VALID JSON\n"
            + entry.to_json_line() + "\n"
        )
        entries = read_log(log_file)
        assert len(entries) == 2


# ------------------------------------------------------------------ read_log_since


class TestReadLogSince:
    def test_filters_by_timestamp(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        timestamps = [
            "2026-04-10T10:00:00Z",
            "2026-04-10T15:00:00Z",
            "2026-04-11T08:00:00Z",
            "2026-04-11T12:00:00Z",
        ]
        for ts in timestamps:
            entry = OpLogEntry(timestamp=ts, operation="op", actor="t")
            append(entry, log_path=log_file)

        result = read_log_since(log_file, "2026-04-11T00:00:00Z")
        assert len(result) == 2
        assert result[0].timestamp == "2026-04-11T08:00:00Z"
        assert result[1].timestamp == "2026-04-11T12:00:00Z"

    def test_inclusive_boundary(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="exact", actor="t")
        append(entry, log_path=log_file)
        result = read_log_since(log_file, "2026-04-11T12:00:00Z")
        assert len(result) == 1

    def test_returns_empty_when_all_before(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-10T12:00:00Z", operation="old", actor="t")
        append(entry, log_path=log_file)
        result = read_log_since(log_file, "2026-04-11T00:00:00Z")
        assert result == []


# ------------------------------------------------------------------ format_log


class TestFormatLog:
    def test_empty_log(self) -> None:
        output = format_log([])
        assert "no operations logged" in output

    def test_formats_entries(self) -> None:
        entries = [
            OpLogEntry(
                timestamp="2026-04-11T12:00:00Z",
                operation="register",
                actor="librarian-cli",
                files=["doc.md"],
                details={"version": "V1.0"},
            ),
        ]
        output = format_log(entries)
        assert "2026-04-11T12:00:00Z" in output
        assert "register" in output
        assert "librarian-cli" in output
        assert "doc.md" in output
        assert "version" in output

    def test_includes_commit_hash(self) -> None:
        entries = [
            OpLogEntry(
                timestamp="2026-04-11T12:00:00Z",
                operation="evidence",
                actor="cli",
                commit_hash="abc12345def67890",
            ),
        ]
        output = format_log(entries)
        assert "abc12345" in output
