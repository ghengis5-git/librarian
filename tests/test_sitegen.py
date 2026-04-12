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
