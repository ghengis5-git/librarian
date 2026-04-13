"""Template registry — discovery, loading, and resolution.

Templates ship in subdirectories alongside this file, organized by preset.
Projects can also define custom templates via ``custom_templates_dir`` in
project_config.

Resolution order (first match wins):
  1. Custom templates dir (project-level overrides)
  2. Preset-specific dir (e.g. ``software/``)
  3. Cross-cutting dirs (``security/``, ``compliance/``)
  4. Universal dir (``universal/``)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ._base import DocumentTemplate, render_template

# Template IDs must be alphanumeric + hyphens only (no slashes, dots, etc.)
_SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")

__all__ = [
    "DocumentTemplate",
    "render_template",
    "discover_templates",
    "load_template",
    "list_templates",
    "build_context",
]

# Cross-cutting presets available to any project
CROSS_CUTTING = ("security", "compliance")

_BUILTIN_DIR = Path(__file__).parent


def discover_templates(
    preset: str = "",
    custom_dir: str | Path | None = None,
) -> dict[str, DocumentTemplate]:
    """Discover all available templates for a preset.

    Returns a dict of template_id → DocumentTemplate, with resolution
    priority: custom > preset > cross-cutting > universal.
    """
    templates: dict[str, DocumentTemplate] = {}

    # 4. Universal (lowest priority — loaded first, overwritten by higher)
    _load_dir(_BUILTIN_DIR / "universal", "universal", templates)

    # 3. Cross-cutting
    for cc in CROSS_CUTTING:
        _load_dir(_BUILTIN_DIR / cc, cc, templates)

    # 2. Preset-specific
    if preset and preset not in CROSS_CUTTING and preset != "universal":
        _load_dir(_BUILTIN_DIR / preset, preset, templates)

    # 1. Custom (highest priority) — validate path is within project
    if custom_dir:
        custom_path = Path(custom_dir).resolve()
        if custom_path.is_dir():
            _load_dir(custom_path, "custom", templates)

    return templates


def _load_dir(
    directory: Path,
    preset_label: str,
    into: dict[str, DocumentTemplate],
) -> None:
    """Load all .md template files from a directory into the dict."""
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.md")):
        try:
            tmpl = DocumentTemplate.from_file(str(path), preset=preset_label)
            if tmpl.template_id and _SAFE_ID_RE.match(tmpl.template_id):
                into[tmpl.template_id] = tmpl
        except Exception:
            continue  # skip malformed templates


def load_template(
    template_id: str,
    preset: str = "",
    custom_dir: str | Path | None = None,
) -> DocumentTemplate | None:
    """Load a single template by ID. Returns None if not found."""
    templates = discover_templates(preset=preset, custom_dir=custom_dir)
    return templates.get(template_id)


def list_templates(
    preset: str = "",
    custom_dir: str | Path | None = None,
) -> list[dict[str, str]]:
    """List available templates as dicts with id, name, preset, description."""
    templates = discover_templates(preset=preset, custom_dir=custom_dir)
    result = []
    for tid in sorted(templates):
        t = templates[tid]
        result.append({
            "id": t.template_id,
            "name": t.display_name,
            "preset": t.preset,
            "description": t.description,
        })
    return result


def build_context(
    project_config: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a context dict for template rendering from project_config.

    The context includes standard variables (title, version, date, etc.),
    config-derived values (preset, compliance flags), and any explicit
    overrides.
    """
    from datetime import date as _date
    from .. import __version__

    pc = project_config or {}

    # Extract compliance flags
    compliance_list: list[str] = []
    header_cfg = pc.get("document_header", {})
    footer_cfg = pc.get("document_footer", {})
    # Check for compliance standards in naming_rules or dedicated field
    compliance_raw = pc.get("compliance_standards", [])
    if isinstance(compliance_raw, list):
        compliance_list = compliance_raw

    today = _date.today()
    date_fmt = pc.get("naming_rules", {}).get("date_format", "YYYYMMDD")
    if date_fmt == "YYYY-MM-DD":
        date_str = today.strftime("%Y-%m-%d")
    elif date_fmt == "off":
        date_str = ""
    else:
        date_str = today.strftime("%Y%m%d")

    ctx: dict[str, Any] = {
        # Standard variables
        "title": "",
        "version": "V1.0",
        "date": date_str,
        "author": pc.get("default_author", ""),
        "classification": pc.get("default_classification", "INTERNAL"),
        "status": "draft",
        "year": str(today.year),
        "project_name": pc.get("project_name", ""),
        "librarian_version": __version__,

        # Config-derived
        "preset": pc.get("preset", ""),
        "compliance": compliance_list,

        # Convenience booleans for compliance
        "hipaa": "hipaa" in compliance_list,
        "dod_5200": "dod_5200" in compliance_list,
        "iso_9001": "iso_9001" in compliance_list,
        "iso_27001": "iso_27001" in compliance_list,
        "sec_finra": "sec_finra" in compliance_list,

        # Document metadata defaults
        "review_cycle_days": pc.get("document_metadata", {}).get("review_cycle_days", 365),
        "retention_period_days": pc.get("document_metadata", {}).get("retention_period_days", 0),
        "classification_authority": "",
        "declassification_date": "",

        # Header/footer from config
        "organization": header_cfg.get("organization", ""),
        "distribution_statement": footer_cfg.get("distribution_statement", ""),
        "copyright_notice": footer_cfg.get("copyright_notice", ""),
    }

    # Apply overrides last
    if overrides:
        ctx.update(overrides)

    return ctx
