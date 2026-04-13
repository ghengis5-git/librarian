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
    verify_chain,
    _hash_line,
    _GENESIS_SENTINEL,
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

    def test_shows_chain_indicator(self) -> None:
        entries = [
            OpLogEntry(
                timestamp="2026-04-11T12:00:00Z",
                operation="test",
                actor="cli",
                prev_hash="genesis",
            ),
        ]
        output = format_log(entries)
        assert "\u26d3" in output  # chain link symbol


# ------------------------------------------------------------------ hash chaining


class TestHashChaining:
    def test_chain_flag_adds_genesis(self, tmp_path: Path) -> None:
        """First chained entry gets 'genesis' as prev_hash."""
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="first", actor="t")
        append(entry, log_path=log_file, chain=True)
        entries = read_log(log_file)
        assert entries[0].prev_hash == _GENESIS_SENTINEL

    def test_chain_links_entries(self, tmp_path: Path) -> None:
        """Second chained entry's prev_hash matches hash of first entry."""
        log_file = tmp_path / "audit.jsonl"
        e1 = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="first", actor="a")
        append(e1, log_path=log_file, chain=True)

        e2 = OpLogEntry(timestamp="2026-04-11T12:01:00Z", operation="second", actor="b")
        append(e2, log_path=log_file, chain=True)

        lines = log_file.read_text().strip().splitlines()
        entries = read_log(log_file)

        # Second entry's prev_hash should be SHA-256 of first line
        expected = _hash_line(lines[0])
        assert entries[1].prev_hash == expected

    def test_chain_three_entries(self, tmp_path: Path) -> None:
        """Three chained entries form a valid chain."""
        log_file = tmp_path / "audit.jsonl"
        for i in range(3):
            e = OpLogEntry(timestamp=f"2026-04-11T12:0{i}:00Z", operation=f"op{i}", actor="t")
            append(e, log_path=log_file, chain=True)

        result = verify_chain(log_file)
        assert result["valid"] is True
        assert result["chained_entries"] == 3
        assert result["total_entries"] == 3

    def test_no_chain_flag_omits_prev_hash(self, tmp_path: Path) -> None:
        """Without chain=True, entries have no prev_hash (v1 compat)."""
        log_file = tmp_path / "audit.jsonl"
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        append(entry, log_path=log_file)
        entries = read_log(log_file)
        assert entries[0].prev_hash == ""

    def test_prev_hash_not_in_v1_json(self, tmp_path: Path) -> None:
        """v1 entries (no chain) should not include prev_hash in JSON."""
        entry = OpLogEntry(timestamp="2026-04-11T12:00:00Z", operation="test", actor="t")
        line = entry.to_json_line()
        parsed = json.loads(line)
        assert "prev_hash" not in parsed

    def test_log_operation_with_chain(self, tmp_path: Path) -> None:
        """log_operation convenience function passes chain flag through."""
        log_file = tmp_path / "audit.jsonl"
        entry = log_operation("test", log_path=log_file, chain=True)
        assert entry.prev_hash == _GENESIS_SENTINEL


# ------------------------------------------------------------------ verify_chain


class TestVerifyChain:
    def test_empty_log_valid(self, tmp_path: Path) -> None:
        result = verify_chain(tmp_path / "nonexistent.jsonl")
        assert result["valid"] is True
        assert result["total_entries"] == 0

    def test_v1_log_valid(self, tmp_path: Path) -> None:
        """v1 logs (no chaining) are considered valid."""
        log_file = tmp_path / "audit.jsonl"
        for i in range(3):
            e = OpLogEntry(timestamp=f"2026-04-11T12:0{i}:00Z", operation=f"op{i}", actor="t")
            append(e, log_path=log_file)  # no chain
        result = verify_chain(log_file)
        assert result["valid"] is True
        assert result["chained_entries"] == 0

    def test_valid_chain(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit.jsonl"
        for i in range(5):
            e = OpLogEntry(timestamp=f"2026-04-11T12:0{i}:00Z", operation=f"op{i}", actor="t")
            append(e, log_path=log_file, chain=True)
        result = verify_chain(log_file)
        assert result["valid"] is True
        assert result["chained_entries"] == 5
        assert result["first_broken_index"] is None
        assert result["error"] == ""

    def test_tampered_entry_detected(self, tmp_path: Path) -> None:
        """Modifying an entry breaks the chain."""
        log_file = tmp_path / "audit.jsonl"
        for i in range(3):
            e = OpLogEntry(timestamp=f"2026-04-11T12:0{i}:00Z", operation=f"op{i}", actor="t")
            append(e, log_path=log_file, chain=True)

        # Tamper with the first entry
        lines = log_file.read_text().splitlines()
        tampered = json.loads(lines[0])
        tampered["operation"] = "TAMPERED"
        lines[0] = json.dumps(tampered, sort_keys=True)
        log_file.write_text("\n".join(lines) + "\n")

        result = verify_chain(log_file)
        assert result["valid"] is False
        assert result["first_broken_index"] is not None
        assert "mismatch" in result["error"]

    def test_deleted_entry_detected(self, tmp_path: Path) -> None:
        """Deleting an entry breaks the chain."""
        log_file = tmp_path / "audit.jsonl"
        for i in range(4):
            e = OpLogEntry(timestamp=f"2026-04-11T12:0{i}:00Z", operation=f"op{i}", actor="t")
            append(e, log_path=log_file, chain=True)

        # Delete the second entry
        lines = log_file.read_text().strip().splitlines()
        del lines[1]
        log_file.write_text("\n".join(lines) + "\n")

        result = verify_chain(log_file)
        assert result["valid"] is False
