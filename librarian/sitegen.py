"""Static site generator — multi-page HTML site from a manifest.

Generates a ``_site/`` directory tree with:

- ``index.html`` — document table, KPI summary, sidebar tree navigation
- ``docs/<filename>.html`` — per-document detail page
- ``graph.html`` — standalone cross-reference graph (cytoscape.js)
- ``dashboard.html`` — link target (rendered separately by dashboard module)
- ``assets/style.css`` — shared stylesheet

Features a sidebar with collapsible document tree that supports three
grouping modes: by status, by tag, and by filesystem path.

All pages share design tokens for visual consistency.
No external dependencies; works offline.

Usage from Python::

    from librarian.sitegen import generate_site
    from librarian.manifest import generate as generate_manifest
    from librarian.registry import Registry

    reg = Registry.load("docs/REGISTRY.yaml")
    manifest = generate_manifest(reg, ".")
    generate_site(manifest, "_site")

Usage from CLI::

    python -m librarian site -o _site
"""

from __future__ import annotations

import html as html_mod
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .manifest import Manifest


def _esc(text: Any) -> str:
    """HTML-escape a value."""
    return html_mod.escape(str(text)) if text else ""


# ── Markdown → HTML (zero-dep) ────────────────────────────────────────────


def _md_to_html(text: str) -> str:
    """Convert Markdown text to HTML.

    Handles headings, fenced code blocks, inline code, bold, italic,
    links, images, unordered/ordered lists, blockquotes, horizontal rules,
    and simple tables. Zero external dependencies.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # ── Fenced code block ──
        if line.strip().startswith("```"):
            lang = line.strip().lstrip("`").strip()
            lang_attr = f' class="language-{_esc(lang)}"' if lang else ""
            code_lines: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_text = _esc("\n".join(code_lines))
            out.append(f"<pre><code{lang_attr}>{code_text}</code></pre>")
            continue

        # ── Horizontal rule ──
        stripped = line.strip()
        if stripped and all(c in "-*_ " for c in stripped) and sum(1 for c in stripped if c in "-*_") >= 3:
            out.append("<hr>")
            i += 1
            continue

        # ── Heading ──
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            content = _inline(m.group(2))
            out.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        # ── Blockquote ──
        if line.startswith(">"):
            bq_lines: list[str] = []
            while i < n and (lines[i].startswith(">") or (lines[i].strip() and bq_lines)):
                bq_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            bq_content = _md_to_html("\n".join(bq_lines))
            out.append(f"<blockquote>{bq_content}</blockquote>")
            continue

        # ── Table ──
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s\-:|]+\|", lines[i + 1]):
            table_lines: list[str] = []
            while i < n and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            out.append(_render_table(table_lines))
            continue

        # ── Unordered list ──
        if re.match(r"^[\s]*[-*+]\s", line):
            list_items: list[str] = []
            while i < n and re.match(r"^[\s]*[-*+]\s", lines[i]):
                item_text = re.sub(r"^[\s]*[-*+]\s+", "", lines[i])
                list_items.append(f"<li>{_inline(item_text)}</li>")
                i += 1
            out.append("<ul>" + "\n".join(list_items) + "</ul>")
            continue

        # ── Ordered list ──
        if re.match(r"^[\s]*\d+\.\s", line):
            list_items_ol: list[str] = []
            while i < n and re.match(r"^[\s]*\d+\.\s", lines[i]):
                item_text = re.sub(r"^[\s]*\d+\.\s+", "", lines[i])
                list_items_ol.append(f"<li>{_inline(item_text)}</li>")
                i += 1
            out.append("<ol>" + "\n".join(list_items_ol) + "</ol>")
            continue

        # ── Blank line ──
        if not stripped:
            i += 1
            continue

        # ── Paragraph: collect consecutive non-empty lines ──
        para_lines: list[str] = []
        while i < n and lines[i].strip() and not lines[i].startswith("#") and not lines[i].startswith("```") and not lines[i].startswith(">") and not re.match(r"^[\s]*[-*+]\s", lines[i]) and not re.match(r"^[\s]*\d+\.\s", lines[i]):
            para_lines.append(lines[i])
            i += 1
        out.append(f"<p>{_inline(' '.join(para_lines))}</p>")

    return "\n".join(out)


def _inline(text: str) -> str:
    """Process inline Markdown: code, bold, italic, links, images."""
    # Inline code first (protect from further processing)
    parts: list[str] = []
    segments = re.split(r"(`[^`]+`)", text)
    for seg in segments:
        if seg.startswith("`") and seg.endswith("`"):
            parts.append(f"<code>{_esc(seg[1:-1])}</code>")
        else:
            s = _esc(seg)
            # Images before links
            s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" style="max-width:100%">', s)
            # Links
            s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
            # Bold (** or __)
            s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            s = re.sub(r"__(.+?)__", r"<strong>\1</strong>", s)
            # Italic (* or _)
            s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
            s = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", s)
            parts.append(s)
    return "".join(parts)


def _render_table(lines: list[str]) -> str:
    """Render a Markdown table to HTML."""
    def _parse_row(line: str) -> list[str]:
        cells = line.strip().strip("|").split("|")
        return [c.strip() for c in cells]

    if len(lines) < 2:
        return _esc("\n".join(lines))

    headers = _parse_row(lines[0])
    # lines[1] is the separator row
    body_rows = [_parse_row(l) for l in lines[2:]]

    html = '<table class="md-table">\n<thead><tr>'
    for h in headers:
        html += f"<th>{_inline(h)}</th>"
    html += "</tr></thead>\n<tbody>"
    for row in body_rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{_inline(cell)}</td>"
        html += "</tr>\n"
    html += "</tbody></table>"
    return html


def _render_file_content(doc: dict, repo_root: str | Path) -> str:
    """Read a governed document from disk and render as HTML.

    For .md files: converts to HTML via ``_md_to_html``.
    For .yaml, .yml, .json, .sh, and other text files: wraps in <pre><code>.
    Returns empty string if file cannot be read.
    """
    path_str = doc.get("path", "")
    if not path_str:
        return ""

    file_path = Path(repo_root) / path_str
    if not file_path.is_file():
        return '<p class="content-missing">File not found on disk.</p>'

    try:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return '<p class="content-missing">Unable to read file.</p>'

    if not raw.strip():
        return '<p class="content-missing">File is empty.</p>'

    fmt = doc.get("format", "").lower()
    if not fmt:
        # Infer from filename extension
        fn = doc.get("filename", path_str)
        ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
        fmt = ext

    # Strip YAML frontmatter from markdown files
    if fmt == "md" and raw.startswith("---"):
        end = raw.find("---", 3)
        if end > 0:
            raw = raw[end + 3:].lstrip("\n")

    if fmt == "md":
        return f'<div class="doc-content prose">{_md_to_html(raw)}</div>'
    else:
        # Syntax-highlighted code block
        lang_map = {"yaml": "yaml", "yml": "yaml", "json": "json", "sh": "bash"}
        lang = lang_map.get(fmt, fmt)
        lang_cls = f' class="language-{_esc(lang)}"' if lang else ""
        return f'<div class="doc-content"><pre><code{lang_cls}>{_esc(raw)}</code></pre></div>'


# ── Tree grouping logic ────────────────────────────────────────────────────


def _group_by_status(documents: list[dict]) -> dict:
    """Group documents by status for the sidebar tree."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for doc in documents:
        status = doc.get("status", "unknown")
        groups[status].append(doc)
    # Sort groups: active first, then draft, then superseded, then rest
    order = {"active": 0, "draft": 1, "superseded": 2}
    return dict(sorted(groups.items(), key=lambda kv: (order.get(kv[0], 99), kv[0])))


def _group_by_tag(documents: list[dict]) -> dict:
    """Group documents by tag for the sidebar tree."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for doc in documents:
        tags = doc.get("tags") or []
        if not tags:
            groups["untagged"].append(doc)
        else:
            for tag in tags:
                groups[tag].append(doc)
    return dict(sorted(groups.items()))


def _group_by_path(documents: list[dict]) -> dict:
    """Group documents by filesystem directory for the sidebar tree."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for doc in documents:
        path = doc.get("path", doc.get("filename", ""))
        parent = str(PurePosixPath(path).parent) if "/" in path else "."
        groups[parent].append(doc)
    return dict(sorted(groups.items()))


def _build_tree_json(documents: list[dict]) -> str:
    """Pre-compute all three grouping structures as JSON for client-side switching."""
    tree_data = {
        "status": {
            group: [
                {"filename": d.get("filename", ""), "title": d.get("title", ""), "status": d.get("status", "")}
                for d in sorted(docs, key=lambda x: x.get("filename", ""))
            ]
            for group, docs in _group_by_status(documents).items()
        },
        "tag": {
            group: [
                {"filename": d.get("filename", ""), "title": d.get("title", ""), "status": d.get("status", "")}
                for d in sorted(docs, key=lambda x: x.get("filename", ""))
            ]
            for group, docs in _group_by_tag(documents).items()
        },
        "path": {
            group: [
                {"filename": d.get("filename", ""), "title": d.get("title", ""), "status": d.get("status", "")}
                for d in sorted(docs, key=lambda x: x.get("filename", ""))
            ]
            for group, docs in _group_by_path(documents).items()
        },
    }
    return json.dumps(tree_data, indent=2, sort_keys=True)


# ── Shared CSS ──────────────────────────────────────────────────────────────

SITE_CSS = """\
/* ── Design Tokens ──────────────────────────────────────────────────────── */
:root {
  --bg: #fafaf8;
  --surface: #ffffff;
  --surface-alt: #f3f2ee;
  --surface-hover: #eceae4;
  --border: #e4e1da;
  --border-strong: #ccc8be;
  --text-primary: #1a1816;
  --text-secondary: #555049;
  --text-muted: #908a82;
  --accent: #2d6a5a;
  --accent-light: #e6f0ec;
  --accent-hover: #1e4f42;
  --accent-text: #ffffff;
  --status-active: #2d6a5a;
  --status-active-bg: #e6f0ec;
  --status-draft: #7d5f0f;
  --status-draft-bg: #faf3e0;
  --status-superseded: #7a7168;
  --status-superseded-bg: #f0eeea;
  --status-warn: #a67208;
  --status-error: #a63d40;
  --radius: 5px;
  --radius-lg: 8px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.03);
  --shadow-md: 0 2px 6px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.03);
  --mono: "SF Mono", "Cascadia Code", "Fira Code", "JetBrains Mono", Consolas, monospace;
  --sans: "Source Sans 3", "Source Sans Pro", -apple-system, BlinkMacSystemFont,
          "Segoe UI", system-ui, sans-serif;
  --sidebar-w: 260px;
  --header-h: 52px;
  --transition: 180ms ease;
}

/* ── Reset ──────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { height: 100%; }
body {
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  height: 100%;
}
a { color: var(--accent); text-decoration: none; transition: color var(--transition); }
a:hover { color: var(--accent-hover); }
code, pre {
  font-family: var(--mono);
  font-size: 0.875em;
}
code {
  background: var(--surface-alt);
  padding: 1px 5px;
  border-radius: 3px;
}

/* ── Top Header ─────────────────────────────────────────────────────────── */
.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--header-h);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 24px;
}
.site-header .brand {
  font-size: 14px;
  font-weight: 700;
  font-family: var(--mono);
  color: var(--text-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
}
.site-header .brand span { color: var(--accent); }

/* Nav */
nav {
  display: flex;
  gap: 4px;
  font-size: 13px;
  font-family: var(--mono);
}
nav a {
  color: var(--text-muted);
  padding: 6px 12px;
  border-radius: var(--radius);
  transition: all var(--transition);
}
nav a:hover { color: var(--text-primary); background: var(--surface-alt); text-decoration: none; }
nav a.active { color: var(--accent); background: var(--accent-light); font-weight: 600; }

.header-spacer { flex: 1; }
.header-seal {
  font-size: 10px;
  font-family: var(--mono);
  color: var(--text-muted);
  white-space: nowrap;
}

/* ── Layout Shell ───────────────────────────────────────────────────────── */
.site-body {
  display: flex;
  min-height: calc(100vh - var(--header-h));
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 16px 0;
  font-size: 13px;
  position: sticky;
  top: var(--header-h);
  height: calc(100vh - var(--header-h));
}
.sidebar-section {
  padding: 0 16px;
  margin-bottom: 16px;
}
.sidebar-heading {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-bottom: 8px;
  padding: 0 4px;
}

/* Grouping toggles */
.group-toggles {
  display: flex;
  gap: 2px;
  padding: 0 16px;
  margin-bottom: 12px;
}
.group-btn {
  flex: 1;
  padding: 5px 0;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: all var(--transition);
  text-align: center;
}
.group-btn:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.group-btn:last-child { border-radius: 0 var(--radius) var(--radius) 0; }
.group-btn:not(:first-child) { border-left: none; }
.group-btn:hover { color: var(--text-primary); background: var(--surface-alt); }
.group-btn.active {
  background: var(--accent);
  color: var(--accent-text);
  border-color: var(--accent);
  font-weight: 600;
}
.group-btn.active + .group-btn { border-left-color: var(--accent); }

/* Tree */
.tree-container { padding: 0 8px; }
.tree-group { margin-bottom: 4px; }
.tree-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  cursor: pointer;
  border-radius: var(--radius);
  user-select: none;
  transition: background var(--transition);
}
.tree-group-header:hover { background: var(--surface-alt); }
.tree-chevron {
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  transition: transform var(--transition);
  flex-shrink: 0;
}
.tree-group.collapsed .tree-chevron { transform: rotate(-90deg); }
.tree-group-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tree-group-count {
  font-size: 10px;
  font-family: var(--mono);
  color: var(--text-muted);
  background: var(--surface-alt);
  padding: 1px 6px;
  border-radius: 8px;
  min-width: 20px;
  text-align: center;
}
.tree-items { padding-left: 12px; }
.tree-group.collapsed .tree-items { display: none; }
.tree-item {
  display: block;
  padding: 4px 8px;
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all var(--transition);
  text-decoration: none;
}
.tree-item:hover {
  background: var(--accent-light);
  color: var(--accent);
  text-decoration: none;
}
.tree-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
  flex-shrink: 0;
}
.tree-dot--active { background: var(--status-active); }
.tree-dot--draft { background: var(--status-draft); }
.tree-dot--superseded { background: var(--status-superseded); }

/* ── Main Content ───────────────────────────────────────────────────────── */
.main {
  flex: 1;
  min-width: 0;
  padding: 28px 36px 48px;
}

/* Page header */
h1 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--mono);
  margin-bottom: 24px;
}

/* KPI row */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}
.kpi {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition);
}
.kpi:hover { box-shadow: var(--shadow-md); }
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  font-family: var(--mono);
  line-height: 1.1;
}
.kpi-value--ok { color: var(--status-active); }
.kpi-value--warn { color: var(--status-warn); }
.kpi-value--error { color: var(--status-error); }
.kpi-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Table */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 32px;
  background: var(--surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
thead th {
  text-align: left;
  padding: 10px 12px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
  background: var(--surface-alt);
  font-weight: 700;
}
tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background var(--transition);
}
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--surface-hover); }
td { padding: 10px 12px; vertical-align: top; }
td a code { color: var(--accent); }
td a:hover code { color: var(--accent-hover); }

/* Status badge */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.badge--active { background: var(--status-active-bg); color: var(--status-active); }
.badge--draft { background: var(--status-draft-bg); color: var(--status-draft); }
.badge--superseded { background: var(--status-superseded-bg); color: var(--status-superseded); }

/* Tags */
.tag {
  font-size: 10px;
  font-family: var(--mono);
  padding: 2px 7px;
  border-radius: 3px;
  background: var(--surface-alt);
  color: var(--text-muted);
  display: inline-block;
  margin: 1px 2px;
}

/* Detail page */
.detail-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 24px;
}
.meta-grid {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 8px 16px;
  font-size: 13px;
}
.meta-key {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 700;
  padding-top: 3px;
}
.meta-val {
  font-family: var(--mono);
  word-break: break-all;
  color: var(--text-primary);
}

/* Section dividers */
.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-secondary);
  margin-top: 28px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* Footer */
footer {
  padding-top: 16px;
  border-top: 1px solid var(--border);
  margin-top: 40px;
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
}

/* Graph page */
#cy {
  width: 100%;
  height: 500px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.graph-controls {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}
.graph-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 11px;
  font-family: var(--mono);
  cursor: pointer;
  transition: all var(--transition);
}
.graph-btn:hover { border-color: var(--border-strong); background: var(--surface-alt); }
.graph-btn.active { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.graph-legend {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  font-size: 11px;
  color: var(--text-muted);
}
.graph-legend-item { display: flex; align-items: center; gap: 6px; }

/* Back link */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 24px;
  transition: color var(--transition);
}
.back-link:hover { color: var(--accent); text-decoration: none; }

/* ── Folder Tree Page ──────────────────────────────────────────────────── */
.tree-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: 20px;
  overflow: hidden;
}
.tree-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--surface-alt);
  border-bottom: 1px solid var(--border);
}
.tree-folder-icon {
  width: 18px;
  height: 18px;
  color: var(--accent);
  flex-shrink: 0;
}
.tree-card-path {
  font-size: 14px;
  font-weight: 600;
  flex: 1;
}
.tree-card-path code {
  background: none;
  padding: 0;
  font-size: 14px;
}
.tree-table {
  box-shadow: none;
  border-radius: 0;
  margin-bottom: 0;
}
.tree-table thead th { font-size: 9px; padding: 8px 12px; }
.tree-table td { padding: 8px 12px; font-size: 12px; }
.tree-table .size-col { text-align: right; font-family: var(--mono); font-size: 11px; color: var(--text-muted); }

/* ── Search & Filter ───────────────────────────────────────────────────── */
.search-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
#search-input {
  flex: 1;
  min-width: 200px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--sans);
  font-size: 13px;
  background: var(--surface);
  color: var(--text-primary);
  outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
}
#search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-light);
}
#search-input::placeholder { color: var(--text-muted); }
.filter-chips { display: flex; gap: 4px; }
.filter-chip {
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--mono);
  cursor: pointer;
  transition: all var(--transition);
}
.filter-chip:hover { color: var(--text-primary); background: var(--surface-alt); }
.filter-chip.active {
  background: var(--accent);
  color: var(--accent-text);
  border-color: var(--accent);
}

/* ── Cross-ref & Supplements (doc page) ────────────────────────────────── */
.xref-supplements {
  margin-top: 24px;
  margin-bottom: 8px;
}
.xref-supplements > summary {
  cursor: pointer;
  list-style: none;
}
.xref-supplements > summary::-webkit-details-marker { display: none; }
.xref-supplements > summary::before {
  content: "\\25B8 ";
  color: var(--text-muted);
  margin-right: 4px;
}
.xref-supplements[open] > summary::before { content: "\\25BE "; }
.xref-grid {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 6px 12px;
  font-size: 13px;
  padding: 12px 0 0 4px;
}
.xref-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 700;
  padding-top: 2px;
}

/* ── Rendered Document Content (prose) ─────────────────────────────────── */
.doc-content {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 28px 32px;
  box-shadow: var(--shadow-sm);
  margin-top: 8px;
  overflow-x: auto;
}
.doc-content pre {
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
  margin: 16px 0;
}
.doc-content pre code {
  background: none;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
}
.content-missing {
  color: var(--text-muted);
  font-style: italic;
  padding: 12px 0;
}

/* Prose typography */
.prose h1 { font-size: 1.5em; font-weight: 700; margin: 1.4em 0 0.6em; padding-bottom: 0.3em; border-bottom: 1px solid var(--border); }
.prose h2 { font-size: 1.25em; font-weight: 700; margin: 1.3em 0 0.5em; padding-bottom: 0.25em; border-bottom: 1px solid var(--border); }
.prose h3 { font-size: 1.1em; font-weight: 700; margin: 1.2em 0 0.4em; }
.prose h4 { font-size: 1em; font-weight: 700; margin: 1em 0 0.3em; }
.prose h5, .prose h6 { font-size: 0.9em; font-weight: 700; margin: 0.8em 0 0.3em; color: var(--text-secondary); }
.prose p { margin: 0.7em 0; line-height: 1.7; }
.prose ul, .prose ol { margin: 0.6em 0; padding-left: 1.8em; }
.prose li { margin: 0.25em 0; line-height: 1.6; }
.prose blockquote {
  border-left: 3px solid var(--accent);
  margin: 1em 0;
  padding: 0.5em 1em;
  color: var(--text-secondary);
  background: var(--surface-alt);
  border-radius: 0 var(--radius) var(--radius) 0;
}
.prose blockquote p { margin: 0.3em 0; }
.prose hr { border: none; border-top: 1px solid var(--border); margin: 1.5em 0; }
.prose a { color: var(--accent); text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 2px; }
.prose a:hover { color: var(--accent-hover); }
.prose strong { font-weight: 700; }
.prose em { font-style: italic; }
.prose img { max-width: 100%; border-radius: var(--radius); margin: 0.8em 0; }
.prose .md-table { margin: 1em 0; font-size: 13px; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 900px) {
  .sidebar { display: none; }
  .main { padding: 20px 16px 40px; }
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
  .meta-grid { grid-template-columns: 1fr; }
  #cy { height: 300px; }
}
@media (max-width: 600px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  nav { gap: 2px; }
  nav a { padding: 6px 8px; font-size: 12px; }
}
"""

# SVG icons used in the sidebar
_CHEVRON_SVG = '<svg class="tree-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 4l4 4-4 4"/></svg>'


# ── Page builders ────────────────────────────────────────────────────────


def _nav(active: str, has_dashboard: bool = False, prefix: str = "") -> str:
    """Build the navigation bar HTML."""
    links = [
        ("index.html", "Index", "index"),
        ("tree.html", "Tree", "tree"),
        ("graph.html", "Graph", "graph"),
    ]
    if has_dashboard:
        links.append(("dashboard.html", "Dashboard", "dashboard"))

    parts = []
    for href, label, key in links:
        cls = ' class="active"' if key == active else ""
        parts.append(f'<a href="{prefix}{href}"{cls}>{label}</a>')
    return "<nav>" + "".join(parts) + "</nav>"


def _sidebar_html(documents: list[dict], base_prefix: str = "") -> str:
    """Build the sidebar HTML with grouping toggles and tree."""
    tree_json = _build_tree_json(documents)

    return f"""<aside class="sidebar" id="sidebar">
  <div class="sidebar-section">
    <div class="sidebar-heading">Documents</div>
  </div>
  <div class="group-toggles">
    <button class="group-btn active" data-group="status" onclick="switchGroup(this, 'status')">Status</button>
    <button class="group-btn" data-group="tag" onclick="switchGroup(this, 'tag')">Tag</button>
    <button class="group-btn" data-group="path" onclick="switchGroup(this, 'path')">Path</button>
  </div>
  <div class="tree-container" id="tree-container"></div>
  <script>
  var TREE_DATA = {tree_json};
  var BASE_PREFIX = "{base_prefix}";
  function renderTree(mode) {{
    var container = document.getElementById("tree-container");
    var groups = TREE_DATA[mode] || {{}};
    var html = "";
    var keys = Object.keys(groups).sort();
    keys.forEach(function(key) {{
      var docs = groups[key];
      html += '<div class="tree-group">';
      html += '<div class="tree-group-header" onclick="this.parentElement.classList.toggle(\\x27collapsed\\x27)">';
      html += '{_CHEVRON_SVG}';
      html += '<span class="tree-group-label">' + key + '</span>';
      html += '<span class="tree-group-count">' + docs.length + '</span>';
      html += '</div>';
      html += '<div class="tree-items">';
      docs.forEach(function(d) {{
        var dotCls = "tree-dot tree-dot--" + (d.status || "");
        html += '<a class="tree-item" href="' + BASE_PREFIX + 'docs/' + d.filename + '.html">';
        html += '<span class="' + dotCls + '"></span>';
        html += d.title || d.filename;
        html += '</a>';
      }});
      html += '</div></div>';
    }});
    container.innerHTML = html;
  }}
  function switchGroup(btn, mode) {{
    document.querySelectorAll(".group-btn").forEach(function(b) {{ b.classList.remove("active"); }});
    btn.classList.add("active");
    renderTree(mode);
  }}
  renderTree("status");
  </script>
</aside>"""


def _page(
    title: str,
    body: str,
    active_nav: str,
    *,
    project_name: str = "Librarian",
    generated_at: str = "",
    seal: str = "",
    extra_head: str = "",
    has_dashboard: bool = False,
    sidebar: str = "",
    path_prefix: str = "",
) -> str:
    """Wrap body content in the full HTML page shell.

    Args:
        path_prefix: Relative path prefix for asset/nav links.
            Root pages use ``""``, pages in ``docs/`` use ``"../"``.
    """
    seal_short = _esc(seal[:16]) + "..." if seal else "N/A"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)} — {_esc(project_name)}</title>
<link rel="stylesheet" href="{path_prefix}assets/style.css">
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="brand"><span>&#9670;</span> {_esc(project_name)}</div>
  {_nav(active_nav, has_dashboard=has_dashboard, prefix=path_prefix)}
  <div class="header-spacer"></div>
  <div class="header-seal">seal {seal_short}</div>
</header>
<div class="site-body">
{sidebar}
<main class="main">
{body}
<footer>
<span>Librarian</span>
<span>Generated {_esc(generated_at)}</span>
</footer>
</main>
</div>
</body>
</html>"""


def _build_index(manifest: "Manifest") -> str:
    """Build the index.html page content."""
    snapshot = manifest.registry_snapshot
    documents = snapshot.get("documents", [])
    meta = snapshot.get("registry_meta", {})
    config = snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")

    # KPI cards
    kpis = [
        ("Total", meta.get("total_documents", len(documents)), ""),
        ("Active", meta.get("active", 0), "ok"),
        ("Draft", meta.get("draft", 0), "warn" if meta.get("draft", 0) > 0 else "ok"),
        ("Superseded", meta.get("superseded", 0), ""),
        ("Violations", meta.get("naming_violations", 0), "error" if meta.get("naming_violations", 0) > 0 else "ok"),
        ("Pending XRefs", meta.get("pending_cross_reference_updates", 0), "warn" if meta.get("pending_cross_reference_updates", 0) > 0 else "ok"),
    ]
    kpi_html = '<div class="kpi-row">'
    for label, value, cls in kpis:
        val_cls = f" kpi-value--{cls}" if cls else ""
        kpi_html += f'<div class="kpi"><div class="kpi-value{val_cls}">{value}</div><div class="kpi-label">{label}</div></div>'
    kpi_html += "</div>"

    # Document table
    rows = ""
    for doc in sorted(documents, key=lambda d: d.get("filename", "")):
        fn = doc.get("filename", "")
        status = doc.get("status", "")
        badge_cls = f"badge--{status}" if status in ("active", "draft", "superseded") else ""
        tags_html = "".join(f'<span class="tag">{_esc(t)}</span>' for t in (doc.get("tags") or []))
        fmt = doc.get("format", fn.rsplit(".", 1)[-1] if "." in fn else "")

        rows += f"""<tr>
<td><a href="docs/{_esc(fn)}.html"><code>{_esc(fn)}</code></a></td>
<td>{_esc(doc.get('title', ''))}</td>
<td><code>{_esc(doc.get('version', ''))}</code></td>
<td><span class="badge {badge_cls}">{_esc(status)}</span></td>
<td>{_esc(doc.get('date', doc.get('created', '')))}</td>
<td><code>{_esc(fmt)}</code></td>
<td>{tags_html}</td>
</tr>"""

    table = f"""<table>
<thead><tr>
<th>Filename</th><th>Title</th><th>Ver</th><th>Status</th><th>Date</th><th>Fmt</th><th>Tags</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>"""

    search_html = """<div class="search-bar">
<input type="text" id="search-input" placeholder="Filter documents..." autocomplete="off">
<div class="filter-chips" id="filter-chips">
<button class="filter-chip active" data-filter="all" onclick="filterStatus(this,'all')">All</button>
<button class="filter-chip" data-filter="active" onclick="filterStatus(this,'active')">Active</button>
<button class="filter-chip" data-filter="draft" onclick="filterStatus(this,'draft')">Draft</button>
<button class="filter-chip" data-filter="superseded" onclick="filterStatus(this,'superseded')">Superseded</button>
</div>
</div>
<script>
(function(){
  var input=document.getElementById("search-input");
  var currentFilter="all";
  function applyFilters(){
    var q=input.value.toLowerCase();
    var rows=document.querySelectorAll("tbody tr");
    var visible=0;
    rows.forEach(function(r){
      var text=r.textContent.toLowerCase();
      var matchQ=!q||text.indexOf(q)>=0;
      var status=r.querySelector(".badge");
      var st=status?status.textContent.trim().toLowerCase():"";
      var matchF=currentFilter==="all"||st===currentFilter;
      r.style.display=(matchQ&&matchF)?"":"none";
      if(matchQ&&matchF)visible++;
    });
  }
  input.addEventListener("input",applyFilters);
  window.filterStatus=function(btn,f){
    currentFilter=f;
    document.querySelectorAll(".filter-chip").forEach(function(b){b.classList.remove("active")});
    btn.classList.add("active");
    applyFilters();
  };
})();
</script>"""

    body = f"""<h1>{_esc(project_name)} — Document Registry</h1>
<div class="subtitle">{len(documents)} registered documents</div>
{kpi_html}
{search_html}
{table}"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Index",
        body,
        "index",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=True,
        sidebar=sidebar,
    )


def _build_tree_page(manifest: "Manifest") -> str:
    """Build a folder-tree page showing directory structure with files."""
    config = manifest.registry_snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")
    documents = manifest.registry_snapshot.get("documents", [])

    # Group by directory
    dirs: dict[str, list[dict]] = defaultdict(list)
    for doc in documents:
        path = doc.get("path", doc.get("filename", ""))
        parent = str(PurePosixPath(path).parent) if "/" in path else "."
        dirs[parent].append(doc)

    # Sort dirs and files
    sorted_dirs = sorted(dirs.items())
    total_dirs = len(sorted_dirs)

    # Build folder cards
    cards = ""
    for dir_path, docs in sorted_dirs:
        docs_sorted = sorted(docs, key=lambda d: d.get("filename", ""))
        dir_label = dir_path if dir_path != "." else "(project root)"

        # File rows
        file_rows = ""
        for doc in docs_sorted:
            fn = doc.get("filename", "")
            status = doc.get("status", "")
            badge_cls = f"badge--{status}" if status in ("active", "draft", "superseded") else ""
            fmt = doc.get("format", fn.rsplit(".", 1)[-1] if "." in fn else "")
            size_str = ""
            file_hash = next((h for h in manifest.file_hashes if h.filename == fn), None)
            if file_hash and file_hash.exists:
                if file_hash.size_bytes >= 1024:
                    size_str = f"{file_hash.size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{file_hash.size_bytes} B"

            file_rows += f"""<tr>
<td><a href="docs/{_esc(fn)}.html"><code>{_esc(fn)}</code></a></td>
<td>{_esc(doc.get('title', ''))}</td>
<td><span class="badge {badge_cls}">{_esc(status)}</span></td>
<td><code>{_esc(fmt)}</code></td>
<td class="size-col">{size_str}</td>
</tr>
"""

        cards += f"""<div class="tree-card">
<div class="tree-card-header">
<svg class="tree-folder-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
<span class="tree-card-path"><code>{_esc(dir_label)}</code></span>
<span class="tree-group-count">{len(docs_sorted)}</span>
</div>
<table class="tree-table">
<thead><tr><th>Filename</th><th>Title</th><th>Status</th><th>Fmt</th><th>Size</th></tr></thead>
<tbody>{file_rows}</tbody>
</table>
</div>
"""

    body = f"""<h1>Folder Structure</h1>
<div class="subtitle">{len(documents)} files across {total_dirs} directories</div>
{cards}"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Tree",
        body,
        "tree",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=True,
        sidebar=sidebar,
    )


def _build_doc_page(doc: dict, manifest: "Manifest", repo_root: str | Path = "") -> str:
    """Build a per-document detail page with rendered file content."""
    config = manifest.registry_snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")
    documents = manifest.registry_snapshot.get("documents", [])
    fn = doc.get("filename", "")
    status = doc.get("status", "")
    badge_cls = f"badge--{status}" if status in ("active", "draft", "superseded") else ""

    # Find hash
    file_hash = next((h for h in manifest.file_hashes if h.filename == fn), None)

    # Cross-references
    xrefs = doc.get("cross_references") or []
    xref_html = ""
    if xrefs:
        xref_items = []
        for x in xrefs:
            if isinstance(x, dict):
                target = x.get("doc", x.get("target", ""))
                xst = x.get("status", "")
                sections = ", ".join(x.get("sections", []))
                xref_items.append(
                    f'<a href="{_esc(target)}.html">{_esc(target)}</a>'
                    f'{" (" + _esc(xst) + ")" if xst else ""}'
                    f'{" — " + _esc(sections) if sections else ""}'
                )
        xref_html = "<br>".join(xref_items) if xref_items else "none"
    else:
        xref_html = "none"

    # Supplements
    supps = doc.get("supplements") or []
    supp_html = ", ".join(f'<a href="{_esc(s)}.html">{_esc(s)}</a>' for s in supps) if supps else "none"

    # Tags
    tags_html = "".join(f'<span class="tag">{_esc(t)}</span> ' for t in (doc.get("tags") or []))

    meta_rows = f"""
<span class="meta-key">Filename</span><span class="meta-val"><code>{_esc(fn)}</code></span>
<span class="meta-key">Title</span><span class="meta-val">{_esc(doc.get('title', ''))}</span>
<span class="meta-key">Version</span><span class="meta-val"><code>{_esc(doc.get('version', ''))}</code></span>
<span class="meta-key">Status</span><span class="meta-val"><span class="badge {badge_cls}">{_esc(status)}</span></span>
<span class="meta-key">Date</span><span class="meta-val">{_esc(doc.get('date', doc.get('created', '')))}</span>
<span class="meta-key">Author</span><span class="meta-val">{_esc(doc.get('author', ''))}</span>
<span class="meta-key">Classification</span><span class="meta-val">{_esc(doc.get('classification', ''))}</span>
<span class="meta-key">Path</span><span class="meta-val"><code>{_esc(doc.get('path', ''))}</code></span>
<span class="meta-key">Format</span><span class="meta-val"><code>{_esc(doc.get('format', ''))}</code></span>
<span class="meta-key">Tags</span><span class="meta-val">{tags_html or 'none'}</span>
<span class="meta-key">Infra Exempt</span><span class="meta-val">{'yes' if doc.get('infrastructure_exempt') else 'no'}</span>
<span class="meta-key">SHA-256</span><span class="meta-val"><code>{_esc(file_hash.sha256) if file_hash and file_hash.exists else 'not on disk'}</code></span>
<span class="meta-key">Size</span><span class="meta-val">{f'{file_hash.size_bytes:,} bytes' if file_hash and file_hash.exists else '—'}</span>
"""

    # Supersedes chain
    sup_chain = ""
    if doc.get("supersedes"):
        s = doc["supersedes"]
        sup_chain += f'<span class="meta-key">Supersedes</span><span class="meta-val"><a href="{_esc(s)}.html"><code>{_esc(s)}</code></a></span>\n'
    if doc.get("superseded_by"):
        s = doc["superseded_by"]
        sup_chain += f'<span class="meta-key">Superseded By</span><span class="meta-val"><a href="{_esc(s)}.html"><code>{_esc(s)}</code></a></span>\n'

    # Render file content from disk
    content_html = ""
    effective_root = repo_root or manifest.repo_root
    if effective_root:
        content_html = _render_file_content(doc, effective_root)

    body = f"""<h1><code>{_esc(fn)}</code></h1>
<div class="subtitle">{_esc(doc.get('title', ''))}</div>

<div class="detail-card">
<div class="meta-grid">
{meta_rows}
{sup_chain}
</div>
</div>

<h3 class="section-title">Description</h3>
<p>{_esc(doc.get('description', '—'))}</p>

<details class="xref-supplements" open>
<summary class="section-title">Cross-References &amp; Supplements</summary>
<div class="xref-grid">
<span class="xref-label">Cross-refs</span><span>{xref_html}</span>
<span class="xref-label">Supplements</span><span>{supp_html}</span>
</div>
</details>

<h3 class="section-title">Contents</h3>
{content_html if content_html else '<p class="content-missing">No content available.</p>'}

<a class="back-link" href="../index.html">&larr; Back to index</a>
"""

    sidebar = _sidebar_html(documents, base_prefix="../")

    return _page(
        fn,
        body,
        "",  # no nav item is "active" on doc pages
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=True,
        sidebar=sidebar,
        path_prefix="../",
    )


def _build_graph_page(manifest: "Manifest") -> str:
    """Build the standalone graph page with inlined cytoscape.js."""
    config = manifest.registry_snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")
    documents = manifest.registry_snapshot.get("documents", [])

    # Build cytoscape elements as JSON
    edges = manifest.dependency_edges
    doc_map = {d.get("filename", ""): d for d in documents}
    node_set: set[str] = set()
    for d in documents:
        node_set.add(d.get("filename", ""))
    for e in edges:
        node_set.add(e.source)
        node_set.add(e.target)

    cy_nodes = []
    for fn in sorted(node_set):
        doc = doc_map.get(fn, {})
        status = doc.get("status", "unknown")
        color_map = {
            "active": "#2d6a5a",
            "draft": "#7d5f0f",
            "superseded": "#7a7168",
        }
        cy_nodes.append({
            "data": {
                "id": fn,
                "label": fn[:28] + "..." if len(fn) > 30 else fn,
                "status": status,
                "title": doc.get("title", fn),
                "color": color_map.get(status, "#908a82"),
            }
        })

    cy_edges = []
    for i, e in enumerate(edges):
        cy_edges.append({
            "data": {
                "id": f"e{i}",
                "source": e.source,
                "target": e.target,
                "edgeType": e.status or "unknown",
            }
        })

    elements_json = json.dumps(cy_nodes + cy_edges, indent=2, sort_keys=True)

    # Try to read cytoscape.min.js from the dashboard template directory
    cytoscape_js = _load_cytoscape_js()

    body = f"""<h1>Cross-Reference Graph</h1>
<div class="subtitle">{len(cy_nodes)} nodes · {len(cy_edges)} edges</div>

<div class="graph-controls">
  <button class="graph-btn active" onclick="setLayout(this, 'cose')">Force</button>
  <button class="graph-btn" onclick="setLayout(this, 'breadthfirst')">Hierarchy</button>
  <button class="graph-btn" onclick="setLayout(this, 'circle')">Circle</button>
</div>
<div id="cy"></div>
<div class="graph-legend">
  <span class="graph-legend-item"><span style="display:inline-block;width:12px;height:3px;background:#2d6a5a;border-radius:2px"></span> cross-ref</span>
  <span class="graph-legend-item"><span style="display:inline-block;width:12px;height:0;border-top:2px dashed #7d5f0f"></span> supplement</span>
  <span class="graph-legend-item"><span style="display:inline-block;width:12px;height:0;border-top:2px dotted #7a7168"></span> supersedes</span>
</div>
"""

    extra_head = f"""<script>
{cytoscape_js}
</script>
<script>
var ELEMENTS = {elements_json};
</script>"""

    graph_script = """
<script>
(function() {
  var cy = cytoscape({
    container: document.getElementById("cy"),
    elements: ELEMENTS,
    style: [
      { selector: "node", style: {
        "label": "data(label)", "background-color": "data(color)",
        "color": "#1a1816", "font-size": "10px",
        "font-family": "Source Sans 3, sans-serif",
        "text-valign": "bottom", "text-margin-y": 6,
        "width": 22, "height": 22,
        "border-width": 2, "border-color": "#ffffff"
      }},
      { selector: "edge", style: {
        "width": 1.5, "line-color": "#908a82",
        "target-arrow-color": "#908a82", "target-arrow-shape": "triangle",
        "arrow-scale": 0.8, "curve-style": "bezier"
      }},
      { selector: 'edge[edgeType = "supplement"]', style: { "line-style": "dashed", "line-color": "#7d5f0f", "target-arrow-color": "#7d5f0f" }},
      { selector: 'edge[edgeType = "supersedes"]', style: { "line-style": "dotted" }},
      { selector: 'edge[edgeType = "pending"]', style: { "line-color": "#a67208", "target-arrow-color": "#a67208" }},
      { selector: "node:selected", style: { "border-width": 3, "border-color": "#2d6a5a" }}
    ],
    layout: { name: "cose", animate: true, animationDuration: 300, padding: 30, nodeRepulsion: function(){ return 8000; } },
    wheelSensitivity: 0.3
  });
  cy.on("tap", "node", function(evt) {
    cy.elements().style("opacity", 0.15);
    evt.target.style("opacity", 1);
    evt.target.neighborhood().style("opacity", 1);
  });
  cy.on("tap", function(evt) {
    if (evt.target === cy) cy.elements().style("opacity", 1);
  });
  window.setLayout = function(btn, name) {
    document.querySelectorAll(".graph-btn").forEach(function(b){ b.classList.remove("active"); });
    btn.classList.add("active");
    cy.layout({ name: name, animate: true, animationDuration: 300, padding: 30, nodeRepulsion: function(){ return 8000; } }).run();
  };
})();
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Graph",
        body + graph_script,
        "graph",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        extra_head=extra_head,
        has_dashboard=True,
        sidebar=sidebar,
    )


def _load_cytoscape_js() -> str:
    """Load cytoscape.min.js from the dashboard template or npm."""
    # Check for npm-installed version
    candidates = [
        Path(__file__).resolve().parent.parent / "node_modules" / "cytoscape" / "dist" / "cytoscape.min.js",
    ]
    for p in candidates:
        try:
            if p.is_file():
                return p.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            continue

    # Extract from the dashboard template as last resort
    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
    templates = sorted(dashboard_dir.glob("librarian-dashboard-template-*.html"), reverse=True)
    if templates:
        html = templates[0].read_text(encoding="utf-8")
        # cytoscape.js is in the second <script> block (after lunr)
        # Find it by looking for the cytoscape signature (case-insensitive)
        scripts = html.split("<script>")
        for block in scripts:
            if "cytoscape" in block[:300].lower():
                end = block.find("</script>")
                if end > 0:
                    return block[:end]

    # Fallback: return a minimal inline stub that prevents errors.
    # The graph page will render without interactive features.
    return (
        '/* cytoscape.js not found — using CDN fallback placeholder */\n'
        'var cytoscape = function(opts){ var noop = function(){ return this; }; '
        'return { on: noop, elements: function(){ return { style: noop }; }, '
        'layout: function(){ return { run: noop }; } }; };'
    )


def _inject_dashboard_nav(dashboard_file: Path) -> None:
    """Inject a floating site navigation bar into the standalone dashboard.

    The dashboard template is self-contained and doesn't include the site
    nav. This injects a small fixed-position nav strip at the top so users
    can navigate back to the rest of the site.
    """
    html = dashboard_file.read_text(encoding="utf-8")
    if "site-nav-overlay" in html:
        return  # already injected

    nav_html = """\
<style>
.site-nav-overlay {
  position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
  height: 36px; background: rgba(255,255,255,0.95);
  border-bottom: 1px solid #e4e1da;
  display: flex; align-items: center; gap: 16px;
  padding: 0 20px; font-family: "SF Mono", Consolas, monospace;
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
}
.site-nav-overlay a {
  font-size: 12px; color: #908a82; text-decoration: none;
  padding: 4px 10px; border-radius: 4px; transition: all 0.15s;
}
.site-nav-overlay a:hover { color: #1a1816; background: #f3f2ee; }
.site-nav-overlay a.active { color: #2d6a5a; background: #e6f0ec; font-weight: 600; }
.site-nav-overlay .brand { font-size: 12px; font-weight: 700; color: #1a1816; }
.site-nav-overlay .brand span { color: #2d6a5a; }
</style>
<div class="site-nav-overlay">
  <div class="brand"><span>&#9670;</span> Librarian</div>
  <a href="index.html">Index</a>
  <a href="tree.html">Tree</a>
  <a href="graph.html">Graph</a>
  <a href="dashboard.html" class="active">Dashboard</a>
</div>
<style>body { padding-top: 36px; }</style>
"""
    # Inject after <body> tag
    html = html.replace("<body>", "<body>\n" + nav_html, 1)
    dashboard_file.write_text(html, encoding="utf-8")


# ── Main entry ───────────────────────────────────────────────────────────


def generate_site(
    manifest: "Manifest",
    output_dir: str | Path,
    *,
    dashboard_path: str | Path | None = None,
) -> Path:
    """Generate the complete static site.

    Args:
        manifest: A populated Manifest dataclass.
        output_dir: Directory to write the site into (created if needed).
        dashboard_path: Optional path to a pre-rendered dashboard HTML.
            If provided, it is copied into the site as ``dashboard.html``.

    Returns:
        The resolved output directory path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Assets
    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "style.css").write_text(SITE_CSS, encoding="utf-8")

    # Determine if dashboard exists
    has_dashboard = False
    if dashboard_path:
        dp = Path(dashboard_path).resolve()
        dest = (out / "dashboard.html").resolve()
        if dp.is_file() and dp != dest:
            shutil.copy2(dp, dest)
        has_dashboard = dest.is_file()
        # Inject site navigation bar into the dashboard
        if has_dashboard:
            _inject_dashboard_nav(dest)

    # Index
    (out / "index.html").write_text(_build_index(manifest), encoding="utf-8")

    # Per-document pages
    docs_dir = out / "docs"
    docs_dir.mkdir(exist_ok=True)
    documents = manifest.registry_snapshot.get("documents", [])
    effective_root = manifest.repo_root or ""
    for doc in documents:
        fn = doc.get("filename", "")
        if not fn:
            continue
        page_html = _build_doc_page(doc, manifest, repo_root=effective_root)
        (docs_dir / f"{fn}.html").write_text(page_html, encoding="utf-8")

    # Graph page
    # Tree page
    (out / "tree.html").write_text(_build_tree_page(manifest), encoding="utf-8")

    # Graph page
    (out / "graph.html").write_text(_build_graph_page(manifest), encoding="utf-8")

    return out.resolve()
