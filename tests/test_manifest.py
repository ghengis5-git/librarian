"""Tests for librarian.manifest — portable JSON, SHA-256, and dependency graph."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from librarian.manifest import (
    DependencyEdge,
    FileHash,
    Manifest,
    generate,
    write_manifest,
    _hash_file,
    _extract_edges,
    _compute_manifest_hash,
    _resolve_file_path,
)
from librarian.registry import Registry


# ------------------------------------------------------------------ fixtures


MANIFEST_REGISTRY = {
    "project_config": {
        "project_name": "Manifest Test Project",
        "default_author": "Test Author",
        "default_classification": "INTERNAL",
        "tracked_dirs": ["docs/"],
        "naming_rules": {
            "infrastructure_exempt": ["REGISTRY.yaml", "README.md"],
        },
    },
    "documents": [
        {
            "filename": "alpha-doc-20260101-V1.0.md",
            "title": "Alpha Document",
            "description": "First test doc",
            "status": "active",
            "version": "V1.0",
            "path": "docs/alpha-doc-20260101-V1.0.md",
            "supplements": ["beta-doc-20260101-V1.0.md"],
            "cross_references": [
                {
                    "doc": "gamma-doc-20260101-V1.0.md",
                    "sections": ["Section 1.1", "Section 2.3"],
                    "status": "resolved",
                },
            ],
        },
        {
            "filename": "beta-doc-20260101-V1.0.md",
            "title": "Beta Document",
            "description": "Second test doc",
            "status": "active",
            "version": "V1.0",
            "path": "docs/beta-doc-20260101-V1.0.md",
            "supplements": [],
            "cross_references": [],
        },
        {
            "filename": "gamma-doc-20260101-V1.0.md",
            "title": "Gamma Document",
            "description": "Third test doc — superseded",
            "status": "superseded",
            "version": "V1.0",
            "path": "docs/gamma-doc-20260101-V1.0.md",
            "superseded_by": "gamma-doc-20260201-V1.1.md",
        },
        {
            "filename": "gamma-doc-20260201-V1.1.md",
            "title": "Gamma Document",
            "description": "Third test doc — current",
            "status": "active",
            "version": "V1.1",
            "path": "docs/gamma-doc-20260201-V1.1.md",
            "supersedes": "gamma-doc-20260101-V1.0.md",
        },
    ],
    "registry_meta": {
        "total_documents": 4,
        "active": 3,
        "superseded": 1,
    },
}


@pytest.fixture
def manifest_repo(tmp_path: Path) -> Path:
    """Create a temp repo with 3 active docs (gamma V1.0 is superseded, file absent)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    reg_path = docs / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(MANIFEST_REGISTRY, f, sort_keys=False)

    (docs / "alpha-doc-20260101-V1.0.md").write_text("# Alpha\nContent here.\n")
    (docs / "beta-doc-20260101-V1.0.md").write_text("# Beta\nMore content.\n")
    # gamma V1.0 intentionally absent (superseded)
    (docs / "gamma-doc-20260201-V1.1.md").write_text("# Gamma V1.1\nUpdated.\n")

    return tmp_path


@pytest.fixture
def manifest_registry(manifest_repo: Path) -> Registry:
    return Registry.load(manifest_repo / "docs" / "REGISTRY.yaml")


# ------------------------------------------------- Type 2: SHA-256 hash tests


class TestFileHash:
    def test_hash_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        content = b"hello world"
        f.write_bytes(content)
        fh = _hash_file(f)
        assert fh.exists is True
        assert fh.sha256 == hashlib.sha256(content).hexdigest()
        assert fh.size_bytes == len(content)
        assert fh.filename == "test.md"

    def test_hash_missing_file(self, tmp_path: Path) -> None:
        fh = _hash_file(tmp_path / "nonexistent.md")
        assert fh.exists is False
        assert fh.sha256 == ""
        assert fh.size_bytes == 0

    def test_hash_deterministic(self, tmp_path: Path) -> None:
        f = tmp_path / "det.md"
        f.write_text("deterministic content")
        h1 = _hash_file(f)
        h2 = _hash_file(f)
        assert h1.sha256 == h2.sha256


# ---------------------------------------------- Type 3: dependency graph tests


class TestDependencyEdges:
    def test_cross_reference_edges(self) -> None:
        docs = MANIFEST_REGISTRY["documents"]
        edges = _extract_edges(docs)
        xref_edges = [e for e in edges if e.status == "resolved"]
        assert len(xref_edges) == 1
        assert xref_edges[0].source == "alpha-doc-20260101-V1.0.md"
        assert xref_edges[0].target == "gamma-doc-20260101-V1.0.md"
        assert "Section 1.1" in xref_edges[0].sections

    def test_supplement_edges(self) -> None:
        docs = MANIFEST_REGISTRY["documents"]
        edges = _extract_edges(docs)
        supp_edges = [e for e in edges if e.status == "supplement"]
        assert len(supp_edges) == 1
        assert supp_edges[0].source == "alpha-doc-20260101-V1.0.md"
        assert supp_edges[0].target == "beta-doc-20260101-V1.0.md"

    def test_supersedes_edges(self) -> None:
        docs = MANIFEST_REGISTRY["documents"]
        edges = _extract_edges(docs)
        sup_edges = [e for e in edges if e.status == "supersedes"]
        assert len(sup_edges) == 1
        assert sup_edges[0].source == "gamma-doc-20260201-V1.1.md"
        assert sup_edges[0].target == "gamma-doc-20260101-V1.0.md"

    def test_edges_sorted(self) -> None:
        docs = MANIFEST_REGISTRY["documents"]
        edges = _extract_edges(docs)
        sources = [e.source for e in edges]
        assert sources == sorted(sources) or all(
            (edges[i].source, edges[i].target) <= (edges[i + 1].source, edges[i + 1].target)
            for i in range(len(edges) - 1)
        )

    def test_empty_docs_no_edges(self) -> None:
        assert _extract_edges([]) == []


# ---------------------------------------- Manifest hash (tamper-evident seal)


class TestManifestHash:
    def test_deterministic(self) -> None:
        hashes = [
            FileHash("b.md", "bbbb", 10, True),
            FileHash("a.md", "aaaa", 5, True),
        ]
        h1 = _compute_manifest_hash(hashes)
        h2 = _compute_manifest_hash(hashes)
        assert h1 == h2

    def test_excludes_missing(self) -> None:
        hashes = [
            FileHash("a.md", "aaaa", 5, True),
            FileHash("b.md", "", 0, False),
        ]
        h_with = _compute_manifest_hash(hashes)
        hashes_only = [FileHash("a.md", "aaaa", 5, True)]
        h_without = _compute_manifest_hash(hashes_only)
        assert h_with == h_without

    def test_order_independent(self) -> None:
        h1 = [FileHash("a.md", "aaa", 1, True), FileHash("b.md", "bbb", 2, True)]
        h2 = [FileHash("b.md", "bbb", 2, True), FileHash("a.md", "aaa", 1, True)]
        assert _compute_manifest_hash(h1) == _compute_manifest_hash(h2)


# ------------------------------------------- Full generate() integration tests


class TestGenerate:
    def test_full_manifest(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        assert m.total_registered == 4
        assert m.total_hashed == 3  # gamma V1.0 is missing on disk
        assert m.total_on_disk == 3
        assert m.total_edges > 0
        assert m.manifest_sha256 != ""

    def test_hashes_for_existing_files(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        existing = [h for h in m.file_hashes if h.exists]
        assert len(existing) == 3
        for h in existing:
            assert len(h.sha256) == 64  # SHA-256 hex length
            assert h.size_bytes > 0

    def test_missing_file_hash(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        missing = [h for h in m.file_hashes if not h.exists]
        assert len(missing) == 1
        assert missing[0].filename == "gamma-doc-20260101-V1.0.md"

    def test_snapshot_includes_registry(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        assert "documents" in m.registry_snapshot
        assert "project_config" in m.registry_snapshot

    def test_no_snapshot_flag(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo, include_snapshot=False)
        assert m.registry_snapshot == {}

    def test_no_hashes_flag(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo, include_hashes=False)
        assert m.file_hashes == []
        assert m.manifest_sha256 == ""

    def test_no_graph_flag(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo, include_graph=False)
        assert m.dependency_edges == []
        assert m.total_edges == 0


# ----------------------------------------------- Serialization tests


class TestSerialization:
    def test_to_json_valid(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        j = m.to_json()
        parsed = json.loads(j)
        assert "meta" in parsed
        assert "summary" in parsed
        assert "file_hashes" in parsed
        assert "dependency_edges" in parsed

    def test_to_json_sorted_keys(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        j = m.to_json()
        parsed = json.loads(j)
        top_keys = list(parsed.keys())
        assert top_keys == sorted(top_keys)

    def test_to_json_deterministic(self, manifest_registry: Registry, manifest_repo: Path) -> None:
        m1 = generate(manifest_registry, manifest_repo)
        m2 = generate(manifest_registry, manifest_repo)
        # Timestamps will differ; zero them for comparison
        j1 = json.loads(m1.to_json())
        j2 = json.loads(m2.to_json())
        j1["meta"]["generated_at"] = ""
        j2["meta"]["generated_at"] = ""
        assert j1 == j2


# ----------------------------------------------- write_manifest tests


class TestWriteManifest:
    def test_write_creates_file(self, manifest_registry: Registry, manifest_repo: Path, tmp_path: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        out = tmp_path / "output" / "manifest.json"
        result = write_manifest(m, out)
        assert result.exists()
        parsed = json.loads(out.read_text())
        assert parsed["summary"]["total_registered"] == 4

    def test_write_creates_parent_dirs(self, manifest_registry: Registry, manifest_repo: Path, tmp_path: Path) -> None:
        m = generate(manifest_registry, manifest_repo)
        deep = tmp_path / "a" / "b" / "c" / "manifest.json"
        write_manifest(m, deep)
        assert deep.exists()


# ----------------------------------------------- File resolution tests


class TestResolveFilePath:
    def test_explicit_path(self, manifest_repo: Path) -> None:
        doc = {"path": "docs/alpha-doc-20260101-V1.0.md"}
        result = _resolve_file_path("alpha-doc-20260101-V1.0.md", doc, manifest_repo, ["docs/"])
        assert result is not None
        assert result.name == "alpha-doc-20260101-V1.0.md"

    def test_search_tracked_dirs(self, manifest_repo: Path) -> None:
        doc = {}  # no explicit path
        result = _resolve_file_path("beta-doc-20260101-V1.0.md", doc, manifest_repo, ["docs/"])
        assert result is not None
        assert result.name == "beta-doc-20260101-V1.0.md"

    def test_missing_file_returns_none(self, manifest_repo: Path) -> None:
        doc = {}
        result = _resolve_file_path("nonexistent-20260101-V1.0.md", doc, manifest_repo, ["docs/"])
        assert result is None

    def test_path_traversal_blocked(self, manifest_repo: Path) -> None:
        """Registry path field with ../ must not escape repo root."""
        doc = {"path": "../../etc/passwd"}
        result = _resolve_file_path("passwd", doc, manifest_repo, ["docs/"])
        assert result is None

    def test_hash_file_missing_no_crash(self, manifest_repo: Path) -> None:
        """_hash_file on nonexistent path returns exists=False, no exception."""
        from librarian.manifest import _hash_file
        fh = _hash_file(manifest_repo / "no-such-file.md")
        assert fh.exists is False
        assert fh.sha256 == ""

    def test_hash_file_permission_error(self, tmp_path: Path) -> None:
        """_hash_file on unreadable file returns exists=False."""
        import os
        from librarian.manifest import _hash_file
        f = tmp_path / "locked.md"
        f.write_text("secret")
        os.chmod(f, 0o000)
        fh = _hash_file(f)
        # Restore permissions for cleanup
        os.chmod(f, 0o644)
        assert fh.exists is False
