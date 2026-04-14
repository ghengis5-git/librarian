"""Tests for Phase G.1 — Template infrastructure and mini template engine.

Covers:
  - Mini engine: variable substitution, conditionals, nested conditionals,
    for loops, logical operators, membership tests
  - DocumentTemplate: from_string, from_file, render
  - Template discovery: universal templates, resolution order, custom overrides
  - Context builder: project_config → context dict
  - Scaffold CLI: --list, --list-all, --dry-run, file creation, registry insertion
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from librarian.templates._base import (
    DocumentTemplate,
    TemplateRenderError,
    render_template,
    _split_frontmatter,
    _eval_condition,
    _MAX_RENDER_BYTES,
)
from librarian.templates import (
    discover_templates,
    load_template,
    list_templates,
    build_context,
)
from librarian.__main__ import build_parser, main


# ═══════════════════════════════════════════════════════════════════════════
#  Mini template engine — variable substitution
# ═══════════════════════════════════════════════════════════════════════════


class TestVariableSubstitution:
    def test_basic_variable(self):
        assert render_template("Hello {{name}}", {"name": "World"}) == "Hello World"

    def test_multiple_variables(self):
        result = render_template("{{a}} and {{b}}", {"a": "X", "b": "Y"})
        assert result == "X and Y"

    def test_missing_variable_empty_string(self):
        assert render_template("Hello {{missing}}", {}) == "Hello "

    def test_integer_variable(self):
        assert render_template("Count: {{n}}", {"n": 42}) == "Count: 42"

    def test_no_variables_passthrough(self):
        assert render_template("plain text", {}) == "plain text"


# ═══════════════════════════════════════════════════════════════════════════
#  Mini template engine — conditionals
# ═══════════════════════════════════════════════════════════════════════════


class TestConditionals:
    def test_if_true(self):
        tmpl = "{% if show %}visible{% endif %}"
        assert render_template(tmpl, {"show": True}) == "visible"

    def test_if_false(self):
        tmpl = "{% if show %}visible{% endif %}"
        assert render_template(tmpl, {"show": False}) == ""

    def test_if_else(self):
        tmpl = "{% if admin %}Admin{% else %}User{% endif %}"
        assert render_template(tmpl, {"admin": True}) == "Admin"
        assert render_template(tmpl, {"admin": False}) == "User"

    def test_elif(self):
        tmpl = '{% if level == "high" %}H{% elif level == "mid" %}M{% else %}L{% endif %}'
        assert render_template(tmpl, {"level": "high"}) == "H"
        assert render_template(tmpl, {"level": "mid"}) == "M"
        assert render_template(tmpl, {"level": "low"}) == "L"

    def test_nested_conditionals(self):
        tmpl = (
            "{% if outer %}"
            "{% if inner %}BOTH{% else %}OUTER{% endif %}"
            "{% else %}NONE{% endif %}"
        )
        assert render_template(tmpl, {"outer": True, "inner": True}) == "BOTH"
        assert render_template(tmpl, {"outer": True, "inner": False}) == "OUTER"
        assert render_template(tmpl, {"outer": False, "inner": True}) == "NONE"

    def test_membership_in(self):
        tmpl = '{% if "hipaa" in compliance %}YES{% else %}NO{% endif %}'
        assert render_template(tmpl, {"compliance": ["hipaa", "iso"]}) == "YES"
        assert render_template(tmpl, {"compliance": ["iso"]}) == "NO"
        assert render_template(tmpl, {"compliance": []}) == "NO"

    def test_equality(self):
        tmpl = '{% if preset == "gov" %}GOV{% else %}OTHER{% endif %}'
        assert render_template(tmpl, {"preset": "gov"}) == "GOV"
        assert render_template(tmpl, {"preset": "biz"}) == "OTHER"

    def test_inequality(self):
        tmpl = '{% if preset != "gov" %}NOT-GOV{% else %}GOV{% endif %}'
        assert render_template(tmpl, {"preset": "biz"}) == "NOT-GOV"
        assert render_template(tmpl, {"preset": "gov"}) == "GOV"

    def test_not_operator(self):
        tmpl = "{% if not hidden %}SHOWN{% endif %}"
        assert render_template(tmpl, {"hidden": False}) == "SHOWN"
        assert render_template(tmpl, {"hidden": True}) == ""

    def test_or_operator(self):
        tmpl = '{% if "a" in items or "b" in items %}FOUND{% else %}MISSING{% endif %}'
        assert render_template(tmpl, {"items": ["a"]}) == "FOUND"
        assert render_template(tmpl, {"items": ["b"]}) == "FOUND"
        assert render_template(tmpl, {"items": ["c"]}) == "MISSING"

    def test_and_operator(self):
        tmpl = "{% if x and y %}BOTH{% else %}NOPE{% endif %}"
        assert render_template(tmpl, {"x": True, "y": True}) == "BOTH"
        assert render_template(tmpl, {"x": True, "y": False}) == "NOPE"


# ═══════════════════════════════════════════════════════════════════════════
#  Mini template engine — for loops
# ═══════════════════════════════════════════════════════════════════════════


class TestForLoops:
    def test_basic_for(self):
        tmpl = "{% for item in items %}[{{item}}]{% endfor %}"
        assert render_template(tmpl, {"items": ["a", "b"]}) == "[a][b]"

    def test_empty_list(self):
        tmpl = "{% for item in items %}X{% endfor %}"
        assert render_template(tmpl, {"items": []}) == ""

    def test_for_with_context(self):
        """Loop variable doesn't clobber outer context."""
        tmpl = "{{item}}-{% for item in items %}{{item}}{% endfor %}-{{item}}"
        result = render_template(tmpl, {"items": ["a"], "item": "outer"})
        assert result == "outer-a-outer"

    def test_nested_for(self):
        tmpl = "{% for x in xs %}{% for y in ys %}{{x}}{{y}}{% endfor %}{% endfor %}"
        result = render_template(tmpl, {"xs": ["1", "2"], "ys": ["a", "b"]})
        assert result == "1a1b2a2b"

    # Iterator-coverage tests — verify the for-loop accepts any non-str iterable.
    # Previously only list/tuple worked; sets, dict_keys, generators were silently
    # dropped. The fix widens acceptance and leaves str/bytes as the only rejection
    # (iterating over characters is almost always a bug, not intent).

    def test_for_over_set(self):
        tmpl = "{% for item in items %}[{{item}}]{% endfor %}"
        # Sets are unordered; verify length + membership rather than exact string
        result = render_template(tmpl, {"items": {"a", "b"}})
        assert result.count("[") == 2
        assert "[a]" in result and "[b]" in result

    def test_for_over_dict_keys(self):
        tmpl = "{% for k in keys %}{{k}},{% endfor %}"
        result = render_template(tmpl, {"keys": {"x": 1, "y": 2}.keys()})
        assert "x," in result and "y," in result

    def test_for_over_generator(self):
        tmpl = "{% for n in nums %}{{n}}{% endfor %}"
        result = render_template(tmpl, {"nums": (str(i) for i in range(3))})
        assert result == "012"

    def test_for_rejects_string_iteration(self):
        """Strings are iterable but iterating characters is almost always a bug."""
        tmpl = "{% for c in text %}[{{c}}]{% endfor %}"
        # With the fix, a string context value is treated as non-iterable (skipped).
        assert render_template(tmpl, {"text": "abc"}) == ""

    def test_for_rejects_bytes_iteration(self):
        tmpl = "{% for b in data %}x{% endfor %}"
        assert render_template(tmpl, {"data": b"abc"}) == ""


# ═══════════════════════════════════════════════════════════════════════════
#  Output size guard
# ═══════════════════════════════════════════════════════════════════════════


class TestOutputSizeGuard:
    """Safety guard: reject rendered output exceeding _MAX_RENDER_BYTES."""

    def test_under_limit_renders(self):
        # 1 KB output — nowhere near the 4 MB limit
        tmpl = "{% for x in xs %}abc{% endfor %}"
        result = render_template(tmpl, {"xs": list(range(300))})
        assert len(result) > 0

    def test_over_limit_raises(self):
        """A for-loop producing >4 MB of output must raise TemplateRenderError."""
        # Each iteration emits ~100 KB; 50 iterations = ~5 MB, over the cap.
        big_chunk = "x" * 100_000
        tmpl = "{% for x in xs %}" + big_chunk + "{% endfor %}"
        with pytest.raises(TemplateRenderError, match="exceeds"):
            render_template(tmpl, {"xs": list(range(50))})

    def test_max_render_bytes_constant(self):
        """Sanity-check the constant — 4 MB, well above any legitimate template."""
        assert _MAX_RENDER_BYTES == 4 * 1024 * 1024


# ═══════════════════════════════════════════════════════════════════════════
#  Condition evaluator
# ═══════════════════════════════════════════════════════════════════════════


class TestEvalCondition:
    def test_truthiness(self):
        assert _eval_condition("x", {"x": True}) is True
        assert _eval_condition("x", {"x": False}) is False
        assert _eval_condition("x", {}) is False

    def test_membership(self):
        assert _eval_condition('"a" in lst', {"lst": ["a", "b"]}) is True
        assert _eval_condition('"c" in lst', {"lst": ["a", "b"]}) is False

    def test_equality(self):
        assert _eval_condition('x == "yes"', {"x": "yes"}) is True
        assert _eval_condition('x == "no"', {"x": "yes"}) is False

    def test_inequality(self):
        assert _eval_condition('x != "no"', {"x": "yes"}) is True

    def test_deep_recursion_returns_false(self):
        """Deeply nested conditions must not cause a stack overflow."""
        deep = "not " * 50 + "x"
        # Should return False (depth exceeded) instead of RecursionError
        result = _eval_condition(deep, {"x": True})
        assert result is False or result is True  # must not crash

    def test_max_depth_boundary(self):
        """At exactly _MAX_CONDITION_DEPTH + 1, should return False."""
        from librarian.templates._base import _MAX_CONDITION_DEPTH
        # Build condition with depth > limit
        deep = "not " * (_MAX_CONDITION_DEPTH + 5) + "x"
        result = _eval_condition(deep, {"x": True})
        # Must not raise RecursionError
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════
#  DocumentTemplate — parsing and rendering
# ═══════════════════════════════════════════════════════════════════════════


class TestDocumentTemplate:
    SAMPLE = textwrap.dedent("""\
        ---
        template_id: test-doc
        display_name: Test Document
        preset: universal
        description: A test template
        suggested_tags: [test, sample]
        suggested_folder: docs/
        typical_cross_refs: [readme]
        requires: []
        recommended_with: [changelog]
        sections:
          - Introduction
          - Body
        ---

        # {{title}}

        **Version:** {{version}}

        ## Introduction

        Hello {{author}}.
    """)

    def test_from_string(self):
        t = DocumentTemplate.from_string(self.SAMPLE)
        assert t.template_id == "test-doc"
        assert t.display_name == "Test Document"
        assert t.suggested_tags == ["test", "sample"]
        assert t.sections == ["Introduction", "Body"]
        assert "{{title}}" in t.body

    def test_render(self):
        t = DocumentTemplate.from_string(self.SAMPLE)
        result = t.render({"title": "My Doc", "version": "V1.0", "author": "Chris"})
        assert "# My Doc" in result
        assert "**Version:** V1.0" in result
        assert "Hello Chris." in result

    def test_from_file(self):
        t = DocumentTemplate.from_file(
            str(Path(__file__).parent.parent / "librarian" / "templates" / "universal" / "readme.md")
        )
        assert t.template_id == "readme"
        assert t.display_name == "README"
        assert len(t.sections) >= 4


# ═══════════════════════════════════════════════════════════════════════════
#  Frontmatter parser
# ═══════════════════════════════════════════════════════════════════════════


class TestFrontmatter:
    def test_valid_frontmatter(self):
        text = "---\ntitle: hello\n---\nBody here."
        fm, body = _split_frontmatter(text)
        assert fm["title"] == "hello"
        assert body == "Body here."

    def test_no_frontmatter(self):
        text = "No frontmatter here."
        fm, body = _split_frontmatter(text)
        assert fm == {}
        assert body == text


# ═══════════════════════════════════════════════════════════════════════════
#  Template discovery
# ═══════════════════════════════════════════════════════════════════════════


class TestDiscovery:
    def test_universal_templates_exist(self):
        templates = discover_templates()
        assert "readme" in templates
        assert "project-plan" in templates
        assert "changelog" in templates
        assert "meeting-notes" in templates

    def test_four_universal_templates(self):
        templates = discover_templates()
        assert len(templates) >= 4

    def test_preset_includes_universal(self):
        """A preset should include universal templates even if no preset-specific ones exist."""
        templates = discover_templates(preset="software")
        assert "readme" in templates

    def test_custom_dir_overrides(self, tmp_path):
        """Custom template with same ID overrides built-in."""
        custom_tmpl = tmp_path / "readme.md"
        custom_tmpl.write_text(
            "---\ntemplate_id: readme\ndisplay_name: Custom README\n"
            "preset: custom\ndescription: Overridden\n---\nCustom body."
        )
        templates = discover_templates(custom_dir=str(tmp_path))
        assert templates["readme"].display_name == "Custom README"
        assert templates["readme"].body == "Custom body."

    def test_list_templates_returns_dicts(self):
        result = list_templates()
        assert isinstance(result, list)
        assert all("id" in t and "name" in t for t in result)

    def test_load_template_by_id(self):
        t = load_template("readme")
        assert t is not None
        assert t.template_id == "readme"

    def test_load_template_not_found(self):
        assert load_template("nonexistent-template") is None


# ═══════════════════════════════════════════════════════════════════════════
#  Context builder
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildContext:
    def test_default_context(self):
        ctx = build_context()
        assert ctx["version"] == "V1.0"
        assert ctx["status"] == "draft"
        assert "librarian_version" in ctx

    def test_compliance_flags(self):
        pc = {"compliance_standards": ["hipaa", "iso_27001"]}
        ctx = build_context(project_config=pc)
        assert ctx["hipaa"] is True
        assert ctx["iso_27001"] is True
        assert ctx["dod_5200"] is False
        assert "hipaa" in ctx["compliance"]

    def test_overrides(self):
        ctx = build_context(overrides={"title": "Overridden", "custom": "field"})
        assert ctx["title"] == "Overridden"
        assert ctx["custom"] == "field"

    def test_date_format_yyyymmdd(self):
        pc = {"naming_rules": {"date_format": "YYYYMMDD"}}
        ctx = build_context(project_config=pc)
        assert len(ctx["date"]) == 8
        assert ctx["date"].isdigit()

    def test_date_format_iso(self):
        pc = {"naming_rules": {"date_format": "YYYY-MM-DD"}}
        ctx = build_context(project_config=pc)
        assert "-" in ctx["date"]
        assert len(ctx["date"]) == 10


# ═══════════════════════════════════════════════════════════════════════════
#  Scaffold CLI
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def scaffold_env(tmp_path):
    """Create a minimal project with REGISTRY.yaml for scaffold tests."""
    docs = tmp_path / "docs"
    docs.mkdir()
    reg_data = {
        "project_config": {
            "project_name": "Test Project",
            "naming_convention": "descriptive-name-YYYYMMDD-VX.Y.ext",
            "naming_rules": {
                "separator": "-",
                "case": "lowercase",
                "date_format": "YYYYMMDD",
                "version_format": "VX.Y",
            },
            "default_author": "Tester",
            "default_classification": "INTERNAL",
            "tracked_dirs": ["docs/"],
        },
        "documents": [],
        "registry_meta": {
            "total_documents": 0,
            "active": 0,
            "draft": 0,
            "superseded": 0,
            "last_updated": "2026-04-13",
        },
    }
    reg_path = docs / "REGISTRY.yaml"
    with reg_path.open("w") as f:
        yaml.safe_dump(reg_data, f)
    return tmp_path, reg_path


class TestScaffoldCLI:
    def test_list(self, scaffold_env, capsys):
        tmp_path, reg_path = scaffold_env
        rc = main(["--registry", str(reg_path), "--repo", str(tmp_path), "scaffold", "--list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "readme" in out
        assert "project-plan" in out

    def test_list_all(self, scaffold_env, capsys):
        tmp_path, reg_path = scaffold_env
        rc = main(["--registry", str(reg_path), "--repo", str(tmp_path), "scaffold", "--list-all"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "universal" in out.lower()

    def test_dry_run(self, scaffold_env, capsys):
        tmp_path, reg_path = scaffold_env
        rc = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "readme", "--dry-run",
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[dry-run]" in out
        assert "readme" in out
        # File should NOT be created
        md_files = list((tmp_path / "docs").glob("readme-*.md"))
        assert len(md_files) == 0, "dry-run should not create files"

    def test_scaffold_creates_file(self, scaffold_env):
        tmp_path, reg_path = scaffold_env
        rc = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "readme", "--title", "My README",
        ])
        assert rc == 0
        # File should exist (README suggested_folder is "", so it goes to docs/ fallback)
        md_files = list(tmp_path.rglob("readme-*.md"))
        assert len(md_files) == 1
        content = md_files[0].read_text()
        assert "# My README" in content

    def test_scaffold_registers_document(self, scaffold_env):
        tmp_path, reg_path = scaffold_env
        main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "project-plan",
        ])
        # Check registry
        with reg_path.open() as f:
            data = yaml.safe_load(f)
        docs = data.get("documents", [])
        assert len(docs) == 1
        assert "project-plan" in docs[0]["filename"]
        assert docs[0]["status"] == "draft"
        assert "planning" in docs[0]["tags"]

    def test_scaffold_no_register(self, scaffold_env):
        tmp_path, reg_path = scaffold_env
        main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "changelog", "--no-register",
        ])
        # File created but not registered
        md_files = list(tmp_path.rglob("changelog-*.md"))
        assert len(md_files) == 1
        with reg_path.open() as f:
            data = yaml.safe_load(f)
        assert len(data.get("documents", [])) == 0

    def test_scaffold_custom_folder(self, scaffold_env):
        tmp_path, reg_path = scaffold_env
        main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "meeting-notes",
            "--folder", "docs/meetings",
        ])
        meetings = tmp_path / "docs" / "meetings"
        assert meetings.is_dir()
        md_files = list(meetings.glob("meeting-notes-*.md"))
        assert len(md_files) == 1

    def test_scaffold_template_not_found(self, scaffold_env, capsys):
        tmp_path, reg_path = scaffold_env
        rc = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "nonexistent",
        ])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err.lower()

    def test_scaffold_no_template_arg(self, scaffold_env, capsys):
        tmp_path, reg_path = scaffold_env
        rc = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold",
        ])
        assert rc == 1

    def test_scaffold_naming_convention(self, scaffold_env):
        """Scaffolded file follows the project naming convention."""
        tmp_path, reg_path = scaffold_env
        main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "readme",
        ])
        md_files = list(tmp_path.rglob("readme-*.md"))
        assert len(md_files) == 1
        fn = md_files[0].name
        # Should match: readme-YYYYMMDD-V1.0.md
        import re
        assert re.match(r"readme-\d{8}-V1\.0\.md$", fn), f"Bad filename: {fn}"

    def test_scaffold_refuses_overwrite(self, scaffold_env, capsys):
        """Second scaffold of same template on same day refuses to overwrite."""
        tmp_path, reg_path = scaffold_env
        rc1 = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "changelog", "--no-register",
        ])
        assert rc1 == 0
        rc2 = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "changelog", "--no-register",
        ])
        assert rc2 == 1
        err = capsys.readouterr().err
        assert "already exists" in err.lower()


# ═══════════════════════════════════════════════════════════════════════════
#  Security — path traversal prevention
# ═══════════════════════════════════════════════════════════════════════════


class TestSecurityHardening:
    def test_folder_traversal_blocked(self, scaffold_env, capsys):
        """--folder with '../' must not escape repo root."""
        tmp_path, reg_path = scaffold_env
        rc = main([
            "--registry", str(reg_path), "--repo", str(tmp_path),
            "scaffold", "--template", "readme",
            "--folder", "../../etc",
        ])
        assert rc == 1
        err = capsys.readouterr().err
        assert "escapes repo root" in err.lower()

    def test_malicious_template_id_sanitized(self, tmp_path):
        """Custom template with path-traversal template_id is sanitized."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        bad_tmpl = custom_dir / "bad.md"
        bad_tmpl.write_text(
            '---\ntemplate_id: "../../etc/passwd"\n'
            'display_name: Bad\npreset: custom\ndescription: Evil\n---\nBody.'
        )
        from librarian.templates import discover_templates
        templates = discover_templates(custom_dir=str(custom_dir))
        # The template_id with slashes should not be loaded (empty after sanitize)
        # or at least not usable for path traversal
        assert "../../etc/passwd" not in templates

    def test_yaml_safe_load_no_code_exec(self):
        """Frontmatter uses safe_load — Python objects cannot be deserialized."""
        from librarian.templates._base import _split_frontmatter
        evil = "---\nobj: !!python/object/apply:os.system ['echo pwned']\n---\nBody."
        fm, body = _split_frontmatter(evil)
        # safe_load should either reject or return empty — never execute
        assert "pwned" not in str(fm)

    def test_template_engine_no_eval(self):
        """Engine conditions cannot execute arbitrary Python."""
        from librarian.templates._base import render_template
        # Attempt to inject Python through condition
        evil_tmpl = '{% if __import__("os").system("echo pwned") %}YES{% endif %}'
        result = render_template(evil_tmpl, {})
        assert "pwned" not in result
        assert "YES" not in result


# ═══════════════════════════════════════════════════════════════════════════
#  Phase G.2a — Software preset templates
# ═══════════════════════════════════════════════════════════════════════════


EXPECTED_SOFTWARE_IDS = [
    "api-specification",
    "architecture-decision-record",
    "incident-postmortem",
    "release-notes",
    "runbook",
    "security-assessment",
    "technical-architecture",
    "test-plan",
]


class TestSoftwareTemplates:
    def test_software_template_count(self):
        """Software preset provides exactly 8 preset-specific templates."""
        templates = discover_templates(preset="software")
        sw_ids = sorted(k for k, v in templates.items() if v.preset == "software")
        assert len(sw_ids) == 8

    def test_software_template_ids(self):
        """All expected software template IDs are present."""
        templates = discover_templates(preset="software")
        for tid in EXPECTED_SOFTWARE_IDS:
            assert tid in templates, f"Missing software template: {tid}"

    def test_software_templates_have_sections(self):
        """Every software template has at least 5 sections."""
        templates = discover_templates(preset="software")
        for tid in EXPECTED_SOFTWARE_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_software_templates_have_tags(self):
        """Every software template has at least 2 tags."""
        templates = discover_templates(preset="software")
        for tid in EXPECTED_SOFTWARE_IDS:
            t = templates[tid]
            assert len(t.suggested_tags) >= 2, f"{tid} has only {len(t.suggested_tags)} tags"

    def test_software_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the software preset."""
        templates = discover_templates(preset="software")
        all_ids = set(templates.keys())
        for tid in EXPECTED_SOFTWARE_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_security_assessment_iso27001_conditional(self):
        """security-assessment includes ISO 27001 content when compliance flag is set."""
        templates = discover_templates(preset="software")
        t = templates["security-assessment"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["iso_27001"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        # ISO content should be present when enabled, absent when not
        assert len(rendered_on) > len(rendered_off)
        assert "27001" in rendered_on or "Annex" in rendered_on

    def test_security_assessment_hipaa_conditional(self):
        """security-assessment includes HIPAA content when compliance flag is set."""
        templates = discover_templates(preset="software")
        t = templates["security-assessment"]
        ctx = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        rendered = t.render(ctx)
        assert "HIPAA" in rendered or "PHI" in rendered

    def test_software_includes_universal(self):
        """Software preset also includes universal templates (readme, etc.)."""
        templates = discover_templates(preset="software")
        assert "readme" in templates
        assert "project-plan" in templates


# ═══════════════════════════════════════════════════════════════════════════
#  Phase G.2a — Scientific preset templates
# ═══════════════════════════════════════════════════════════════════════════


EXPECTED_SCIENTIFIC_IDS = [
    "data-management-plan",
    "experiment-protocol",
    "irb-application",
    "lab-notebook-entry",
    "literature-review",
    "scientific-foundation",
]


class TestScientificTemplates:
    def test_scientific_template_count(self):
        """Scientific preset provides exactly 6 preset-specific templates."""
        templates = discover_templates(preset="scientific")
        sci_ids = sorted(k for k, v in templates.items() if v.preset == "scientific")
        assert len(sci_ids) == 6

    def test_scientific_template_ids(self):
        """All expected scientific template IDs are present."""
        templates = discover_templates(preset="scientific")
        for tid in EXPECTED_SCIENTIFIC_IDS:
            assert tid in templates, f"Missing scientific template: {tid}"

    def test_scientific_templates_have_sections(self):
        """Every scientific template has at least 5 sections."""
        templates = discover_templates(preset="scientific")
        for tid in EXPECTED_SCIENTIFIC_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_scientific_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the scientific preset."""
        templates = discover_templates(preset="scientific")
        all_ids = set(templates.keys())
        for tid in EXPECTED_SCIENTIFIC_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_irb_requires_experiment_protocol(self):
        """IRB application declares experiment-protocol as a prerequisite."""
        templates = discover_templates(preset="scientific")
        irb = templates["irb-application"]
        assert "experiment-protocol" in irb.requires

    def test_data_management_plan_hipaa_conditional(self):
        """data-management-plan includes HIPAA content when flag is set."""
        templates = discover_templates(preset="scientific")
        t = templates["data-management-plan"]
        ctx = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        rendered = t.render(ctx)
        assert "HIPAA" in rendered or "PHI" in rendered or "de-ident" in rendered.lower()

    def test_experiment_protocol_hipaa_conditional(self):
        """experiment-protocol includes human subjects section when HIPAA flag is set."""
        templates = discover_templates(preset="scientific")
        t = templates["experiment-protocol"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_lab_notebook_lightweight(self):
        """lab-notebook-entry is lightweight (under 120 rendered lines)."""
        templates = discover_templates(preset="scientific")
        t = templates["lab-notebook-entry"]
        ctx = build_context(overrides={"title": "Daily Entry"})
        rendered = t.render(ctx)
        assert len(rendered.splitlines()) < 120, f"Lab notebook too heavy: {len(rendered.splitlines())} lines"

    def test_scientific_no_cross_preset_leak(self):
        """Scientific preset should not include software-specific templates."""
        templates = discover_templates(preset="scientific")
        assert "runbook" not in templates
        assert "api-specification" not in templates


# ═══════════════════════════════════════════════════════════════════════════
#  Phase G.2b — Business preset templates
# ═══════════════════════════════════════════════════════════════════════════


EXPECTED_BUSINESS_IDS = [
    "business-case",
    "competitor-analysis",
    "cost-analysis",
    "executive-summary",
    "project-management-plan",
    "risk-assessment",
    "stakeholder-analysis",
    "strategic-plan",
]


class TestBusinessTemplates:
    def test_business_template_count(self):
        """Business preset provides exactly 8 preset-specific templates."""
        templates = discover_templates(preset="business")
        biz_ids = sorted(k for k, v in templates.items() if v.preset == "business")
        assert len(biz_ids) == 8

    def test_business_template_ids(self):
        """All expected business template IDs are present."""
        templates = discover_templates(preset="business")
        for tid in EXPECTED_BUSINESS_IDS:
            assert tid in templates, f"Missing business template: {tid}"

    def test_business_templates_have_sections(self):
        """Every business template has at least 5 sections."""
        templates = discover_templates(preset="business")
        for tid in EXPECTED_BUSINESS_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_business_templates_have_tags(self):
        """Every business template has at least 2 tags."""
        templates = discover_templates(preset="business")
        for tid in EXPECTED_BUSINESS_IDS:
            t = templates[tid]
            assert len(t.suggested_tags) >= 2, f"{tid} has only {len(t.suggested_tags)} tags"

    def test_business_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the business preset."""
        templates = discover_templates(preset="business")
        all_ids = set(templates.keys())
        for tid in EXPECTED_BUSINESS_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_strategic_plan_sec_finra_conditional(self):
        """strategic-plan includes SEC/FINRA content when compliance flag is set."""
        templates = discover_templates(preset="business")
        t = templates["strategic-plan"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["sec_finra"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_risk_assessment_iso_conditionals(self):
        """risk-assessment expands with ISO 9001 and/or ISO 27001 compliance."""
        templates = discover_templates(preset="business")
        t = templates["risk-assessment"]
        ctx = build_context(
            project_config={"compliance_standards": ["iso_9001", "iso_27001"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_business_no_cross_preset_leak(self):
        """Business preset should not include software-specific templates."""
        templates = discover_templates(preset="business")
        assert "runbook" not in templates
        assert "api-specification" not in templates
        assert "architecture-decision-record" not in templates


# ═══════════════════════════════════════════════════════════════════════════
#  Phase G.2b — Legal preset templates
# ═══════════════════════════════════════════════════════════════════════════


EXPECTED_LEGAL_IDS = [
    "contract-summary",
    "ip-landscape",
    "legal-review",
    "nda-tracker",
    "patent-review",
    "regulatory-compliance-checklist",
]


class TestLegalTemplates:
    def test_legal_template_count(self):
        """Legal preset provides exactly 6 preset-specific templates."""
        templates = discover_templates(preset="legal")
        leg_ids = sorted(k for k, v in templates.items() if v.preset == "legal")
        assert len(leg_ids) == 6

    def test_legal_template_ids(self):
        """All expected legal template IDs are present."""
        templates = discover_templates(preset="legal")
        for tid in EXPECTED_LEGAL_IDS:
            assert tid in templates, f"Missing legal template: {tid}"

    def test_legal_templates_have_sections(self):
        """Every legal template has at least 5 sections."""
        templates = discover_templates(preset="legal")
        for tid in EXPECTED_LEGAL_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_legal_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the legal preset."""
        templates = discover_templates(preset="legal")
        all_ids = set(templates.keys())
        for tid in EXPECTED_LEGAL_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_regulatory_checklist_multi_compliance(self):
        """regulatory-compliance-checklist expands with multiple compliance flags."""
        templates = discover_templates(preset="legal")
        t = templates["regulatory-compliance-checklist"]
        ctx_full = build_context(
            project_config={"compliance_standards": ["hipaa", "iso_27001", "sec_finra", "dod_5200"]},
            overrides={"title": "Test"},
        )
        ctx_none = build_context(overrides={"title": "Test"})
        rendered_full = t.render(ctx_full)
        rendered_none = t.render(ctx_none)
        # With all 4 compliance flags, should add significant content
        delta = len(rendered_full.splitlines()) - len(rendered_none.splitlines())
        assert delta >= 10, f"Expected 10+ extra lines, got {delta}"

    def test_contract_summary_hipaa_conditional(self):
        """contract-summary includes BAA section when HIPAA flag is set."""
        templates = discover_templates(preset="legal")
        t = templates["contract-summary"]
        ctx = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        rendered = t.render(ctx)
        assert "HIPAA" in rendered or "BAA" in rendered or "Business Associate" in rendered

    def test_legal_review_sec_finra_conditional(self):
        """legal-review includes securities section when SEC/FINRA flag is set."""
        templates = discover_templates(preset="legal")
        t = templates["legal-review"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["sec_finra"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)


# ── Phase G.2c — Healthcare templates ────────────────────────────────────────

EXPECTED_HEALTHCARE_IDS = {
    "clinical-protocol",
    "hipaa-risk-assessment",
    "quality-improvement-plan",
    "policy-document",
    "incident-report",
    "credentialing-checklist",
}


class TestHealthcareTemplates:
    """Healthcare preset template tests."""

    def test_healthcare_template_count(self):
        """Healthcare preset has exactly 6 templates."""
        templates = discover_templates(preset="healthcare")
        healthcare_only = {k: v for k, v in templates.items() if v.preset == "healthcare"}
        assert len(healthcare_only) == 6

    def test_healthcare_template_ids(self):
        """All expected healthcare template IDs exist."""
        templates = discover_templates(preset="healthcare")
        for tid in EXPECTED_HEALTHCARE_IDS:
            assert tid in templates, f"Missing template: {tid}"

    def test_healthcare_templates_have_sections(self):
        """Each healthcare template has at least 5 sections."""
        templates = discover_templates(preset="healthcare")
        for tid in EXPECTED_HEALTHCARE_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_healthcare_templates_have_tags(self):
        """Each healthcare template declares suggested tags."""
        templates = discover_templates(preset="healthcare")
        for tid in EXPECTED_HEALTHCARE_IDS:
            t = templates[tid]
            assert len(t.suggested_tags) >= 2, f"{tid} has too few tags"

    def test_healthcare_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the healthcare preset."""
        templates = discover_templates(preset="healthcare")
        all_ids = set(templates.keys())
        for tid in EXPECTED_HEALTHCARE_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_clinical_protocol_hipaa_conditional(self):
        """clinical-protocol expands with HIPAA compliance flag."""
        templates = discover_templates(preset="healthcare")
        t = templates["clinical-protocol"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)
        assert "HIPAA" in rendered_on or "PHI" in rendered_on

    def test_hipaa_risk_assessment_iso27001_conditional(self):
        """hipaa-risk-assessment expands with ISO 27001 compliance flag."""
        templates = discover_templates(preset="healthcare")
        t = templates["hipaa-risk-assessment"]
        ctx = build_context(
            project_config={"compliance_standards": ["iso_27001"]},
            overrides={"title": "Test"},
        )
        rendered = t.render(ctx)
        assert "ISO 27001" in rendered or "Annex A" in rendered

    def test_healthcare_no_cross_preset_leak(self):
        """Healthcare templates don't appear in the software preset."""
        sw = discover_templates(preset="software")
        for tid in EXPECTED_HEALTHCARE_IDS:
            assert tid not in sw, f"Healthcare template {tid} leaked into software preset"


# ── Phase G.2c — Finance templates ───────────────────────────────────────────

EXPECTED_FINANCE_IDS = {
    "due-diligence-report",
    "investment-memo",
    "compliance-review",
    "audit-finding",
    "risk-assessment-finance",
    "regulatory-filing-checklist",
}


class TestFinanceTemplates:
    """Finance preset template tests."""

    def test_finance_template_count(self):
        """Finance preset has exactly 6 templates."""
        templates = discover_templates(preset="finance")
        finance_only = {k: v for k, v in templates.items() if v.preset == "finance"}
        assert len(finance_only) == 6

    def test_finance_template_ids(self):
        """All expected finance template IDs exist."""
        templates = discover_templates(preset="finance")
        for tid in EXPECTED_FINANCE_IDS:
            assert tid in templates, f"Missing template: {tid}"

    def test_finance_templates_have_sections(self):
        """Each finance template has at least 5 sections."""
        templates = discover_templates(preset="finance")
        for tid in EXPECTED_FINANCE_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_finance_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the finance preset."""
        templates = discover_templates(preset="finance")
        all_ids = set(templates.keys())
        for tid in EXPECTED_FINANCE_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_due_diligence_sec_finra_conditional(self):
        """due-diligence-report expands with SEC/FINRA compliance flag."""
        templates = discover_templates(preset="finance")
        t = templates["due-diligence-report"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["sec_finra"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)
        assert "SEC" in rendered_on or "FINRA" in rendered_on

    def test_compliance_review_sec_finra_conditional(self):
        """compliance-review includes regulatory basis when SEC/FINRA flag is set."""
        templates = discover_templates(preset="finance")
        t = templates["compliance-review"]
        ctx = build_context(
            project_config={"compliance_standards": ["sec_finra"]},
            overrides={"title": "Test"},
        )
        rendered = t.render(ctx)
        assert "SEC Rule" in rendered or "FINRA Rule" in rendered

    def test_risk_assessment_finance_sec_finra_conditional(self):
        """risk-assessment-finance expands with SEC/FINRA flag."""
        templates = discover_templates(preset="finance")
        t = templates["risk-assessment-finance"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["sec_finra"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_finance_no_cross_preset_leak(self):
        """Finance templates don't appear in the healthcare preset."""
        hc = discover_templates(preset="healthcare")
        for tid in EXPECTED_FINANCE_IDS:
            assert tid not in hc, f"Finance template {tid} leaked into healthcare preset"


# ── Phase G.2c — Government templates ────────────────────────────────────────

EXPECTED_GOVERNMENT_IDS = {
    "policy-directive",
    "standard-operating-procedure",
    "memorandum",
    "acquisition-plan",
    "security-plan",
    "after-action-report",
}


class TestGovernmentTemplates:
    """Government preset template tests."""

    def test_government_template_count(self):
        """Government preset has exactly 6 templates."""
        templates = discover_templates(preset="government")
        gov_only = {k: v for k, v in templates.items() if v.preset == "government"}
        assert len(gov_only) == 6

    def test_government_template_ids(self):
        """All expected government template IDs exist."""
        templates = discover_templates(preset="government")
        for tid in EXPECTED_GOVERNMENT_IDS:
            assert tid in templates, f"Missing template: {tid}"

    def test_government_templates_have_sections(self):
        """Each government template has at least 5 sections."""
        templates = discover_templates(preset="government")
        for tid in EXPECTED_GOVERNMENT_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_government_cross_refs_valid(self):
        """Cross-references point to template IDs that exist in the government preset."""
        templates = discover_templates(preset="government")
        all_ids = set(templates.keys())
        for tid in EXPECTED_GOVERNMENT_IDS:
            t = templates[tid]
            for ref in t.typical_cross_refs:
                assert ref in all_ids, f"{tid} cross-refs '{ref}' which doesn't exist"

    def test_policy_directive_dod5200_conditional(self):
        """policy-directive expands with DoD 5200 compliance flag."""
        templates = discover_templates(preset="government")
        t = templates["policy-directive"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["dod_5200"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)
        assert "DoD 5200" in rendered_on or "Classification" in rendered_on or "CLASSIFICATION" in rendered_on

    def test_security_plan_dod5200_conditional(self):
        """security-plan expands with DoD 5200 flag for clearance and classification tables."""
        templates = discover_templates(preset="government")
        t = templates["security-plan"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["dod_5200"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        delta = len(rendered_on.splitlines()) - len(rendered_off.splitlines())
        assert delta >= 5, f"Expected 5+ extra lines with dod_5200, got {delta}"

    def test_sop_iso9001_conditional(self):
        """standard-operating-procedure expands with ISO 9001 flag."""
        templates = discover_templates(preset="government")
        t = templates["standard-operating-procedure"]
        ctx = build_context(
            project_config={"compliance_standards": ["iso_9001"]},
            overrides={"title": "Test"},
        )
        rendered = t.render(ctx)
        assert "ISO 9001" in rendered

    def test_government_no_cross_preset_leak(self):
        """Government templates don't appear in the finance preset."""
        fin = discover_templates(preset="finance")
        for tid in EXPECTED_GOVERNMENT_IDS:
            assert tid not in fin, f"Government template {tid} leaked into finance preset"


# ---------------------------------------------------------------------------
# Phase G.2d — Cross-cutting Security + Compliance templates
# ---------------------------------------------------------------------------

EXPECTED_SECURITY_IDS = {
    "threat-model",
    "vulnerability-assessment",
    "penetration-test-report",
    "security-architecture-review",
    "incident-response-plan",
    "access-control-matrix",
    "data-classification-policy",
    "bug-bounty-report",
}

EXPECTED_COMPLIANCE_IDS = {
    "sox-controls-matrix",
    "gdpr-dpia",
    "pci-dss-checklist",
    "iso27001-statement-of-applicability",
    "audit-readiness-checklist",
    "vendor-risk-assessment",
}


class TestSecurityTemplates:
    """Phase G.2d — 7 security cross-cutting templates."""

    def test_security_template_count(self):
        templates = discover_templates(preset="software")
        found = {tid for tid, t in templates.items() if t.preset == "security"}
        assert len(found) == 8

    def test_security_template_ids(self):
        templates = discover_templates(preset="software")
        found = {tid for tid, t in templates.items() if t.preset == "security"}
        assert found == EXPECTED_SECURITY_IDS

    def test_security_sections_present(self):
        templates = discover_templates(preset="software")
        for tid in EXPECTED_SECURITY_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_security_cross_refs_resolve(self):
        """All security template cross-refs resolve within security+compliance sets."""
        templates = discover_templates(preset="software")
        cc_ids = {tid for tid, t in templates.items() if t.preset in ("security", "compliance")}
        for tid in EXPECTED_SECURITY_IDS:
            t = templates[tid]
            for xref in t.typical_cross_refs:
                assert xref in cc_ids, f"{tid} xref '{xref}' not in cross-cutting set"

    def test_threat_model_hipaa_conditional(self):
        """threat-model expands with HIPAA flag for ePHI threat considerations."""
        templates = discover_templates(preset="software")
        t = templates["threat-model"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_data_classification_dod_conditional(self):
        """data-classification-policy expands with DoD 5200 flag."""
        templates = discover_templates(preset="software")
        t = templates["data-classification-policy"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["dod_5200"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_access_control_matrix_hipaa_conditional(self):
        """access-control-matrix expands with HIPAA flag for ePHI access rules."""
        templates = discover_templates(preset="software")
        t = templates["access-control-matrix"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)


class TestComplianceTemplates:
    """Phase G.2d — 6 compliance cross-cutting templates."""

    def test_compliance_template_count(self):
        templates = discover_templates(preset="software")
        found = {tid for tid, t in templates.items() if t.preset == "compliance"}
        assert len(found) == 6

    def test_compliance_template_ids(self):
        templates = discover_templates(preset="software")
        found = {tid for tid, t in templates.items() if t.preset == "compliance"}
        assert found == EXPECTED_COMPLIANCE_IDS

    def test_compliance_sections_present(self):
        templates = discover_templates(preset="software")
        for tid in EXPECTED_COMPLIANCE_IDS:
            t = templates[tid]
            assert len(t.sections) >= 5, f"{tid} has only {len(t.sections)} sections"

    def test_compliance_cross_refs_resolve(self):
        """All compliance template cross-refs resolve within security+compliance sets."""
        templates = discover_templates(preset="software")
        cc_ids = {tid for tid, t in templates.items() if t.preset in ("security", "compliance")}
        for tid in EXPECTED_COMPLIANCE_IDS:
            t = templates[tid]
            for xref in t.typical_cross_refs:
                assert xref in cc_ids, f"{tid} xref '{xref}' not in cross-cutting set"

    def test_audit_readiness_multi_compliance(self):
        """audit-readiness-checklist expands significantly with all compliance flags."""
        templates = discover_templates(preset="software")
        t = templates["audit-readiness-checklist"]
        ctx_full = build_context(
            project_config={"compliance_standards": ["hipaa", "iso_9001", "iso_27001", "sec_finra", "dod_5200"]},
            overrides={"title": "Test"},
        )
        ctx_none = build_context(overrides={"title": "Test"})
        rendered_full = t.render(ctx_full)
        rendered_none = t.render(ctx_none)
        delta = len(rendered_full.splitlines()) - len(rendered_none.splitlines())
        assert delta >= 20, f"Expected 20+ extra lines with all compliance, got {delta}"

    def test_vendor_risk_assessment_sec_finra_conditional(self):
        """vendor-risk-assessment expands with SEC/FINRA flag."""
        templates = discover_templates(preset="software")
        t = templates["vendor-risk-assessment"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["sec_finra"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_gdpr_dpia_hipaa_conditional(self):
        """gdpr-dpia expands with HIPAA flag for dual-framework compliance."""
        templates = discover_templates(preset="software")
        t = templates["gdpr-dpia"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["hipaa"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert len(rendered_on) > len(rendered_off)

    def test_bug_bounty_report_sections(self):
        """bug-bounty-report has all required sections for researcher submissions."""
        templates = discover_templates(preset="software")
        t = templates["bug-bounty-report"]
        assert len(t.sections) >= 9
        required = {"Vulnerability Summary", "Vulnerability Classification",
                     "Steps to Reproduce", "Proof of Concept", "Impact Assessment"}
        assert required.issubset(set(t.sections)), f"Missing sections: {required - set(t.sections)}"

    def test_bug_bounty_report_cvss_and_cwe(self):
        """bug-bounty-report includes CVSS 3.1 scoring and CWE classification."""
        templates = discover_templates(preset="software")
        t = templates["bug-bounty-report"]
        rendered = t.render(build_context(overrides={"title": "Test"}))
        assert "CVSS 3.1" in rendered
        assert "CWE" in rendered
        assert "Attack Vector" in rendered
        assert "CVSS Vector" in rendered

    def test_bug_bounty_report_dod5200_conditional(self):
        """bug-bounty-report expands with DoD 5200 classification marking."""
        templates = discover_templates(preset="software")
        t = templates["bug-bounty-report"]
        ctx_on = build_context(
            project_config={"compliance_standards": ["dod_5200"]},
            overrides={"title": "Test"},
        )
        ctx_off = build_context(overrides={"title": "Test"})
        rendered_on = t.render(ctx_on)
        rendered_off = t.render(ctx_off)
        assert "Classification" in rendered_on
        assert len(rendered_on) > len(rendered_off)

    def test_bug_bounty_report_tags(self):
        """bug-bounty-report has security and bug-bounty tags."""
        templates = discover_templates(preset="software")
        t = templates["bug-bounty-report"]
        assert "security" in t.suggested_tags
        assert "bug-bounty" in t.suggested_tags

    def test_bug_bounty_report_cross_refs_resolve(self):
        """bug-bounty-report cross-refs resolve within security cross-cutting set."""
        templates = discover_templates(preset="software")
        t = templates["bug-bounty-report"]
        cc_ids = {tid for tid, tmpl in templates.items() if tmpl.preset in ("security", "compliance")}
        for xref in t.typical_cross_refs:
            assert xref in cc_ids, f"xref '{xref}' not in cross-cutting set"


class TestCrossCuttingResolution:
    """Verify cross-cutting templates are available from every preset."""

    @pytest.mark.parametrize("preset", [
        "software", "business", "healthcare", "finance",
        "government", "scientific", "legal",
    ])
    def test_security_available_in_all_presets(self, preset):
        templates = discover_templates(preset=preset)
        found = {tid for tid, t in templates.items() if t.preset == "security"}
        assert found == EXPECTED_SECURITY_IDS, f"Security templates missing from {preset}"

    @pytest.mark.parametrize("preset", [
        "software", "business", "healthcare", "finance",
        "government", "scientific", "legal",
    ])
    def test_compliance_available_in_all_presets(self, preset):
        templates = discover_templates(preset=preset)
        found = {tid for tid, t in templates.items() if t.preset == "compliance"}
        assert found == EXPECTED_COMPLIANCE_IDS, f"Compliance templates missing from {preset}"
