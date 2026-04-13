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
.settings-gear {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: var(--radius);
  color: var(--text-muted);
  transition: all var(--transition);
  position: relative;
  margin-left: 8px;
}
.settings-gear:hover { color: var(--accent); background: var(--surface-alt); }
.settings-gear.active { color: var(--accent); background: var(--accent-light); }
.settings-gear svg { width: 16px; height: 16px; }
.settings-gear[title]:hover::after {
  content: attr(title);
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  padding: 4px 8px;
  font-size: 11px;
  font-family: var(--sans);
  color: var(--accent-text);
  background: var(--text-primary);
  border-radius: var(--radius);
  white-space: nowrap;
  pointer-events: none;
  z-index: 10;
}
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

/* ── Interactive Tree Diagram ─────────────────────────────────────────── */
.tree-diagram {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 20px 24px;
  margin-bottom: 28px;
  overflow-x: auto;
}
.tree-diagram-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 14px;
}
.td-node { list-style: none; padding-left: 0; margin: 0; }
.td-node .td-node { padding-left: 22px; }
.td-entry {
  position: relative;
  padding: 3px 0;
}
/* vertical + horizontal connector lines */
.td-node .td-node .td-entry::before {
  content: "";
  position: absolute;
  left: -14px;
  top: 0;
  width: 14px;
  height: 13px;
  border-left: 1px solid var(--border-strong);
  border-bottom: 1px solid var(--border-strong);
  border-bottom-left-radius: 4px;
}
.td-node .td-node .td-entry:not(:last-child)::after {
  content: "";
  position: absolute;
  left: -14px;
  top: 13px;
  bottom: -3px;
  border-left: 1px solid var(--border-strong);
}
.td-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-family: var(--mono);
  padding: 3px 8px;
  border-radius: var(--radius);
  cursor: default;
  transition: background var(--transition);
  color: var(--text-primary);
}
.td-label--folder {
  font-weight: 600;
  cursor: pointer;
  color: var(--accent);
}
.td-label--folder:hover {
  background: var(--accent-light);
}
.td-label--file a {
  color: var(--text-secondary);
  text-decoration: none;
}
.td-label--file a:hover {
  color: var(--accent);
  text-decoration: underline;
}
.td-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
.td-icon--folder { color: var(--accent); }
.td-icon--file { color: var(--text-muted); }
.td-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  color: var(--text-muted);
  transition: transform var(--transition);
  flex-shrink: 0;
}
.td-toggle svg { width: 12px; height: 12px; }
.td-branch.collapsed > .td-entry > .td-label > .td-toggle { transform: rotate(-90deg); }
.td-branch.collapsed > .td-node { display: none; }
.td-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.td-status-dot--active { background: var(--status-active); }
.td-status-dot--draft { background: var(--status-draft); }
.td-status-dot--superseded { background: var(--status-superseded); }
.td-file-count {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--surface-alt);
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 500;
}

/* ── Settings Page ────────────────────────────────────────────────────── */
.settings-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: 24px;
  overflow: hidden;
}
.settings-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: var(--surface-alt);
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.settings-section-header svg {
  width: 16px; height: 16px; color: var(--accent); flex-shrink: 0;
}
.settings-grid {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 0;
  padding: 0;
}
.settings-row {
  display: contents;
}
.settings-row:hover .settings-label,
.settings-row:hover .settings-control {
  background: var(--surface-alt);
}
.settings-label {
  padding: 10px 20px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
}
.settings-control {
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}
.settings-control select,
.settings-control input[type="text"] {
  font-family: var(--mono);
  font-size: 12px;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text-primary);
  outline: none;
  transition: border-color var(--transition);
}
.settings-control select:focus,
.settings-control input[type="text"]:focus {
  border-color: var(--accent);
}
.settings-control select { min-width: 160px; cursor: pointer; }
.settings-control input[type="text"] { width: 100%; max-width: 300px; }
.settings-toggle {
  position: relative;
  width: 36px; height: 20px;
  background: var(--border-strong);
  border-radius: 10px;
  cursor: pointer;
  transition: background var(--transition);
  border: none;
  padding: 0;
}
.settings-toggle.on { background: var(--accent); }
.settings-toggle::after {
  content: "";
  position: absolute;
  top: 2px; left: 2px;
  width: 16px; height: 16px;
  background: white;
  border-radius: 50%;
  transition: transform var(--transition);
}
.settings-toggle.on::after { transform: translateX(16px); }
.settings-hint {
  font-size: 10px;
  color: var(--text-muted);
  margin-left: 4px;
}
.settings-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.settings-tag-item {
  font-size: 11px;
  font-family: var(--mono);
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.settings-tag-item .tag-remove {
  cursor: pointer;
  opacity: 0.7;
  font-size: 14px;
  line-height: 1;
  font-style: normal;
  color: var(--danger, #d32f2f);
  margin-left: 2px;
  padding: 0 2px;
  border-radius: 3px;
}
.settings-tag-item .tag-remove:hover { opacity: 1; background: var(--danger, #d32f2f); color: #fff; }
.settings-tag-add {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  margin-top: 4px;
}
.settings-tag-add input {
  font-size: 11px;
  font-family: var(--mono);
  padding: 2px 6px;
  border: 1px solid var(--border);
  border-radius: 4px;
  width: 140px;
  background: var(--surface);
  color: var(--text-primary);
}
.settings-tag-add button {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--accent);
  border-radius: 4px;
  background: var(--accent-light);
  color: var(--accent);
  cursor: pointer;
}
.settings-tag-add button:hover { background: var(--accent); color: #fff; }
.settings-disclaimer-select {
  font-size: 12px;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text-primary);
  width: 100%;
  margin-top: 4px;
}
.settings-preview {
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
  margin: 16px 20px 20px;
  font-family: var(--mono);
  font-size: 13px;
  color: var(--accent);
  font-weight: 600;
}
.settings-preview-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 6px;
  font-family: var(--sans);
}
.settings-actions {
  display: flex;
  gap: 10px;
  margin: 20px 0 8px;
}
.settings-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--sans);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition);
}
.settings-btn:hover {
  background: var(--surface-alt);
  border-color: var(--border-strong);
}
.settings-btn--primary {
  background: var(--accent);
  color: var(--accent-text);
  border-color: var(--accent);
}
.settings-btn--primary:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}
.settings-btn svg { width: 14px; height: 14px; }
.settings-yaml {
  background: var(--text-primary);
  color: #e8e6e1;
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  margin-top: 12px;
  display: none;
}
.settings-yaml.visible { display: block; }
.settings-copied {
  font-size: 11px;
  color: var(--status-active);
  opacity: 0;
  transition: opacity 0.3s;
}
.settings-copied.show { opacity: 1; }

/* Settings layout: forms + preview side-by-side */
.settings-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.settings-forms { flex: 1; min-width: 0; }
.settings-preview-panel {
  width: 300px;
  flex-shrink: 0;
  position: sticky;
  top: 80px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  font-size: 12px;
}
.settings-preview-panel-header {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent);
  margin-bottom: 12px;
}
.settings-preview-card {
  margin-bottom: 14px;
}
.settings-preview-card-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.settings-preview-card-value {
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-light);
  padding: 8px 12px;
  border-radius: var(--radius);
  word-break: break-all;
}
.settings-preview-doc {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  font-size: 11px;
}
.preview-banner {
  text-align: center;
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 0.1em;
  padding: 3px 0;
}
.banner-green { background: #d5e8d4; color: #2d6a2d; }
.banner-amber { background: #fef3cd; color: #856404; }
.banner-red { background: #f8d7da; color: #721c24; }
.banner-purple { background: #e8d5f5; color: #5b2d8e; }
.preview-hdr-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px 2px;
  color: var(--text-muted);
}
.preview-hdr-org { font-weight: 600; color: var(--text-primary); }
.preview-hdr-meta { font-size: 10px; }
.preview-hdr-title {
  padding: 2px 10px 8px;
  font-weight: 600;
  font-size: 12px;
  color: var(--text-primary);
}
.preview-ftr-row {
  padding: 6px 10px;
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.5;
}
.settings-preview-meta {
  font-size: 11px;
  line-height: 1.6;
  color: var(--text-secondary);
}
.settings-preview-meta div { padding: 1px 0; }

/* Compliance standards grid */
.settings-compliance-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.settings-compliance-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  cursor: pointer;
  transition: all var(--transition);
  text-align: center;
}
.settings-compliance-btn:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}
.settings-compliance-btn.active {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
  box-shadow: 0 0 0 2px var(--accent), 0 2px 8px rgba(0,0,0,0.15);
}
.settings-compliance-btn.active .settings-compliance-icon svg { color: #fff; }
.settings-compliance-btn.active .settings-compliance-name { color: #fff; }
.settings-compliance-btn.active .settings-compliance-desc { color: rgba(255,255,255,0.85); }
.settings-compliance-icon svg { width: 20px; height: 20px; color: var(--accent); }
.settings-compliance-name {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-primary);
}
.settings-compliance-desc {
  font-size: 10px;
  color: var(--text-muted);
}
@media (max-width: 900px) {
  .settings-layout { flex-direction: column; }
  .settings-preview-panel { width: 100%; position: static; }
  .settings-compliance-grid { grid-template-columns: repeat(2, 1fr); }
}

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


def _gear_link(active: str = "", prefix: str = "") -> str:
    """Gear icon link — rendered far right in header, tooltip only, no text."""
    GEAR_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'style="width:14px;height:14px;vertical-align:-2px">'
                '<circle cx="12" cy="12" r="3"/>'
                '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06'
                'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09'
                'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83'
                'l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09'
                'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83'
                'l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09'
                'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83'
                'l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09'
                'a1.65 1.65 0 0 0-1.51 1z"/></svg>')
    cls = "settings-gear active" if active == "settings" else "settings-gear"
    return (f'<a href="{prefix}settings.html" class="{cls}" '
            f'title="Settings" aria-label="Settings">{GEAR_SVG}</a>')


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
  {_gear_link(active_nav, path_prefix)}
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


def _build_tree_diagram(dirs: dict[str, list[dict]]) -> str:
    """Build an interactive folder-tree diagram as nested HTML lists."""
    FOLDER_SVG = ('<svg class="td-icon td-icon--folder" viewBox="0 0 24 24" '
                  'fill="none" stroke="currentColor" stroke-width="2">'
                  '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 '
                  '1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>')
    FILE_SVG = ('<svg class="td-icon td-icon--file" viewBox="0 0 24 24" '
                'fill="none" stroke="currentColor" stroke-width="2">'
                '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 '
                '0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>')
    CHEVRON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
               'stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>')

    # Build a nested tree: project root -> intermediate dirs -> files
    # First decompose paths into a nested dict
    tree: dict = {}  # nested: key = segment, value = dict or None (leaf)
    for dir_path, docs in sorted(dirs.items()):
        parts = [] if dir_path == "." else dir_path.split("/")
        node = tree
        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]
        # Store docs at this level under a sentinel key
        node["__docs__"] = docs

    def _render_node(subtree: dict, depth: int = 0) -> str:
        """Recursively render tree nodes as <ul>/<li> elements."""
        html = '<ul class="td-node">'
        # Render sub-folders first, then files
        folders = sorted(k for k in subtree if k != "__docs__" and isinstance(subtree[k], dict))
        docs = subtree.get("__docs__", [])

        for folder_name in folders:
            child = subtree[folder_name]
            # Count total docs recursively under this folder
            def _count(n: dict) -> int:
                c = len(n.get("__docs__", []))
                for k, v in n.items():
                    if k != "__docs__" and isinstance(v, dict):
                        c += _count(v)
                return c
            count = _count(child)
            # Build an anchor-safe id from the full path
            folder_id = _esc(folder_name).replace("/", "-").replace(" ", "-").lower()

            html += (f'<li class="td-entry td-branch">'
                     f'<span class="td-label td-label--folder" '
                     f'data-folder="{_esc(folder_name)}">'
                     f'<button class="td-toggle" aria-label="Toggle">{CHEVRON}</button>'
                     f'{FOLDER_SVG} {_esc(folder_name)}/'
                     f'<span class="td-file-count">{count}</span>'
                     f'</span>')
            html += _render_node(child, depth + 1)
            html += '</li>'

        # Render files at this level
        for doc in sorted(docs, key=lambda d: d.get("filename", "")):
            fn = doc.get("filename", "")
            status = doc.get("status", "")
            dot_cls = f"td-status-dot--{status}" if status in ("active", "draft", "superseded") else ""
            html += (f'<li class="td-entry">'
                     f'<span class="td-label td-label--file">'
                     f'{FILE_SVG} '
                     f'<span class="td-status-dot {dot_cls}"></span>'
                     f'<a href="docs/{_esc(fn)}.html">{_esc(fn)}</a>'
                     f'</span></li>')
        html += '</ul>'
        return html

    # Wrap in root node
    root_docs = tree.get("__docs__", [])
    root_folders = sorted(k for k in tree if k != "__docs__" and isinstance(tree[k], dict))

    diagram_inner = '<ul class="td-node">'
    diagram_inner += ('<li class="td-entry td-branch">'
                      '<span class="td-label td-label--folder">'
                      f'<button class="td-toggle" aria-label="Toggle">{CHEVRON}</button>'
                      f'{FOLDER_SVG} <strong>project root</strong>'
                      '</span>')
    # Render root children
    root_subtree = {k: tree[k] for k in root_folders}
    root_subtree["__docs__"] = root_docs
    diagram_inner += _render_node(root_subtree, 1)
    diagram_inner += '</li></ul>'

    # JS for toggle + click-to-scroll
    js = """<script>
document.querySelectorAll('.td-toggle').forEach(function(btn){
  btn.addEventListener('click', function(e){
    e.stopPropagation();
    var branch = btn.closest('.td-branch');
    if(branch) branch.classList.toggle('collapsed');
  });
});
document.querySelectorAll('.td-label--folder[data-folder]').forEach(function(lbl){
  lbl.addEventListener('click', function(e){
    if(e.target.closest('.td-toggle')) return;
    var name = lbl.getAttribute('data-folder');
    var cards = document.querySelectorAll('.tree-card-path code');
    for(var i=0;i<cards.length;i++){
      if(cards[i].textContent.indexOf(name) !== -1){
        cards[i].closest('.tree-card').scrollIntoView({behavior:'smooth',block:'start'});
        cards[i].closest('.tree-card').style.boxShadow='0 0 0 2px var(--accent)';
        setTimeout(function(){cards[i].closest('.tree-card').style.boxShadow='';},1500);
        break;
      }
    }
  });
});
</script>"""

    return f"""<div class="tree-diagram">
<div class="tree-diagram-title">Interactive Folder Map</div>
{diagram_inner}
</div>
{js}"""


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

    # Build interactive tree diagram
    diagram = _build_tree_diagram(dict(sorted_dirs))

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
{diagram}
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
  <a href="settings.html" title="Settings" aria-label="Settings" style="margin-left:auto"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;vertical-align:-2px"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></a>
</div>
<style>body { padding-top: 36px; }</style>
"""
    # Inject after <body> tag
    html = html.replace("<body>", "<body>\n" + nav_html, 1)
    dashboard_file.write_text(html, encoding="utf-8")


# ── Main entry ───────────────────────────────────────────────────────────


def _build_settings_page(manifest: "Manifest") -> str:
    """Build an interactive settings page to view/edit configuration."""
    from .config import PRESETS, NAMING_TEMPLATES, load_config

    snapshot = manifest.registry_snapshot
    pc = snapshot.get("project_config", {})
    config = load_config(project_config=pc)
    documents = snapshot.get("documents", [])
    project_name = config.project_name

    # SVG icons
    NAMING_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                   '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                   '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>'
                   '<line x1="16" y1="17" x2="8" y2="17"/></svg>')
    FOLDER_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                   '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>')
    TAG_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>'
                '<line x1="7" y1="7" x2="7.01" y2="7"/></svg>')
    COPY_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                 '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>'
                 '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>')
    DOWNLOAD_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                     '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                     '<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>')
    SHIELD_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                   '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>')
    HEADER_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                   '<rect x="3" y="3" width="18" height="18" rx="2"/>'
                   '<line x1="3" y1="9" x2="21" y2="9"/></svg>')
    CHECKLIST_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                      '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5'
                      'a2 2 0 0 1 2-2h11"/></svg>')

    # Detect active preset and template from project_config
    active_preset = pc.get("preset", "")
    active_template = pc.get("naming_rules", {}).get("template", "")

    # Build preset options
    preset_opts = '<option value="">— none —</option>'
    for name in PRESETS:
        sel = " selected" if name == active_preset else ""
        preset_opts += f'<option value="{_esc(name)}"{sel}>{_esc(name)}</option>'

    # Build naming template options
    template_opts = '<option value="">— custom —</option>'
    for name, rules in NAMING_TEMPLATES.items():
        from .config import NamingConfig as _NC
        nc = _NC(**{k: v for k, v in rules.items() if k in _NC.__dataclass_fields__})
        sel = " selected" if name == active_template else ""
        template_opts += f'<option value="{_esc(name)}"{sel}>{_esc(name)} — {_esc(nc.human_pattern)}</option>'

    # Build separator options
    sep_opts = ""
    for val, label in [("-", "Hyphen (-)"), ("_", "Underscore (_)"), (".", "Dot (.)")]:
        sel = " selected" if config.naming.separator == val else ""
        sep_opts += f'<option value="{_esc(val)}"{sel}>{_esc(label)}</option>'

    # Case options
    case_opts = ""
    for val in ["lowercase", "mixed", "uppercase"]:
        sel = " selected" if config.naming.case == val else ""
        case_opts += f'<option value="{val}"{sel}>{val}</option>'

    # Date format options
    date_opts = ""
    for val, label in [("YYYYMMDD", "YYYYMMDD"), ("YYYY-MM-DD", "YYYY-MM-DD"), ("off", "Off (no date)")]:
        sel = " selected" if config.naming.date_format == val else ""
        date_opts += f'<option value="{val}"{sel}>{_esc(label)}</option>'

    # Version format options
    ver_opts = ""
    for val in ["VX.Y", "vX.Y", "X.Y"]:
        sel = " selected" if config.naming.version_format == val else ""
        ver_opts += f'<option value="{val}"{sel}>{val}</option>'

    # Domain prefix toggle
    domain_on = "on" if config.naming.domain_prefix else ""

    # Strict mode toggle
    strict_on = "on" if config.categories.strict_mode else ""

    # Folder list
    folder_tags = ""
    for f in config.categories.folders:
        label = config.categories.labels.get(f.rstrip("/"), "")
        display = f"{f} — {label}" if label else f
        folder_tags += f'<span class="settings-tag-item">{_esc(display)}</span>'
    if not folder_tags:
        folder_tags = '<span class="settings-hint">No folders configured</span>'

    # Tags taxonomy (editable)
    tax_html = ""
    for group, tags in config.tags_taxonomy.items():
        gid = f"cfg-tax-{_esc(group)}"
        tag_spans = "".join(
            f'<span class="settings-tag-item">{_esc(t)}<i class="tag-remove" onclick="removeTag(this)">&times;</i></span>'
            for t in tags
        )
        tax_html += f"""<div class="settings-row">
<div class="settings-label">{_esc(group)}</div>
<div class="settings-control">
  <div class="settings-tag-list" id="{gid}">{tag_spans}</div>
  <div class="settings-tag-add"><input type="text" id="{gid}-input" placeholder="add tag" onkeydown="if(event.key==='Enter')addTag('{gid}','{gid}-input')"><button type="button" onclick="addTag('{gid}','{gid}-input')">+ Add</button></div>
</div>
</div>"""
    if not tax_html:
        tax_html = """<div class="settings-row">
<div class="settings-label">tags</div>
<div class="settings-control"><span class="settings-hint">No taxonomy configured</span></div>
</div>"""

    # Exempt files (editable)
    exempt_tags = "".join(
        f'<span class="settings-tag-item">{_esc(e)}<i class="tag-remove" onclick="removeTag(this)">&times;</i></span>'
        for e in config.naming.infrastructure_exempt
    )
    if not exempt_tags:
        exempt_tags = ''

    # Forbidden words (editable)
    forbidden_tags = "".join(
        f'<span class="settings-tag-item">{_esc(w)}<i class="tag-remove" onclick="removeTag(this)">&times;</i></span>'
        for w in config.naming.forbidden_words
    )

    # Build templates JSON for client-side template application
    _templates_json = json.dumps({
        name: {k: v for k, v in rules.items()}
        for name, rules in NAMING_TEMPLATES.items()
    })

    # Build compliance standards data for toggles
    # Each standard maps to a preset + specific settings it enables
    COMPLIANCE_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                       '<path d="M9 12l2 2 4-4"/><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2'
                       ' 2 6.477 2 12s4.477 10 10 10z"/></svg>')

    body = f"""<h1>Settings</h1>
<div class="subtitle">Current configuration for <strong>{_esc(project_name)}</strong> — values reflect your project_config in REGISTRY.yaml</div>

<div class="settings-layout">
<div class="settings-forms">

<div class="settings-section">
<div class="settings-section-header">{COMPLIANCE_ICON} Compliance Standards</div>
<div class="settings-hint" style="margin:0 0 12px">Toggle a standard to auto-apply its naming, header/footer, and metadata rules</div>
<div class="settings-compliance-grid">
  <button type="button" class="settings-compliance-btn" id="std-dod" onclick="applyStandard('dod')" title="DoD 5200.01 — Classification markings, distribution statements, FOUO/CUI banners">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">DoD 5200.01</span>
    <span class="settings-compliance-desc">Classification Markings</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-iso9001" onclick="applyStandard('iso9001')" title="ISO 9001:2015 / ISO 10013 — Document control numbering, revision tracking, approval workflows">
    <span class="settings-compliance-icon">{CHECKLIST_ICON}</span>
    <span class="settings-compliance-name">ISO 9001</span>
    <span class="settings-compliance-desc">Quality Management</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-hipaa" onclick="applyStandard('hipaa')" title="HIPAA Privacy Rule (45 CFR 164) — PHI protections, 6-year retention, access controls">
    <span class="settings-compliance-icon">{HEADER_ICON}</span>
    <span class="settings-compliance-name">HIPAA</span>
    <span class="settings-compliance-desc">Healthcare Privacy</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-sec" onclick="applyStandard('sec')" title="SEC 17a-4 / FINRA 4511 — WORM retention, 6-year records, audit trail requirements">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">SEC / FINRA</span>
    <span class="settings-compliance-desc">Financial Recordkeeping</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-scientific" onclick="applyStandard('scientific')" title="NIH/NSF data management — 10-year retention, PI ownership, revision history, ISO 8601 dates">
    <span class="settings-compliance-icon">{NAMING_ICON}</span>
    <span class="settings-compliance-name">Research / Academic</span>
    <span class="settings-compliance-desc">Data Management Plans</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-legal" onclick="applyStandard('legal')" title="Legal DMS conventions — privilege markings, matter codes, Bates-style numbering, 7-year retention">
    <span class="settings-compliance-icon">{FOLDER_ICON}</span>
    <span class="settings-compliance-name">Legal / Law Firm</span>
    <span class="settings-compliance-desc">Matter Management</span>
  </button>
</div>
</div>

<div class="settings-section">
<div class="settings-section-header">{NAMING_ICON} Naming Convention</div>
<div class="settings-grid">
  <div class="settings-row">
    <div class="settings-label">Template</div>
    <div class="settings-control"><select id="cfg-template" onchange="applyTemplate();updatePreview()">{template_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Separator</div>
    <div class="settings-control"><select id="cfg-sep" onchange="updatePreview()">{sep_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Case</div>
    <div class="settings-control"><select id="cfg-case" onchange="updatePreview()">{case_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Date Format</div>
    <div class="settings-control"><select id="cfg-date" onchange="updatePreview()">{date_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Version Format</div>
    <div class="settings-control"><select id="cfg-ver" onchange="updatePreview()">{ver_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Domain Prefix</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {domain_on}" id="cfg-domain" onclick="this.classList.toggle('on');updatePreview()"></button>
      <span class="settings-hint">Prepend category domain to filenames</span>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Forbidden Words</div>
    <div class="settings-control">
      <div class="settings-tag-list" id="cfg-forbidden">{forbidden_tags}</div>
      <div class="settings-tag-add"><input type="text" id="cfg-forbidden-input" placeholder="add word" onkeydown="if(event.key==='Enter')addTag('cfg-forbidden','cfg-forbidden-input')"><button type="button" onclick="addTag('cfg-forbidden','cfg-forbidden-input')">+ Add</button></div>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Exempt Files</div>
    <div class="settings-control">
      <div class="settings-tag-list" id="cfg-exempt">{exempt_tags}</div>
      <div class="settings-tag-add"><input type="text" id="cfg-exempt-input" placeholder="add filename" onkeydown="if(event.key==='Enter')addTag('cfg-exempt','cfg-exempt-input')"><button type="button" onclick="addTag('cfg-exempt','cfg-exempt-input')">+ Add</button></div>
    </div>
  </div>
</div>
</div>

<div class="settings-section">
<div class="settings-section-header">{FOLDER_ICON} Folder Categories</div>
<div class="settings-grid">
  <div class="settings-row">
    <div class="settings-label">Preset</div>
    <div class="settings-control"><select id="cfg-preset">{preset_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Strict Mode</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {strict_on}" id="cfg-strict" onclick="this.classList.toggle('on')"></button>
      <span class="settings-hint">Reject files outside declared categories</span>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Folders</div>
    <div class="settings-control"><div class="settings-tag-list">{folder_tags}</div></div>
  </div>
</div>
</div>

<div class="settings-section">
<div class="settings-section-header">{TAG_ICON} Tags Taxonomy</div>
<div class="settings-grid">
{tax_html}
</div>
</div>

<div class="settings-section">
<div class="settings-section-header">{SHIELD_ICON} Governance</div>
<div class="settings-grid">
  <div class="settings-row">
    <div class="settings-label">Default Author</div>
    <div class="settings-control"><input type="text" id="cfg-author" value="{_esc(config.default_author)}" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Classification</div>
    <div class="settings-control"><input type="text" id="cfg-class" value="{_esc(config.default_classification)}" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Staleness</div>
    <div class="settings-control"><input type="text" id="cfg-stale" value="{config.staleness_threshold_days}" style="width:80px"> <span class="settings-hint">days</span></div>
  </div>
</div>
</div>

<div class="settings-section">
<div class="settings-section-header">{HEADER_ICON} Document Header / Footer</div>
<div class="settings-grid">
  <div class="settings-row">
    <div class="settings-label">Header Enabled</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.header.enabled else ""}" id="cfg-hdr-enabled" onclick="this.classList.toggle('on');updatePreview()"></button>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Organization</div>
    <div class="settings-control"><input type="text" id="cfg-hdr-org" value="{_esc(config.header.organization)}" placeholder="e.g. Acme Corporation" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Logo URL</div>
    <div class="settings-control"><input type="text" id="cfg-hdr-logo" value="{_esc(getattr(config.header, 'logo_url', ''))}" placeholder="e.g. https://example.com/logo.png or ./assets/logo.png" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Classification Banner</div>
    <div class="settings-control"><input type="text" id="cfg-hdr-banner" value="{_esc(config.header.classification_banner)}" placeholder="e.g. UNCLASSIFIED, CUI, CONFIDENTIAL" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Doc ID Prefix</div>
    <div class="settings-control"><input type="text" id="cfg-hdr-prefix" value="{_esc(config.header.document_id_prefix)}" placeholder="e.g. DOC-, POL-, SOP-" style="width:140px" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Show Version</div>
    <div class="settings-control"><button type="button" class="settings-toggle {"on" if config.header.show_version else ""}" id="cfg-hdr-ver" onclick="this.classList.toggle('on');updatePreview()"></button></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Show Date</div>
    <div class="settings-control"><button type="button" class="settings-toggle {"on" if config.header.show_date else ""}" id="cfg-hdr-date" onclick="this.classList.toggle('on');updatePreview()"></button></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Show Status</div>
    <div class="settings-control"><button type="button" class="settings-toggle {"on" if config.header.show_status else ""}" id="cfg-hdr-status" onclick="this.classList.toggle('on');updatePreview()"></button></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Page Numbers</div>
    <div class="settings-control"><button type="button" class="settings-toggle {"on" if config.header.show_page_numbers else ""}" id="cfg-hdr-pages" onclick="this.classList.toggle('on');updatePreview()"></button></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Footer Enabled</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.footer.enabled else ""}" id="cfg-ftr-enabled" onclick="this.classList.toggle('on');updatePreview()"></button>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Distribution</div>
    <div class="settings-control"><input type="text" id="cfg-ftr-dist" value="{_esc(config.footer.distribution_statement)}" placeholder="e.g. Distribution A: Public release" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Retention Notice</div>
    <div class="settings-control"><input type="text" id="cfg-ftr-ret" value="{_esc(config.footer.retention_notice)}" placeholder="e.g. Retain for 7 years per policy" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Copyright</div>
    <div class="settings-control"><input type="text" id="cfg-ftr-copy" value="{_esc(config.footer.copyright_notice)}" placeholder="e.g. &copy; 2026 Acme Corp." oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Custom Footer</div>
    <div class="settings-control"><input type="text" id="cfg-ftr-custom" value="{_esc(config.footer.custom_text)}" placeholder="Any additional footer text" oninput="updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Legal Disclaimer</div>
    <div class="settings-control">
      <select class="settings-disclaimer-select" id="cfg-ftr-disclaimer" onchange="applyDisclaimer();updatePreview()">
        <option value="">— none —</option>
        <option value="general">General Business</option>
        <option value="hipaa">Healthcare / HIPAA</option>
        <option value="financial">Financial Services</option>
        <option value="legal">Legal / Privilege</option>
        <option value="government">Government / CUI</option>
        <option value="academic">Academic / Research</option>
        <option value="technology">Technology / IP</option>
      </select>
      <span class="settings-hint">Auto-fills custom footer with industry-standard disclaimer</span>
    </div>
  </div>
</div>
</div>

<div class="settings-section">
<div class="settings-section-header">{CHECKLIST_ICON} Required Metadata</div>
<div class="settings-grid">
  <div class="settings-row">
    <div class="settings-label">Require Owner</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.metadata.require_owner else ""}" id="cfg-meta-owner" onclick="this.classList.toggle('on');updatePreview()"></button>
      <span class="settings-hint">Responsible owner</span>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Require Approver</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.metadata.require_approver else ""}" id="cfg-meta-approver" onclick="this.classList.toggle('on');updatePreview()"></button>
      <span class="settings-hint">Approval authority</span>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Require Review Date</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.metadata.require_review_date else ""}" id="cfg-meta-review" onclick="this.classList.toggle('on');updatePreview()"></button>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Require Distribution List</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.metadata.require_distribution_list else ""}" id="cfg-meta-distlist" onclick="this.classList.toggle('on');updatePreview()"></button>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Require Revision History</div>
    <div class="settings-control">
      <button type="button" class="settings-toggle {"on" if config.metadata.require_revision_history else ""}" id="cfg-meta-revhist" onclick="this.classList.toggle('on');updatePreview()"></button>
    </div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Retention Period</div>
    <div class="settings-control"><input type="text" id="cfg-meta-retention" value="{config.metadata.retention_period_days}" style="width:80px" oninput="updatePreview()"> <span class="settings-hint">days (0 = none)</span></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Review Cycle</div>
    <div class="settings-control"><input type="text" id="cfg-meta-cycle" value="{config.metadata.review_cycle_days}" style="width:80px" oninput="updatePreview()"> <span class="settings-hint">days (0 = none)</span></div>
  </div>
</div>
</div>

<div class="settings-actions">
  <button type="button" class="settings-btn settings-btn--primary" onclick="generateYaml()">
    {DOWNLOAD_ICON} Generate YAML
  </button>
  <button type="button" class="settings-btn" id="copy-btn" onclick="copyYaml()">
    {COPY_ICON} Copy to Clipboard
  </button>
  <span class="settings-copied" id="copied-msg">Copied!</span>
</div>
<pre class="settings-yaml" id="yaml-output"></pre>

</div><!-- /settings-forms -->

<div class="settings-preview-panel" id="preview-panel">
  <div class="settings-preview-panel-header">Live Preview</div>

  <div class="settings-preview-card">
    <div class="settings-preview-card-label">Filename</div>
    <div class="settings-preview-card-value" id="preview-filename">{_esc(config.naming.human_pattern)}</div>
  </div>

  <div class="settings-preview-card" id="preview-header-card">
    <div class="settings-preview-card-label">Document Header</div>
    <div class="settings-preview-doc" id="preview-header">
      <div class="preview-banner" id="preview-banner-top"></div>
      <div class="preview-hdr-row">
        <span class="preview-hdr-org" id="preview-org"></span>
        <span class="preview-hdr-logo" id="preview-logo" style="display:none;font-size:0.72rem;color:var(--muted);margin-left:0.5rem"></span>
        <span class="preview-hdr-meta" id="preview-hdr-meta"></span>
      </div>
      <div class="preview-hdr-title" id="preview-title"></div>
    </div>
  </div>

  <div class="settings-preview-card" id="preview-footer-card">
    <div class="settings-preview-card-label">Document Footer</div>
    <div class="settings-preview-doc" id="preview-footer">
      <div class="preview-ftr-row" id="preview-ftr-text"></div>
      <div class="preview-banner" id="preview-banner-bottom"></div>
    </div>
  </div>

  <div class="settings-preview-card">
    <div class="settings-preview-card-label">Metadata Requirements</div>
    <div class="settings-preview-meta" id="preview-meta"></div>
  </div>
</div>
</div><!-- /settings-layout -->

<script>
var TEMPLATES = {_templates_json};

function applyTemplate() {{
  var name = document.getElementById('cfg-template').value;
  if (!name || !TEMPLATES[name]) return;
  var t = TEMPLATES[name];
  if (t.separator) setSelect('cfg-sep', t.separator);
  if (t.case) setSelect('cfg-case', t['case']);
  if (t.date_format) setSelect('cfg-date', t.date_format);
  if (t.version_format) setSelect('cfg-ver', t.version_format);
  var domBtn = document.getElementById('cfg-domain');
  if (t.domain_prefix) domBtn.classList.add('on'); else domBtn.classList.remove('on');
  updatePreview();
}}

function setSelect(id, val) {{
  var el = document.getElementById(id);
  for (var i = 0; i < el.options.length; i++) {{
    if (el.options[i].value === val) {{ el.selectedIndex = i; break; }}
  }}
}}

function setToggle(id, on) {{
  var el = document.getElementById(id);
  if (on) el.classList.add('on'); else el.classList.remove('on');
}}

function escHtml(s) {{
  var d = document.createElement('div');
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}}

function renderLines(el, lines) {{
  el.innerHTML = lines.map(function(l) {{ return '<div>' + escHtml(l) + '</div>'; }}).join('');
}}

function removeTag(el) {{
  el.parentElement.remove();
}}

function addTag(listId, inputId) {{
  var input = document.getElementById(inputId);
  var val = input.value.trim();
  if (!val) return;
  var list = document.getElementById(listId);
  var span = document.createElement('span');
  span.className = 'settings-tag-item';
  span.innerHTML = escHtml(val) + '<i class="tag-remove" onclick="removeTag(this)">&times;</i>';
  list.appendChild(span);
  input.value = '';
}}

function getTagValues(listId) {{
  var tags = [];
  var items = document.getElementById(listId).querySelectorAll('.settings-tag-item');
  items.forEach(function(el) {{
    // Text content minus the × remove button
    var t = el.firstChild.textContent.trim();
    if (t) tags.push(t);
  }});
  return tags;
}}

var DISCLAIMERS = {{
  general: 'This document is proprietary and confidential. Unauthorized distribution, copying, or disclosure is strictly prohibited.',
  hipaa: 'This document may contain Protected Health Information (PHI) subject to HIPAA Privacy Rule (45 CFR Part 164). Unauthorized disclosure may result in civil and criminal penalties.',
  financial: 'This document contains confidential financial information subject to SEC Rule 17a-4 and FINRA Rule 4511. Not for public distribution. Unauthorized trading on material non-public information is a federal offense.',
  legal: 'PRIVILEGED AND CONFIDENTIAL — This document is protected by attorney-client privilege and/or work product doctrine. If you are not the intended recipient, notify the sender immediately and destroy all copies.',
  government: 'CONTROLLED UNCLASSIFIED INFORMATION (CUI) — Handling, storage, and dissemination must comply with 32 CFR Part 2002. Unauthorized disclosure may result in administrative or legal action.',
  academic: 'This document is shared for research and educational purposes. Citation required for any referenced data or findings. Subject to institutional review board (IRB) protocols where applicable.',
  technology: 'CONFIDENTIAL — Contains trade secrets and proprietary intellectual property. Protected under applicable trade secret laws and non-disclosure agreements. Do not reverse engineer, copy, or distribute.'
}};

function applyDisclaimer() {{
  var sel = document.getElementById('cfg-ftr-disclaimer').value;
  if (sel && DISCLAIMERS[sel]) {{
    document.getElementById('cfg-ftr-custom').value = DISCLAIMERS[sel];
    updatePreview();
  }}
}}

var STANDARDS = {{
  dod: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: false,
    hdr: true, org: '', logo: '', banner: 'UNCLASSIFIED', prefix: 'DOC-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Distribution A: Approved for public release; distribution unlimited.',
    ret: '', copy: '', custom: '',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2555, cycle: 365, cls: 'UNCLASSIFIED'
  }},
  iso9001: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: '', prefix: 'QMS-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Controlled Document — Do Not Copy Without Authorization',
    ret: '', copy: '', custom: 'ISO 9001:2015 Controlled Document',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: ''
  }},
  hipaa: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: 'POL-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 Contains Protected Health Information',
    ret: 'Retain per facility records retention schedule', copy: '',
    custom: 'HIPAA Privacy Rule (45 CFR Part 164) applies to all PHI',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  sec: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 Not for Public Distribution',
    ret: '', copy: '', custom: 'SEC Rule 17a-4 / FINRA Rule 4511 retention applies',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  scientific: {{
    sep: '_', 'case': 'mixed', date: 'YYYY-MM-DD', ver: 'vX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: '', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: false, dist: '', ret: '', copy: '', custom: '',
    metaOwner: true, metaApprover: false, metaReview: true, metaDist: false, metaRev: true,
    retention: 3650, cycle: 180, cls: ''
  }},
  legal: {{
    sep: '-', 'case': 'mixed', date: 'YYYY-MM-DD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: '', ret: '', copy: '',
    custom: 'Privileged and Confidential \\u2014 Do Not Distribute Without Authorization',
    metaOwner: true, metaApprover: true, metaReview: false, metaDist: true, metaRev: true,
    retention: 2555, cycle: 0, cls: 'CONFIDENTIAL'
  }}
}};

// Snapshot of project defaults — captured on first load
var PROJECT_DEFAULTS = null;

function captureDefaults() {{
  PROJECT_DEFAULTS = {{
    sep: document.getElementById('cfg-sep').value,
    'case': document.getElementById('cfg-case').value,
    date: document.getElementById('cfg-date').value,
    ver: document.getElementById('cfg-ver').value,
    domain: document.getElementById('cfg-domain').classList.contains('on'),
    hdr: document.getElementById('cfg-hdr-enabled').classList.contains('on'),
    org: document.getElementById('cfg-hdr-org').value,
    logo: document.getElementById('cfg-hdr-logo').value,
    banner: document.getElementById('cfg-hdr-banner').value,
    prefix: document.getElementById('cfg-hdr-prefix').value,
    hdrVer: document.getElementById('cfg-hdr-ver').classList.contains('on'),
    hdrDate: document.getElementById('cfg-hdr-date').classList.contains('on'),
    hdrStatus: document.getElementById('cfg-hdr-status').classList.contains('on'),
    hdrPages: document.getElementById('cfg-hdr-pages').classList.contains('on'),
    ftr: document.getElementById('cfg-ftr-enabled').classList.contains('on'),
    dist: document.getElementById('cfg-ftr-dist').value,
    ret: document.getElementById('cfg-ftr-ret').value,
    copy: document.getElementById('cfg-ftr-copy').value,
    custom: document.getElementById('cfg-ftr-custom').value,
    metaOwner: document.getElementById('cfg-meta-owner').classList.contains('on'),
    metaApprover: document.getElementById('cfg-meta-approver').classList.contains('on'),
    metaReview: document.getElementById('cfg-meta-review').classList.contains('on'),
    metaDist: document.getElementById('cfg-meta-distlist').classList.contains('on'),
    metaRev: document.getElementById('cfg-meta-revhist').classList.contains('on'),
    retention: document.getElementById('cfg-meta-retention').value,
    cycle: document.getElementById('cfg-meta-cycle').value,
    cls: document.getElementById('cfg-class').value
  }};
}}

function applyFields(s) {{
  setSelect('cfg-sep', s.sep);
  setSelect('cfg-case', s['case']);
  setSelect('cfg-date', s.date);
  setSelect('cfg-ver', s.ver);
  setToggle('cfg-domain', s.domain);
  setToggle('cfg-hdr-enabled', s.hdr);
  document.getElementById('cfg-hdr-org').value = s.org;
  document.getElementById('cfg-hdr-logo').value = s.logo || '';
  document.getElementById('cfg-hdr-banner').value = s.banner;
  document.getElementById('cfg-hdr-prefix').value = s.prefix;
  setToggle('cfg-hdr-ver', s.hdrVer);
  setToggle('cfg-hdr-date', s.hdrDate);
  setToggle('cfg-hdr-status', s.hdrStatus);
  setToggle('cfg-hdr-pages', s.hdrPages);
  setToggle('cfg-ftr-enabled', s.ftr);
  document.getElementById('cfg-ftr-dist').value = s.dist;
  document.getElementById('cfg-ftr-ret').value = s.ret;
  document.getElementById('cfg-ftr-copy').value = s.copy;
  document.getElementById('cfg-ftr-custom').value = s.custom;
  setToggle('cfg-meta-owner', s.metaOwner);
  setToggle('cfg-meta-approver', s.metaApprover);
  setToggle('cfg-meta-review', s.metaReview);
  setToggle('cfg-meta-distlist', s.metaDist);
  setToggle('cfg-meta-revhist', s.metaRev);
  document.getElementById('cfg-meta-retention').value = s.retention;
  document.getElementById('cfg-meta-cycle').value = s.cycle;
  document.getElementById('cfg-class').value = s.cls;
  updatePreview();
}}

function applyStandard(name) {{
  var s = STANDARDS[name];
  if (!s) return;
  var btn = document.getElementById('std-' + name);
  var wasActive = btn.classList.contains('active');

  // Clear all buttons
  var btns = document.querySelectorAll('.settings-compliance-btn');
  btns.forEach(function(b) {{ b.classList.remove('active'); }});

  if (wasActive) {{
    // Deselect — restore project defaults
    if (PROJECT_DEFAULTS) applyFields(PROJECT_DEFAULTS);
  }} else {{
    // Select — apply standard
    btn.classList.add('active');
    applyFields(s);
  }}
}}

function updatePreview() {{
  var sep = document.getElementById('cfg-sep').value;
  var dateF = document.getElementById('cfg-date').value;
  var verF = document.getElementById('cfg-ver').value;
  var domain = document.getElementById('cfg-domain').classList.contains('on');
  var caseFmt = document.getElementById('cfg-case').value;

  // Filename preview
  var parts = [];
  if (domain) parts.push('domain');
  if (caseFmt === 'uppercase') parts.push('DESCRIPTIVE-NAME');
  else if (caseFmt === 'mixed') parts.push('Descriptive-Name');
  else parts.push('descriptive-name');
  if (dateF !== 'off') parts.push(dateF);
  parts.push(verF);
  var pattern = parts.join(sep) + '.ext';
  document.getElementById('preview-filename').textContent = pattern;

  // Header preview — always visible, dimmed when disabled
  var hdrOn = document.getElementById('cfg-hdr-enabled').classList.contains('on');
  var hdrCard = document.getElementById('preview-header-card');
  hdrCard.style.opacity = hdrOn ? '1' : '0.4';
  var hdrLabel = hdrCard.querySelector('.settings-preview-card-label');
  hdrLabel.textContent = hdrOn ? 'Document Header' : 'Document Header (disabled)';
  {{
    var banner = document.getElementById('cfg-hdr-banner').value;
    var org = document.getElementById('cfg-hdr-org').value || 'Organization';
    var prefix = document.getElementById('cfg-hdr-prefix').value || '';
    var topBanner = document.getElementById('preview-banner-top');
    topBanner.textContent = banner || '(no banner)';
    topBanner.style.display = '';
    if (banner) {{
      topBanner.className = 'preview-banner' + (banner.indexOf('SECRET') >= 0 ? ' banner-red' : banner.indexOf('CONFIDENTIAL') >= 0 ? ' banner-amber' : banner.indexOf('CUI') >= 0 ? ' banner-purple' : ' banner-green');
    }} else {{
      topBanner.className = 'preview-banner';
      topBanner.style.color = '#aaa';
    }}
    document.getElementById('preview-org').textContent = org;
    var logoUrl = document.getElementById('cfg-hdr-logo').value;
    var logoEl = document.getElementById('preview-logo');
    if (logoUrl) {{
      logoEl.textContent = '\\ud83d\\uddbc ' + logoUrl.split('/').pop();
      logoEl.style.display = '';
    }} else {{
      logoEl.style.display = 'none';
    }}
    var metaParts = [];
    if (prefix) metaParts.push(prefix + '0001');
    if (document.getElementById('cfg-hdr-ver').classList.contains('on')) metaParts.push(verF.replace('X','1').replace('Y','0'));
    if (document.getElementById('cfg-hdr-date').classList.contains('on')) metaParts.push(new Date().toISOString().slice(0,10));
    if (document.getElementById('cfg-hdr-status').classList.contains('on')) metaParts.push('Active');
    document.getElementById('preview-hdr-meta').textContent = metaParts.join(' \\u2022 ');
    var titleParts = [];
    if (domain) titleParts.push('domain');
    titleParts.push('descriptive-name');
    document.getElementById('preview-title').textContent = titleParts.join(sep);
  }}

  // Footer preview — always visible, dimmed when disabled
  var ftrOn = document.getElementById('cfg-ftr-enabled').classList.contains('on');
  var ftrCard = document.getElementById('preview-footer-card');
  ftrCard.style.opacity = ftrOn ? '1' : '0.4';
  var ftrLabel = ftrCard.querySelector('.settings-preview-card-label');
  ftrLabel.textContent = ftrOn ? 'Document Footer' : 'Document Footer (disabled)';
  {{
    var ftrParts = [];
    var dist = document.getElementById('cfg-ftr-dist').value;
    var ret = document.getElementById('cfg-ftr-ret').value;
    var cpy = document.getElementById('cfg-ftr-copy').value;
    var cust = document.getElementById('cfg-ftr-custom').value;
    if (dist) ftrParts.push(dist);
    if (ret) ftrParts.push(ret);
    if (cpy) ftrParts.push(cpy);
    if (cust) ftrParts.push(cust);
    var pages = document.getElementById('cfg-hdr-pages').classList.contains('on');
    if (pages) ftrParts.push('Page 1 of 3');
    if (ftrParts.length === 0) ftrParts.push('(no footer content configured)');
    renderLines(document.getElementById('preview-ftr-text'), ftrParts);
    var banner2 = document.getElementById('cfg-hdr-banner').value;
    var botBanner = document.getElementById('preview-banner-bottom');
    botBanner.textContent = banner2 || '(no banner)';
    botBanner.style.display = '';
    if (banner2) {{
      botBanner.className = 'preview-banner' + (banner2.indexOf('SECRET') >= 0 ? ' banner-red' : banner2.indexOf('CONFIDENTIAL') >= 0 ? ' banner-amber' : banner2.indexOf('CUI') >= 0 ? ' banner-purple' : ' banner-green');
    }} else {{
      botBanner.className = 'preview-banner';
      botBanner.style.color = '#aaa';
    }}
  }}

  // Metadata summary
  var metaLines = [];
  if (document.getElementById('cfg-meta-owner').classList.contains('on')) metaLines.push('\\u2713 Owner required');
  if (document.getElementById('cfg-meta-approver').classList.contains('on')) metaLines.push('\\u2713 Approver required');
  if (document.getElementById('cfg-meta-review').classList.contains('on')) metaLines.push('\\u2713 Review date required');
  if (document.getElementById('cfg-meta-distlist').classList.contains('on')) metaLines.push('\\u2713 Distribution list required');
  if (document.getElementById('cfg-meta-revhist').classList.contains('on')) metaLines.push('\\u2713 Revision history required');
  var retDays = parseInt(document.getElementById('cfg-meta-retention').value) || 0;
  if (retDays > 0) metaLines.push('Retention: ' + (retDays >= 365 ? (retDays / 365).toFixed(1) + ' years' : retDays + ' days'));
  var cycDays = parseInt(document.getElementById('cfg-meta-cycle').value) || 0;
  if (cycDays > 0) metaLines.push('Review cycle: ' + (cycDays >= 365 ? (cycDays / 365).toFixed(1) + ' years' : cycDays + ' days'));
  if (metaLines.length === 0) metaLines.push('No metadata requirements');
  renderLines(document.getElementById('preview-meta'), metaLines);
}}

function generateYaml() {{
  var sep = document.getElementById('cfg-sep').value;
  var caseFmt = document.getElementById('cfg-case').value;
  var dateF = document.getElementById('cfg-date').value;
  var verF = document.getElementById('cfg-ver').value;
  var domain = document.getElementById('cfg-domain').classList.contains('on');
  var strict = document.getElementById('cfg-strict').classList.contains('on');
  var author = document.getElementById('cfg-author').value;
  var cls = document.getElementById('cfg-class').value;
  var stale = document.getElementById('cfg-stale').value;
  var hdrOn = document.getElementById('cfg-hdr-enabled').classList.contains('on');
  var hdrOrg = document.getElementById('cfg-hdr-org').value;
  var hdrLogo = document.getElementById('cfg-hdr-logo').value;
  var hdrBanner = document.getElementById('cfg-hdr-banner').value;
  var hdrPrefix = document.getElementById('cfg-hdr-prefix').value;
  var hdrVer = document.getElementById('cfg-hdr-ver').classList.contains('on');
  var hdrDate = document.getElementById('cfg-hdr-date').classList.contains('on');
  var hdrStatus = document.getElementById('cfg-hdr-status').classList.contains('on');
  var hdrPages = document.getElementById('cfg-hdr-pages').classList.contains('on');
  var ftrOn = document.getElementById('cfg-ftr-enabled').classList.contains('on');
  var ftrDist = document.getElementById('cfg-ftr-dist').value;
  var ftrRet = document.getElementById('cfg-ftr-ret').value;
  var ftrCopy = document.getElementById('cfg-ftr-copy').value;
  var ftrCustom = document.getElementById('cfg-ftr-custom').value;
  var metaOwner = document.getElementById('cfg-meta-owner').classList.contains('on');
  var metaApprover = document.getElementById('cfg-meta-approver').classList.contains('on');
  var metaReview = document.getElementById('cfg-meta-review').classList.contains('on');
  var metaDistList = document.getElementById('cfg-meta-distlist').classList.contains('on');
  var metaRevHist = document.getElementById('cfg-meta-revhist').classList.contains('on');
  var metaRetention = document.getElementById('cfg-meta-retention').value;
  var metaCycle = document.getElementById('cfg-meta-cycle').value;

  // YAML-safe quoting: wrap in single quotes if value contains : # [ ] {{ }} , & * ? | - < > = ! % @ or leading/trailing spaces
  function yq(v) {{
    var s = String(v);
    if (/[:\\#\\[\\]\\{{\\}},&*?|\\-<>=!%@'"]/.test(s) || s !== s.trim() || s === '') {{
      return "'" + s.replace(/'/g, "''") + "'";
    }}
    return s;
  }}

  var yaml = 'project_config:\\n';
  yaml += '  naming_rules:\\n';
  yaml += '    separator: ' + yq(sep) + '\\n';
  yaml += '    case: ' + caseFmt + '\\n';
  yaml += '    date_format: ' + dateF + '\\n';
  yaml += '    version_format: ' + verF + '\\n';
  yaml += '    domain_prefix: ' + domain + '\\n';
  yaml += '  categories:\\n';
  yaml += '    strict_mode: ' + strict + '\\n';
  if (author) yaml += '  default_author: ' + yq(author) + '\\n';
  if (cls) yaml += '  default_classification: ' + yq(cls) + '\\n';
  if (stale) yaml += '  staleness_threshold_days: ' + stale + '\\n';
  yaml += '  document_header:\\n';
  yaml += '    enabled: ' + hdrOn + '\\n';
  if (hdrOrg) yaml += '    organization: ' + yq(hdrOrg) + '\\n';
  if (hdrLogo) yaml += '    logo_url: ' + yq(hdrLogo) + '\\n';
  if (hdrBanner) yaml += '    classification_banner: ' + yq(hdrBanner) + '\\n';
  if (hdrPrefix) yaml += '    document_id_prefix: ' + yq(hdrPrefix) + '\\n';
  yaml += '    show_version: ' + hdrVer + '\\n';
  yaml += '    show_date: ' + hdrDate + '\\n';
  yaml += '    show_status: ' + hdrStatus + '\\n';
  yaml += '    show_page_numbers: ' + hdrPages + '\\n';
  yaml += '  document_footer:\\n';
  yaml += '    enabled: ' + ftrOn + '\\n';
  if (hdrBanner) yaml += '    classification_banner: ' + yq(hdrBanner) + '\\n';
  if (ftrDist) yaml += '    distribution_statement: ' + yq(ftrDist) + '\\n';
  if (ftrRet) yaml += '    retention_notice: ' + yq(ftrRet) + '\\n';
  if (ftrCopy) yaml += '    copyright_notice: ' + yq(ftrCopy) + '\\n';
  if (ftrCustom) yaml += '    custom_text: ' + yq(ftrCustom) + '\\n';
  yaml += '  document_metadata:\\n';
  yaml += '    require_owner: ' + metaOwner + '\\n';
  yaml += '    require_approver: ' + metaApprover + '\\n';
  yaml += '    require_review_date: ' + metaReview + '\\n';
  yaml += '    require_distribution_list: ' + metaDistList + '\\n';
  yaml += '    require_revision_history: ' + metaRevHist + '\\n';
  if (metaRetention !== '0') yaml += '    retention_period_days: ' + metaRetention + '\\n';
  if (metaCycle !== '0') yaml += '    review_cycle_days: ' + metaCycle + '\\n';

  // Forbidden words
  var forbidden = getTagValues('cfg-forbidden');
  if (forbidden.length) {{
    yaml += '  forbidden_words:\\n';
    forbidden.forEach(function(w) {{ yaml += '    - ' + yq(w) + '\\n'; }});
  }}

  // Exempt files
  var exempt = getTagValues('cfg-exempt');
  if (exempt.length) {{
    yaml += '  exempt_files:\\n';
    exempt.forEach(function(f) {{ yaml += '    - ' + yq(f) + '\\n'; }});
  }}

  // Tags taxonomy
  var taxGroups = document.querySelectorAll('[id^="cfg-tax-"]');
  var hasTax = false;
  taxGroups.forEach(function(g) {{
    var vals = getTagValues(g.id);
    if (vals.length) {{
      if (!hasTax) {{ yaml += '  tags_taxonomy:\\n'; hasTax = true; }}
      var gName = g.id.replace('cfg-tax-', '');
      yaml += '    ' + yq(gName) + ':\\n';
      vals.forEach(function(t) {{ yaml += '      - ' + yq(t) + '\\n'; }});
    }}
  }});

  var el = document.getElementById('yaml-output');
  el.textContent = yaml;
  el.classList.add('visible');
}}

function copyYaml() {{
  var el = document.getElementById('yaml-output');
  if (!el.textContent) {{ generateYaml(); }}
  navigator.clipboard.writeText(el.textContent).then(function() {{
    var msg = document.getElementById('copied-msg');
    msg.classList.add('show');
    setTimeout(function(){{ msg.classList.remove('show'); }}, 1500);
  }});
}}

// Initialize: snapshot defaults then render preview
document.addEventListener('DOMContentLoaded', function() {{ captureDefaults(); updatePreview(); }});
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")
    return _page(
        "Settings",
        body,
        "settings",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=True,
        sidebar=sidebar,
    )


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

    # Tree page
    (out / "tree.html").write_text(_build_tree_page(manifest), encoding="utf-8")

    # Graph page
    (out / "graph.html").write_text(_build_graph_page(manifest), encoding="utf-8")

    # Settings page
    (out / "settings.html").write_text(_build_settings_page(manifest), encoding="utf-8")

    return out.resolve()
