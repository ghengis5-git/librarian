"""Tests for the dashboard module (Phase D).

Covers template discovery, manifest injection, HTML output, CLI integration,
and edge cases (empty registry, large registry).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from librarian.dashboard import (
    PLACEHOLDER,
    _find_template,
    render,
    write_dashboard,
)
from librarian.manifest import Manifest, generate as generate_manifest
from librarian.registry import Registry


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mini_template(tmp_path: Path) -> Path:
    """Minimal valid dashboard template for fast tests."""
    tpl = tmp_path / "dashboard" / "librarian-dashboard-template-20260412-V3.0.html"
    tpl.parent.mkdir()
    tpl.write_text(
        "<!DOCTYPE html><html><head></head><body>"
        "<script>const MANIFEST = __MANIFEST_DATA__;</script>"
        "</body></html>",
        encoding="utf-8",
    )
    return tpl


@pytest.fixture
def sample_manifest(temp_repo: Path, temp_registry_path: Path) -> Manifest:
    """A manifest generated from the shared conftest temp_repo."""
    reg = Registry.load(temp_registry_path)
    return generate_manifest(reg, temp_repo)


@pytest.fixture
def empty_manifest(tmp_path: Path) -> Manifest:
    """A manifest from an empty registry (0 documents)."""
    reg_data = {
        "project_config": {
            "project_name": "Empty",
            "tracked_dirs": ["docs/"],
        },
        "documents": [],
        "registry_meta": {"total_documents": 0},
    }
    (tmp_path / "docs").mkdir()
    reg_path = tmp_path / "docs" / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(reg_data, f, sort_keys=False)
    reg = Registry.load(reg_path)
    return generate_manifest(reg, tmp_path)


@pytest.fixture
def large_manifest(tmp_path: Path) -> Manifest:
    """A manifest with 50 synthetic documents for payload testing."""
    docs = []
    for i in range(50):
        fn = f"synthetic-doc-20260101-V1.{i}.md"
        docs.append({
            "filename": fn,
            "title": f"Synthetic Document {i}",
            "description": f"Auto-generated test document number {i}",
            "status": "active" if i % 3 != 0 else "draft",
            "version": f"V1.{i}",
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "author": "Test Bot",
            "classification": "INTERNAL",
            "tags": ["test", f"batch-{i // 10}"],
            "path": f"docs/{fn}",
            "infrastructure_exempt": False,
            "cross_references": [{"doc": docs[i - 1]["filename"], "status": "resolved"}] if i > 0 else [],
        })
    reg_data = {
        "project_config": {
            "project_name": "Large Test",
            "tracked_dirs": ["docs/"],
        },
        "documents": docs,
        "registry_meta": {"total_documents": len(docs)},
    }
    (tmp_path / "docs").mkdir()
    reg_path = tmp_path / "docs" / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(reg_data, f, sort_keys=False)
    # Create files on disk so hashes can be computed
    for doc in docs:
        (tmp_path / doc["path"]).write_text(f"# {doc['title']}\n")
    reg = Registry.load(reg_path)
    return generate_manifest(reg, tmp_path)


# ─── Template Discovery ─────────────────────────────────────────────────────


class TestFindTemplate:
    def test_finds_template_in_directory(self, mini_template: Path):
        found = _find_template(mini_template.parent)
        assert found == mini_template

    def test_accepts_direct_file_path(self, mini_template: Path):
        found = _find_template(mini_template)
        assert found == mini_template

    def test_raises_for_missing_directory(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            _find_template(tmp_path / "nonexistent")

    def test_raises_for_empty_directory(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(FileNotFoundError, match="No dashboard template"):
            _find_template(empty)

    def test_uses_default_bundled_template(self):
        """The bundled template in dashboard/ should be discoverable."""
        project_root = Path(__file__).resolve().parent.parent
        dashboard_dir = project_root / "dashboard"
        if not dashboard_dir.is_dir():
            pytest.skip("Bundled dashboard template not present")
        found = _find_template(dashboard_dir)
        assert found.name.startswith("librarian-dashboard-template-")


# ─── Render ──────────────────────────────────────────────────────────────────


class TestRender:
    def test_render_replaces_placeholder(self, mini_template: Path, sample_manifest: Manifest):
        html = render(sample_manifest, template_path=mini_template)
        assert PLACEHOLDER not in html

    def test_render_produces_valid_html(self, mini_template: Path, sample_manifest: Manifest):
        html = render(sample_manifest, template_path=mini_template)
        assert "<html>" in html
        assert "</html>" in html
        assert "<script>" in html

    def test_manifest_data_parseable_in_html(self, mini_template: Path, sample_manifest: Manifest):
        """The injected JSON should parse back to the original manifest dict."""
        html = render(sample_manifest, template_path=mini_template)
        # Extract JSON between "const MANIFEST = " and ";"
        start = html.index("const MANIFEST = ") + len("const MANIFEST = ")
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(html, start)
        assert obj["summary"]["total_registered"] == sample_manifest.total_registered
        assert len(obj["file_hashes"]) == len(sample_manifest.file_hashes)

    def test_render_raises_without_placeholder(self, tmp_path: Path, sample_manifest: Manifest):
        bad_tpl = tmp_path / "bad.html"
        bad_tpl.write_text("<html><body>No placeholder here</body></html>")
        with pytest.raises(ValueError, match="placeholder"):
            render(sample_manifest, template_path=bad_tpl)

    def test_render_empty_registry(self, mini_template: Path, empty_manifest: Manifest):
        html = render(empty_manifest, template_path=mini_template)
        assert PLACEHOLDER not in html
        start = html.index("const MANIFEST = ") + len("const MANIFEST = ")
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(html, start)
        assert obj["summary"]["total_registered"] == 0

    def test_render_large_registry(self, mini_template: Path, large_manifest: Manifest):
        html = render(large_manifest, template_path=mini_template)
        assert PLACEHOLDER not in html
        start = html.index("const MANIFEST = ") + len("const MANIFEST = ")
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(html, start)
        assert obj["summary"]["total_registered"] == 50
        assert len(obj["dependency_edges"]) == 49  # chain of 50 docs


# ─── Write ───────────────────────────────────────────────────────────────────


class TestWriteDashboard:
    def test_creates_file(self, tmp_path: Path, mini_template: Path, sample_manifest: Manifest):
        out = tmp_path / "output" / "dashboard.html"
        result = write_dashboard(sample_manifest, out, template_path=mini_template)
        assert result.is_file()
        assert result.stat().st_size > 0

    def test_creates_parent_dirs(self, tmp_path: Path, mini_template: Path, sample_manifest: Manifest):
        out = tmp_path / "deep" / "nested" / "dir" / "dashboard.html"
        result = write_dashboard(sample_manifest, out, template_path=mini_template)
        assert result.is_file()

    def test_output_contains_manifest(self, tmp_path: Path, mini_template: Path, sample_manifest: Manifest):
        out = tmp_path / "dashboard.html"
        write_dashboard(sample_manifest, out, template_path=mini_template)
        html = out.read_text(encoding="utf-8")
        assert PLACEHOLDER not in html
        assert "total_registered" in html


# ─── CLI Integration ─────────────────────────────────────────────────────────


class TestCLIDashboard:
    def test_cli_runs(self, temp_repo: Path, mini_template: Path):
        out = temp_repo / "test-dash.html"
        result = subprocess.run(
            [
                sys.executable, "-m", "librarian",
                "--registry", str(temp_repo / "docs" / "REGISTRY.yaml"),
                "--repo", str(temp_repo),
                "dashboard",
                "-o", str(out),
                "--template", str(mini_template),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out.is_file()

    def test_cli_output_flag(self, temp_repo: Path, mini_template: Path):
        out = temp_repo / "custom-output.html"
        result = subprocess.run(
            [
                sys.executable, "-m", "librarian",
                "--registry", str(temp_repo / "docs" / "REGISTRY.yaml"),
                "--repo", str(temp_repo),
                "dashboard",
                "-o", str(out),
                "--template", str(mini_template),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Dashboard written to:" in result.stdout
        html = out.read_text()
        assert "total_registered" in html
