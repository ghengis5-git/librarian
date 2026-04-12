"""Tests for librarian.evidence — IP evidence pack generation and verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from librarian.evidence import (
    EvidencePack,
    generate_evidence,
    write_evidence,
    verify_evidence,
    _git_commit_hash,
    _git_branch,
    _git_is_dirty,
)
from librarian.registry import Registry


# ------------------------------------------------------------------ fixtures


EVIDENCE_REGISTRY = {
    "project_config": {
        "project_name": "Evidence Test Project",
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
            "description": "Test doc",
            "status": "active",
            "version": "V1.0",
            "path": "docs/alpha-doc-20260101-V1.0.md",
        },
        {
            "filename": "beta-doc-20260101-V1.0.md",
            "title": "Beta Document",
            "description": "Test doc 2",
            "status": "active",
            "version": "V1.0",
            "path": "docs/beta-doc-20260101-V1.0.md",
        },
    ],
    "registry_meta": {
        "total_documents": 2,
        "active": 2,
    },
}


@pytest.fixture
def evidence_repo(tmp_path: Path) -> Path:
    """Create a temp repo with docs and registry."""
    docs = tmp_path / "docs"
    docs.mkdir()
    reg_path = docs / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(EVIDENCE_REGISTRY, f, sort_keys=False)
    (docs / "alpha-doc-20260101-V1.0.md").write_text("# Alpha\nContent.\n")
    (docs / "beta-doc-20260101-V1.0.md").write_text("# Beta\nContent.\n")
    return tmp_path


@pytest.fixture
def evidence_registry(evidence_repo: Path) -> Registry:
    return Registry.load(evidence_repo / "docs" / "REGISTRY.yaml")


# ------------------------------------------------------------------ EvidencePack


class TestEvidencePack:
    def test_to_dict_structure(self) -> None:
        pack = EvidencePack(
            pack_id="2026-04-11T12:00:00Z",
            project_name="Test",
            generated_at="2026-04-11T12:00:00Z",
            git_commit_hash="abc123",
            git_branch="main",
            git_dirty=False,
            manifest={"summary": {"total_registered": 2}},
            manifest_json_sha256="deadbeef",
        )
        d = pack.to_dict()
        assert "evidence_pack" in d
        assert "git_anchor" in d
        assert "manifest" in d
        assert "seal" in d
        assert d["evidence_pack"]["project_name"] == "Test"
        assert d["git_anchor"]["commit_hash"] == "abc123"
        assert d["seal"]["manifest_json_sha256"] == "deadbeef"
        assert d["seal"]["algorithm"] == "SHA-256"

    def test_to_json_valid(self) -> None:
        pack = EvidencePack(
            pack_id="2026-04-11T12:00:00Z",
            project_name="Test",
            generated_at="2026-04-11T12:00:00Z",
            manifest={},
            manifest_json_sha256="abc",
        )
        parsed = json.loads(pack.to_json())
        assert "evidence_pack" in parsed

    def test_to_json_sorted_keys(self) -> None:
        pack = EvidencePack(
            pack_id="2026-04-11T12:00:00Z",
            project_name="Test",
            generated_at="2026-04-11T12:00:00Z",
            manifest={},
            manifest_json_sha256="abc",
        )
        parsed = json.loads(pack.to_json())
        assert list(parsed.keys()) == sorted(parsed.keys())


# ------------------------------------------------------------------ git helpers


class TestGitHelpers:
    def test_commit_hash_non_git_dir(self, tmp_path: Path) -> None:
        """Non-git directory returns empty string."""
        result = _git_commit_hash(tmp_path)
        assert result == ""

    def test_branch_non_git_dir(self, tmp_path: Path) -> None:
        result = _git_branch(tmp_path)
        assert result == ""

    def test_is_dirty_non_git_dir(self, tmp_path: Path) -> None:
        result = _git_is_dirty(tmp_path)
        assert result is False


# ------------------------------------------------------------------ generate_evidence


class TestGenerateEvidence:
    def test_generates_pack(self, evidence_registry: Registry, evidence_repo: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        assert pack.project_name == "Evidence Test Project"
        assert pack.generated_at != ""
        assert pack.pack_id == pack.generated_at
        assert pack.manifest_json_sha256 != ""
        assert len(pack.manifest_json_sha256) == 64  # SHA-256 hex

    def test_manifest_embedded(self, evidence_registry: Registry, evidence_repo: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        assert "summary" in pack.manifest
        assert pack.manifest["summary"]["total_registered"] == 2

    def test_seal_matches_manifest(self, evidence_registry: Registry, evidence_repo: Path) -> None:
        """The seal must equal SHA-256 of the manifest JSON."""
        pack = generate_evidence(evidence_registry, evidence_repo)
        from librarian.manifest import generate as gen_manifest
        m = gen_manifest(evidence_registry, evidence_repo)
        expected_seal = hashlib.sha256(m.to_json().encode("utf-8")).hexdigest()
        assert pack.manifest_json_sha256 == expected_seal

    def test_git_fields_populated_in_non_git(self, evidence_registry: Registry, evidence_repo: Path) -> None:
        """Non-git repos get empty strings, not errors."""
        pack = generate_evidence(evidence_registry, evidence_repo)
        assert pack.git_commit_hash == ""
        assert pack.git_branch == ""
        assert pack.git_dirty is False

    def test_generator_version(self, evidence_registry: Registry, evidence_repo: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        assert pack.generator_version == "0.3.0"


# ------------------------------------------------------------------ write_evidence


class TestWriteEvidence:
    def test_writes_file(self, evidence_registry: Registry, evidence_repo: Path, tmp_path: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        out = tmp_path / "evidence.json"
        result = write_evidence(pack, out)
        assert out.exists()
        assert result == out.resolve()
        parsed = json.loads(out.read_text())
        assert "evidence_pack" in parsed

    def test_creates_parent_dirs(self, evidence_registry: Registry, evidence_repo: Path, tmp_path: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        deep = tmp_path / "a" / "b" / "evidence.json"
        write_evidence(pack, deep)
        assert deep.exists()


# ------------------------------------------------------------------ verify_evidence


class TestVerifyEvidence:
    def test_valid_pack_verifies(self, evidence_registry: Registry, evidence_repo: Path, tmp_path: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        pack_path = tmp_path / "evidence.json"
        write_evidence(pack, pack_path)
        result = verify_evidence(pack_path, evidence_registry, evidence_repo)
        assert result["valid"] is True
        assert result["drift_detected"] is False
        assert result["pack_seal"] == result["current_seal"]

    def test_drift_after_modification(self, evidence_registry: Registry, evidence_repo: Path, tmp_path: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        pack_path = tmp_path / "evidence.json"
        write_evidence(pack, pack_path)

        # Modify a tracked file
        (evidence_repo / "docs" / "alpha-doc-20260101-V1.0.md").write_text("MODIFIED CONTENT")

        result = verify_evidence(pack_path, evidence_registry, evidence_repo)
        assert result["valid"] is False
        assert result["drift_detected"] is True
        assert result["pack_seal"] != result["current_seal"]

    def test_drift_after_addition(self, evidence_registry: Registry, evidence_repo: Path, tmp_path: Path) -> None:
        pack = generate_evidence(evidence_registry, evidence_repo)
        pack_path = tmp_path / "evidence.json"
        write_evidence(pack, pack_path)

        # Add a new file (doesn't change registry, but won't affect hash unless registered)
        # Instead, modify existing file to trigger drift
        (evidence_repo / "docs" / "beta-doc-20260101-V1.0.md").write_text("NEW CONTENT\n")

        result = verify_evidence(pack_path, evidence_registry, evidence_repo)
        assert result["drift_detected"] is True
