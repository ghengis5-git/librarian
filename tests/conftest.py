"""Pytest fixtures for librarian tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SAMPLE_REGISTRY = {
    "project_config": {
        "project_name": "Test Project",
        "default_author": "Test Author",
        "default_classification": "INTERNAL",
        "tracked_dirs": ["docs/"],
        "naming_rules": {
            "infrastructure_exempt": [
                "SKILL.md",
                "REGISTRY.yaml",
                "README.md",
                ".gitignore",
            ],
        },
    },
    "documents": [
        {
            "filename": "baseline-doc-20260101-V1.0.md",
            "title": "Baseline Document",
            "description": "Seed document for tests",
            "status": "active",
            "version": "V1.0",
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "author": "Test Author",
            "classification": "INTERNAL",
            "tags": ["test"],
            "path": "docs/baseline-doc-20260101-V1.0.md",
            "infrastructure_exempt": False,
        },
    ],
    "registry_meta": {
        "total_documents": 1,
        "active": 1,
        "draft": 0,
        "superseded": 0,
        "pending_cross_reference_updates": 0,
        "naming_violations": 0,
        "last_updated": "2026-01-01",
    },
}


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temp repo with docs/ and a valid REGISTRY.yaml.

    Layout:
        <tmp_path>/
            docs/
                REGISTRY.yaml
                baseline-doc-20260101-V1.0.md
    """
    (tmp_path / "docs").mkdir()
    reg_path = tmp_path / "docs" / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(SAMPLE_REGISTRY, f, sort_keys=False)
    (tmp_path / "docs" / "baseline-doc-20260101-V1.0.md").write_text("# baseline\n")
    return tmp_path


@pytest.fixture
def temp_registry_path(temp_repo: Path) -> Path:
    return temp_repo / "docs" / "REGISTRY.yaml"
