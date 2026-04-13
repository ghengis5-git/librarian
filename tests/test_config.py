"""Tests for the configuration system — presets, naming templates, merge logic."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from librarian.config import (
    DEFAULTS,
    PRESETS,
    NAMING_TEMPLATES,
    NamingConfig,
    CategoryConfig,
    LibrarianConfig,
    load_config,
    load_defaults,
    list_presets,
    list_naming_templates,
    _deep_merge,
)
from librarian.naming import parse_filename, validate, ParsedName


# ─── Deep Merge ───────────────────────────────────────────────────────────


class TestDeepMerge:
    def test_simple_override(self):
        base = {"a": 1, "b": 2}
        over = {"b": 3}
        assert _deep_merge(base, over) == {"a": 1, "b": 3}

    def test_nested_merge(self):
        base = {"x": {"a": 1, "b": 2}}
        over = {"x": {"b": 3, "c": 4}}
        result = _deep_merge(base, over)
        assert result["x"] == {"a": 1, "b": 3, "c": 4}

    def test_list_replaced(self):
        base = {"items": [1, 2, 3]}
        over = {"items": [4, 5]}
        assert _deep_merge(base, over)["items"] == [4, 5]

    def test_does_not_mutate_base(self):
        base = {"x": {"a": 1}}
        over = {"x": {"a": 2}}
        _deep_merge(base, over)
        assert base["x"]["a"] == 1


# ─── Presets ──────────────────────────────────────────────────────────────


class TestPresets:
    def test_all_presets_exist(self):
        expected = {"software", "business", "accounting", "government", "scientific", "finance", "healthcare", "legal", "minimal"}
        assert set(PRESETS.keys()) == expected

    def test_software_has_docs_folder(self):
        assert "docs/" in PRESETS["software"]["categories"]["folders"]

    def test_business_has_legal_folder(self):
        assert "legal/" in PRESETS["business"]["categories"]["folders"]

    def test_accounting_has_ar_ap(self):
        folders = PRESETS["accounting"]["categories"]["folders"]
        assert "accounts-receivable/" in folders
        assert "accounts-payable/" in folders

    def test_government_has_classification_markings(self):
        gov = PRESETS["government"]
        assert "document_header" in gov
        assert "classification_banner" in gov["document_header"]

    def test_minimal_has_empty_folders(self):
        assert PRESETS["minimal"]["categories"]["folders"] == []

    def test_each_preset_has_labels_for_all_folders(self):
        for name, preset in PRESETS.items():
            cats = preset.get("categories", {})
            folders = cats.get("folders", [])
            labels = cats.get("labels", {})
            for f in folders:
                key = f.rstrip("/")
                assert key in labels, f"Preset {name}: folder {f} missing label"

    def test_list_presets_returns_all(self):
        result = list_presets()
        names = {p["name"] for p in result}
        assert names == set(PRESETS.keys())


# ─── Naming Templates ────────────────────────────────────────────────────


class TestNamingTemplates:
    def test_all_templates_exist(self):
        expected = {"default", "legal", "engineering", "corporate", "dateless", "scientific", "healthcare", "finance"}
        assert set(NAMING_TEMPLATES.keys()) == expected

    def test_default_template_is_hyphen_lowercase(self):
        t = NAMING_TEMPLATES["default"]
        assert t["separator"] == "-"
        assert t["case"] == "lowercase"

    def test_legal_has_domain_prefix(self):
        assert NAMING_TEMPLATES["legal"]["domain_prefix"] is True

    def test_dateless_has_date_off(self):
        assert NAMING_TEMPLATES["dateless"]["date_format"] == "off"

    def test_corporate_uses_underscore(self):
        assert NAMING_TEMPLATES["corporate"]["separator"] == "_"

    def test_list_templates_returns_patterns(self):
        result = list_naming_templates()
        names = {t["name"] for t in result}
        assert names == set(NAMING_TEMPLATES.keys())
        for t in result:
            assert "pattern" in t and len(t["pattern"]) > 0


# ─── Config Loading ──────────────────────────────────────────────────────


class TestLoadConfig:
    def test_bare_defaults(self):
        config = load_config()
        assert config.naming.separator == "-"
        assert config.naming.case == "lowercase"
        assert config.naming.date_format == "YYYYMMDD"
        assert config.naming.version_format == "VX.Y"
        assert config.categories.strict_mode is False

    def test_with_preset(self):
        config = load_config(preset="software")
        assert "docs/" in config.categories.folders
        assert "specs/" in config.categories.folders
        assert config.preset == "software"

    def test_project_override(self):
        overrides = {
            "project_name": "My Project",
            "naming_rules": {"separator": "_", "case": "mixed"},
        }
        config = load_config(project_config=overrides)
        assert config.project_name == "My Project"
        assert config.naming.separator == "_"
        assert config.naming.case == "mixed"
        # Non-overridden defaults survive
        assert config.naming.date_format == "YYYYMMDD"

    def test_preset_plus_override(self):
        overrides = {
            "naming_rules": {"date_format": "YYYY-MM-DD"},
            "categories": {"strict_mode": True},
        }
        config = load_config(project_config=overrides, preset="business")
        assert config.naming.date_format == "YYYY-MM-DD"
        assert config.categories.strict_mode is True
        # Preset categories still present
        assert "legal/" in config.categories.folders

    def test_naming_template_shortcut(self):
        overrides = {
            "naming_rules": {"template": "legal"},
        }
        config = load_config(project_config=overrides)
        assert config.naming.case == "mixed"
        assert config.naming.date_format == "YYYY-MM-DD"
        assert config.naming.domain_prefix is True

    def test_template_values_overridden_by_explicit_rules(self):
        overrides = {
            "naming_rules": {"template": "corporate", "separator": "."},
        }
        config = load_config(project_config=overrides)
        # Template says "_" but explicit override wins
        assert config.naming.separator == "."
        # Template's other values survive
        assert config.naming.case == "mixed"

    def test_unknown_preset_uses_defaults(self):
        config = load_config(preset="nonexistent")
        assert config.naming.separator == "-"
        assert config.categories.folders == []


# ─── NamingConfig ─────────────────────────────────────────────────────────


class TestNamingConfig:
    def test_default_human_pattern(self):
        nc = NamingConfig()
        assert nc.human_pattern == "descriptive-name-YYYYMMDD-VX.Y.ext"

    def test_dateless_pattern(self):
        nc = NamingConfig(date_format="off")
        assert "YYYYMMDD" not in nc.human_pattern
        assert nc.human_pattern == "descriptive-name-VX.Y.ext"

    def test_domain_prefix_pattern(self):
        nc = NamingConfig(domain_prefix=True)
        assert nc.human_pattern.startswith("domain-")

    def test_underscore_separator(self):
        nc = NamingConfig(separator="_")
        assert "_" in nc.human_pattern

    def test_regex_matches_default(self):
        nc = NamingConfig()
        rx = re.compile(nc.regex_pattern)
        m = rx.match("my-doc-20260412-V1.0.md")
        assert m is not None
        assert m.group("stem") == "my-doc"
        assert m.group("date") == "20260412"
        assert m.group("major") == "1"

    def test_regex_matches_lowercase_v(self):
        nc = NamingConfig(version_format="vX.Y")
        rx = re.compile(nc.regex_pattern)
        m = rx.match("report-20260412-v2.3.pdf")
        assert m is not None

    def test_regex_matches_dateless(self):
        nc = NamingConfig(date_format="off")
        rx = re.compile(nc.regex_pattern)
        m = rx.match("report-V1.0.pdf")
        assert m is not None
        assert "date" not in m.groupdict() or m.group("date") is None

    def test_regex_matches_iso_date(self):
        nc = NamingConfig(date_format="YYYY-MM-DD")
        rx = re.compile(nc.regex_pattern)
        m = rx.match("contract-2026-04-12-V1.0.pdf")
        assert m is not None
        assert m.group("date") == "2026-04-12"

    def test_regex_matches_domain_prefix(self):
        nc = NamingConfig(domain_prefix=True)
        rx = re.compile(nc.regex_pattern)
        m = rx.match("legal-nda-template-20260412-V1.0.pdf")
        assert m is not None
        assert m.group("domain") == "legal"

    def test_regex_matches_underscore(self):
        nc = NamingConfig(separator="_", case="mixed")
        rx = re.compile(nc.regex_pattern)
        m = rx.match("My_Report_20260412_V1.0.pdf")
        assert m is not None


# ─── Configurable Naming Validation ───────────────────────────────────────


class TestConfigurableNaming:
    def test_default_validates_canonical(self):
        result = validate("my-doc-20260412-V1.0.md")
        assert result.valid

    def test_lowercase_v_with_config(self):
        nc = NamingConfig(version_format="vX.Y")
        result = validate("report-20260412-v2.3.pdf", config=nc)
        assert result.valid
        assert result.parsed.major == 2
        assert result.parsed.minor == 3

    def test_dateless_with_config(self):
        nc = NamingConfig(date_format="off")
        result = validate("report-V1.0.pdf", config=nc)
        assert result.valid
        assert result.parsed.date == ""

    def test_iso_date_with_config(self):
        nc = NamingConfig(date_format="YYYY-MM-DD")
        result = validate("contract-2026-04-12-V1.0.pdf", config=nc)
        assert result.valid
        assert result.parsed.date == "2026-04-12"

    def test_underscore_separator(self):
        nc = NamingConfig(separator="_", case="mixed")
        result = validate("My_Report_20260412_V1.0.pdf", config=nc)
        assert result.valid

    def test_domain_prefix_parsing(self):
        nc = NamingConfig(domain_prefix=True)
        result = validate("legal-nda-template-20260412-V1.0.pdf", config=nc)
        assert result.valid
        assert result.parsed.domain == "legal"

    def test_forbidden_words_from_config(self):
        nc = NamingConfig(forbidden_words=["draft", "temp"])
        result = validate("draft-20260412-V1.0.md", config=nc)
        # "draft" is a single-char stem so it's both stem and token
        assert not result.valid
        assert "forbidden" in result.errors[0]

    def test_config_exempt_still_works(self):
        nc = NamingConfig()
        result = validate("README.md", exempt=frozenset({"README.md"}), config=nc)
        assert result.valid

    def test_version_format_xy_no_prefix(self):
        nc = NamingConfig(version_format="X.Y")
        result = validate("report-20260412-1.0.pdf", config=nc)
        assert result.valid
        assert result.parsed.major == 1


# ─── Parse with Config ────────────────────────────────────────────────────


class TestParseWithConfig:
    def test_parse_default(self):
        parsed = parse_filename("my-doc-20260412-V1.0.md")
        assert parsed is not None
        assert parsed.stem == "my-doc"

    def test_parse_with_vx_y(self):
        nc = NamingConfig(version_format="vX.Y")
        parsed = parse_filename("report-20260412-v2.3.pdf", config=nc)
        assert parsed is not None
        assert parsed.major == 2

    def test_parse_dateless(self):
        nc = NamingConfig(date_format="off")
        parsed = parse_filename("report-V1.0.pdf", config=nc)
        assert parsed is not None
        assert parsed.date == ""

    def test_parse_returns_none_on_mismatch(self):
        nc = NamingConfig(version_format="VX.Y")
        parsed = parse_filename("bad file.txt", config=nc)
        assert parsed is None


# ─── CLI: init ────────────────────────────────────────────────────────────


class TestCLIInit:
    def test_init_creates_registry(self, tmp_path):
        out = tmp_path / "REGISTRY.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "--repo", str(tmp_path),
             "init", "--preset", "software", "--name", "TestProj",
             "-o", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert out.exists()
        data = yaml.safe_load(out.read_text())
        assert data["project_config"]["project_name"] == "TestProj"
        assert "docs/" in data["project_config"]["categories"]["folders"]

    def test_init_refuses_overwrite(self, tmp_path):
        out = tmp_path / "REGISTRY.yaml"
        out.write_text("existing: true\n")
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "--repo", str(tmp_path),
             "init", "-o", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "already exists" in result.stderr

    def test_init_force_overwrites(self, tmp_path):
        out = tmp_path / "REGISTRY.yaml"
        out.write_text("existing: true\n")
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "--repo", str(tmp_path),
             "init", "-o", str(out), "--force"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_init_creates_folders(self, tmp_path):
        out = tmp_path / "REGISTRY.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "--repo", str(tmp_path),
             "init", "--preset", "business", "-o", str(out), "--create-folders"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (tmp_path / "finance").is_dir()
        assert (tmp_path / "legal").is_dir()

    def test_init_naming_template(self, tmp_path):
        out = tmp_path / "REGISTRY.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "--repo", str(tmp_path),
             "init", "--naming-template", "legal", "-o", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = yaml.safe_load(out.read_text())
        assert data["project_config"]["naming_rules"]["domain_prefix"] is True


# ─── CLI: config ──────────────────────────────────────────────────────────


class TestCLIConfig:
    def test_list_presets(self):
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "config", "--list-presets"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "software" in result.stdout
        assert "business" in result.stdout
        assert "accounting" in result.stdout

    def test_list_templates(self):
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "config", "--list-templates"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "default" in result.stdout
        assert "legal" in result.stdout
        assert "dateless" in result.stdout

    def test_show_config_with_preset(self):
        result = subprocess.run(
            [sys.executable, "-m", "librarian", "config", "--preset", "accounting"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "accounts-receivable" in result.stdout
