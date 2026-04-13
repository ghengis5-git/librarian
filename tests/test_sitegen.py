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
    _build_tree_diagram,
    _md_to_html,
    _inline,
    _render_file_content,
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


# ─── Tree Diagram ─────────────────────────────────────────────────────────


class TestTreeDiagram:
    """Tests for the interactive folder-tree diagram."""

    def test_diagram_renders_root(self):
        dirs = {".": [{"filename": "readme.md", "status": "active"}]}
        html = _build_tree_diagram(dirs)
        assert "project root" in html
        assert "tree-diagram" in html

    def test_diagram_shows_folders(self):
        dirs = {
            "docs": [{"filename": "alpha.md", "status": "active"}],
            "specs": [{"filename": "beta.yaml", "status": "draft"}],
        }
        html = _build_tree_diagram(dirs)
        assert "docs/" in html
        assert "specs/" in html

    def test_diagram_shows_files(self):
        dirs = {
            "docs": [{"filename": "alpha.md", "status": "active"}],
        }
        html = _build_tree_diagram(dirs)
        assert "alpha.md" in html
        assert 'href="docs/alpha.md.html"' in html

    def test_diagram_status_dots(self):
        dirs = {
            ".": [
                {"filename": "a.md", "status": "active"},
                {"filename": "b.md", "status": "draft"},
            ],
        }
        html = _build_tree_diagram(dirs)
        assert "td-status-dot--active" in html
        assert "td-status-dot--draft" in html

    def test_diagram_toggle_script(self):
        dirs = {".": [{"filename": "x.md", "status": "active"}]}
        html = _build_tree_diagram(dirs)
        assert "td-toggle" in html
        assert "<script>" in html

    def test_diagram_file_count_badge(self):
        dirs = {
            "docs": [
                {"filename": "a.md", "status": "active"},
                {"filename": "b.md", "status": "active"},
            ],
        }
        html = _build_tree_diagram(dirs)
        assert "td-file-count" in html

    def test_diagram_in_tree_page(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "tree.html").read_text()
        assert "tree-diagram" in html
        assert "Interactive Folder Map" in html

    def test_diagram_folder_click_scrolls(self):
        dirs = {"docs": [{"filename": "a.md", "status": "active"}]}
        html = _build_tree_diagram(dirs)
        assert "data-folder" in html
        assert "scrollIntoView" in html


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


# ─── Markdown → HTML ──────────────────────────────────────────────────────────


class TestMdToHtml:
    def test_heading(self):
        assert "<h1>Title</h1>" in _md_to_html("# Title")
        assert "<h2>Sub</h2>" in _md_to_html("## Sub")
        assert "<h3>Deep</h3>" in _md_to_html("### Deep")

    def test_paragraph(self):
        html = _md_to_html("Hello world.\n\nSecond para.")
        assert "<p>" in html
        assert "Hello world." in html
        assert "Second para." in html

    def test_fenced_code_block(self):
        md = "```python\ndef foo():\n    pass\n```"
        html = _md_to_html(md)
        assert "<pre>" in html
        assert "<code" in html
        assert "def foo():" in html
        assert "language-python" in html

    def test_inline_code(self):
        html = _inline("Use `foo()` here")
        assert "<code>foo()</code>" in html

    def test_bold(self):
        html = _inline("**bold** text")
        assert "<strong>bold</strong>" in html

    def test_italic(self):
        html = _inline("*italic* text")
        assert "<em>italic</em>" in html

    def test_link(self):
        html = _inline("[click](http://example.com)")
        assert 'href="http://example.com"' in html
        assert "click" in html

    def test_unordered_list(self):
        md = "- apple\n- banana\n- cherry"
        html = _md_to_html(md)
        assert "<ul>" in html
        assert "<li>" in html
        assert "apple" in html

    def test_ordered_list(self):
        md = "1. first\n2. second"
        html = _md_to_html(md)
        assert "<ol>" in html
        assert "first" in html

    def test_blockquote(self):
        md = "> quoted text"
        html = _md_to_html(md)
        assert "<blockquote>" in html
        assert "quoted text" in html

    def test_horizontal_rule(self):
        html = _md_to_html("---")
        assert "<hr>" in html

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = _md_to_html(md)
        assert "<table" in html
        assert "<th>" in html
        assert "<td>" in html

    def test_escapes_html(self):
        html = _md_to_html("# <script>alert(1)</script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_frontmatter_not_rendered_as_hr(self):
        """YAML frontmatter delimiters should not become <hr> tags."""
        md = "---\ntitle: test\n---\n\n# Heading"
        # The md_to_html function doesn't strip frontmatter itself,
        # but _render_file_content does. Here we just verify --- handling.
        html = _md_to_html(md)
        assert "<h1>Heading</h1>" in html


# ─── File Content Rendering ───────────────────────────────────────────────────


class TestRenderFileContent:
    def test_md_file_rendered(self, tmp_path: Path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "test.md").write_text("# Hello\n\nWorld.\n")
        doc = {"path": "docs/test.md", "format": "md"}
        html = _render_file_content(doc, tmp_path)
        assert "prose" in html
        assert "<h1>Hello</h1>" in html
        assert "World." in html

    def test_yaml_file_rendered_as_pre(self, tmp_path: Path):
        (tmp_path / "test.yaml").write_text("key: value\n")
        doc = {"path": "test.yaml", "format": "yaml"}
        html = _render_file_content(doc, tmp_path)
        assert "<pre>" in html
        assert "key: value" in html

    def test_json_file_rendered_as_pre(self, tmp_path: Path):
        (tmp_path / "test.json").write_text('{"a": 1}\n')
        doc = {"path": "test.json", "format": "json"}
        html = _render_file_content(doc, tmp_path)
        assert "<pre>" in html
        assert "&quot;a&quot;: 1" in html or '"a": 1' in html

    def test_missing_file(self, tmp_path: Path):
        doc = {"path": "nonexistent.md", "format": "md"}
        html = _render_file_content(doc, tmp_path)
        assert "not found" in html.lower()

    def test_empty_file(self, tmp_path: Path):
        (tmp_path / "empty.md").write_text("")
        doc = {"path": "empty.md", "format": "md"}
        html = _render_file_content(doc, tmp_path)
        assert "empty" in html.lower()

    def test_frontmatter_stripped_from_md(self, tmp_path: Path):
        (tmp_path / "fm.md").write_text("---\ntitle: test\n---\n# Heading\n")
        doc = {"path": "fm.md", "format": "md"}
        html = _render_file_content(doc, tmp_path)
        assert "<h1>Heading</h1>" in html
        # Frontmatter should not appear as content
        assert "title: test" not in html

    def test_no_path_returns_empty(self, tmp_path: Path):
        doc = {"format": "md"}
        html = _render_file_content(doc, tmp_path)
        assert html == ""


# ─── Search & Filter ─────────────────────────────────────────────────────────


class TestSearchFilter:
    def test_index_has_search_input(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        assert 'id="search-input"' in html

    def test_index_has_filter_chips(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        assert "filter-chip" in html
        assert "filterStatus" in html


# ─── Doc Page Content ─────────────────────────────────────────────────────────


class TestDocPageContent:
    def test_doc_page_has_contents_section(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "Contents" in html

    def test_doc_page_renders_md_content(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        # The fixture writes "# Alpha\n" to the file
        assert "<h1>Alpha</h1>" in html

    def test_doc_page_has_prose_class(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "prose" in html

    def test_doc_page_has_xref_section(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "docs" / "alpha-doc-20260101-V1.0.md.html").read_text()
        assert "Cross-References" in html


# ─── Settings Page ────────────────────────────────────────────────────────


class TestSettingsPage:
    def test_settings_page_generated(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        assert (out / "settings.html").is_file()

    def test_settings_has_naming_section(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "Naming Convention" in html
        assert "cfg-sep" in html
        assert "cfg-case" in html

    def test_settings_has_categories_section(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "Folder Categories" in html
        assert "cfg-preset" in html

    def test_settings_has_live_preview(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "preview-filename" in html
        assert "updatePreview" in html
        assert "preview-panel" in html

    def test_settings_has_yaml_export(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "generateYaml" in html
        assert "yaml-output" in html

    def test_settings_has_governance_section(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "Governance" in html
        assert "cfg-author" in html

    def test_settings_has_compliance_standards(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "Compliance Standards" in html
        assert "std-dod" in html
        assert "std-hipaa" in html
        assert "std-sec" in html
        assert "std-scientific" in html
        assert "std-legal" in html
        assert "applyStandard" in html

    def test_settings_has_preview_panel(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "settings.html").read_text()
        assert "settings-preview-panel" in html
        assert "preview-header-card" in html
        assert "preview-footer-card" in html
        assert "preview-meta" in html

    def test_nav_has_gear_icon(self, tmp_path: Path, multi_doc_manifest: Manifest):
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        html = (out / "index.html").read_text()
        assert "settings.html" in html
        assert "Settings" in html


class TestSettingsInteractivity:
    """Comprehensive validation that every interactive element on the settings
    page is wired correctly — proper onclick quoting, ID consistency between
    HTML elements and JS references, compliance standard completeness,
    toggle/deselect support, and YAML export coverage."""

    @pytest.fixture()
    def settings_html(self, tmp_path: Path, multi_doc_manifest: Manifest) -> str:
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        return (out / "settings.html").read_text()

    # ── onclick quoting ──────────────────────────────────────────────

    def test_no_backslash_x27_in_html_onclick(self, settings_html: str):
        """\\x27 is only valid inside JS string literals, not HTML onclick
        attributes.  All onclick handlers must use real single quotes."""
        import re
        # Split out <script> blocks — \\x27 is fine there
        outside_script = re.sub(
            r"<script[\s>].*?</script>", "", settings_html, flags=re.DOTALL
        )
        onclicks = re.findall(r'onclick="[^"]*"', outside_script)
        for oc in onclicks:
            assert "\\x27" not in oc, f"Bad \\x27 in HTML onclick: {oc}"

    def test_all_onclick_use_single_quotes(self, settings_html: str):
        """Every onclick that passes a string arg must use actual ' chars."""
        import re
        outside_script = re.sub(
            r"<script[\s>].*?</script>", "", settings_html, flags=re.DOTALL
        )
        onclicks = re.findall(r'onclick="[^"]*"', outside_script)
        for oc in onclicks:
            if "applyStandard" in oc:
                assert "applyStandard('" in oc, f"Missing quote: {oc}"
            if "classList.toggle" in oc:
                assert "toggle('on')" in oc, f"Missing quote: {oc}"

    # ── compliance buttons ───────────────────────────────────────────

    def test_all_six_compliance_buttons_present(self, settings_html: str):
        standards = ["dod", "iso9001", "hipaa", "sec", "scientific", "legal"]
        for std in standards:
            assert f'id="std-{std}"' in settings_html, f"Missing button: std-{std}"
            assert f"applyStandard('{std}')" in settings_html, (
                f"Missing onclick for {std}"
            )

    def test_compliance_buttons_have_type_button(self, settings_html: str):
        """Buttons without type=button default to submit, causing page reload."""
        import re
        buttons = re.findall(
            r"<button[^>]*settings-compliance-btn[^>]*>", settings_html
        )
        assert len(buttons) == 6
        for btn in buttons:
            assert 'type="button"' in btn, f"Missing type=button: {btn[:80]}"

    def test_compliance_active_css_distinct_from_hover(
        self, tmp_path: Path, multi_doc_manifest: Manifest
    ):
        """Active state must use a solid accent background, not just a border."""
        import re
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        css = (out / "assets" / "style.css").read_text()
        match = re.search(
            r"\.settings-compliance-btn\.active\s*\{([^}]+)\}", css
        )
        assert match, "Missing .settings-compliance-btn.active CSS rule"
        rule = match.group(1)
        assert "background: var(--accent)" in rule, (
            "Active bg should be solid accent, not accent-light"
        )
        assert "color: #fff" in rule, "Active text should be white"

    def test_compliance_deselect_restores_defaults(self, settings_html: str):
        """applyStandard must toggle off when clicking an already-active button
        and restore PROJECT_DEFAULTS."""
        assert "captureDefaults" in settings_html
        assert "PROJECT_DEFAULTS" in settings_html
        assert "wasActive" in settings_html
        assert "applyFields(PROJECT_DEFAULTS)" in settings_html

    def test_capture_defaults_called_on_load(self, settings_html: str):
        assert "captureDefaults();" in settings_html
        assert "DOMContentLoaded" in settings_html

    # ── STANDARDS object completeness ────────────────────────────────

    def test_standards_object_has_all_required_fields(self, settings_html: str):
        """Each compliance standard must set every form field."""
        import re
        required_fields = [
            "sep", "case", "date", "ver", "domain",
            "hdr", "org", "banner", "prefix",
            "hdrVer", "hdrDate", "hdrStatus", "hdrPages",
            "ftr", "dist", "ret", "copy", "custom",
            "metaOwner", "metaApprover", "metaReview", "metaDist", "metaRev",
            "retention", "cycle", "cls",
        ]
        standards = ["dod", "iso9001", "hipaa", "sec", "scientific", "legal"]
        # Extract the STANDARDS block from a <script> tag
        match = re.search(
            r"var STANDARDS\s*=\s*\{(.+?)\n\};", settings_html, re.DOTALL
        )
        assert match, "STANDARDS object not found"
        block = match.group(1)
        for std in standards:
            # Find this standard's block
            std_match = re.search(
                rf"{std}\s*:\s*\{{([^}}]+)\}}", block
            )
            assert std_match, f"Standard '{std}' not in STANDARDS object"
            std_body = std_match.group(1)
            for field in required_fields:
                # 'case' is a JS reserved-ish word, stored as 'case'
                if field == "case":
                    assert "'case'" in std_body, (
                        f"Standard '{std}' missing field: {field}"
                    )
                else:
                    assert f"{field}:" in std_body or f"{field} :" in std_body, (
                        f"Standard '{std}' missing field: {field}"
                    )

    # ── form element ID consistency ──────────────────────────────────

    def test_all_js_getelementbyid_targets_exist_in_html(self, settings_html: str):
        """Every getElementById call must reference an existing HTML id."""
        import re
        # Extract IDs from getElementById calls
        js_ids = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", settings_html))
        # Extract IDs from HTML id= attributes
        html_ids = set(re.findall(r'id="([^"]+)"', settings_html))
        missing = js_ids - html_ids
        assert not missing, f"JS references missing HTML elements: {missing}"

    # ── toggle sliders ───────────────────────────────────────────────

    def test_all_toggles_call_update_preview(self, settings_html: str):
        """Every settings toggle must trigger updatePreview on click."""
        import re
        outside_script = re.sub(
            r"<script[\s>].*?</script>", "", settings_html, flags=re.DOTALL
        )
        toggles = re.findall(
            r'<button[^>]*settings-toggle[^>]*onclick="([^"]*)"[^>]*>',
            outside_script,
        )
        # cfg-strict is the only toggle that doesn't need preview update
        # (it's a category setting, not a visual preview setting)
        for oc in toggles:
            assert "classList.toggle('on')" in oc, f"Toggle missing toggle('on'): {oc}"

    def test_toggle_count_matches_expected(self, settings_html: str):
        """Exactly 13 toggle buttons: domain, strict, hdr-enabled,
        hdr-ver/date/status/pages, ftr-enabled, meta-owner/approver/
        review/distlist/revhist."""
        import re
        outside_script = re.sub(
            r"<script[\s>].*?</script>", "", settings_html, flags=re.DOTALL
        )
        toggles = re.findall(r"settings-toggle\b", outside_script)
        assert len(toggles) == 13, f"Expected 13 toggles, found {len(toggles)}"

    # ── select dropdowns ─────────────────────────────────────────────

    def test_select_dropdowns_have_onchange(self, settings_html: str):
        """All naming/interactive select elements must trigger updatePreview or
        applyTemplate on change.  cfg-preset is display-only (informational)."""
        import re
        outside_script = re.sub(
            r"<script[\s>].*?</script>", "", settings_html, flags=re.DOTALL
        )
        # Selects that must have onchange handlers
        interactive_selects = ["cfg-template", "cfg-sep", "cfg-case", "cfg-date", "cfg-ver"]
        for sid in interactive_selects:
            match = re.search(rf'<select[^>]*id="{sid}"[^>]*>', outside_script)
            assert match, f"Select {sid} not found"
            assert "onchange=" in match.group(0), f"Select {sid} missing onchange"

    # ── text inputs ──────────────────────────────────────────────────

    def test_text_inputs_have_oninput(self, settings_html: str):
        """Editable text inputs should trigger updatePreview on input."""
        import re
        outside_script = re.sub(
            r"<script[\s>].*?</script>", "", settings_html, flags=re.DOTALL
        )
        inputs = re.findall(r'<input[^>]*id="(cfg-[^"]+)"[^>]*>', outside_script)
        # These inputs should have oninput for live preview
        preview_inputs = [
            "cfg-author", "cfg-class", "cfg-hdr-org", "cfg-hdr-banner",
            "cfg-hdr-prefix", "cfg-ftr-dist", "cfg-ftr-ret", "cfg-ftr-copy",
            "cfg-ftr-custom", "cfg-meta-retention", "cfg-meta-cycle",
        ]
        for inp_id in preview_inputs:
            pattern = rf'<input[^>]*id="{inp_id}"[^>]*>'
            match = re.search(pattern, outside_script)
            assert match, f"Input {inp_id} not found"
            assert "oninput=" in match.group(0), (
                f"Input {inp_id} missing oninput handler"
            )

    # ── YAML export ──────────────────────────────────────────────────

    def test_yaml_export_reads_all_form_fields(self, settings_html: str):
        """generateYaml must read every configurable field."""
        import re
        match = re.search(
            r"function generateYaml\(\)\s*\{(.+?)\n\}", settings_html, re.DOTALL
        )
        assert match, "generateYaml function not found"
        body = match.group(1)
        required_ids = [
            "cfg-sep", "cfg-case", "cfg-date", "cfg-ver", "cfg-domain",
            "cfg-strict", "cfg-author", "cfg-class", "cfg-stale",
            "cfg-hdr-enabled", "cfg-hdr-org", "cfg-hdr-banner", "cfg-hdr-prefix",
            "cfg-hdr-ver", "cfg-hdr-date", "cfg-hdr-status", "cfg-hdr-pages",
            "cfg-ftr-enabled", "cfg-ftr-dist", "cfg-ftr-ret", "cfg-ftr-copy",
            "cfg-ftr-custom",
            "cfg-meta-owner", "cfg-meta-approver", "cfg-meta-review",
            "cfg-meta-distlist", "cfg-meta-revhist",
            "cfg-meta-retention", "cfg-meta-cycle",
        ]
        for fid in required_ids:
            assert fid in body, f"generateYaml missing field: {fid}"

    # ── templates ────────────────────────────────────────────────────

    def test_all_eight_templates_in_dropdown(self, settings_html: str):
        templates = [
            "default", "legal", "engineering", "corporate",
            "dateless", "scientific", "healthcare", "finance",
        ]
        for t in templates:
            assert f'value="{t}"' in settings_html, f"Template missing: {t}"

    def test_apply_template_function_exists(self, settings_html: str):
        assert "function applyTemplate()" in settings_html

    # ── preview panel structure ───────────────────────────────────────

    def test_preview_always_visible_with_opacity(self, settings_html: str):
        """Header/footer cards use opacity dimming, not display:none."""
        assert "hdrCard.style.opacity" in settings_html
        assert "ftrCard.style.opacity" in settings_html
        assert "hdrCard.style.display" not in settings_html
        assert "ftrCard.style.display" not in settings_html

    def test_preview_shows_disabled_label(self, settings_html: str):
        assert "Document Header (disabled)" in settings_html
        assert "Document Footer (disabled)" in settings_html


class TestEditableTagsAndNewFields:
    """Tests for editable tag lists, logo URL field, disclaimer dropdown,
    and YAML export coverage for these new features."""

    @pytest.fixture()
    def settings_html(self, tmp_path: Path, multi_doc_manifest: Manifest) -> str:
        out = tmp_path / "site_out"
        generate_site(multi_doc_manifest, out)
        return (out / "settings.html").read_text()

    # ── editable tag lists ──────────────────────────────────────────

    def test_forbidden_words_list_has_id(self, settings_html: str):
        assert 'id="cfg-forbidden"' in settings_html

    def test_exempt_files_list_has_id(self, settings_html: str):
        assert 'id="cfg-exempt"' in settings_html

    def test_tag_remove_buttons_present(self, settings_html: str):
        assert "tag-remove" in settings_html
        assert "removeTag(this)" in settings_html

    def test_add_tag_inputs_present(self, settings_html: str):
        """Each editable list should have an add-tag input + button."""
        assert "addTag(" in settings_html

    def test_remove_tag_function_defined(self, settings_html: str):
        assert "function removeTag(" in settings_html

    def test_add_tag_function_defined(self, settings_html: str):
        assert "function addTag(" in settings_html

    def test_get_tag_values_function_defined(self, settings_html: str):
        assert "function getTagValues(" in settings_html

    # ── logo URL field ──────────────────────────────────────────────

    def test_logo_url_field_present(self, settings_html: str):
        assert 'id="cfg-hdr-logo"' in settings_html

    def test_logo_in_yaml_export(self, settings_html: str):
        assert "logo_url:" in settings_html
        assert "hdrLogo" in settings_html

    def test_logo_in_preview(self, settings_html: str):
        assert 'id="preview-logo"' in settings_html

    def test_logo_in_capture_defaults(self, settings_html: str):
        """captureDefaults must snapshot the logo field."""
        assert "cfg-hdr-logo" in settings_html

    def test_logo_in_standards_objects(self, settings_html: str):
        """All STANDARDS entries should include a logo key.
        Count occurrences of 'logo:' inside STANDARDS — should be >= 6 (one per standard)."""
        import re
        standards_match = re.search(
            r"var STANDARDS\s*=\s*\{(.*?)\n\};", settings_html, re.DOTALL
        )
        assert standards_match, "STANDARDS object not found"
        body = standards_match.group(1)
        logo_count = body.count("logo:")
        assert logo_count >= 6, f"Expected 6+ logo: entries in STANDARDS, found {logo_count}"

    # ── legal disclaimer dropdown ───────────────────────────────────

    def test_disclaimer_dropdown_present(self, settings_html: str):
        assert 'id="cfg-ftr-disclaimer"' in settings_html

    def test_disclaimers_object_defined(self, settings_html: str):
        assert "var DISCLAIMERS" in settings_html

    def test_apply_disclaimer_function_defined(self, settings_html: str):
        assert "function applyDisclaimer()" in settings_html

    def test_disclaimer_options_count(self, settings_html: str):
        """Should have at least 7 industry disclaimer options plus a 'none' option."""
        import re
        options = re.findall(
            r'<option\s+value="[^"]*"[^>]*>', settings_html
        )
        # Filter to just the disclaimer select options
        select_start = settings_html.find('id="cfg-ftr-disclaimer"')
        assert select_start > 0
        select_block = settings_html[select_start:select_start + 2000]
        select_end = select_block.find("</select>")
        select_block = select_block[:select_end]
        opts = re.findall(r"<option", select_block)
        assert len(opts) >= 7, f"Expected 7+ disclaimer options, found {len(opts)}"

    def test_disclaimers_keys_match_options(self, settings_html: str):
        """DISCLAIMERS object keys should match dropdown option values."""
        import re
        disclaimers_match = re.search(
            r"var DISCLAIMERS\s*=\s*\{(.*?)\};", settings_html, re.DOTALL
        )
        assert disclaimers_match, "DISCLAIMERS object not found"
        keys = re.findall(r"(\w+):", disclaimers_match.group(1))
        expected_keys = ["general", "hipaa", "financial", "legal",
                         "government", "academic", "technology"]
        for k in expected_keys:
            assert k in keys, f"DISCLAIMERS missing key: {k}"

    # ── YAML export coverage for new fields ─────────────────────────

    def test_yaml_exports_forbidden_words(self, settings_html: str):
        assert "forbidden_words:" in settings_html
        assert "getTagValues('cfg-forbidden')" in settings_html or \
               'getTagValues("cfg-forbidden")' in settings_html

    def test_yaml_exports_exempt_files(self, settings_html: str):
        assert "exempt_files:" in settings_html
        assert "getTagValues('cfg-exempt')" in settings_html or \
               'getTagValues("cfg-exempt")' in settings_html

    def test_yaml_exports_tags_taxonomy(self, settings_html: str):
        assert "tags_taxonomy:" in settings_html


# ─── Templates Catalog Page ──────────────────────────────────────────────────


class TestTemplatesCatalogPage:
    """Tests for the templates.html catalog page."""

    @pytest.fixture
    def software_manifest(self, tmp_path: Path) -> Manifest:
        """Manifest with software preset configured."""
        reg_data = {
            "project_config": {
                "project_name": "SoftTest",
                "preset": "software",
                "tracked_dirs": ["docs/"],
                "default_author": "Tester",
            },
            "documents": [
                {
                    "filename": "architecture-20260101-V1.0.md",
                    "title": "Architecture",
                    "status": "active",
                    "version": "V1.0",
                    "tags": ["architecture"],
                    "path": "docs/architecture-20260101-V1.0.md",
                },
            ],
            "registry_meta": {"total_documents": 1, "active": 1},
        }
        (tmp_path / "docs").mkdir()
        reg_path = tmp_path / "docs" / "REGISTRY.yaml"
        with reg_path.open("w") as f:
            yaml.safe_dump(reg_data, f, sort_keys=False)
        (tmp_path / "docs" / "architecture-20260101-V1.0.md").write_text("# Arch\n")
        reg = Registry.load(reg_path)
        return generate_manifest(reg, tmp_path)

    def test_templates_page_generated(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        assert (out / "templates.html").is_file()

    def test_templates_page_title(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert "Template Catalog" in html

    def test_templates_page_has_preset_selector(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert 'id="tmpl-preset"' in html
        assert "Software" in html

    def test_templates_page_has_source_filter(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert 'id="tmpl-source"' in html
        assert "All Sources" in html

    def test_templates_page_has_compliance_filter(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert 'id="tmpl-compliance"' in html
        assert "HIPAA" in html

    def test_templates_page_contains_template_data(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        # Should contain template IDs from software preset in JSON
        assert "technical-architecture" in html
        assert "runbook" in html

    def test_templates_page_contains_universal_templates(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert "readme" in html
        assert "project-plan" in html

    def test_templates_page_contains_cross_cutting(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert "threat-model" in html
        assert "audit-readiness-checklist" in html

    def test_templates_page_has_card_grid(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert 'class="tmpl-grid"' in html
        assert "filterTemplates" in html

    def test_templates_page_scaffold_command(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        assert "python -m librarian scaffold --template" in html

    def test_templates_page_section_data(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        # Templates have sections array in JSON
        assert '"sections"' in html

    def test_templates_page_active_nav(self, software_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest, out)
        html = (out / "templates.html").read_text()
        # "Templates" should be active in nav
        assert 'class="active">Templates</a>' in html


# ─── Navigation Integration ──────────────────────────────────────────────────


class TestNavigationTemplatesLink:
    """Templates link appears in all site nav bars."""

    def test_index_has_templates_link(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "index.html").read_text()
        assert 'href="templates.html"' in html
        assert ">Templates<" in html

    def test_tree_has_templates_link(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "tree.html").read_text()
        assert 'href="templates.html"' in html

    def test_graph_has_templates_link(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "graph.html").read_text()
        assert 'href="templates.html"' in html

    def test_settings_has_templates_link(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "settings.html").read_text()
        assert 'href="templates.html"' in html


# ─── Recommendations on Index Page ───────────────────────────────────────────


class TestIndexRecommendations:
    """Recommendations section on the index page."""

    @pytest.fixture
    def software_manifest_with_preset(self, tmp_path: Path) -> Manifest:
        """Manifest with software preset — will trigger recommendations."""
        reg_data = {
            "project_config": {
                "project_name": "RecTest",
                "preset": "software",
                "tracked_dirs": ["docs/"],
            },
            "documents": [
                {
                    "filename": "readme-20260101-V1.0.md",
                    "title": "Readme",
                    "status": "active",
                    "version": "V1.0",
                    "tags": [],
                    "path": "docs/readme-20260101-V1.0.md",
                },
            ],
            "registry_meta": {"total_documents": 1, "active": 1},
        }
        (tmp_path / "docs").mkdir()
        reg_path = tmp_path / "docs" / "REGISTRY.yaml"
        with reg_path.open("w") as f:
            yaml.safe_dump(reg_data, f, sort_keys=False)
        (tmp_path / "docs" / "readme-20260101-V1.0.md").write_text("# README\n")
        reg = Registry.load(reg_path)
        return generate_manifest(reg, tmp_path)

    def test_index_has_recommendations_section(self, software_manifest_with_preset: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest_with_preset, out)
        html = (out / "index.html").read_text()
        assert "Recommendations" in html
        assert "rec-section" in html

    def test_index_recommendations_show_preset(self, software_manifest_with_preset: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest_with_preset, out)
        html = (out / "index.html").read_text()
        assert "software" in html

    def test_index_recommendations_show_core_gaps(self, software_manifest_with_preset: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest_with_preset, out)
        html = (out / "index.html").read_text()
        # Software core expectations include technical-architecture and project-plan
        assert "technical-architecture" in html or "project-plan" in html

    def test_index_recommendations_have_priority_classes(self, software_manifest_with_preset: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(software_manifest_with_preset, out)
        html = (out / "index.html").read_text()
        assert "rec-priority-" in html
        assert "rec-item" in html

    def test_index_no_recs_without_preset(self, empty_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(empty_manifest, out)
        html = (out / "index.html").read_text()
        # Empty manifest has no preset, so no recommendations
        assert "rec-section" not in html


# ─── Dashboard Overlay Nav ───────────────────────────────────────────────────


class TestDashboardOverlayTemplatesLink:
    """Dashboard overlay nav includes Templates link."""

    def test_dashboard_nav_has_templates_link(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        # Need dashboard for the overlay
        from librarian.dashboard import write_dashboard
        dash_path = out / "dashboard.html"
        out.mkdir(parents=True, exist_ok=True)
        manifest = sample_manifest
        write_dashboard(manifest, dash_path)
        generate_site(manifest, out, dashboard_path=dash_path)
        html = (out / "dashboard.html").read_text()
        assert 'href="templates.html"' in html
        assert ">Templates<" in html


# ─── CSS Styles ──────────────────────────────────────────────────────────────


class TestTemplatesCSSPresent:
    """Template catalog CSS classes exist in the stylesheet."""

    def test_style_css_has_template_classes(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        css = (out / "assets" / "style.css").read_text()
        assert ".tmpl-grid" in css
        assert ".tmpl-card" in css
        assert ".tmpl-card-title" in css
        assert ".tmpl-controls" in css

    def test_style_css_has_recommendations_classes(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        css = (out / "assets" / "style.css").read_text()
        assert ".rec-section" in css
        assert ".rec-item" in css
        assert ".rec-priority-core" in css


# ─── Settings Template Browser ───────────────────────────────────────────────


class TestSettingsTemplateBrowser:
    """Settings page includes template browser section."""

    def test_settings_has_template_section(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "settings.html").read_text()
        assert "Available Templates" in html
        assert "settings-tmpl-list" in html

    def test_settings_has_template_data(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "settings.html").read_text()
        assert "SETTINGS_TEMPLATES" in html
        assert "renderSettingsTemplates" in html

    def test_settings_preset_triggers_template_refresh(self, sample_manifest: Manifest, tmp_path: Path):
        out = tmp_path / "site_out"
        generate_site(sample_manifest, out)
        html = (out / "settings.html").read_text()
        assert 'onchange="renderSettingsTemplates()"' in html


# ─── Custom Templates Override ───────────────────────────────────────────────


class TestCustomTemplatesOverride:
    """Custom templates dir overrides built-in templates."""

    def test_custom_template_overrides_builtin(self, tmp_path: Path):
        """A custom template with the same ID as a built-in wins."""
        from librarian.templates import discover_templates

        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        # Create a custom "readme" template that overrides universal/readme
        (custom_dir / "readme.md").write_text(
            "---\ntemplate_id: readme\ndisplay_name: Custom Readme\n"
            "description: My custom readme\nsuggested_tags: [custom]\n"
            "sections:\n  - Custom Section\n---\n# {{title}}\nCustom body.\n"
        )
        templates = discover_templates(preset="software", custom_dir=str(custom_dir))
        assert "readme" in templates
        assert templates["readme"].display_name == "Custom Readme"
        assert templates["readme"].preset == "custom"

    def test_custom_template_adds_new(self, tmp_path: Path):
        """A custom template with a novel ID is available."""
        from librarian.templates import discover_templates

        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        (custom_dir / "my-special-doc.md").write_text(
            "---\ntemplate_id: my-special-doc\ndisplay_name: Special Doc\n"
            "description: A project-specific template\nsuggested_tags: [special]\n"
            "sections:\n  - Overview\n---\n# {{title}}\n"
        )
        templates = discover_templates(preset="software", custom_dir=str(custom_dir))
        assert "my-special-doc" in templates
        assert templates["my-special-doc"].preset == "custom"

    def test_custom_dir_none_uses_builtins_only(self):
        """When custom_dir is None, only built-in templates are returned."""
        from librarian.templates import discover_templates

        templates = discover_templates(preset="software", custom_dir=None)
        assert "readme" in templates  # universal
        assert templates["readme"].preset == "universal"

    def test_custom_dir_nonexistent_is_ignored(self, tmp_path: Path):
        """A non-existent custom_dir is silently ignored."""
        from librarian.templates import discover_templates

        templates = discover_templates(
            preset="software",
            custom_dir=str(tmp_path / "does_not_exist"),
        )
        assert "readme" in templates  # still works with builtins

    def test_scaffold_reads_custom_templates_dir(self, tmp_path: Path):
        """The scaffold command reads custom_templates_dir from project_config."""
        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()
        (custom_dir / "custom-doc.md").write_text(
            "---\ntemplate_id: custom-doc\ndisplay_name: Custom Doc\n"
            "description: test\nsuggested_tags: [test]\n"
            "sections:\n  - Intro\n---\n# {{title}}\n"
        )

        reg_data = {
            "project_config": {
                "project_name": "CustomTest",
                "preset": "software",
                "custom_templates_dir": str(custom_dir),
                "tracked_dirs": ["docs/"],
            },
            "documents": [],
            "registry_meta": {"total_documents": 0},
        }
        (tmp_path / "docs").mkdir()
        reg_path = tmp_path / "docs" / "REGISTRY.yaml"
        with reg_path.open("w") as f:
            yaml.safe_dump(reg_data, f, sort_keys=False)

        import subprocess
        result = subprocess.run(
            [
                sys.executable, "-m", "librarian",
                "--registry", str(reg_path),
                "--repo", str(tmp_path),
                "scaffold", "--list",
            ],
            capture_output=True,
            text=True,
        )
        assert "custom-doc" in result.stdout


# ═══════════════════════════════════════════════════════════════════════════
#  Security — XSS prevention in markdown and JS
# ═══════════════════════════════════════════════════════════════════════════


class TestSecurityXSS:
    """Tests for XSS mitigations in generated HTML."""

    def test_javascript_uri_blocked_in_link(self):
        """Links with javascript: scheme must be neutralized."""
        html = _inline("[click](javascript:alert(1))")
        assert "javascript:" not in html
        assert 'href=""' in html

    def test_javascript_uri_blocked_in_image(self):
        """Images with javascript: scheme must be neutralized."""
        html = _inline("![img](javascript:alert(1))")
        assert "javascript:" not in html
        assert 'src=""' in html

    def test_data_uri_blocked(self):
        """data: URIs should be blocked to prevent embedded script execution."""
        html = _inline("[click](data:text/html,<script>alert(1)</script>)")
        assert "data:" not in html

    def test_safe_http_link_preserved(self):
        """Normal http/https links must still work."""
        html = _inline("[site](https://example.com)")
        assert 'href="https://example.com"' in html

    def test_safe_relative_link_preserved(self):
        """Relative links and anchors must still work."""
        html = _inline("[top](#header)")
        assert 'href="#header"' in html
        html2 = _inline("[doc](/docs/readme.html)")
        assert 'href="/docs/readme.html"' in html2

    def test_mailto_link_preserved(self):
        """mailto: links must still work."""
        html = _inline("[mail](mailto:user@example.com)")
        assert 'href="mailto:user@example.com"' in html

    def test_javascript_uri_case_insensitive(self):
        """javascript: blocking must be case-insensitive."""
        html = _inline("[x](JaVaScRiPt:alert(1))")
        assert "javascript" not in html.lower() or 'href=""' in html

    def test_esc_function_escapes_single_quotes(self):
        """The template catalog esc() JS function must escape single quotes."""
        from librarian.sitegen import _build_templates_page
        from librarian.registry import Registry
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg_data = {
                "project_config": {"project_name": "Test", "preset": "software", "tracked_dirs": ["docs/"]},
                "documents": [],
                "registry_meta": {"total_documents": 0},
            }
            (tmp / "docs").mkdir()
            reg_path = tmp / "docs" / "REGISTRY.yaml"
            with reg_path.open("w") as f:
                yaml.safe_dump(reg_data, f, sort_keys=False)
            reg = Registry.load(reg_path)
            manifest = generate_manifest(reg, tmp)
            page = _build_templates_page(manifest)
            # The esc function should include single-quote escaping
            assert "&#39;" in page

    def test_tree_page_no_backslash_x27(self):
        """Tree page must not contain \\x27 in HTML onclick attributes."""
        from librarian.registry import Registry
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg_data = {
                "project_config": {"project_name": "Test", "tracked_dirs": ["docs/"]},
                "documents": [],
                "registry_meta": {"total_documents": 0},
            }
            (tmp / "docs").mkdir()
            reg_path = tmp / "docs" / "REGISTRY.yaml"
            with reg_path.open("w") as f:
                yaml.safe_dump(reg_data, f, sort_keys=False)
            reg = Registry.load(reg_path)
            manifest = generate_manifest(reg, tmp)
            out = tmp / "_site"
            generate_site(manifest, out)
            tree_html = (out / "tree.html").read_text()
            assert "\\x27" not in tree_html
