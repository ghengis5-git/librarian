"""Dashboard generation — render a single-file HTML dashboard from a manifest.

The dashboard template is a self-contained HTML file with inlined CSS,
Lunr.js (client-side search), and cytoscape.js (cross-reference graph).
Manifest data is injected by replacing the ``__MANIFEST_DATA__`` placeholder
with deterministic JSON.

Usage from Python::

    from librarian.manifest import generate as generate_manifest
    from librarian.dashboard import render, write_dashboard
    from librarian.registry import Registry

    reg = Registry.load("docs/REGISTRY.yaml")
    manifest = generate_manifest(reg, ".")
    html = render(manifest)
    write_dashboard(manifest, "docs/diagrams/dashboard.html")

Usage from CLI::

    python -m librarian dashboard -o dashboard.html
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manifest import Manifest

# The bundled template ships alongside the package in dashboard/
_PACKAGE_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_ROOT.parent
DEFAULT_TEMPLATE = _PROJECT_ROOT / "dashboard"

PLACEHOLDER = "__MANIFEST_DATA__"


def _find_template(template_dir: Path | None = None) -> Path:
    """Locate the dashboard template HTML file.

    Search order:
    1. Explicit ``template_dir`` if provided
    2. ``<project_root>/dashboard/`` (default install location)

    Returns the path to the newest ``librarian-dashboard-template-*.html``
    file found.  Raises FileNotFoundError if none exists.
    """
    search_dir = template_dir or DEFAULT_TEMPLATE
    search_dir = Path(search_dir)

    if search_dir.is_file() and search_dir.suffix == ".html":
        return search_dir

    if not search_dir.is_dir():
        raise FileNotFoundError(
            f"Dashboard template directory not found: {search_dir}"
        )

    candidates = sorted(
        search_dir.glob("librarian-dashboard-template-*.html"),
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"No dashboard template found in {search_dir}. "
            "Expected: librarian-dashboard-template-YYYYMMDD-V*.html"
        )
    return candidates[0]


def render(
    manifest: "Manifest",
    template_path: Path | str | None = None,
) -> str:
    """Inject manifest JSON into the dashboard template.

    Args:
        manifest: A populated ``Manifest`` dataclass.
        template_path: Optional path to a template file or directory.
            If a directory, the newest ``librarian-dashboard-template-*.html``
            is used.  If omitted, the bundled default template is used.

    Returns:
        The rendered HTML string with manifest data embedded.

    Raises:
        FileNotFoundError: If no template can be found.
        ValueError: If the template does not contain the ``__MANIFEST_DATA__``
            placeholder.
    """
    tpl_path = _find_template(
        Path(template_path) if template_path else None
    )
    template_html = tpl_path.read_text(encoding="utf-8")

    if PLACEHOLDER not in template_html:
        raise ValueError(
            f"Template {tpl_path} does not contain the "
            f"{PLACEHOLDER!r} placeholder."
        )

    # Deterministic JSON, sorted keys — matches manifest.to_json() format
    manifest_json = json.dumps(
        manifest.to_dict(),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )

    rendered = template_html.replace(PLACEHOLDER, manifest_json)
    return rendered


def write_dashboard(
    manifest: "Manifest",
    output_path: str | Path,
    template_path: Path | str | None = None,
) -> Path:
    """Render and write the dashboard to disk.

    Args:
        manifest: A populated ``Manifest`` dataclass.
        output_path: Where to write the rendered HTML.
        template_path: Optional path to a template file or directory.

    Returns:
        The resolved output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = render(manifest, template_path=template_path)
    output_path.write_text(html, encoding="utf-8")
    return output_path.resolve()
