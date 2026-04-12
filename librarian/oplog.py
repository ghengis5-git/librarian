"""Append-only operation log.

Every librarian action writes a timestamped JSON line to a log file.
Each entry records: who, what, when, files touched, and an optional
git commit hash.

The log file is append-only by design — entries are never modified or
deleted.  This provides a reliable audit trail for all governance
operations.  The evidence pack and diff audit both consume this log.

Format: one JSON object per line (JSONL / newline-delimited JSON).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ data model


@dataclass
class OpLogEntry:
    """A single operation log entry."""

    timestamp: str  # ISO 8601 UTC
    operation: str  # e.g., "register", "bump", "audit", "manifest", "evidence"
    actor: str  # who performed the operation (user or "librarian-cli")
    files: list[str] = field(default_factory=list)  # files touched
    details: dict[str, Any] = field(default_factory=dict)  # operation-specific data
    commit_hash: str = ""  # git commit hash if available

    def to_json_line(self) -> str:
        """Serialize as a single JSON line (no trailing newline)."""
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "OpLogEntry":
        """Deserialize from a single JSON line."""
        d = json.loads(line.strip())
        return cls(**d)


# ------------------------------------------------------------------ log writer


def _default_log_path(repo_root: Path) -> Path:
    """Default oplog location: operator/librarian-audit.jsonl"""
    return repo_root / "operator" / "librarian-audit.jsonl"


def append(
    entry: OpLogEntry,
    log_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> Path:
    """Append an entry to the operation log.

    Args:
        entry: the log entry to append.
        log_path: explicit path to the log file.  If None, uses the
                  default location under repo_root.
        repo_root: project root.  Used to compute the default log path
                   if log_path is not provided.

    Returns:
        The resolved path to the log file.
    """
    if log_path is not None:
        p = Path(log_path)
    elif repo_root is not None:
        p = _default_log_path(Path(repo_root))
    else:
        raise ValueError("either log_path or repo_root must be provided")

    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(entry.to_json_line() + "\n")
    return p.resolve()


def log_operation(
    operation: str,
    *,
    actor: str = "librarian-cli",
    files: list[str] | None = None,
    details: dict[str, Any] | None = None,
    commit_hash: str = "",
    log_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> OpLogEntry:
    """Convenience function: create an entry and append it in one call.

    Returns the created OpLogEntry.
    """
    entry = OpLogEntry(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        operation=operation,
        actor=actor,
        files=files or [],
        details=details or {},
        commit_hash=commit_hash,
    )
    append(entry, log_path=log_path, repo_root=repo_root)
    return entry


# ------------------------------------------------------------------ log reader


def read_log(log_path: str | Path) -> list[OpLogEntry]:
    """Read all entries from an operation log file.

    Returns entries in chronological order (oldest first).
    Skips blank lines and lines that fail to parse (logged to stderr).
    """
    p = Path(log_path)
    if not p.exists():
        return []

    entries: list[OpLogEntry] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(OpLogEntry.from_json_line(line))
        except (json.JSONDecodeError, TypeError, KeyError):
            import sys
            print(f"oplog: skipping malformed line: {line[:80]}...", file=sys.stderr)
    return entries


def read_log_since(
    log_path: str | Path,
    since: str,
) -> list[OpLogEntry]:
    """Read log entries from a given ISO timestamp onward (inclusive).

    Args:
        log_path: path to the log file.
        since: ISO 8601 timestamp string (e.g., "2026-04-11T00:00:00Z").

    Returns:
        Entries with timestamp >= since, in chronological order.
    """
    all_entries = read_log(log_path)
    return [e for e in all_entries if e.timestamp >= since]


def format_log(entries: list[OpLogEntry]) -> str:
    """Format log entries as a human-readable report."""
    if not entries:
        return "  (no operations logged)"

    lines: list[str] = []
    for e in entries:
        files_str = ", ".join(e.files) if e.files else "(none)"
        commit_str = f" [{e.commit_hash[:8]}]" if e.commit_hash else ""
        lines.append(f"  {e.timestamp}  {e.operation:<12} {e.actor}{commit_str}")
        if e.files:
            lines.append(f"    files: {files_str}")
        if e.details:
            for k, v in e.details.items():
                lines.append(f"    {k}: {v}")
    return "\n".join(lines)
