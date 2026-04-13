"""Manifest generation — portable JSON, SHA-256 cryptographic, and dependency graph.

Three manifest types produced from a single Registry + repo root:

1. **Portable JSON manifest** — full REGISTRY.yaml content as deterministic JSON.
   Enables external tools and CI to consume registry state without YAML parsing.

2. **Cryptographic manifest (SHA-256)** — per-file hash of every registered document
   that exists on disk.  Separate from git SHA-1 because SHA-1 is cryptographically
   weak; SHA-256 is the current legal standard for IP evidence.

3. **Dependency graph** — cross-reference edges extracted from registry entries.
   Each edge is (source_filename, target_filename, sections[]).  Enables impact
   analysis and feeds the dashboard cross-reference visualization.

All outputs are deterministic: sorted keys, stable ordering, no runtime-dependent
values except the generation timestamp.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .registry import Registry


# ------------------------------------------------------------------ data model


@dataclass
class FileHash:
    """SHA-256 hash of a single registered file."""

    filename: str
    sha256: str
    size_bytes: int
    exists: bool


@dataclass
class DependencyEdge:
    """One cross-reference edge: source document references target document."""

    source: str
    target: str
    sections: list[str] = field(default_factory=list)
    status: str = "unknown"  # resolved | pending | unknown


@dataclass
class Manifest:
    """Combined manifest container — all three types in one object."""

    # Metadata
    generated_at: str = ""
    generator_version: str = "0.2.0"
    repo_root: str = ""
    registry_path: str = ""

    # Type 1: portable JSON (registry content)
    registry_snapshot: dict[str, Any] = field(default_factory=dict)

    # Type 2: SHA-256 cryptographic
    file_hashes: list[FileHash] = field(default_factory=list)
    manifest_sha256: str = ""  # hash of the sorted hash list itself

    # Type 3: dependency graph
    dependency_edges: list[DependencyEdge] = field(default_factory=list)

    # Summary counts
    total_registered: int = 0
    total_on_disk: int = 0
    total_hashed: int = 0
    total_edges: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON output."""
        d: dict[str, Any] = {
            "meta": {
                "generated_at": self.generated_at,
                "generator_version": self.generator_version,
                "repo_root": self.repo_root,
                "registry_path": self.registry_path,
            },
            "summary": {
                "total_registered": self.total_registered,
                "total_on_disk": self.total_on_disk,
                "total_hashed": self.total_hashed,
                "total_edges": self.total_edges,
            },
            "registry_snapshot": self.registry_snapshot,
            "file_hashes": [asdict(h) for h in self.file_hashes],
            "manifest_sha256": self.manifest_sha256,
            "dependency_edges": [asdict(e) for e in self.dependency_edges],
        }
        return d

    def to_json(self, indent: int = 2) -> str:
        """Deterministic JSON string (sorted keys)."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)


# ------------------------------------------------------------------ builders


def _hash_file(path: Path) -> FileHash:
    """Compute SHA-256 of a file. Returns FileHash with exists=False if missing."""
    try:
        data = path.read_bytes()
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return FileHash(filename=path.name, sha256="", size_bytes=0, exists=False)
    h = hashlib.sha256(data).hexdigest()
    return FileHash(filename=path.name, sha256=h, size_bytes=len(data), exists=True)


def _resolve_file_path(
    filename: str,
    doc_entry: dict[str, Any],
    repo_root: Path,
    tracked_dirs: list[str],
) -> Path | None:
    """Find the actual file path for a registered filename.

    Checks the explicit ``path`` field first, then walks tracked_dirs.
    Returns None if the file cannot be found.
    """
    # Explicit path in registry entry
    explicit = doc_entry.get("path")
    if explicit:
        candidate = (repo_root / explicit).resolve()
        # Ensure resolved path is within the repo root (prevent traversal)
        try:
            candidate.relative_to(repo_root.resolve())
        except ValueError:
            return None
        if candidate.is_file():
            return candidate

    # Search tracked dirs
    for td in tracked_dirs:
        candidate = repo_root / td / filename
        if candidate.is_file():
            return candidate
        # Also check subdirs (archive/, diagrams/, etc.)
        base = repo_root / td
        if base.is_dir():
            for p in base.rglob(filename):
                if p.is_file():
                    return p

    return None


def _extract_edges(documents: list[dict[str, Any]]) -> list[DependencyEdge]:
    """Extract cross-reference edges from document entries.

    Sources of edges:
    1. ``cross_references`` list — each entry has a target doc and sections
    2. ``supplements`` list — each entry is a filename this doc supplements
    3. ``supersedes`` / ``superseded_by`` — version chain edges
    """
    edges: list[DependencyEdge] = []

    for doc in documents:
        source = doc.get("filename", "")
        if not source:
            continue

        # cross_references → explicit edges
        for xref in doc.get("cross_references") or []:
            if isinstance(xref, dict):
                target = xref.get("doc", xref.get("target", ""))
                sections = xref.get("sections", [])
                status = xref.get("status", "unknown")
                if target:
                    edges.append(DependencyEdge(
                        source=source,
                        target=target,
                        sections=sections if isinstance(sections, list) else [sections],
                        status=status,
                    ))

        # supplements → dependency edges (source supplements target)
        for supp in doc.get("supplements") or []:
            if isinstance(supp, str) and supp:
                edges.append(DependencyEdge(
                    source=source,
                    target=supp,
                    sections=[],
                    status="supplement",
                ))

        # supersedes → version chain edge
        supersedes = doc.get("supersedes")
        if supersedes:
            if isinstance(supersedes, str):
                supersedes = [supersedes]
            for old in supersedes:
                if isinstance(old, str) and old:
                    edges.append(DependencyEdge(
                        source=source,
                        target=old,
                        sections=[],
                        status="supersedes",
                    ))

    # Sort for determinism
    edges.sort(key=lambda e: (e.source, e.target))
    return edges


def _compute_manifest_hash(file_hashes: list[FileHash]) -> str:
    """Compute a single SHA-256 over the sorted hash list.

    This serves as a tamper-evident seal: if any file changes, this hash changes.
    The input is the canonical string ``filename:sha256\\n`` for each file, sorted.
    """
    lines = sorted(f"{h.filename}:{h.sha256}" for h in file_hashes if h.exists)
    combined = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


# ------------------------------------------------------------------ main entry


def generate(
    registry: Registry,
    repo_root: str | Path,
    *,
    include_snapshot: bool = True,
    include_hashes: bool = True,
    include_graph: bool = True,
) -> Manifest:
    """Generate a combined manifest from a Registry and repo root.

    Args:
        registry: loaded Registry instance
        repo_root: path to the project root
        include_snapshot: include the full registry as JSON (Type 1)
        include_hashes: compute SHA-256 hashes (Type 2)
        include_graph: extract dependency edges (Type 3)

    Returns:
        A Manifest dataclass with all requested sections populated.
    """
    repo_root = Path(repo_root).resolve()
    tracked_dirs = registry.tracked_dirs
    documents = registry.documents

    manifest = Manifest(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo_root=str(repo_root),
        registry_path=str(registry.path),
        total_registered=len(documents),
    )

    # Type 1: portable JSON snapshot
    if include_snapshot:
        manifest.registry_snapshot = registry.data

    # Type 2: SHA-256 cryptographic hashes
    if include_hashes:
        on_disk_count = 0
        for doc in documents:
            fname = doc.get("filename", "")
            if not fname:
                continue
            fpath = _resolve_file_path(fname, doc, repo_root, tracked_dirs)
            if fpath:
                fh = _hash_file(fpath)
                on_disk_count += 1
            else:
                fh = FileHash(filename=fname, sha256="", size_bytes=0, exists=False)
            manifest.file_hashes.append(fh)

        # Sort hashes by filename for determinism
        manifest.file_hashes.sort(key=lambda h: h.filename)
        manifest.total_on_disk = on_disk_count
        manifest.total_hashed = sum(1 for h in manifest.file_hashes if h.exists)
        manifest.manifest_sha256 = _compute_manifest_hash(manifest.file_hashes)

    # Type 3: dependency graph
    if include_graph:
        manifest.dependency_edges = _extract_edges(documents)
        manifest.total_edges = len(manifest.dependency_edges)

    return manifest


def write_manifest(manifest: Manifest, output_path: str | Path) -> Path:
    """Write the manifest to a JSON file. Returns the resolved output path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.to_json(), encoding="utf-8")
    return output_path.resolve()
