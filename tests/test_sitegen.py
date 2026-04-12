"""Tests for the static site generator (Phase E + folder/tree features).

Covers site structure, page content, graph page, dashboard inclusion,
sidebar tree, grouping modes, CLI integration, and edge cases.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from librarian.manifest import Manifest, generate as generate_manifest
from librarian.registry import Registry
from librarian.sitegen import (
    generate_site,
    _group_by_status,
    _group_by_tag,
    _group_by_path,
    _build_tree_json,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_manifest(temp_repo: Path, temp_registry_path: Path) -> Manifest:
    reg = Registry.load(temp_registry_path)
    return generate_manifest(reg, temp_repo)


@pytest.fixture
def empty_manifest(tmp_path: Path) -> Manifest:
    reg_data = {
        "project_config": {"project_name": "Empty", "tracked_dirs": ["docs/"]},
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
def multi_doc_manifest(tmp_path: Path) -> Manifest:
    """Manifest with 5 documents including cross-refs and supplements."""
    docs = [
        {
            "filename": "alpha-doc-20260101-V1.0.md",
            "title": "Alpha",
            "description": "First document",
            "status": "active",
            "version": "V1.0",
            "created": "2026-01-01",
            "author": "Test",
            "classification": "INTERNAL",
            "tags": ["test"],
            "path": "docs/alpha-doc-20260101-V1.0.md",
            "infrastructure_exempt": False,
            "cross_references": [
                {"doc": "beta-doc-20260101-V1.0.md", "status": "resolved", "sections": ["Intro"]}
            ],
        },
        {
            "filename": "beta-doc-20260101-V1.0.md",
            "title": "Beta",
            "description": "Second document",
            "status": "draft",
            "version": "V1.0",
            "created": "2026-01-15",
            "author": "Test",
            "classification": "INTERNAL",
            "tags": ["test", "draft"],
            "path": "docs/beta-doc-20260101-V1.0.md",
            "infrastructure_exempt": False,
            "supplements": ["alpha-doc-20260101-V1.0.md"],
        },
        {
            "filename": "gamma-doc-20260101-V1.0.md",
            "title": "Gamma",
            "description": "Third, superseded",
            "status": "superseded",
            "version": "V1.0",
            "created": "2026-01-20",
            "author": "Test",
            "classification": "INTERNAL",
            "tags": [],
            "path": "docs/gamma-doc-20260101-V1.0.md",
            "infrastructure_exempt": False,
            "superseded_by": "gamma-doc-20260201-V2.0.md",
        },
        {
            "filename": "gamma-doc-20260201-V2.0.md",
            "title": "Gamma V2",
            "description": "Third, current",
            "status": "active",
            "version": "V2.0",
            "created": "2026-02-01",
            "author": "Test",
            "classification": "INTERNAL",
            "tags": ["updated"],
            "path": "docs/gamma-doc-20260201-V2.0.md",
            "infrastructure_exempt": False,
            "supersedes": "gamma-doc-20260101-V1.0.md",
        },
        {
            "filename": "README.md",
            "title": "Project README",
            "description": "Top-level readme",
            "status": "active",
            "version": "V1.0",
            "created": "2026-01-01",
            "author": "Test",
            "classification": "INTERNAL",
            "tags": ["meta"],
            "path": "README.md",
            "infrastructure_exempt": True,
        },
    ]
    reg_data = {
        "project_config": {
            "project_name": "Multi Test",
            "tracked_dirs": ["docs/"],
            "naming_rules": {"infrastructure_exempt": ["README.md"]},
        },
        "documents": docs,
        "registry_meta": {
            "total_documents": 5,
            "active": 3,
            "draft": 1,
            "superseded": 1,
            "pending_cross_reference_updates": 0,
            "naming_violations": 0,
        },
    }
    (tmp_path / "docs").mkdir()
    reg_path = tmp_path / "docs" / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(reg_data, f, sort_keys=False)
    for d in docs:
        (tmp_path / d["path"]).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / d["path"]).write_text(f"# {d['title']}\n")
    reg = Registry.load(reg_path)
    return generate_manifest(reg, tmp_path)


# ─── Site Structure ──────────────────────────────────────────────────────────


class TestSiteStructure:
    def test_creates_output_dir(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        assert out.is_dir()

    def test_creates_index(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        assert (out / "index.html").is_file()

    def test_creates_graph(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        assert (out / "graph.html").is_file()

    def test_creates_assets(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        assert (out / "assets" / "style.css").is_file()

    def test_creates_doc_pages(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        assert (out / "docs").is_dir()
        doc_pages = list((out / "docs").glob("*.html"))
        docs = sample_manifest.registry_snapshot.get("documents", [])
        assert len(doc_pages) == len(docs)

    def test_doc_page_per_document(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        docs = multi_doc_manifest.registry_snapshot["documents"]
        for doc in docs:
            fn = doc["filename"]
            assert (out / "docs" / f"{fn}.html").is_file(), f"Missing page for {fn}"


# ─── Page Content ────────────────────────────────────────────────────────────


class TestPageContent:
    def test_index_has_html_structure(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "index.html").read_text()
        assert "<html" in html
        assert "</html>" in html
        assert "<nav>" in html

    def test_index_has_kpi_cards(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "index.html").read_text()
        assert "kpi-value" in html
        assert "Total" in html

    def test_index_has_table_rows(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        # 5 docs = 5 data rows + 1 header row
        assert html.count("<tr>") == 6

    def test_index_links_to_doc_pages(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        assert 'href="docs/alpha-doc-20260101-V1.0.md.html"' in html

    def test_doc_page_has_metadata(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "alpha-doc-20260101-V1.0.md" in html
        assert "Alpha" in html
        assert "First document" in html
        assert "Back to index" in html

    def test_doc_page_has_cross_refs(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "beta-doc-20260101-V1.0.md" in html
        assert "resolved" in html

    def test_doc_page_has_supersedes_chain(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "gamma-doc-20260201-V2.0.md.html").read_text()
        assert "Supersedes" in html
        assert "gamma-doc-20260101-V1.0.md" in html

    def test_doc_page_has_sha256(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "SHA-256" in html

    def test_graph_page_has_cytoscape(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "graph.html").read_text()
        assert "cytoscape" in html
        assert "ELEMENTS" in html


# ─── Dashboard Inclusion ─────────────────────────────────────────────────────


class TestDashboardInclusion:
    def test_dashboard_included_when_provided(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        dash = tmp_path / "dash.html"
        dash.write_text("<html><body>Dashboard</body></html>")
        generate_site(sample_manifest, out, dashboard_path=dash)
        assert (out / "dashboard.html").is_file()
        assert "Dashboard" in (out / "dashboard.html").read_text()

    def test_nav_includes_dashboard_link(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        dash = tmp_path / "dash.html"
        dash.write_text("<html><body>Dashboard</body></html>")
        generate_site(sample_manifest, out, dashboard_path=dash)
        html = (out / "index.html").read_text()
        assert "dashboard.html" in html

    def test_no_dashboard_when_not_provided(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        assert not (out / "dashboard.html").is_file()


# ─── Edge Cases ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_registry(self, tmp_path: Path, empty_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(empty_manifest, out)
        assert (out / "index.html").is_file()
        assert (out / "graph.html").is_file()
        doc_pages = list((out / "docs").glob("*.html"))
        assert len(doc_pages) == 0

    def test_creates_nested_output_dir(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "deep" / "nested" / "site"
        generate_site(sample_manifest, out)
        assert (out / "index.html").is_file()

    def test_css_file_not_empty(self, tmp_path: Path, sample_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        css = (out / "assets" / "style.css").read_text()
        assert len(css) > 100
        assert "--accent" in css


# ─── CLI Integration ─────────────────────────────────────────────────────────


class TestCLISite:
    def test_cli_runs(self, temp_repo: Path):
        out = temp_repo / "test_site"
        result = subprocess.run(
            [
                sys.executable, "-m", "librarian",
                "--registry", str(temp_repo / "docs" / "REGISTRY.yaml"),
                "--repo", str(temp_repo),
                "site",
                "-o", str(out),
                "--no-dashboard",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (out / "index.html").is_file()
        assert (out / "graph.html").is_file()

    def test_cli_page_count(self, temp_repo: Path):
        out = temp_repo / "test_site"
        result = subprocess.run(
            [
                sys.executable, "-m", "librarian",
                "--registry", str(temp_repo / "docs" / "REGISTRY.yaml"),
                "--repo", str(temp_repo),
                "site",
                "-o", str(out),
                "--no-dashboard",
            ],
            capture_output=True,
            text=True,
        )
        assert "Pages:" in result.stdout


# ─── Grouping Logic ────────────────────────────────────────────────────────


SAMPLE_DOCS = [
    {"filename": "a.md", "title": "A", "status": "active", "tags": ["core", "v1"], "path": "docs/a.md"},
    {"filename": "b.md", "title": "B", "status": "draft", "tags": ["core"], "path": "docs/b.md"},
    {"filename": "c.md", "title": "C", "status": "active", "tags": [], "path": "specs/c.md"},
    {"filename": "d.md", "title": "D", "status": "superseded", "tags": ["v1"], "path": "d.md"},
]


class TestGroupByStatus:
    def test_groups_correct(self):
        groups = _group_by_status(SAMPLE_DOCS)
        assert "active" in groups
        assert "draft" in groups
        assert "superseded" in groups
        assert len(groups["active"]) == 2
        assert len(groups["draft"]) == 1

    def test_order_active_first(self):
        groups = _group_by_status(SAMPLE_DOCS)
        keys = list(groups.keys())
        assert keys.index("active") < keys.index("draft")
        assert keys.index("draft") < keys.index("superseded")

    def test_empty_list(self):
        groups = _group_by_status([])
        assert groups == {}


class TestGroupByTag:
    def test_groups_correct(self):
        groups = _group_by_tag(SAMPLE_DOCS)
        assert "core" in groups
        assert "v1" in groups
        assert "untagged" in groups
        assert len(groups["core"]) == 2
        assert len(groups["untagged"]) == 1

    def test_doc_appears_in_multiple_tags(self):
        groups = _group_by_tag(SAMPLE_DOCS)
        # "a.md" has tags ["core", "v1"] — should appear in both
        a_in_core = any(d["filename"] == "a.md" for d in groups["core"])
        a_in_v1 = any(d["filename"] == "a.md" for d in groups["v1"])
        assert a_in_core
        assert a_in_v1

    def test_empty_list(self):
        groups = _group_by_tag([])
        assert groups == {}


class TestGroupByPath:
    def test_groups_correct(self):
        groups = _group_by_path(SAMPLE_DOCS)
        assert "docs" in groups
        assert "specs" in groups
        assert "." in groups
        assert len(groups["docs"]) == 2
        assert len(groups["specs"]) == 1
        assert len(groups["."]) == 1

    def test_empty_list(self):
        groups = _group_by_path([])
        assert groups == {}


class TestTreeJSON:
    def test_valid_json(self):
        result = _build_tree_json(SAMPLE_DOCS)
        data = json.loads(result)
        assert "status" in data
        assert "tag" in data
        assert "path" in data

    def test_structure(self):
        data = json.loads(_build_tree_json(SAMPLE_DOCS))
        # Each group mode is a dict of group_name -> list of doc dicts
        for doc in data["status"]["active"]:
            assert "filename" in doc
            assert "title" in doc
            assert "status" in doc


# ─── Sidebar in Pages ──────────────────────────────────────────────────────


class TestSidebar:
    def test_index_has_sidebar(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        assert "sidebar" in html
        assert "TREE_DATA" in html
        assert "group-btn" in html

    def test_doc_page_has_sidebar(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "sidebar" in html
        assert "TREE_DATA" in html

    def test_graph_page_has_sidebar(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "graph.html").read_text()
        assert "sidebar" in html

    def test_sidebar_has_three_group_modes(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        assert 'data-group="status"' in html
        assert 'data-group="tag"' in html
        assert 'data-group="path"' in html

    def test_sidebar_tree_data_valid_json(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        # Extract TREE_DATA JSON from the HTML
        start = html.index("var TREE_DATA = ") + len("var TREE_DATA = ")
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(html, start)
        assert "status" in obj
        assert "tag" in obj
        assert "path" in obj
        # Should have active docs in status grouping
        assert "active" in obj["status"]

    def test_empty_registry_sidebar(self, tmp_path: Path, empty_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(empty_manifest, out)
        html = (out / "index.html").read_text()
        assert "sidebar" in html
        # Tree data should be empty
        start = html.index("var TREE_DATA = ") + len("var TREE_DATA = ")
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(html, start)
        assert obj["status"] == {}
        assert obj["tag"] == {}
        assert obj["path"] == {}
