"""Tests for librarian.diffaudit — delta report between two manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from librarian.diffaudit import (
    DiffReport,
    diff_manifests,
    format_diff,
)


# ------------------------------------------------------------------ fixtures


def _make_manifest(
    *,
    files: dict[str, str] | None = None,
    edges: list[dict] | None = None,
    seal: str = "aaa",
    generated_at: str = "2026-04-11T12:00:00Z",
) -> dict:
    """Build a minimal manifest dict for testing."""
    file_hashes = []
    for fname, sha in (files or {}).items():
        file_hashes.append({
            "filename": fname,
            "sha256": sha,
            "size_bytes": 100,
            "exists": True,
        })
    return {
        "meta": {"generated_at": generated_at},
        "file_hashes": file_hashes,
        "dependency_edges": edges or [],
        "manifest_sha256": seal,
    }


@pytest.fixture
def baseline_manifest() -> dict:
    return _make_manifest(
        files={
            "alpha-doc-20260101-V1.0.md": "aaaa",
            "beta-doc-20260101-V1.0.md": "bbbb",
            "gamma-doc-20260101-V1.0.md": "cccc",
        },
        edges=[
            {"source": "alpha-doc-20260101-V1.0.md", "target": "beta-doc-20260101-V1.0.md", "status": "supplement"},
        ],
        seal="seal_old",
        generated_at="2026-04-10T10:00:00Z",
    )


# ------------------------------------------------------------------ DiffReport


class TestDiffReport:
    def test_has_changes_false_when_empty(self) -> None:
        r = DiffReport()
        assert r.has_changes is False

    def test_has_changes_true_with_added(self) -> None:
        r = DiffReport(added=["new.md"])
        assert r.has_changes is True

    def test_has_changes_true_with_removed(self) -> None:
        r = DiffReport(removed=["gone.md"])
        assert r.has_changes is True

    def test_has_changes_true_with_modified(self) -> None:
        r = DiffReport(modified=[{"filename": "a.md", "old_sha256": "x", "new_sha256": "y"}])
        assert r.has_changes is True

    def test_has_changes_true_with_edges(self) -> None:
        r = DiffReport(edges_added=[{"source": "a", "target": "b", "status": "supplement"}])
        assert r.has_changes is True

    def test_to_dict_structure(self) -> None:
        r = DiffReport(
            added=["new.md"],
            removed=["old.md"],
            modified=[{"filename": "changed.md", "old_sha256": "x", "new_sha256": "y"}],
        )
        d = r.to_dict()
        assert "diff" in d
        assert "documents" in d
        assert "edges" in d
        assert "summary" in d
        assert d["summary"]["total_added"] == 1
        assert d["summary"]["total_removed"] == 1
        assert d["summary"]["total_modified"] == 1
        assert d["summary"]["has_changes"] is True

    def test_to_json_valid(self) -> None:
        r = DiffReport(added=["a.md"])
        parsed = json.loads(r.to_json())
        assert parsed["documents"]["added"] == ["a.md"]

    def test_to_json_sorted_keys(self) -> None:
        r = DiffReport()
        parsed = json.loads(r.to_json())
        assert list(parsed.keys()) == sorted(parsed.keys())


# ------------------------------------------------------------------ diff_manifests


class TestDiffManifests:
    def test_no_changes(self, baseline_manifest: dict) -> None:
        report = diff_manifests(baseline_manifest, baseline_manifest)
        assert report.has_changes is False
        assert report.added == []
        assert report.removed == []
        assert report.modified == []

    def test_added_document(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "bbbb",
                "gamma-doc-20260101-V1.0.md": "cccc",
                "delta-doc-20260201-V1.0.md": "dddd",
            },
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert "delta-doc-20260201-V1.0.md" in report.added
        assert report.removed == []
        assert report.modified == []

    def test_removed_document(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "bbbb",
            },
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert "gamma-doc-20260101-V1.0.md" in report.removed
        assert report.added == []

    def test_modified_document(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "CHANGED",
                "gamma-doc-20260101-V1.0.md": "cccc",
            },
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert len(report.modified) == 1
        assert report.modified[0]["filename"] == "beta-doc-20260101-V1.0.md"
        assert report.modified[0]["old_sha256"] == "bbbb"
        assert report.modified[0]["new_sha256"] == "CHANGED"

    def test_edge_added(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "bbbb",
                "gamma-doc-20260101-V1.0.md": "cccc",
            },
            edges=[
                {"source": "alpha-doc-20260101-V1.0.md", "target": "beta-doc-20260101-V1.0.md", "status": "supplement"},
                {"source": "alpha-doc-20260101-V1.0.md", "target": "gamma-doc-20260101-V1.0.md", "status": "resolved"},
            ],
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert len(report.edges_added) == 1
        assert report.edges_added[0]["target"] == "gamma-doc-20260101-V1.0.md"
        assert report.edges_removed == []

    def test_edge_removed(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "bbbb",
                "gamma-doc-20260101-V1.0.md": "cccc",
            },
            edges=[],
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert len(report.edges_removed) == 1
        assert report.edges_added == []

    def test_seal_changed(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "bbbb",
                "gamma-doc-20260101-V1.0.md": "cccc",
            },
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert report.seal_changed is True
        assert report.old_seal == "seal_old"
        assert report.new_seal == "seal_new"

    def test_seal_unchanged(self, baseline_manifest: dict) -> None:
        report = diff_manifests(baseline_manifest, baseline_manifest)
        assert report.seal_changed is False

    def test_timestamps_captured(self, baseline_manifest: dict) -> None:
        new = _make_manifest(
            files={"alpha-doc-20260101-V1.0.md": "aaaa", "beta-doc-20260101-V1.0.md": "bbbb", "gamma-doc-20260101-V1.0.md": "cccc"},
            generated_at="2026-04-11T14:00:00Z",
        )
        report = diff_manifests(baseline_manifest, new)
        assert report.old_generated_at == "2026-04-10T10:00:00Z"
        assert report.new_generated_at == "2026-04-11T14:00:00Z"

    def test_from_file_paths(self, tmp_path: Path, baseline_manifest: dict) -> None:
        old_path = tmp_path / "old.json"
        new_path = tmp_path / "new.json"
        old_path.write_text(json.dumps(baseline_manifest))

        new_data = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "aaaa",
                "beta-doc-20260101-V1.0.md": "bbbb",
                "gamma-doc-20260101-V1.0.md": "cccc",
                "new-doc-20260201-V1.0.md": "nnnn",
            },
            seal="seal_new",
        )
        new_path.write_text(json.dumps(new_data))

        report = diff_manifests(str(old_path), str(new_path))
        assert "new-doc-20260201-V1.0.md" in report.added

    def test_combined_changes(self, baseline_manifest: dict) -> None:
        """Test a manifest with adds, removes, and modifications at once."""
        new = _make_manifest(
            files={
                "alpha-doc-20260101-V1.0.md": "MODIFIED_ALPHA",
                # beta removed
                "gamma-doc-20260101-V1.0.md": "cccc",
                "new-doc-20260201-V1.0.md": "nnnn",
            },
            seal="seal_new",
        )
        report = diff_manifests(baseline_manifest, new)
        assert "new-doc-20260201-V1.0.md" in report.added
        assert "beta-doc-20260101-V1.0.md" in report.removed
        assert len(report.modified) == 1
        assert report.modified[0]["filename"] == "alpha-doc-20260101-V1.0.md"


# ------------------------------------------------------------------ format_diff


class TestFormatDiff:
    def test_no_changes_message(self) -> None:
        r = DiffReport()
        output = format_diff(r)
        assert "No changes detected" in output

    def test_shows_added(self) -> None:
        r = DiffReport(added=["new.md"])
        output = format_diff(r)
        assert "Added" in output
        assert "+ new.md" in output

    def test_shows_removed(self) -> None:
        r = DiffReport(removed=["old.md"])
        output = format_diff(r)
        assert "Removed" in output
        assert "- old.md" in output

    def test_shows_modified(self) -> None:
        r = DiffReport(modified=[{"filename": "changed.md", "old_sha256": "x", "new_sha256": "y"}])
        output = format_diff(r)
        assert "Modified" in output
        assert "~ changed.md" in output

    def test_shows_edges(self) -> None:
        r = DiffReport(
            edges_added=[{"source": "a.md", "target": "b.md", "status": "supplement"}],
            edges_removed=[{"source": "c.md", "target": "d.md", "status": "resolved"}],
        )
        output = format_diff(r)
        assert "Edges added" in output
        assert "Edges removed" in output
        assert "a.md -> b.md" in output
        assert "c.md -> d.md" in output

    def test_shows_seal_changed(self) -> None:
        r = DiffReport(seal_changed=True, added=["trigger.md"])
        output = format_diff(r)
        assert "Seal changed: YES" in output

    def test_shows_seal_unchanged(self) -> None:
        r = DiffReport(seal_changed=False)
        output = format_diff(r)
        assert "Seal changed: no" in output

    def test_banner_present(self) -> None:
        r = DiffReport()
        output = format_diff(r)
        assert "Librarian Diff Audit" in output
        assert "=" * 55 in output
