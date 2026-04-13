"""Append-only operation log with optional hash chaining.

Every librarian action writes a timestamped JSON line to a log file.
Each entry records: who, what, when, files touched, and an optional
git commit hash.

The log file is append-only by design — entries are never modified or
deleted.  This provides a reliable audit trail for all governance
operations.  The evidence pack and diff audit both consume this log.

**Hash chaining** (v2 format): when enabled, each entry includes a
``prev_hash`` field containing the SHA-256 hash of the previous entry's
JSON line.  The first entry uses the sentinel ``"genesis"``.  This makes
deletion, reordering, or modification of any entry detectable by walking
the chain and verifying each link.

Format: one JSON object per line (JSONL / newline-delimited JSON).
"""

from __future__ import annotations

import fcntl
import hashlib
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
    prev_hash: str = ""  # SHA-256 of previous entry's JSON line (hash chaining)

    def to_json_line(self) -> str:
        """Serialize as a single JSON line (no trailing newline)."""
        d = asdict(self)
        # Omit prev_hash when empty to stay backward-compatible with v1 logs
        if not d.get("prev_hash"):
            d.pop("prev_hash", None)
        return json.dumps(d, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "OpLogEntry":
        """Deserialize from a single JSON line."""
        d = json.loads(line.strip())
        # Handle v1 entries that lack prev_hash
        if "prev_hash" not in d:
            d["prev_hash"] = ""
        return cls(**d)


# ------------------------------------------------------------------ hashing


def _hash_line(line: str) -> str:
    """SHA-256 hash of a single JSON line (stripped of whitespace)."""
    return hashlib.sha256(line.strip().encode("utf-8")).hexdigest()


_GENESIS_SENTINEL = "genesis"


def _read_last_line(path: Path) -> str:
    """Read the last non-empty line from a file. Returns '' if empty/missing."""
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except (PermissionError, OSError):
        return ""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


# ------------------------------------------------------------------ log writer


def _default_log_path(repo_root: Path) -> Path:
    """Default oplog location: operator/librarian-audit.jsonl"""
    return repo_root / "operator" / "librarian-audit.jsonl"


def append(
    entry: OpLogEntry,
    log_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    *,
    chain: bool = False,
) -> Path:
    """Append an entry to the operation log.

    Args:
        entry: the log entry to append.
        log_path: explicit path to the log file.  If None, uses the
                  default location under repo_root.
        repo_root: project root.  Used to compute the default log path
                   if log_path is not provided.
        chain: if True, compute and set ``prev_hash`` from the last
               existing entry (hash chaining).  Default False for
               backward compatibility.

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

    # Use file locking for write exclusivity
    with p.open("a", encoding="utf-8") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        except OSError:
            pass  # Fallback: proceed without lock (e.g., unsupported FS)

        if chain:
            last_line = _read_last_line(p)
            if last_line:
                entry.prev_hash = _hash_line(last_line)
            else:
                entry.prev_hash = _GENESIS_SENTINEL

        f.write(entry.to_json_line() + "\n")
        f.flush()
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
    chain: bool = False,
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
    append(entry, log_path=log_path, repo_root=repo_root, chain=chain)
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


# ------------------------------------------------------------------ chain verify


def verify_chain(log_path: str | Path) -> dict[str, Any]:
    """Verify the hash chain integrity of an operation log.

    Returns a dict with:
        valid: bool — True if the chain is intact
        total_entries: int — total entries in the log
        chained_entries: int — entries with prev_hash set
        first_broken_index: int | None — index of the first broken link
        error: str — description if invalid, empty if valid
    """
    p = Path(log_path)
    if not p.exists():
        return {
            "valid": True,
            "total_entries": 0,
            "chained_entries": 0,
            "first_broken_index": None,
            "error": "",
        }

    lines: list[str] = []
    for raw_line in p.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped:
            lines.append(stripped)

    if not lines:
        return {
            "valid": True,
            "total_entries": 0,
            "chained_entries": 0,
            "first_broken_index": None,
            "error": "",
        }

    entries: list[OpLogEntry] = []
    for line in lines:
        try:
            entries.append(OpLogEntry.from_json_line(line))
        except (json.JSONDecodeError, TypeError, KeyError):
            pass  # skip malformed

    chained = sum(1 for e in entries if e.prev_hash)
    if chained == 0:
        # v1 log — no chain to verify
        return {
            "valid": True,
            "total_entries": len(entries),
            "chained_entries": 0,
            "first_broken_index": None,
            "error": "",
        }

    # Verify chain
    for i, entry in enumerate(entries):
        if not entry.prev_hash:
            continue  # skip v1 entries at the start

        if i == 0:
            # First chained entry should have genesis sentinel
            if entry.prev_hash != _GENESIS_SENTINEL:
                return {
                    "valid": False,
                    "total_entries": len(entries),
                    "chained_entries": chained,
                    "first_broken_index": i,
                    "error": f"Entry {i}: expected genesis sentinel, got {entry.prev_hash[:16]}...",
                }
        else:
            expected_hash = _hash_line(lines[i - 1])
            if entry.prev_hash != expected_hash:
                return {
                    "valid": False,
                    "total_entries": len(entries),
                    "chained_entries": chained,
                    "first_broken_index": i,
                    "error": f"Entry {i}: prev_hash mismatch (expected {expected_hash[:16]}..., got {entry.prev_hash[:16]}...)",
                }

    return {
        "valid": True,
        "total_entries": len(entries),
        "chained_entries": chained,
        "first_broken_index": None,
        "error": "",
    }


def format_log(entries: list[OpLogEntry]) -> str:
    """Format log entries as a human-readable report."""
    if not entries:
        return "  (no operations logged)"

    lines: list[str] = []
    for e in entries:
        files_str = ", ".join(e.files) if e.files else "(none)"
        commit_str = f" [{e.commit_hash[:8]}]" if e.commit_hash else ""
        chain_str = " \u26d3" if e.prev_hash else ""  # chain link emoji
        lines.append(f"  {e.timestamp}  {e.operation:<12} {e.actor}{commit_str}{chain_str}")
        if e.files:
            lines.append(f"    files: {files_str}")
        if e.details:
            for k, v in e.details.items():
                lines.append(f"    {k}: {v}")
    return "\n".join(lines)
