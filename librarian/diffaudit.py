"""Diff audit — delta report between two manifests.

Compares two manifest JSON files (or Manifest objects) and produces a
structured report of what changed: added documents, removed documents,
modified files (SHA-256 changed), and edge changes in the dependency graph.

Primary use case: "what changed since last session?"
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ data model


@dataclass
class DiffReport:
    """Structured diff between two manifests."""

    # Identity
    old_generated_at: str = ""
    new_generated_at: str = ""

    # Document changes
    added: list[str] = field(default_factory=list)  # filenames in new but not old
    removed: list[str] = field(default_factory=list)  # filenames in old but not new
    modified: list[dict[str, str]] = field(default_factory=list)  # SHA-256 changed

    # Edge changes
    edges_added: list[dict[str, str]] = field(default_factory=list)
    edges_removed: list[dict[str, str]] = field(default_factory=list)

    # Summary
    seal_changed: bool = False
    old_seal: str = ""
    new_seal: str = ""

    @property
    def has_changes(self) -> bool:
        return bool(
            self.added or self.removed or self.modified
            or self.edges_added or self.edges_removed
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "diff": {
                "old_generated_at": self.old_generated_at,
                "new_generated_at": self.new_generated_at,
                "seal_changed": self.seal_changed,
                "old_seal": self.old_seal,
                "new_seal": self.new_seal,
            },
            "documents": {
                "added": self.added,
                "removed": self.removed,
                "modified": self.modified,
            },
            "edges": {
                "added": self.edges_added,
                "removed": self.edges_removed,
            },
            "summary": {
                "total_added": len(self.added),
                "total_removed": len(self.removed),
                "total_modified": len(self.modified),
                "total_edges_added": len(self.edges_added),
                "total_edges_removed": len(self.edges_removed),
                "has_changes": self.has_changes,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)


# ------------------------------------------------------------------ differ


def _load_manifest(source: str | Path | dict) -> dict[str, Any]:
    """Load a manifest from a file path or dict."""
    if isinstance(source, dict):
        return source
    p = Path(source)
    return json.loads(p.read_text(encoding="utf-8"))


def _hash_map(manifest: dict[str, Any]) -> dict[str, str]:
    """Build filename -> sha256 map from file_hashes array."""
    result: dict[str, str] = {}
    for h in manifest.get("file_hashes", []):
        if h.get("exists"):
            result[h["filename"]] = h["sha256"]
    return result


def _edge_set(manifest: dict[str, Any]) -> set[tuple[str, str, str]]:
    """Build a set of (source, target, status) tuples from dependency_edges."""
    edges: set[tuple[str, str, str]] = set()
    for e in manifest.get("dependency_edges", []):
        edges.add((e["source"], e["target"], e.get("status", "unknown")))
    return edges


def diff_manifests(
    old: str | Path | dict,
    new: str | Path | dict,
) -> DiffReport:
    """Compare two manifests and produce a DiffReport.

    Args:
        old: the baseline manifest (file path or dict)
        new: the current manifest (file path or dict)

    Returns:
        A DiffReport with all changes enumerated.
    """
    old_data = _load_manifest(old)
    new_data = _load_manifest(new)

    report = DiffReport(
        old_generated_at=old_data.get("meta", {}).get("generated_at", ""),
        new_generated_at=new_data.get("meta", {}).get("generated_at", ""),
        old_seal=old_data.get("manifest_sha256", ""),
        new_seal=new_data.get("manifest_sha256", ""),
    )
    report.seal_changed = report.old_seal != report.new_seal

    # Document diff by SHA-256
    old_hashes = _hash_map(old_data)
    new_hashes = _hash_map(new_data)

    old_files = set(old_hashes.keys())
    new_files = set(new_hashes.keys())

    report.added = sorted(new_files - old_files)
    report.removed = sorted(old_files - new_files)

    for fname in sorted(old_files & new_files):
        if old_hashes[fname] != new_hashes[fname]:
            report.modified.append({
                "filename": fname,
                "old_sha256": old_hashes[fname],
                "new_sha256": new_hashes[fname],
            })

    # Edge diff
    old_edges = _edge_set(old_data)
    new_edges = _edge_set(new_data)

    for src, tgt, status in sorted(new_edges - old_edges):
        report.edges_added.append({"source": src, "target": tgt, "status": status})

    for src, tgt, status in sorted(old_edges - new_edges):
        report.edges_removed.append({"source": src, "target": tgt, "status": status})

    return report


def format_diff(report: DiffReport) -> str:
    """Format a DiffReport as a human-readable string."""
    lines: list[str] = []
    bar = "=" * 55
    lines.append(bar)
    lines.append("  Librarian Diff Audit")
    lines.append(bar)
    lines.append("")
    lines.append(f"  Old: {report.old_generated_at}")
    lines.append(f"  New: {report.new_generated_at}")
    lines.append(f"  Seal changed: {'YES' if report.seal_changed else 'no'}")
    lines.append("")

    if report.added:
        lines.append(f"-- Added ({len(report.added)}) --")
        for f in report.added:
            lines.append(f"  + {f}")
        lines.append("")

    if report.removed:
        lines.append(f"-- Removed ({len(report.removed)}) --")
        for f in report.removed:
            lines.append(f"  - {f}")
        lines.append("")

    if report.modified:
        lines.append(f"-- Modified ({len(report.modified)}) --")
        for m in report.modified:
            lines.append(f"  ~ {m['filename']}")
        lines.append("")

    if report.edges_added:
        lines.append(f"-- Edges added ({len(report.edges_added)}) --")
        for e in report.edges_added:
            lines.append(f"  + {e['source']} -> {e['target']} ({e['status']})")
        lines.append("")

    if report.edges_removed:
        lines.append(f"-- Edges removed ({len(report.edges_removed)}) --")
        for e in report.edges_removed:
            lines.append(f"  - {e['source']} -> {e['target']} ({e['status']})")
        lines.append("")

    if not report.has_changes:
        lines.append("  No changes detected.")

    lines.append(bar)
    return "\n".join(lines)
