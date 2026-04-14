"""Static site generator — multi-page HTML site from a manifest.

Generates a ``_site/`` directory tree with:

- ``index.html`` — document table, KPI summary, sidebar tree navigation
- ``docs/<filename>.html`` — per-document detail page
- ``graph.html`` — standalone cross-reference graph (cytoscape.js)
- ``templates.html`` — template catalog with filterable card grid
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

# Module-level search index JSON string — set by generate_site() before page building.
_SEARCH_INDEX_JSON: str = "[]"


def _esc(text: Any) -> str:
    """HTML-escape a value."""
    return html_mod.escape(str(text)) if text else ""


def _json_safe(data: Any, **kwargs: Any) -> str:
    """Serialize *data* to JSON safe for embedding in HTML <script> tags.

    Standard ``json.dumps`` can produce ``</script>`` inside string values,
    which the browser interprets as the end of the script block — allowing
    an attacker to inject arbitrary HTML/JS via crafted filenames, titles,
    or descriptions.  This helper escapes ``</`` → ``<\\/`` after
    serialization so the JSON remains valid JS while the closing-tag
    sequence never appears in the HTML source.
    """
    return json.dumps(data, **kwargs).replace("</", r"<\/")


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


_SAFE_URL_SCHEMES = frozenset({"http", "https", "mailto", ""})


def _safe_url(url: str) -> str:
    """Sanitize a URL — block javascript: and data: schemes."""
    stripped = url.strip().lower()
    # Allow relative URLs (start with /, #, or no scheme)
    if stripped.startswith(("/", "#")):
        return url
    # Check scheme
    if ":" in stripped:
        scheme = stripped.split(":", 1)[0]
        if scheme not in _SAFE_URL_SCHEMES:
            return ""
    return url


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
            # Images before links — sanitize URLs
            s = re.sub(
                r"!\[([^\]]*)\]\(([^)]+)\)",
                lambda m: f'<img src="{_safe_url(m.group(2))}" alt="{m.group(1)}" style="max-width:100%">',
                s,
            )
            # Links — sanitize URLs
            s = re.sub(
                r"\[([^\]]+)\]\(([^)]+)\)",
                lambda m: f'<a href="{_safe_url(m.group(2))}">{m.group(1)}</a>',
                s,
            )
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
    # Prevent path traversal — resolved path must stay within repo_root
    try:
        file_path.resolve().relative_to(Path(repo_root).resolve())
    except ValueError:
        return '<p class="content-missing">Path outside repository.</p>'
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
        # Use friendly labels for display
        label = parent if parent != "." else "/ (root)"
        groups[label].append(doc)
    return dict(sorted(groups.items()))


def _build_nested_tree(documents: list[dict]) -> dict:
    """Build a nested folder tree structure for the TREE sidebar mode."""
    root: dict = {"dirs": {}, "docs": []}
    for doc in documents:
        path = doc.get("path", doc.get("filename", ""))
        parts = PurePosixPath(path).parts if "/" in path else []
        # Navigate to the correct nested folder
        node = root
        for part in parts[:-1]:  # all parts except the filename
            if part not in node["dirs"]:
                node["dirs"][part] = {"dirs": {}, "docs": []}
            node = node["dirs"][part]
        node["docs"].append({
            "filename": doc.get("filename", ""),
            "title": doc.get("title", ""),
            "status": doc.get("status", ""),
        })
    # Sort docs in each node
    def _sort_tree(node: dict) -> dict:
        node["docs"] = sorted(node["docs"], key=lambda d: d.get("filename", ""))
        node["dirs"] = {k: _sort_tree(v) for k, v in sorted(node["dirs"].items())}
        return node
    return _sort_tree(root)


def _build_tree_json(documents: list[dict]) -> str:
    """Pre-compute all grouping structures as JSON for client-side switching."""
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
    return _json_safe(tree_data, indent=2, sort_keys=True)


def _build_nested_tree_json(documents: list[dict]) -> str:
    """Serialize the nested tree structure for the TREE sidebar mode."""
    return _json_safe(_build_nested_tree(documents), indent=2, sort_keys=True)


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
  --display: "Playfair Display", "Georgia", "Palatino Linotype", "Book Antiqua", Palatino, serif;
  --gear-color: #b07d2e;
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
  font-size: 20px;
  font-weight: 800;
  font-family: var(--display);
  color: var(--text-primary);
  letter-spacing: -0.01em;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-logo {
  width: 26px;
  height: 26px;
  color: var(--accent);
  flex-shrink: 0;
}

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
  padding: 8px;
  border-radius: var(--radius);
  color: var(--gear-color);
  transition: all var(--transition);
  position: relative;
  margin-left: 8px;
}
.settings-gear:hover { color: #956a1f; background: #faf3e0; }
.settings-gear.active { color: #7d5a18; background: #f5ebd0; }
.settings-gear svg { width: 22px; height: 22px; }
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
.footer-seal {
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-muted);
  opacity: 0.7;
}

/* ── Global Search ─────────────────────────────────────────────────────── */
.global-search {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: auto;
}
.global-search-icon {
  position: absolute;
  left: 10px;
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  pointer-events: none;
}
.global-search input {
  font-family: var(--mono);
  font-size: 12px;
  padding: 6px 10px 6px 30px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text-primary);
  width: 240px;
  transition: border-color 0.15s, width 0.2s, box-shadow 0.15s;
}
.global-search input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(37,99,235,0.12);
  width: 320px;
}
.global-search input::placeholder { color: var(--text-muted); opacity: 0.7; }
.global-search-results {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  max-height: 400px;
  overflow-y: auto;
  z-index: 200;
  min-width: 320px;
}
.global-search-results.open { display: block; }
.gsr-section {
  padding: 6px 12px 2px;
  font-size: 10px;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
}
.gsr-section:first-child { border-top: none; }
.gsr-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.1s;
}
.gsr-item:hover, .gsr-item.gsr-active { background: rgba(37,99,235,0.06); }
.gsr-item-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: var(--text-muted);
}
.gsr-item-title { font-weight: 500; }
.gsr-item-meta {
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-muted);
  margin-left: auto;
  white-space: nowrap;
}
.gsr-empty {
  padding: 16px 12px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}
.gsr-kbd {
  display: inline-block;
  font-family: var(--mono);
  font-size: 10px;
  padding: 1px 5px;
  border: 1px solid var(--border);
  border-radius: 3px;
  background: var(--bg);
  color: var(--text-muted);
  margin-left: 8px;
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
  gap: 0;
  padding: 0 16px;
  margin-bottom: 14px;
}
.group-btn {
  flex: 1;
  padding: 6px 0;
  border: 1.5px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  cursor: pointer;
  transition: all var(--transition);
  text-align: center;
  font-weight: 500;
}
.group-btn:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.group-btn:last-child { border-radius: 0 var(--radius) var(--radius) 0; }
.group-btn:not(:first-child) { border-left: none; }
.group-btn:hover { color: var(--text-primary); background: var(--surface-alt); }
.group-btn.active {
  background: var(--accent);
  color: var(--accent-text);
  border-color: var(--accent);
  font-weight: 700;
}
.group-btn.active + .group-btn { border-left-color: var(--accent); }

/* Tree */
.tree-container { padding: 0 8px; }
.tree-group { margin-bottom: 2px; }
.tree-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
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
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-transform: capitalize;
}
.tree-group-count {
  font-size: 10px;
  font-family: var(--mono);
  color: var(--accent);
  background: var(--accent-light);
  padding: 2px 7px;
  border-radius: 10px;
  min-width: 22px;
  text-align: center;
  font-weight: 600;
}
.tree-items { padding-left: 14px; border-left: 1.5px solid var(--border); margin-left: 14px; }
.tree-group.collapsed .tree-items { display: none; }
.tree-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--radius);
  font-size: 12.5px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all var(--transition);
  text-decoration: none;
  line-height: 1.4;
}
.tree-item:hover {
  background: var(--accent-light);
  color: var(--accent);
  text-decoration: none;
}
.tree-item.tree-item--current {
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 600;
  border-left: 2.5px solid var(--accent);
  padding-left: 8px;
}
.tree-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.tree-dot--active { background: var(--status-active); }
.tree-dot--draft { background: var(--status-draft); }
.tree-dot--superseded { background: var(--status-superseded); }
.tree-folder-icon { font-size: 13px; flex-shrink: 0; }
.tree-nested .tree-items { margin-left: 10px; }

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
.tree-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.tree-ctrl-btn {
  font-size: 12px;
  font-family: var(--sans);
  padding: 5px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}
.tree-ctrl-btn:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-light); }
.tree-ctrl-btn--active { color: var(--accent-text); background: var(--accent); border-color: var(--accent); }
.tree-ctrl-btn--active:hover { background: var(--accent-hover); }
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
.settings-view-toggle {
  display: flex;
  align-items: center;
  gap: 0;
  margin: 0 0 20px;
  padding: 0;
}
.view-toggle-btn {
  font-family: var(--mono);
  font-size: 12px;
  padding: 6px 18px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.view-toggle-btn:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.view-toggle-btn:nth-child(2) { border-radius: 0 var(--radius) var(--radius) 0; border-left: none; }
.view-toggle-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.view-toggle-btn:hover:not(.active) { background: var(--surface-alt); }
.settings-topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.settings-search { position: relative; display: flex; align-items: center; }
.settings-search-icon { width: 16px; height: 16px; position: absolute; left: 10px; color: var(--text-muted); pointer-events: none; }
.settings-search input {
  font-family: var(--mono); font-size: 12px; padding: 7px 28px 7px 32px;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface);
  color: var(--text-primary); width: 220px; transition: border-color 0.15s;
}
.settings-search input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(37,99,235,0.12); }
.settings-search-clear {
  position: absolute; right: 8px; cursor: pointer; font-size: 16px; color: var(--text-muted);
  line-height: 1; padding: 2px;
}
.settings-search-clear:hover { color: var(--text-primary); }
.settings-row.search-highlight { background: rgba(37,99,235,0.08); border-radius: var(--radius); }
.settings-compliance-btn.search-highlight { outline: 2px solid var(--accent); outline-offset: 2px; box-shadow: 0 0 0 4px rgba(37,99,235,0.15); }
.settings-section.search-no-match { opacity: 0.3; }
/* Wizard */
.wizard-container { max-width: 680px; margin: 0 auto; }
.wizard-progress { height: 4px; background: var(--border); border-radius: 2px; margin-bottom: 32px; overflow: hidden; }
.wizard-progress-bar { height: 100%; background: var(--accent); transition: width 0.3s ease; border-radius: 2px; }
.wizard-step { display: none; }
.wizard-step.active { display: block; animation: wizFadeIn 0.25s ease; }
@keyframes wizFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.wizard-step h2 { font-size: 18px; font-weight: 700; margin: 0 0 6px; color: var(--text-primary); }
.wizard-step-number { font-size: 11px; font-family: var(--mono); color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.wizard-desc { font-size: 13px; color: var(--text-secondary); margin: 0 0 20px; }
.wizard-options { display: flex; gap: 12px; flex-wrap: wrap; }
.wizard-options--grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
.wizard-option {
  flex: 1; min-width: 160px; padding: 16px; border: 2px solid var(--border);
  border-radius: var(--radius-lg); background: var(--surface); cursor: pointer;
  text-align: left; transition: all 0.15s; font-family: inherit;
}
.wizard-option:hover { border-color: var(--accent); background: var(--surface-alt); }
.wizard-option.selected { border-color: var(--accent); background: rgba(37,99,235,0.06); box-shadow: 0 0 0 1px var(--accent); }
.wizard-option--compact { padding: 10px 14px; min-width: 120px; }
.wizard-option-icon { margin-bottom: 8px; }
.wizard-option-icon svg { width: 28px; height: 28px; color: var(--accent); }
.wizard-option-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.wizard-option-desc { font-size: 11px; color: var(--text-muted); line-height: 1.4; }
.wizard-nav { display: flex; justify-content: space-between; align-items: center; margin-top: 28px; padding-top: 16px; border-top: 1px solid var(--border); }
.wizard-btn {
  font-family: var(--mono); font-size: 12px; padding: 8px 20px; border: 1px solid var(--border);
  border-radius: var(--radius); background: var(--surface); color: var(--text-secondary); cursor: pointer;
}
.wizard-btn:hover { background: var(--surface-alt); }
.wizard-btn--next { background: var(--accent); color: #fff; border-color: var(--accent); }
.wizard-btn--next:hover { background: #1d4ed8; }
.wizard-btn--next:disabled { opacity: 0.4; cursor: not-allowed; }
.wizard-btn--finish { background: #059669; border-color: #059669; color: #fff; }
.wizard-btn--finish:hover { background: #047857; }
.wizard-fields { display: flex; flex-direction: column; gap: 16px; }
.wizard-field label { display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; }
.wizard-field input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; font-family: var(--mono); background: var(--surface); color: var(--text-primary); }
.wizard-field input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(37,99,235,0.12); }
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

/* ── Template Catalog ───────────────────────────────────────────────────── */
.tmpl-controls { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; align-items: center; }
.tmpl-controls select {
  padding: 5px 10px; border: 1px solid var(--border); border-radius: var(--radius);
  font-size: 12px; font-family: var(--mono); background: var(--surface);
  color: var(--text-primary); cursor: pointer;
}
.tmpl-search { position: relative; display: flex; align-items: center; }
.tmpl-search-icon { width: 14px; height: 14px; position: absolute; left: 8px; color: var(--text-muted); pointer-events: none; }
.tmpl-search input {
  padding: 5px 10px 5px 28px; border: 1px solid var(--border); border-radius: var(--radius);
  font-size: 12px; font-family: var(--mono); background: var(--surface);
  color: var(--text-primary); width: 180px;
}
.tmpl-search input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(37,99,235,0.12); }
.tmpl-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px; margin-top: 16px;
}
.tmpl-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 20px;
  box-shadow: var(--shadow-sm); transition: box-shadow var(--transition);
  cursor: pointer; position: relative;
}
.tmpl-card:hover { box-shadow: var(--shadow-md); }
.tmpl-card.expanded { grid-column: 1 / -1; }
.tmpl-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.tmpl-card-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.tmpl-card-source {
  font-size: 10px; font-family: var(--mono); text-transform: uppercase;
  letter-spacing: 0.04em; padding: 2px 7px; border-radius: 3px;
  background: var(--surface-alt); color: var(--text-muted); white-space: nowrap;
}
.tmpl-card-source--universal { background: #e8eef5; color: #3b5998; }
.tmpl-card-source--security { background: #fce8e8; color: #a63d40; }
.tmpl-card-source--compliance { background: #faf3e0; color: #7d5f0f; }
.tmpl-card-source--custom { background: #e6f0ec; color: #2d6a5a; }
.tmpl-card-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.5; }
.tmpl-card-meta { display: flex; gap: 12px; flex-wrap: wrap; font-size: 11px; font-family: var(--mono); color: var(--text-muted); }
.tmpl-card-meta span { display: inline-flex; align-items: center; gap: 3px; }
.tmpl-card-tags { margin-top: 10px; }
.tmpl-card-xrefs { margin-top: 10px; font-size: 12px; color: var(--text-secondary); }
.tmpl-card-xrefs a { font-size: 12px; }
.tmpl-card-detail { display: none; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); }
.tmpl-card.expanded .tmpl-card-detail { display: block; }
.tmpl-card-sections { list-style: none; padding: 0; }
.tmpl-card-sections li {
  font-size: 13px; padding: 4px 0 4px 16px; color: var(--text-secondary);
  border-left: 2px solid var(--border); margin-bottom: 2px;
}
.tmpl-card-sections li:hover { border-color: var(--accent); color: var(--text-primary); }
.tmpl-card-compliance { margin-top: 10px; }
.tmpl-card-compliance .tag { background: #faf3e0; color: #7d5f0f; }
.tmpl-count { font-size: 13px; color: var(--text-muted); font-family: var(--mono); }

/* ── Recommendations Panel ─────────────────────────────────────────────── */
.rec-section { margin-top: 32px; }
.rec-section h2 { font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; }
.rec-group-title {
  font-size: 11px; font-family: var(--mono); text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--text-muted); font-weight: 700;
  margin-top: 16px; margin-bottom: 8px;
}
.rec-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 12px;
  border-radius: var(--radius); background: var(--surface);
  border: 1px solid var(--border); margin-bottom: 6px; font-size: 13px;
}
.rec-item:hover { background: var(--surface-alt); }
.rec-priority-core { border-left: 3px solid var(--status-error); }
.rec-priority-recommended { border-left: 3px solid var(--status-warn); }
.rec-priority-cross_ref { border-left: 3px solid var(--accent); }
.rec-priority-compliance { border-left: 3px solid #6a5acd; }
.rec-priority-maturity { border-left: 3px solid var(--text-muted); }
.rec-id { font-family: var(--mono); font-weight: 600; color: var(--text-primary); min-width: 200px; }
.rec-name { color: var(--text-secondary); flex: 1; }
.rec-refs { font-size: 11px; color: var(--text-muted); font-family: var(--mono); }

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

/* ── Project Manager Page ── */
.mgr-sections { display: flex; flex-direction: column; gap: 16px; }
.mgr-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); overflow: hidden; }
.mgr-section-header { display: flex; align-items: center; gap: 10px; padding: 14px 20px; cursor: pointer; user-select: none; transition: background 0.15s; }
.mgr-section-header:hover { background: var(--surface-alt); }
.mgr-section-header h2 { margin: 0; font-size: 15px; font-weight: 600; flex: 1; }
.mgr-section-icon { font-size: 16px; color: var(--accent); width: 20px; text-align: center; }
.mgr-badge { background: var(--accent); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-family: var(--mono); }
.mgr-chevron { color: var(--text-muted); font-size: 10px; transition: transform 0.2s; }
.mgr-section.collapsed .mgr-chevron { transform: rotate(-90deg); }
.mgr-section.collapsed .mgr-section-body { display: none; }
.mgr-section-body { padding: 0 20px 20px; border-top: 1px solid var(--border); }
.mgr-hint { font-size: 12px; color: var(--text-muted); margin: 12px 0 16px; }
.mgr-form { display: flex; flex-direction: column; gap: 12px; }
.mgr-row { display: flex; align-items: center; gap: 12px; }
.mgr-row label { width: 120px; font-size: 13px; font-weight: 500; color: var(--text-secondary); flex-shrink: 0; }
.mgr-row input, .mgr-row select { flex: 1; padding: 7px 10px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; font-family: var(--sans); background: var(--bg); color: var(--text-primary); }
.mgr-row input:focus, .mgr-row select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(37,99,235,0.12); }
.mgr-row-btn { justify-content: flex-end; gap: 8px; padding-top: 4px; }
.mgr-btn { padding: 7px 16px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); color: var(--text-primary); font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.15s; font-family: var(--sans); }
.mgr-btn:hover { background: var(--surface-alt); border-color: var(--accent); }
.mgr-btn--primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.mgr-btn--primary:hover { background: #1d4ed8; }
.mgr-btn--sm { padding: 4px 10px; font-size: 11px; }
.mgr-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mgr-table th { text-align: left; padding: 8px 12px; background: var(--surface-alt); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); font-weight: 600; }
.mgr-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.mgr-filename { font-family: var(--mono); font-size: 12px; }
.mgr-table tr:hover { background: var(--surface-alt); }
.mgr-preview { background: var(--surface-alt); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 16px; }
.mgr-preview-row { font-size: 12px; padding: 2px 0; }
.mgr-preview-row code { background: var(--bg); padding: 2px 6px; border-radius: 3px; font-size: 11px; }
.mgr-output { position: sticky; bottom: 0; background: var(--surface); border: 2px solid var(--accent); border-radius: var(--radius-lg); margin-top: 24px; box-shadow: 0 -4px 24px rgba(0,0,0,0.12); z-index: 50; }
.mgr-output-header { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-bottom: 1px solid var(--border); }
.mgr-output-header h3 { margin: 0; font-size: 13px; font-weight: 600; flex: 1; }
.mgr-output pre { margin: 0; padding: 16px; background: #1e293b; color: #e2e8f0; border-radius: 0; font-size: 13px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
.mgr-output-hint { font-size: 11px; color: var(--text-muted); padding: 8px 16px; margin: 0; }
.mgr-folder-ref { font-size: 12px; color: var(--text-muted); padding: 12px 0 0; }
.mgr-folder-ref code { background: var(--bg); padding: 2px 6px; border-radius: 3px; font-size: 11px; margin: 0 2px; }

/* Audit & Verify page */
.audit-sections { display: flex; flex-direction: column; gap: 12px; }
.aud-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; }
.aud-section.collapsed .aud-section-body { display: none; }
.aud-section.collapsed .mgr-chevron { transform: rotate(-90deg); }
.aud-section-header { display: flex; align-items: center; gap: 10px; padding: 14px 20px; cursor: pointer; user-select: none; transition: background 0.15s; }
.aud-section-header:hover { background: var(--surface-alt); }
.aud-section-header h2 { margin: 0; font-size: 15px; font-weight: 600; flex: 1; }
.aud-section-body { padding: 0 20px 20px; }
.aud-status { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; letter-spacing: 0.03em; text-transform: uppercase; }
.aud-pass { background: #dcfce7; color: #166534; }
.aud-fail { background: #fef2f2; color: #991b1b; }
.aud-info { background: var(--surface-alt); color: var(--text-muted); }
.aud-ok-banner { padding: 20px; text-align: center; font-size: 14px; color: #166534; background: #f0fdf4; border-radius: var(--radius); }
.aud-finding { margin-bottom: 16px; }
.aud-finding-title { font-size: 14px; margin: 0 0 6px; font-weight: 600; }
.aud-finding-hint { font-size: 12px; color: var(--text-muted); margin: 0 0 8px; }
.aud-finding--warn { color: #92400e; }
.aud-finding--err { color: #991b1b; }
.aud-finding--info { color: #1e40af; }
.aud-finding-list { margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.7; }
.aud-finding-list code { background: var(--bg); padding: 2px 6px; border-radius: 3px; font-size: 12px; }
.aud-dot { font-weight: 700; font-size: 14px; }
.aud-dot--ok { color: #166534; }
.aud-dot--err { color: #991b1b; }
.aud-hash { font-family: var(--mono); font-size: 11px; color: var(--text-muted); word-break: break-all; }
.aud-row--err { background: #fef2f2; }
.aud-controls { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.aud-controls input[type="text"] { flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; background: var(--bg); }
.aud-toggle { font-size: 12px; display: flex; align-items: center; gap: 6px; cursor: pointer; white-space: nowrap; }
.aud-chain-status { margin-top: 12px; padding: 10px 16px; border-radius: var(--radius); font-size: 13px; }
.aud-chain-ok { color: #166534; }
.aud-chain-broken { color: #991b1b; font-weight: 600; }
.aud-chain-info { color: var(--text-muted); font-style: italic; }
.aud-seal-box { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.aud-seal-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; }
.aud-seal-label { font-size: 12px; font-weight: 600; color: var(--text-muted); min-width: 100px; }
.aud-seal-value { font-family: var(--mono); font-size: 12px; word-break: break-all; background: var(--surface); padding: 6px 10px; border-radius: var(--radius); flex: 1; }
.aud-seal-explain { font-size: 12px; color: var(--text-muted); line-height: 1.6; margin: 12px 0 0; }
.aud-seal-explain code { background: var(--surface); padding: 2px 5px; border-radius: 3px; font-size: 11px; }
.aud-rec-group { margin-bottom: 16px; }
.aud-rec-cat { font-size: 13px; font-weight: 600; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted); }
.aud-op-badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; background: var(--surface-alt); color: var(--text); text-transform: uppercase; letter-spacing: 0.03em; }
.aud-op--register { background: #dbeafe; color: #1e40af; }
.aud-op--bump { background: #fef3c7; color: #92400e; }
.aud-op--audit { background: #dcfce7; color: #166534; }
.aud-op--manifest { background: #f3e8ff; color: #6b21a8; }
.aud-op--evidence { background: #ffe4e6; color: #9f1239; }
.aud-op--scaffold { background: #e0f2fe; color: #0369a1; }
.aud-cli-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.aud-cli-card { padding: 16px; border: 1px solid var(--border); border-radius: var(--radius); cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.aud-cli-card:hover { border-color: var(--accent); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.aud-cli-card code { display: block; font-size: 12px; font-family: var(--mono); margin-top: 8px; padding: 8px 10px; background: #1e293b; color: #e2e8f0; border-radius: var(--radius); white-space: pre-wrap; word-break: break-all; }
.aud-cli-title { font-size: 13px; font-weight: 600; }
.aud-cli-hint { font-size: 11px; color: var(--text-muted); margin-top: 12px; text-align: center; }
.kpi-ok { color: #166534; }
.kpi-warn { color: #92400e; }
.kpi-err { color: #991b1b; }
"""

# SVG icons used in the sidebar
_CHEVRON_SVG = '<svg class="tree-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 4l4 4-4 4"/></svg>'


# ── Page builders ────────────────────────────────────────────────────────


def _nav(active: str, has_dashboard: bool = False, prefix: str = "") -> str:
    """Build the navigation bar HTML."""
    links = [
        ("index.html", "Home", "index"),
        ("manage.html", "Manage", "manage"),
        ("audit.html", "Audit", "audit"),
        ("tree.html", "Tree", "tree"),
        ("graph.html", "Graph", "graph"),
        ("templates.html", "Templates", "templates"),
    ]
    # Dashboard link intentionally omitted from site nav —
    # standalone dashboard is available via `librarian dashboard` CLI.

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
    nested_json = _build_nested_tree_json(documents)

    return f"""<aside class="sidebar" id="sidebar">
  <div class="sidebar-section">
    <div class="sidebar-heading">Documents</div>
  </div>
  <div class="group-toggles">
    <button class="group-btn active" data-group="status" onclick="switchGroup(this, &#39;status&#39;)">Status</button>
    <button class="group-btn" data-group="tag" onclick="switchGroup(this, &#39;tag&#39;)">Tag</button>
    <button class="group-btn" data-group="tree" onclick="switchGroup(this, &#39;tree&#39;)">Tree</button>
  </div>
  <div class="tree-container" id="tree-container"></div>
  <script>
  var TREE_DATA = {tree_json};
  var NESTED_TREE = {nested_json};
  var BASE_PREFIX = "{base_prefix}";
  var CURRENT_PAGE = window.location.pathname.split("/").pop() || "index.html";
  function renderDocItems(docs) {{
    var html = "";
    docs.forEach(function(d) {{
      var dotCls = "tree-dot tree-dot--" + (d.status || "");
      var href = BASE_PREFIX + "docs/" + d.filename + ".html";
      var isCurrent = href.split("/").pop() === CURRENT_PAGE;
      var itemCls = "tree-item" + (isCurrent ? " tree-item--current" : "");
      html += '<a class="' + itemCls + '" href="' + href + '">';
      html += '<span class="' + dotCls + '"></span>';
      html += '<span style="overflow:hidden;text-overflow:ellipsis">' + (d.title || d.filename) + '</span>';
      html += '</a>';
    }});
    return html;
  }}
  function countAllDocs(node) {{
    var n = (node.docs || []).length;
    var dirs = node.dirs || {{}};
    Object.keys(dirs).forEach(function(k) {{ n += countAllDocs(dirs[k]); }});
    return n;
  }}
  function renderNestedNode(node) {{
    var html = "";
    /* Render subfolders first */
    var dirKeys = Object.keys(node.dirs || {{}}).sort();
    dirKeys.forEach(function(dirName) {{
      var child = node.dirs[dirName];
      var total = countAllDocs(child);
      html += '<div class="tree-group tree-nested">';
      html += '<div class="tree-group-header" onclick="this.parentElement.classList.toggle(&#39;collapsed&#39;)">';
      html += '{_CHEVRON_SVG}';
      html += '<span class="tree-folder-icon">&#128193;</span>';
      html += '<span class="tree-group-label">' + dirName + '/</span>';
      html += '<span class="tree-group-count">' + total + '</span>';
      html += '</div>';
      html += '<div class="tree-items">';
      /* Docs directly in this folder */
      html += renderDocItems(child.docs || []);
      /* Recurse into subfolders */
      html += renderNestedNode(child);
      html += '</div></div>';
    }});
    return html;
  }}
  function renderTree(mode) {{
    var container = document.getElementById("tree-container");
    if (mode === "tree") {{
      var html = "";
      /* Root-level docs first */
      var rootDocs = NESTED_TREE.docs || [];
      if (rootDocs.length) {{
        html += renderDocItems(rootDocs);
      }}
      /* Then top-level folders */
      html += renderNestedNode(NESTED_TREE);
      container.innerHTML = html;
      return;
    }}
    var groups = TREE_DATA[mode] || {{}};
    var html = "";
    var keys = Object.keys(groups).sort();
    keys.forEach(function(key) {{
      var docs = groups[key];
      html += '<div class="tree-group">';
      html += '<div class="tree-group-header" onclick="this.parentElement.classList.toggle(&#39;collapsed&#39;)">';
      html += '{_CHEVRON_SVG}';
      html += '<span class="tree-group-label">' + key + '</span>';
      html += '<span class="tree-group-count">' + docs.length + '</span>';
      html += '</div>';
      html += '<div class="tree-items">';
      html += renderDocItems(docs);
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
    search_index: str | None = None,
) -> str:
    """Wrap body content in the full HTML page shell.

    Args:
        path_prefix: Relative path prefix for asset/nav links.
            Root pages use ``""``, pages in ``docs/`` use ``"../"``.
        search_index: JSON array of search entries for the global search bar.
            If ``None``, falls back to the module-level ``_SEARCH_INDEX_JSON``.
    """
    if search_index is None:
        search_index = _SEARCH_INDEX_JSON
    seal_short = _esc(seal[:16]) + "..." if seal else "N/A"
    search_icon_svg = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                       'stroke-width="2" class="global-search-icon">'
                       '<circle cx="11" cy="11" r="8"/>'
                       '<line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(title)} — {_esc(project_name)}</title>
<link rel="stylesheet" href="{path_prefix}assets/style.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="brand"><svg class="brand-logo" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="16" height="20" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M7 9h8M7 12.5h8M7 16h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M22 7v14a3 3 0 0 1-3 3H8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="21" cy="7" r="3.5" fill="var(--accent)" stroke="var(--surface)" stroke-width="1.2"/><path d="M19.8 7l.8.8 1.6-1.6" stroke="var(--surface)" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>{_esc(project_name)}</div>
  {_nav(active_nav, has_dashboard=has_dashboard, prefix=path_prefix)}
  <div class="header-spacer"></div>
  <div class="global-search" id="global-search">
    {search_icon_svg}
    <input type="text" id="global-search-input" placeholder="Search docs &amp; settings..." autocomplete="off">
    <div class="global-search-results" id="global-search-results"></div>
  </div>
  {_gear_link(active_nav, path_prefix)}
</header>
<div class="site-body">
{sidebar}
<main class="main">
{body}
<footer>
<span>Librarian</span>
<span class="footer-seal">seal {seal_short}</span>
<span>Generated {_esc(generated_at)}</span>
</footer>
</main>
</div>
<script>
(function() {{
  var SEARCH_INDEX = {search_index};
  var PREFIX = '{path_prefix}';
  var input = document.getElementById('global-search-input');
  var results = document.getElementById('global-search-results');
  var activeIdx = -1;
  var currentItems = [];

  // SVG icons for result categories
  var ICONS = {{
    document: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="gsr-item-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    setting: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="gsr-item-icon"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    page: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="gsr-item-icon"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/></svg>',
    template: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="gsr-item-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
  }};

  function esc(s) {{
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }}

  // Date range parsing: supports YYYY, YYYY-MM, YYYY-MM-DD, and X..Y ranges
  var DATE_RE = /^(\d{{4}})(?:-(\d{{2}}))?(?:-(\d{{2}}))?$/;
  function parseDate(s) {{
    var m = DATE_RE.exec(s.trim());
    if (!m) return null;
    return {{ y: parseInt(m[1],10), m: m[2] ? parseInt(m[2],10) : 0, d: m[3] ? parseInt(m[3],10) : 0 }};
  }}
  function dateToNum(d) {{
    // Convert to YYYYMMDD int for range comparison — fill missing parts
    return d.y * 10000 + (d.m || 1) * 100 + (d.d || 1);
  }}
  function dateToMax(d) {{
    // Upper bound: if only year, end of year; if year-month, end of month
    return d.y * 10000 + (d.m || 12) * 100 + (d.d || 31);
  }}
  function entryDateNum(e) {{
    if (!e.date) return 0;
    var m = DATE_RE.exec(e.date);
    if (!m) return 0;
    return parseInt(m[1],10) * 10000 + (m[2] ? parseInt(m[2],10) : 1) * 100 + (m[3] ? parseInt(m[3],10) : 1);
  }}

  function doSearch(q) {{
    q = q.toLowerCase().trim();
    if (!q) {{ results.classList.remove('open'); return; }}

    // Check for date range pattern: "2026-04-01..2026-04-13" or single date "2026-04"
    var dateFrom = null, dateTo = null, textQuery = q;
    var rangeMatch = q.match(/^(\d{{4}}(?:-\d{{2}})?(?:-\d{{2}})?)\.\.(\d{{4}}(?:-\d{{2}})?(?:-\d{{2}})?)\s*(.*)$/);
    if (rangeMatch) {{
      dateFrom = parseDate(rangeMatch[1]);
      dateTo = parseDate(rangeMatch[2]);
      textQuery = (rangeMatch[3] || '').trim();
    }} else {{
      var singleMatch = q.match(/^(\d{{4}}(?:-\d{{2}})(?:-\d{{2}})?)\s*(.*)$/);
      if (!singleMatch) singleMatch = q.match(/^(\d{{4}})\s+(.+)$/);
      if (!singleMatch && /^\d{{4}}(?:-\d{{2}})?(?:-\d{{2}})?$/.test(q)) {{
        singleMatch = [null, q, ''];
      }}
      if (singleMatch) {{
        var sd = parseDate(singleMatch[1]);
        if (sd) {{
          dateFrom = sd;
          dateTo = sd;
          textQuery = (singleMatch[2] || '').trim();
        }}
      }}
    }}

    var hasDateFilter = dateFrom && dateTo;
    var fromNum = hasDateFilter ? dateToNum(dateFrom) : 0;
    var toNum = hasDateFilter ? dateToMax(dateTo) : 0;

    var matches = SEARCH_INDEX.filter(function(e) {{
      // Date filter: only applies to entries that have a date field
      if (hasDateFilter) {{
        if (e.date) {{
          var eNum = entryDateNum(e);
          if (eNum < fromNum || eNum > toNum) return false;
        }} else if (!textQuery) {{
          // Date-only query: skip non-dated entries
          return false;
        }}
      }}
      // Text filter
      if (textQuery) {{
        return e.text.toLowerCase().indexOf(textQuery) >= 0;
      }}
      return true;
    }});

    if (matches.length === 0) {{
      var hint = hasDateFilter ? '<br><span style="font-size:11px">Try: YYYY-MM-DD, YYYY-MM, or YYYY-MM-DD..YYYY-MM-DD</span>' : '';
      results.innerHTML = '<div class="gsr-empty">No results for &#34;' + esc(q) + '&#34;' + hint + '</div>';
      results.classList.add('open');
      currentItems = [];
      activeIdx = -1;
      return;
    }}

    // Group by category
    var groups = {{}};
    matches.forEach(function(m) {{
      var cat = m.category || 'other';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(m);
    }});

    var order = ['document', 'setting', 'template', 'page'];
    var labels = {{ document: 'Documents', setting: 'Settings', template: 'Templates', page: 'Pages' }};
    var html = '';
    currentItems = [];

    order.forEach(function(cat) {{
      if (!groups[cat]) return;
      html += '<div class="gsr-section">' + (labels[cat] || cat) + '</div>';
      groups[cat].slice(0, 8).forEach(function(m) {{
        var idx = currentItems.length;
        var icon = ICONS[cat] || ICONS.page;
        var href = m.href ? (m.href.indexOf('://') >= 0 ? m.href : PREFIX + m.href) : '#';
        var metaText = hasDateFilter && m.date ? m.date : (m.meta || '');
        html += '<a class="gsr-item" data-idx="' + idx + '" href="' + esc(href) + '">'
              + icon
              + '<span class="gsr-item-title">' + esc(m.title) + '</span>'
              + (metaText ? '<span class="gsr-item-meta">' + esc(metaText) + '</span>' : '')
              + '</a>';
        currentItems.push({{ href: href, el: null }});
      }});
    }});

    results.innerHTML = html;
    results.classList.add('open');
    activeIdx = -1;

    // Cache element references
    results.querySelectorAll('.gsr-item').forEach(function(el, i) {{
      currentItems[i].el = el;
    }});
  }}

  function setActive(idx) {{
    if (currentItems[activeIdx] && currentItems[activeIdx].el) {{
      currentItems[activeIdx].el.classList.remove('gsr-active');
    }}
    activeIdx = idx;
    if (currentItems[activeIdx] && currentItems[activeIdx].el) {{
      currentItems[activeIdx].el.classList.add('gsr-active');
      currentItems[activeIdx].el.scrollIntoView({{ block: 'nearest' }});
    }}
  }}

  input.addEventListener('input', function() {{ doSearch(this.value); }});

  input.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
      results.classList.remove('open');
      input.blur();
      return;
    }}
    if (!results.classList.contains('open') || currentItems.length === 0) return;
    if (e.key === 'ArrowDown') {{
      e.preventDefault();
      setActive(Math.min(activeIdx + 1, currentItems.length - 1));
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      setActive(Math.max(activeIdx - 1, 0));
    }} else if (e.key === 'Enter' && activeIdx >= 0) {{
      e.preventDefault();
      var href = currentItems[activeIdx].href;
      if (href && href !== '#') window.location.href = href;
    }}
  }});

  // Close on outside click
  document.addEventListener('click', function(e) {{
    if (!document.getElementById('global-search').contains(e.target)) {{
      results.classList.remove('open');
    }}
  }});

  // Keyboard shortcut: / to focus search
  document.addEventListener('keydown', function(e) {{
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'SELECT') {{
      e.preventDefault();
      input.focus();
    }}
  }});
}})();
</script>
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

    # Recommendations section (may be empty if no gaps)
    rec_html = _build_recommendations_html(manifest)

    body = f"""<h1>{_esc(project_name)} — Document Registry</h1>
<div class="subtitle">{len(documents)} registered documents</div>
{kpi_html}
{search_html}
{table}
{rec_html}"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Index",
        body,
        "index",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
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
<div class="tree-controls">
<button class="tree-ctrl-btn" onclick="toggleAllBranches(false)">Collapse All</button>
<button class="tree-ctrl-btn" onclick="toggleAllBranches(true)">Expand All</button>
<button class="tree-ctrl-btn" id="folders-only-btn" onclick="toggleFoldersOnly()">Folders Only</button>
</div>
{diagram}
<div id="tree-cards-section">
{cards}
</div>
<script>
function toggleAllBranches(expand) {{
  document.querySelectorAll('.td-branch').forEach(function(b) {{
    if (expand) b.classList.remove('collapsed');
    else b.classList.add('collapsed');
  }});
}}
function toggleFoldersOnly() {{
  var btn = document.getElementById('folders-only-btn');
  var section = document.getElementById('tree-cards-section');
  var diagram = document.querySelector('.tree-diagram');
  if (section.style.display === 'none') {{
    section.style.display = '';
    btn.classList.remove('tree-ctrl-btn--active');
    if (diagram) {{
      diagram.querySelectorAll('.td-entry:not(.td-branch)').forEach(function(e) {{
        e.style.display = '';
      }});
    }}
  }} else {{
    section.style.display = 'none';
    btn.classList.add('tree-ctrl-btn--active');
    if (diagram) {{
      // Expand all branches so nested folders are visible at every depth
      diagram.querySelectorAll('.td-branch.collapsed').forEach(function(b) {{
        b.classList.remove('collapsed');
      }});
      // Hide file entries (non-branch entries)
      diagram.querySelectorAll('.td-entry:not(.td-branch)').forEach(function(e) {{
        e.style.display = 'none';
      }});
    }}
  }}
}}
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Tree",
        body,
        "tree",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
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
        has_dashboard=False,
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

    elements_json = _json_safe(cy_nodes + cy_edges, indent=2, sort_keys=True)

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
        has_dashboard=False,
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
.site-nav-overlay .brand { font-size: 16px; font-weight: 800; font-family: "Playfair Display", Georgia, serif; color: #1a1816; display: flex; align-items: center; gap: 6px; }
.site-nav-overlay .brand-logo { width: 20px; height: 20px; color: #2d6a5a; }
</style>
<div class="site-nav-overlay">
  <div class="brand"><svg class="brand-logo" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="16" height="20" rx="2" stroke="currentColor" stroke-width="1.8"/><path d="M7 9h8M7 12.5h8M7 16h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M22 7v14a3 3 0 0 1-3 3H8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="21" cy="7" r="3.5" fill="#2d6a5a" stroke="white" stroke-width="1.2"/><path d="M19.8 7l.8.8 1.6-1.6" stroke="white" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>Librarian</div>
  <a href="index.html">Index</a>
  <a href="tree.html">Tree</a>
  <a href="graph.html">Graph</a>
  <a href="templates.html">Templates</a>
  <a href="dashboard.html" class="active">Dashboard</a>
  <a href="settings.html" title="Settings" aria-label="Settings" style="margin-left:auto"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;vertical-align:-2px"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></a>
</div>
<style>body { padding-top: 36px; }</style>
"""
    # Inject after <body> tag
    html = html.replace("<body>", "<body>\n" + nav_html, 1)
    dashboard_file.write_text(html, encoding="utf-8")


# ── Templates Catalog Page ────────────────────────────────────────────────


def _build_templates_page(manifest: "Manifest") -> str:
    """Build the templates catalog page (templates.html).

    Displays a filterable card grid of all available templates for each
    preset.  Cards show template name, description, section count, tags,
    cross-references, and compliance conditionals.  Clicking a card expands
    it to show the full section list.
    """
    from .templates import discover_templates, CROSS_CUTTING

    snapshot = manifest.registry_snapshot
    config = snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")
    active_preset = config.get("preset", "")
    custom_dir = config.get("custom_templates_dir", None)
    documents = snapshot.get("documents", [])

    # All preset names for the switcher
    all_presets = [
        "software", "business", "legal", "scientific",
        "healthcare", "finance", "government",
    ]

    # Discover templates for ALL presets so JS can filter client-side
    all_templates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for preset_name in all_presets:
        tmpls = discover_templates(preset=preset_name, custom_dir=custom_dir)
        for tid, tmpl in sorted(tmpls.items()):
            source = tmpl.preset  # "universal", "security", "compliance", or preset
            card_key = f"{tid}|{source}"
            if card_key in seen_ids:
                continue
            seen_ids.add(card_key)

            # Detect compliance conditionals from body
            _ALL_COMP_FLAGS = (
                "hipaa", "gdpr", "dod_5200", "iso_9001", "iso_27001",
                "sec_finra", "sox", "pci_dss", "soc2", "ccpa",
                "nist_csf", "fda_21cfr11", "cmmc", "ferpa", "fedramp",
                "gxp", "itar_ear", "nerc_cip", "nis2", "dora",
                "pipeda", "lgpd",
            )
            comp_flags: list[str] = []
            for flag in _ALL_COMP_FLAGS:
                if flag in tmpl.body:
                    comp_flags.append(flag)

            # Determine which presets this template is available to
            if source in CROSS_CUTTING or source == "universal":
                available_presets = all_presets
            elif source == "custom":
                available_presets = all_presets
            else:
                available_presets = [source]

            all_templates.append({
                "id": tid,
                "name": tmpl.display_name,
                "description": tmpl.description,
                "source": source,
                "sections": tmpl.sections,
                "tags": tmpl.suggested_tags,
                "cross_refs": tmpl.typical_cross_refs,
                "requires": tmpl.requires,
                "recommended_with": tmpl.recommended_with,
                "compliance": comp_flags,
                "presets": available_presets,
            })

    # Sort: universal first, then cross-cutting, then preset-specific
    source_order = {"universal": 0, "security": 1, "compliance": 2, "custom": 3}
    all_templates.sort(key=lambda t: (source_order.get(t["source"], 10), t["id"]))

    # Serialize template data for client-side filtering
    tmpl_json = _json_safe(all_templates, indent=None)

    # Preset options for dropdown
    preset_opts = ""
    for p in all_presets:
        sel = " selected" if p == active_preset else ""
        preset_opts += f'<option value="{_esc(p)}"{sel}>{_esc(p.title())}</option>'

    # Source filter options
    source_labels = {
        "all": "All Sources",
        "universal": "Universal",
        "security": "Security",
        "compliance": "Compliance",
        "custom": "Custom",
    }
    # Add preset-specific sources
    for p in all_presets:
        source_labels[p] = p.title()

    source_opts = ""
    for key, label in source_labels.items():
        source_opts += f'<option value="{_esc(key)}">{_esc(label)}</option>'

    # Compliance filter options — only show flags that actually appear in templates
    _active_comp_flags: set[str] = set()
    for t in all_templates:
        _active_comp_flags.update(t["compliance"])

    _comp_label_map = {
        "hipaa": "HIPAA", "gdpr": "GDPR", "dod_5200": "DoD 5200",
        "iso_9001": "ISO 9001", "iso_27001": "ISO 27001",
        "sec_finra": "SEC/FINRA", "sox": "SOX", "pci_dss": "PCI DSS",
        "soc2": "SOC 2", "ccpa": "CCPA/CPRA", "nist_csf": "NIST CSF",
        "fda_21cfr11": "FDA 21 CFR 11", "cmmc": "CMMC", "ferpa": "FERPA",
        "fedramp": "FedRAMP", "gxp": "GxP", "itar_ear": "ITAR/EAR",
        "nerc_cip": "NERC CIP", "nis2": "NIS2", "dora": "DORA",
        "pipeda": "PIPEDA", "lgpd": "LGPD",
    }
    comp_labels: list[tuple[str, str]] = [("all", "All Compliance")]
    # Stable order: iterate the label map, include only flags with actual templates
    for flag, label in _comp_label_map.items():
        if flag in _active_comp_flags:
            comp_labels.append((flag, label))
    comp_opts = ""
    for val, label in comp_labels:
        comp_opts += f'<option value="{_esc(val)}">{_esc(label)}</option>'

    body = f"""<h1>Template Catalog</h1>
<div class="subtitle">Document templates available for scaffolding</div>

<div class="tmpl-controls">
  <label style="font-size:12px;color:var(--text-muted);font-family:var(--mono)">Preset:</label>
  <select id="tmpl-preset" onchange="filterTemplates()">{preset_opts}</select>
  <label style="font-size:12px;color:var(--text-muted);font-family:var(--mono)">Source:</label>
  <select id="tmpl-source" onchange="filterTemplates()">{source_opts}</select>
  <label style="font-size:12px;color:var(--text-muted);font-family:var(--mono)">Compliance:</label>
  <select id="tmpl-compliance" onchange="filterTemplates()">{comp_opts}</select>
  <div class="tmpl-search">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tmpl-search-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input type="text" id="tmpl-search" placeholder="Search templates..." oninput="filterTemplates()">
  </div>
  <span class="tmpl-count" id="tmpl-count"></span>
</div>

<div class="tmpl-grid" id="tmpl-grid"></div>

<script>
(function() {{
  var TEMPLATES = {tmpl_json};

  function esc(s) {{ var d=document.createElement("div"); d.appendChild(document.createTextNode(s||"")); return d.innerHTML.replace(/'/g,"&#39;"); }}

  function renderCards(filtered) {{
    var grid = document.getElementById("tmpl-grid");
    var html = "";
    for (var i = 0; i < filtered.length; i++) {{
      var t = filtered[i];
      var src = t.source;
      var srcCls = "tmpl-card-source";
      if (src === "universal") srcCls += " tmpl-card-source--universal";
      else if (src === "security") srcCls += " tmpl-card-source--security";
      else if (src === "compliance") srcCls += " tmpl-card-source--compliance";
      else if (src === "custom") srcCls += " tmpl-card-source--custom";

      var tags = "";
      for (var j = 0; j < t.tags.length; j++) tags += '<span class="tag">' + esc(t.tags[j]) + '</span>';

      var xrefs = "";
      if (t.cross_refs.length > 0) {{
        xrefs = '<div class="tmpl-card-xrefs">Cross-refs: ';
        for (var j = 0; j < t.cross_refs.length; j++) {{
          if (j > 0) xrefs += ", ";
          xrefs += '<a href="#" onclick="scrollToCard(\\'' + esc(t.cross_refs[j]) + '\\');return false">' + esc(t.cross_refs[j]) + '</a>';
        }}
        xrefs += '</div>';
      }}

      var compTags = "";
      if (t.compliance.length > 0) {{
        compTags = '<div class="tmpl-card-compliance">';
        for (var j = 0; j < t.compliance.length; j++) compTags += '<span class="tag">' + esc(t.compliance[j]) + '</span>';
        compTags += '</div>';
      }}

      var sections = "";
      if (t.sections.length > 0) {{
        sections = '<ul class="tmpl-card-sections">';
        for (var j = 0; j < t.sections.length; j++) sections += '<li>' + esc(t.sections[j]) + '</li>';
        sections += '</ul>';
      }}

      var reqHtml = "";
      if (t.requires && t.requires.length > 0) {{
        reqHtml = '<div style="font-size:12px;color:var(--text-muted);margin-top:8px">Requires: ';
        for (var j = 0; j < t.requires.length; j++) {{
          if (j > 0) reqHtml += ", ";
          reqHtml += '<code>' + esc(t.requires[j]) + '</code>';
        }}
        reqHtml += '</div>';
      }}

      var recHtml = "";
      if (t.recommended_with && t.recommended_with.length > 0) {{
        recHtml = '<div style="font-size:12px;color:var(--text-muted);margin-top:6px">Recommended with: ';
        for (var j = 0; j < t.recommended_with.length; j++) {{
          if (j > 0) recHtml += ", ";
          recHtml += '<a href="#" onclick="scrollToCard(\\'' + esc(t.recommended_with[j]) + '\\');return false">' + esc(t.recommended_with[j]) + '</a>';
        }}
        recHtml += '</div>';
      }}

      html += '<div class="tmpl-card" data-id="' + esc(t.id) + '" onclick="toggleCard(this)">';
      html += '<div class="tmpl-card-header"><div class="tmpl-card-title">' + esc(t.name) + '</div>';
      html += '<span class="' + srcCls + '">' + esc(src) + '</span></div>';
      html += '<div class="tmpl-card-desc">' + esc(t.description) + '</div>';
      html += '<div class="tmpl-card-meta">';
      html += '<span>' + t.sections.length + ' sections</span>';
      html += '<span>' + t.tags.length + ' tags</span>';
      if (t.cross_refs.length > 0) html += '<span>' + t.cross_refs.length + ' cross-refs</span>';
      html += '</div>';
      if (tags) html += '<div class="tmpl-card-tags">' + tags + '</div>';
      html += '<div class="tmpl-card-detail">';
      html += '<div class="section-title" style="margin-top:0">Sections</div>';
      html += sections;
      html += xrefs;
      html += compTags;
      html += reqHtml;
      html += recHtml;
      html += '<div style="margin-top:12px;font-size:12px;font-family:var(--mono);color:var(--text-muted)">';
      html += 'scaffold: <code>python -m librarian scaffold --template ' + esc(t.id) + '</code>';
      html += '</div>';
      html += '</div></div>';
    }}
    grid.innerHTML = html;
    document.getElementById("tmpl-count").textContent = filtered.length + " templates";
  }}

  window.toggleCard = function(el) {{
    el.classList.toggle("expanded");
  }};

  window.scrollToCard = function(id) {{
    var cards = document.querySelectorAll(".tmpl-card");
    for (var i = 0; i < cards.length; i++) {{
      if (cards[i].getAttribute("data-id") === id) {{
        cards[i].scrollIntoView({{ behavior: "smooth", block: "center" }});
        cards[i].classList.add("expanded");
        cards[i].style.outline = "2px solid var(--accent)";
        setTimeout(function() {{ cards[i].style.outline = ""; }}, 2000);
        return;
      }}
    }}
  }};

  window.filterTemplates = function() {{
    var preset = document.getElementById("tmpl-preset").value;
    var source = document.getElementById("tmpl-source").value;
    var comp = document.getElementById("tmpl-compliance").value;
    var query = (document.getElementById("tmpl-search").value || "").toLowerCase().trim();

    var filtered = TEMPLATES.filter(function(t) {{
      // Preset filter: template must be available to the selected preset
      if (t.presets.indexOf(preset) < 0) return false;
      // Source filter
      if (source !== "all" && t.source !== source) return false;
      // Compliance filter
      if (comp !== "all" && t.compliance.indexOf(comp) < 0) return false;
      // Text search: match against id, name, description, tags, sections, compliance
      if (query) {{
        var haystack = (t.id + " " + t.name + " " + t.description + " " + t.tags.join(" ") + " " + t.sections.join(" ") + " " + t.compliance.join(" ")).toLowerCase();
        if (haystack.indexOf(query) < 0) return false;
      }}
      return true;
    }});

    renderCards(filtered);
  }};

  // Initial render
  filterTemplates();
}})();
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Templates",
        body,
        "templates",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
        sidebar=sidebar,
    )


# ── Recommendations HTML helper ──────────────────────────────────────────


def _build_recommendations_html(manifest: "Manifest") -> str:
    """Build the recommendations section HTML for the index page.

    Returns an empty string if no recommendations are generated.
    """
    from .recommend import generate_recommendations

    snapshot = manifest.registry_snapshot
    config = snapshot.get("project_config", {})
    documents = snapshot.get("documents", [])

    try:
        report = generate_recommendations(
            registry_documents=documents,
            project_config=config,
        )
    except Exception:
        return ""

    if not report.recommendations:
        return ""

    groups = [
        ("Core", "core", report.core),
        ("Recommended", "recommended", report.recommended),
        ("Cross-Reference Gaps", "cross_ref", report.cross_ref_gaps),
        ("Maturity Progression", "maturity", report.maturity),
        ("Compliance", "compliance", report.compliance),
    ]

    items_html = ""
    for group_name, priority, recs in groups:
        if not recs:
            continue
        items_html += f'<div class="rec-group-title">{_esc(group_name)}</div>'
        for r in recs:
            refs = ""
            if r.referenced_by:
                refs = f'<span class="rec-refs">← {_esc(", ".join(r.referenced_by))}</span>'
            items_html += (
                f'<div class="rec-item rec-priority-{_esc(priority)}">'
                f'<span class="rec-id">{_esc(r.template_id)}</span>'
                f'<span class="rec-name">{_esc(r.display_name)}</span>'
                f'{refs}'
                f'</div>'
            )

    return f"""<div class="rec-section">
<h2>Recommendations</h2>
<div class="subtitle" style="margin-bottom:12px">
  {len(report.recommendations)} gap{"s" if len(report.recommendations) != 1 else ""} detected for
  <strong>{_esc(report.preset or "unknown")}</strong> preset
</div>
{items_html}
</div>"""


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
    _templates_json = _json_safe({
        name: {k: v for k, v in rules.items()}
        for name, rules in NAMING_TEMPLATES.items()
    })

    # Build compliance standards data for toggles
    # Each standard maps to a preset + specific settings it enables
    COMPLIANCE_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                       '<path d="M9 12l2 2 4-4"/><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2'
                       ' 2 6.477 2 12s4.477 10 10 10z"/></svg>')

    # Build template browser data for settings page
    from .templates import discover_templates as _discover_templates
    _settings_templates: list[dict[str, Any]] = []
    _active_preset = pc.get("preset", "")
    _custom_dir = pc.get("custom_templates_dir", None)
    _all_presets = ["software", "business", "legal", "scientific",
                    "healthcare", "finance", "government"]
    _seen_tmpl: set[str] = set()
    for _p in _all_presets:
        _tmpls = _discover_templates(preset=_p, custom_dir=_custom_dir)
        for _tid, _t in sorted(_tmpls.items()):
            _key = f"{_tid}|{_t.preset}"
            if _key in _seen_tmpl:
                continue
            _seen_tmpl.add(_key)
            _avail = _all_presets if _t.preset in ("universal", "security", "compliance", "custom") else [_t.preset]
            _settings_templates.append({
                "id": _tid, "name": _t.display_name, "source": _t.preset,
                "sections": len(_t.sections), "presets": _avail,
            })
    _settings_templates.sort(key=lambda t: ({"universal": 0, "security": 1, "compliance": 2}.get(t["source"], 10), t["id"]))
    _settings_tmpl_json = _json_safe(_settings_templates, indent=None)

    body = f"""<h1>Settings</h1>
<div class="subtitle">Current configuration for <strong>{_esc(project_name)}</strong> — values reflect your project_config in REGISTRY.yaml</div>

<div class="settings-topbar">
<div class="settings-view-toggle" id="view-toggle">
  <button type="button" class="view-toggle-btn active" id="view-basic-btn" onclick="switchSettingsView('basic')">Basic</button>
  <button type="button" class="view-toggle-btn" id="view-advanced-btn" onclick="switchSettingsView('advanced')">Advanced</button>
  <span class="settings-hint" style="margin-left:12px" id="view-hint">Showing essential settings only. Switch to Advanced for full control.</span>
</div>
<div class="settings-search" id="settings-search">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="settings-search-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
  <input type="text" id="settings-search-input" placeholder="Search settings..." oninput="searchSettings(this.value)">
  <span class="settings-search-clear" id="settings-search-clear" onclick="clearSettingsSearch()" style="display:none">&times;</span>
</div>
</div>

<div class="settings-layout">
<div class="settings-forms">

<div class="settings-section" data-view="basic">
<div class="settings-section-header">{FOLDER_ICON} Project Basics</div>
<div class="settings-grid">
  <div class="settings-row">
    <div class="settings-label">Preset</div>
    <div class="settings-control"><select id="cfg-preset" onchange="renderSettingsTemplates()">{preset_opts}</select></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Organization</div>
    <div class="settings-control"><input type="text" id="cfg-hdr-org-basic" value="{_esc(config.header.organization)}" placeholder="e.g. Acme Corporation" oninput="document.getElementById('cfg-hdr-org').value=this.value;updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Default Author</div>
    <div class="settings-control"><input type="text" id="cfg-author-basic" value="{_esc(config.default_author)}" oninput="document.getElementById('cfg-author').value=this.value;updatePreview()"></div>
  </div>
  <div class="settings-row">
    <div class="settings-label">Review Cycle</div>
    <div class="settings-control"><input type="text" id="cfg-meta-cycle-basic" value="{config.metadata.review_cycle_days}" style="width:80px" oninput="document.getElementById('cfg-meta-cycle').value=this.value;updatePreview()"> <span class="settings-hint">days (0 = none)</span></div>
  </div>
</div>
<div class="settings-hint" style="margin-top:8px">Need a guided setup? <a href="wizard.html" style="color:var(--accent)">Use the Setup Wizard</a></div>
</div>

<div class="settings-section" data-view="basic">
<div class="settings-section-header">{COMPLIANCE_ICON} Compliance Standards</div>
<div class="settings-hint" style="margin:0 0 8px">Toggle a standard to auto-apply its naming, header/footer, and metadata rules</div>
<div style="margin-bottom:12px">
  <select id="compliance-industry-filter" onchange="filterComplianceButtons()" style="font-size:12px;font-family:var(--mono);padding:4px 8px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface);color:var(--text-secondary)">
    <option value="all">All Industries</option>
    <option value="privacy">Privacy &amp; Data Protection</option>
    <option value="financial">Financial &amp; Audit</option>
    <option value="healthcare">Healthcare &amp; Life Sciences</option>
    <option value="government">Government &amp; Defense</option>
    <option value="technology">Technology &amp; Security</option>
    <option value="quality">Quality &amp; Standards</option>
    <option value="education">Education</option>
  </select>
</div>
<div class="settings-compliance-grid" id="compliance-grid">
  <button type="button" class="settings-compliance-btn" id="std-hipaa" data-industry="healthcare" onclick="applyStandard('hipaa')" title="HIPAA Privacy Rule (45 CFR 164) — PHI protections, 6-year retention, access controls">
    <span class="settings-compliance-icon">{HEADER_ICON}</span>
    <span class="settings-compliance-name">HIPAA</span>
    <span class="settings-compliance-desc">Healthcare Privacy</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-gdpr" data-industry="privacy" onclick="applyStandard('gdpr')" title="GDPR (EU 2016/679) — Data protection by design, DPIAs, data subject rights, 72-hour breach notification">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">GDPR</span>
    <span class="settings-compliance-desc">EU Data Protection</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-iso27001" data-industry="technology" onclick="applyStandard('iso27001')" title="ISO/IEC 27001:2022 — Information security management system, Annex A controls, risk treatment">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">ISO 27001</span>
    <span class="settings-compliance-desc">Information Security</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-sox" data-industry="financial" onclick="applyStandard('sox')" title="Sarbanes-Oxley Act (SOX) — Internal controls over financial reporting, Section 302/404 compliance">
    <span class="settings-compliance-icon">{CHECKLIST_ICON}</span>
    <span class="settings-compliance-name">SOX</span>
    <span class="settings-compliance-desc">Financial Controls</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-soc2" data-industry="technology" onclick="applyStandard('soc2')" title="SOC 2 Type II — Trust Service Criteria: security, availability, processing integrity, confidentiality, privacy">
    <span class="settings-compliance-icon">{CHECKLIST_ICON}</span>
    <span class="settings-compliance-name">SOC 2</span>
    <span class="settings-compliance-desc">Trust Services</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-pcidss" data-industry="financial" onclick="applyStandard('pcidss')" title="PCI DSS v4.0 — Payment card data security, network segmentation, encryption, access controls">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">PCI DSS</span>
    <span class="settings-compliance-desc">Payment Card Security</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-nist" data-industry="government" onclick="applyStandard('nist')" title="NIST CSF 2.0 / SP 800-171 — Identify, Protect, Detect, Respond, Recover + CUI safeguarding">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">NIST CSF</span>
    <span class="settings-compliance-desc">Cybersecurity Framework</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-ccpa" data-industry="privacy" onclick="applyStandard('ccpa')" title="CCPA/CPRA (Cal. Civ. Code 1798) — Consumer privacy rights, opt-out, data sale restrictions, right to delete">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">CCPA/CPRA</span>
    <span class="settings-compliance-desc">CA Privacy Rights</span>
  </button>
</div>
<div style="margin:8px 0 4px">
  <button type="button" class="tree-ctrl-btn" id="show-more-compliance" onclick="toggleMoreCompliance()" style="font-size:11px">Show More Standards</button>
</div>
<div class="settings-compliance-grid" id="compliance-grid-more" style="display:none">
  <button type="button" class="settings-compliance-btn" id="std-sec" data-industry="financial" onclick="applyStandard('sec')" title="SEC 17a-4 / FINRA 4511 — WORM retention, 6-year records, audit trail requirements">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">SEC / FINRA</span>
    <span class="settings-compliance-desc">Financial Recordkeeping</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-iso9001" data-industry="quality" onclick="applyStandard('iso9001')" title="ISO 9001:2015 / ISO 10013 — Document control numbering, revision tracking, approval workflows">
    <span class="settings-compliance-icon">{CHECKLIST_ICON}</span>
    <span class="settings-compliance-name">ISO 9001</span>
    <span class="settings-compliance-desc">Quality Management</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-dod" data-industry="government" onclick="applyStandard('dod')" title="DoD 5200.01 — Classification markings, distribution statements, FOUO/CUI banners">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">DoD 5200.01</span>
    <span class="settings-compliance-desc">Classification Markings</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-fda" data-industry="healthcare" onclick="applyStandard('fda')" title="FDA 21 CFR Part 11 — Electronic records and signatures, audit trails, system validation, data integrity">
    <span class="settings-compliance-icon">{HEADER_ICON}</span>
    <span class="settings-compliance-name">FDA 21 CFR 11</span>
    <span class="settings-compliance-desc">Electronic Records</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-cmmc" data-industry="government" onclick="applyStandard('cmmc')" title="CMMC 2.0 Level 2 — 110 NIST SP 800-171 practices, CUI protection, DoD contractor certification">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">CMMC</span>
    <span class="settings-compliance-desc">DoD Cyber Maturity</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-gxp" data-industry="healthcare" onclick="applyStandard('gxp')" title="GxP (GMP/GLP/GCP) — Good practice regulations for pharma manufacturing, lab, and clinical trials">
    <span class="settings-compliance-icon">{CHECKLIST_ICON}</span>
    <span class="settings-compliance-name">GxP</span>
    <span class="settings-compliance-desc">Pharma/Life Sciences</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-fedramp" data-industry="government" onclick="applyStandard('fedramp')" title="FedRAMP — Federal cloud security authorization, NIST 800-53 controls, continuous monitoring, ATO process">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">FedRAMP</span>
    <span class="settings-compliance-desc">Federal Cloud Auth</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-ferpa" data-industry="education" onclick="applyStandard('ferpa')" title="FERPA (20 U.S.C. 1232g) — Student education records privacy, directory information, consent requirements">
    <span class="settings-compliance-icon">{HEADER_ICON}</span>
    <span class="settings-compliance-name">FERPA</span>
    <span class="settings-compliance-desc">Student Records</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-scientific" data-industry="education" onclick="applyStandard('scientific')" title="NIH/NSF data management — 10-year retention, PI ownership, revision history, ISO 8601 dates">
    <span class="settings-compliance-icon">{NAMING_ICON}</span>
    <span class="settings-compliance-name">Research / Academic</span>
    <span class="settings-compliance-desc">Data Management Plans</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-legal" data-industry="financial" onclick="applyStandard('legal')" title="Legal DMS conventions — privilege markings, matter codes, Bates-style numbering, 7-year retention">
    <span class="settings-compliance-icon">{FOLDER_ICON}</span>
    <span class="settings-compliance-name">Legal / Law Firm</span>
    <span class="settings-compliance-desc">Matter Management</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-itar" data-industry="government" onclick="applyStandard('itar')" title="ITAR/EAR — International Traffic in Arms Regulations &amp; Export Administration Regulations, export-controlled technical data">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">ITAR / EAR</span>
    <span class="settings-compliance-desc">Export Controls</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-nerccip" data-industry="technology" onclick="applyStandard('nerccip')" title="NERC CIP — Critical Infrastructure Protection standards for bulk electric system cybersecurity">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">NERC CIP</span>
    <span class="settings-compliance-desc">Energy Infrastructure</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-nis2" data-industry="technology" onclick="applyStandard('nis2')" title="NIS2 Directive (EU 2022/2555) — Network and information security, incident reporting, supply chain security">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">NIS2</span>
    <span class="settings-compliance-desc">EU Network Security</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-dora" data-industry="financial" onclick="applyStandard('dora')" title="DORA (EU 2022/2554) — Digital Operational Resilience Act for financial entities, ICT risk management">
    <span class="settings-compliance-icon">{CHECKLIST_ICON}</span>
    <span class="settings-compliance-name">DORA</span>
    <span class="settings-compliance-desc">EU Financial Resilience</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-pipeda" data-industry="privacy" onclick="applyStandard('pipeda')" title="PIPEDA — Personal Information Protection and Electronic Documents Act (Canada), consent-based processing">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">PIPEDA</span>
    <span class="settings-compliance-desc">Canadian Privacy</span>
  </button>
  <button type="button" class="settings-compliance-btn" id="std-lgpd" data-industry="privacy" onclick="applyStandard('lgpd')" title="LGPD (Lei 13.709/2018) — Brazilian General Data Protection Law, consent, data subject rights, DPO requirement">
    <span class="settings-compliance-icon">{SHIELD_ICON}</span>
    <span class="settings-compliance-name">LGPD</span>
    <span class="settings-compliance-desc">Brazilian Privacy</span>
  </button>
</div>
</div>

<div class="settings-section" data-view="advanced">
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

<div class="settings-section" data-view="advanced">
<div class="settings-section-header">{FOLDER_ICON} Folder Categories</div>
<div class="settings-grid">
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

<div class="settings-section" data-view="advanced">
<div class="settings-section-header">{TAG_ICON} Tags Taxonomy</div>
<div class="settings-grid">
{tax_html}
</div>
</div>

<div class="settings-section" data-view="advanced">
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

<div class="settings-section" data-view="advanced">
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
        <option value="gdpr">GDPR / EU Data Protection</option>
        <option value="iso27001">ISO 27001 / ISMS</option>
        <option value="sox">SOX / Financial Controls</option>
        <option value="pcidss">PCI DSS / Payment Cards</option>
        <option value="soc2">SOC 2 / Trust Services</option>
        <option value="ccpa">CCPA/CPRA / CA Privacy</option>
        <option value="nist">NIST CSF / Cybersecurity</option>
        <option value="fda">FDA 21 CFR Part 11</option>
        <option value="cmmc">CMMC / DoD Cyber</option>
        <option value="ferpa">FERPA / Student Records</option>
        <option value="fedramp">FedRAMP / Federal Cloud</option>
        <option value="gxp">GxP / Pharma Life Sciences</option>
        <option value="itar">ITAR/EAR / Export Controls</option>
        <option value="nerccip">NERC CIP / Energy Infrastructure</option>
        <option value="nis2">NIS2 / EU Network Security</option>
        <option value="dora">DORA / EU Financial Resilience</option>
        <option value="pipeda">PIPEDA / Canadian Privacy</option>
        <option value="lgpd">LGPD / Brazilian Privacy</option>
      </select>
      <span class="settings-hint">Auto-fills custom footer with industry-standard disclaimer</span>
    </div>
  </div>
</div>
</div>

<div class="settings-section" data-view="advanced">
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

<div class="settings-section" id="sect-templates" data-view="advanced">
  <div class="settings-section-title">{CHECKLIST_ICON} Available Templates</div>
  <div class="settings-hint" style="margin-bottom:10px">Templates available for the selected preset. Click a row to copy the scaffold command.</div>
  <div id="settings-tmpl-list" style="max-height:320px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius-lg);background:var(--surface)"></div>
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
  technology: 'CONFIDENTIAL — Contains trade secrets and proprietary intellectual property. Protected under applicable trade secret laws and non-disclosure agreements. Do not reverse engineer, copy, or distribute.',
  gdpr: 'This document contains personal data subject to the General Data Protection Regulation (EU 2016/679). Processing must have a lawful basis under Article 6. Data subjects retain rights under Articles 15\\u201322. Report any breach to the supervisory authority within 72 hours per Article 33.',
  iso27001: 'ISMS Controlled Document \\u2014 This document is part of the Information Security Management System per ISO/IEC 27001:2022. Changes require approval through the document control process. Unauthorized modification or distribution is prohibited.',
  sox: 'This document supports internal controls over financial reporting under the Sarbanes-Oxley Act. Retain per Section 802 (minimum 7 years). Destruction, alteration, or falsification of records may result in criminal penalties under 18 U.S.C. \\u00a7 1519.',
  pcidss: 'RESTRICTED \\u2014 This document pertains to the Cardholder Data Environment (CDE) and is subject to PCI DSS v4.0 requirements. Do not store, process, or transmit cardholder data outside approved systems. Report suspected breaches immediately.',
  soc2: 'This document supports SOC 2 Type II Trust Service Criteria (AICPA). Covers security, availability, processing integrity, confidentiality, and privacy controls. Subject to annual audit. Retain per organizational control framework.',
  ccpa: 'This document may contain personal information as defined under the California Consumer Privacy Act (CCPA/CPRA, Cal. Civ. Code \\u00a7 1798). Consumers have the right to know, delete, and opt out of the sale of their personal information.',
  nist: 'CONTROLLED UNCLASSIFIED INFORMATION (CUI) \\u2014 This document is subject to safeguarding requirements under NIST SP 800-171. Handle, store, and transmit in accordance with CUI handling procedures. Unauthorized disclosure may result in administrative or legal action.',
  fda: 'GxP CONTROLLED DOCUMENT \\u2014 This document is subject to FDA 21 CFR Part 11 requirements for electronic records and signatures. All changes must be documented with audit trail. System validation required per 11.10(a).',
  cmmc: 'CUI \\u2014 CMMC Level 2 Controlled Document. Contains Controlled Unclassified Information subject to 110 NIST SP 800-171 security practices. Handle per DFARS 252.204-7012 and organizational CMMC policies.',
  ferpa: 'This document contains student education records protected under the Family Educational Rights and Privacy Act (FERPA, 20 U.S.C. \\u00a7 1232g). Disclosure without written consent of the eligible student or parent is prohibited except as authorized under 34 CFR \\u00a7 99.31.',
  fedramp: 'FEDERAL USE ONLY \\u2014 This document supports FedRAMP authorization and contains security control documentation per NIST SP 800-53. Subject to continuous monitoring requirements. Handle per agency-specific CUI procedures.',
  gxp: 'GxP CONTROLLED DOCUMENT \\u2014 Subject to Good Manufacturing Practice (GMP), Good Laboratory Practice (GLP), or Good Clinical Practice (GCP) regulations as applicable. All copies must be controlled. Superseded versions must be archived per regulatory retention requirements.',
  itar: 'WARNING \\u2014 This document contains technical data subject to the International Traffic in Arms Regulations (ITAR, 22 CFR 120\\u2013130) and/or the Export Administration Regulations (EAR, 15 CFR 730\\u2013774). Export, re-export, or transfer to foreign persons without prior authorization from the U.S. Department of State or Commerce is strictly prohibited and may result in criminal penalties.',
  nerccip: 'BES CYBER SYSTEM INFORMATION (BCSI) \\u2014 This document contains information related to Bulk Electric System Cyber Systems and is subject to NERC Critical Infrastructure Protection (CIP) standards. Handle, store, and destroy per CIP-004 and CIP-011 requirements. Unauthorized access or disclosure may result in penalties under the Federal Power Act.',
  nis2: 'This document supports compliance with the NIS2 Directive (EU 2022/2555) on measures for a high common level of cybersecurity across the Union. Significant incidents must be reported to the relevant CSIRT within 24 hours (early warning) and 72 hours (full notification) per Article 23.',
  dora: 'This document supports compliance with the Digital Operational Resilience Act (DORA, EU 2022/2554). Financial entities must maintain ICT risk management frameworks, report major ICT-related incidents, and conduct digital operational resilience testing per Articles 5\\u201315.',
  pipeda: 'This document contains personal information subject to the Personal Information Protection and Electronic Documents Act (PIPEDA, S.C. 2000, c. 5). Collection, use, and disclosure of personal information requires meaningful consent per Principle 3. Report breaches creating a real risk of significant harm to the Privacy Commissioner per section 10.1.',
  lgpd: 'Este documento cont\\u00e9m dados pessoais sujeitos \\u00e0 Lei Geral de Prote\\u00e7\\u00e3o de Dados (LGPD, Lei 13.709/2018). O tratamento deve ter base legal conforme Art. 7\\u00ba. Titulares de dados t\\u00eam direitos previstos nos Arts. 17\\u201322. Incidentes de seguran\\u00e7a devem ser comunicados \\u00e0 ANPD e aos titulares conforme Art. 48.'
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
  }},
  gdpr: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'PERSONAL DATA', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 Contains personal data subject to GDPR',
    ret: 'Retain only as long as processing purpose requires (Art. 5(1)(e))', copy: '',
    custom: 'GDPR (EU 2016/679) \\u2014 Data protection by design and by default (Art. 25)',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: 'PERSONAL DATA'
  }},
  iso27001: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: 'ISMS-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Controlled Document \\u2014 ISMS',
    ret: '', copy: '', custom: 'ISO/IEC 27001:2022 Information Security Management System',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  sox: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: 'SOX-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 SOX Controlled Document',
    ret: 'Retain per SOX Section 802 (7 years minimum)', copy: '',
    custom: 'Sarbanes-Oxley Act \\u2014 Internal controls documentation per Section 302/404',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2555, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  pcidss: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: 'PCI-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Restricted \\u2014 Cardholder Data Environment Documentation',
    ret: 'Retain for at least one year per PCI DSS Req. 10.7', copy: '',
    custom: 'PCI DSS v4.0 \\u2014 Payment Card Industry Data Security Standard',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1095, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  soc2: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 SOC 2 Trust Services Documentation',
    ret: '', copy: '', custom: 'SOC 2 Type II \\u2014 Trust Service Criteria (AICPA)',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  ccpa: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'PERSONAL INFORMATION', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 Contains consumer personal information',
    ret: '', copy: '',
    custom: 'CCPA/CPRA (Cal. Civ. Code \\u00a7 1798) \\u2014 California Consumer Privacy Rights',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: 'PERSONAL INFORMATION'
  }},
  nist: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CUI', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'CUI \\u2014 Controlled Unclassified Information',
    ret: '', copy: '', custom: 'NIST SP 800-171 / Cybersecurity Framework 2.0',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CUI'
  }},
  fda: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: '', prefix: 'VAL-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'GxP Controlled Document \\u2014 Do Not Copy Without Authorization',
    ret: 'Retain per 21 CFR 11.10(c) audit trail requirements', copy: '',
    custom: 'FDA 21 CFR Part 11 \\u2014 Electronic Records and Signatures',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: ''
  }},
  cmmc: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: false,
    hdr: true, org: '', logo: '', banner: 'CUI', prefix: 'SSP-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'CUI \\u2014 CMMC Level 2 Controlled Document',
    ret: '', copy: '', custom: 'CMMC 2.0 Level 2 \\u2014 110 NIST SP 800-171 practices',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CUI'
  }},
  ferpa: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'STUDENT RECORDS', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 Contains student education records',
    ret: 'Retain per institutional records retention schedule', copy: '',
    custom: 'FERPA (20 U.S.C. \\u00a7 1232g) \\u2014 Student Education Records Privacy',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: 'STUDENT RECORDS'
  }},
  fedramp: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CUI', prefix: 'FR-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'FedRAMP Controlled \\u2014 Federal Use Only',
    ret: '', copy: '',
    custom: 'FedRAMP \\u2014 NIST 800-53 controls for federal cloud authorization',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'CUI'
  }},
  gxp: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: '', prefix: 'SOP-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'GxP Controlled Document \\u2014 Approved Copy Only',
    ret: 'Retain per applicable GxP regulation', copy: '',
    custom: 'GxP (GMP/GLP/GCP) \\u2014 Good Practice Regulations',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: ''
  }},
  itar: {{
    sep: '-', 'case': 'uppercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: false,
    hdr: true, org: '', logo: '', banner: 'EXPORT CONTROLLED', prefix: 'ITAR-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'WARNING \\u2014 This document contains technical data controlled under ITAR/EAR. Export without authorization is prohibited.',
    ret: '', copy: '',
    custom: 'ITAR (22 CFR 120\\u2013130) / EAR (15 CFR 730\\u2013774) \\u2014 Export Controlled',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2555, cycle: 365, cls: 'EXPORT CONTROLLED'
  }},
  nerccip: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'BCSI', prefix: 'CIP-',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'BES Cyber System Information (BCSI) \\u2014 Handle per CIP-004/011',
    ret: '', copy: '',
    custom: 'NERC CIP \\u2014 Critical Infrastructure Protection Standards',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 2190, cycle: 365, cls: 'BCSI'
  }},
  nis2: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: '', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 NIS2 security documentation',
    ret: '', copy: '',
    custom: 'NIS2 Directive (EU 2022/2555) \\u2014 Network and Information Security',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: ''
  }},
  dora: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'CONFIDENTIAL', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 ICT risk management documentation',
    ret: '', copy: '',
    custom: 'DORA (EU 2022/2554) \\u2014 Digital Operational Resilience Act',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: 'CONFIDENTIAL'
  }},
  pipeda: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'PERSONAL INFORMATION', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Internal Use Only \\u2014 Contains personal information subject to PIPEDA',
    ret: '', copy: '',
    custom: 'PIPEDA (S.C. 2000, c. 5) \\u2014 Personal Information Protection (Canada)',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: 'PERSONAL INFORMATION'
  }},
  lgpd: {{
    sep: '-', 'case': 'lowercase', date: 'YYYYMMDD', ver: 'VX.Y', domain: true,
    hdr: true, org: '', logo: '', banner: 'DADOS PESSOAIS', prefix: '',
    hdrVer: true, hdrDate: true, hdrStatus: true, hdrPages: true,
    ftr: true, dist: 'Uso Interno \\u2014 Cont\\u00e9m dados pessoais sujeitos \\u00e0 LGPD',
    ret: '', copy: '',
    custom: 'LGPD (Lei 13.709/2018) \\u2014 Lei Geral de Prote\\u00e7\\u00e3o de Dados (Brazil)',
    metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true,
    retention: 1825, cycle: 365, cls: 'DADOS PESSOAIS'
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

function toggleMoreCompliance() {{
  var more = document.getElementById('compliance-grid-more');
  var btn = document.getElementById('show-more-compliance');
  if (more.style.display === 'none') {{
    more.style.display = '';
    btn.textContent = 'Show Fewer Standards';
    btn.classList.add('tree-ctrl-btn--active');
  }} else {{
    more.style.display = 'none';
    btn.textContent = 'Show More Standards';
    btn.classList.remove('tree-ctrl-btn--active');
  }}
}}

function filterComplianceButtons() {{
  var sel = document.getElementById('compliance-industry-filter').value;
  var grids = [document.getElementById('compliance-grid'), document.getElementById('compliance-grid-more')];
  // When filtering, always show the "more" section
  var more = document.getElementById('compliance-grid-more');
  var moreBtn = document.getElementById('show-more-compliance');
  if (sel !== 'all') {{
    more.style.display = '';
    moreBtn.style.display = 'none';
  }} else {{
    more.style.display = 'none';
    moreBtn.style.display = '';
    moreBtn.textContent = 'Show More Standards';
    moreBtn.classList.remove('tree-ctrl-btn--active');
  }}
  grids.forEach(function(grid) {{
    grid.querySelectorAll('.settings-compliance-btn').forEach(function(btn) {{
      if (sel === 'all') {{
        btn.style.display = '';
      }} else {{
        btn.style.display = (btn.getAttribute('data-industry') === sel) ? '' : 'none';
      }}
    }});
  }});
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

// Template browser for settings page
var SETTINGS_TEMPLATES = {_settings_tmpl_json};
function renderSettingsTemplates() {{
  var preset = document.getElementById('cfg-preset') ? document.getElementById('cfg-preset').value : '{_esc(_active_preset)}';
  var el = document.getElementById('settings-tmpl-list');
  if (!el) return;
  var filtered = preset ? SETTINGS_TEMPLATES.filter(function(t) {{ return t.presets.indexOf(preset) >= 0; }}) : SETTINGS_TEMPLATES;
  var html = '<table style="width:100%;font-size:12px;border-collapse:collapse">';
  html += '<thead><tr style="background:var(--surface-alt);text-align:left">';
  html += '<th style="padding:6px 10px">Template ID</th><th style="padding:6px 10px">Name</th>';
  html += '<th style="padding:6px 10px">Source</th><th style="padding:6px 10px">Sections</th></tr></thead><tbody>';
  for (var i = 0; i < filtered.length; i++) {{
    var t = filtered[i];
    var cmd = 'python -m librarian scaffold --template ' + t.id;
    html += '<tr style="cursor:pointer;border-bottom:1px solid var(--border)" ';
    html += 'onclick="navigator.clipboard.writeText(\\'' + cmd.replace(/'/g, "\\\\'") + '\\');';
    html += 'this.style.background=\\'var(--accent-light)\\';var r=this;setTimeout(function(){{r.style.background=\\'\\'}},800)" ';
    html += 'title="Click to copy: ' + cmd + '">';
    html += '<td style="padding:5px 10px;font-family:var(--mono)">' + t.id + '</td>';
    html += '<td style="padding:5px 10px">' + t.name + '</td>';
    html += '<td style="padding:5px 10px;font-family:var(--mono);font-size:10px;text-transform:uppercase">' + t.source + '</td>';
    html += '<td style="padding:5px 10px;text-align:center">' + t.sections + '</td>';
    html += '</tr>';
  }}
  html += '</tbody></table>';
  html += '<div style="font-size:11px;color:var(--text-muted);padding:6px 10px">' + filtered.length + ' templates available</div>';
  el.innerHTML = html;
}}

// Settings search
function searchSettings(query) {{
  var q = query.toLowerCase().trim();
  var clearBtn = document.getElementById('settings-search-clear');
  clearBtn.style.display = q ? '' : 'none';
  // Remove old highlights
  document.querySelectorAll('.search-highlight').forEach(function(el) {{ el.classList.remove('search-highlight'); }});
  document.querySelectorAll('.search-no-match').forEach(function(el) {{ el.classList.remove('search-no-match'); }});
  if (!q) return;

  // Switch to Advanced view so all sections are visible for searching
  switchSettingsView('advanced');

  // Search through settings sections and rows
  var sections = document.querySelectorAll('.settings-section');
  sections.forEach(function(section) {{
    var hasMatch = false;
    // Check section header
    var header = section.querySelector('.settings-section-header');
    if (header && header.textContent.toLowerCase().indexOf(q) >= 0) {{
      hasMatch = true;
    }}
    // Check individual rows
    var rows = section.querySelectorAll('.settings-row');
    rows.forEach(function(row) {{
      var label = row.querySelector('.settings-label');
      var hint = row.querySelector('.settings-hint');
      var labelText = label ? label.textContent.toLowerCase() : '';
      var hintText = hint ? hint.textContent.toLowerCase() : '';
      if (labelText.indexOf(q) >= 0 || hintText.indexOf(q) >= 0) {{
        row.classList.add('search-highlight');
        hasMatch = true;
      }}
    }});
    // Check compliance buttons
    var compBtns = section.querySelectorAll('.settings-compliance-btn');
    compBtns.forEach(function(btn) {{
      if (btn.textContent.toLowerCase().indexOf(q) >= 0) {{
        btn.classList.add('search-highlight');
        hasMatch = true;
      }}
    }});
    // Check select/dropdown option labels
    var selects = section.querySelectorAll('select');
    selects.forEach(function(sel) {{
      for (var i = 0; i < sel.options.length; i++) {{
        if (sel.options[i].text.toLowerCase().indexOf(q) >= 0) {{
          hasMatch = true;
          var row = sel.closest('.settings-row');
          if (row) row.classList.add('search-highlight');
          break;
        }}
      }}
    }});
    if (!hasMatch) section.classList.add('search-no-match');
  }});

  // Scroll to first highlighted element
  var first = document.querySelector('.search-highlight');
  if (first) first.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
}}

function clearSettingsSearch() {{
  document.getElementById('settings-search-input').value = '';
  searchSettings('');
}}

// View toggle — Basic / Advanced
function switchSettingsView(mode) {{
  var sections = document.querySelectorAll('.settings-section[data-view]');
  var basicBtn = document.getElementById('view-basic-btn');
  var advBtn = document.getElementById('view-advanced-btn');
  var hint = document.getElementById('view-hint');
  var previewPanel = document.getElementById('preview-panel');
  if (mode === 'advanced') {{
    sections.forEach(function(s) {{ s.style.display = ''; }});
    basicBtn.classList.remove('active');
    advBtn.classList.add('active');
    hint.textContent = 'Showing all settings. Switch to Basic for a simplified view.';
    if (previewPanel) previewPanel.style.display = '';
  }} else {{
    sections.forEach(function(s) {{
      s.style.display = (s.getAttribute('data-view') === 'basic') ? '' : 'none';
    }});
    basicBtn.classList.add('active');
    advBtn.classList.remove('active');
    hint.textContent = 'Showing essential settings only. Switch to Advanced for full control.';
    if (previewPanel) previewPanel.style.display = 'none';
  }}
}}

// Sync basic fields into advanced when they exist
function syncBasicFields() {{
  var orgBasic = document.getElementById('cfg-hdr-org-basic');
  var orgAdv = document.getElementById('cfg-hdr-org');
  if (orgBasic && orgAdv && orgBasic.value !== orgAdv.value) orgBasic.value = orgAdv.value;
  var authorBasic = document.getElementById('cfg-author-basic');
  var authorAdv = document.getElementById('cfg-author');
  if (authorBasic && authorAdv && authorBasic.value !== authorAdv.value) authorBasic.value = authorAdv.value;
  var cycleBasic = document.getElementById('cfg-meta-cycle-basic');
  var cycleAdv = document.getElementById('cfg-meta-cycle');
  if (cycleBasic && cycleAdv && cycleBasic.value !== cycleAdv.value) cycleBasic.value = cycleAdv.value;
}}

// Initialize: snapshot defaults, render preview, start in Basic mode
document.addEventListener('DOMContentLoaded', function() {{
  captureDefaults();
  updatePreview();
  renderSettingsTemplates();
  switchSettingsView('basic');
}});
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")
    return _page(
        "Settings",
        body,
        "settings",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
        sidebar=sidebar,
    )


def _build_wizard_page(manifest: "Manifest") -> str:
    """Build a setup wizard page — guided questionnaire to generate project_config."""
    from .config import PRESETS, NAMING_TEMPLATES

    snapshot = manifest.registry_snapshot
    pc = snapshot.get("project_config", {})
    documents = snapshot.get("documents", [])
    project_name = pc.get("project_name", "Untitled Project")

    # Wizard SVG icons
    WAND_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                 '<path d="M15 4V2"/><path d="M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/>'
                 '<path d="M17.8 11.8L19 13"/><path d="M15 9h0"/><path d="M17.8 6.2L19 5"/>'
                 '<path d="M3 21l9-9"/><path d="M12.2 6.2L11 5"/></svg>')

    body = f"""<h1>{WAND_ICON} Setup Wizard</h1>
<div class="subtitle">Answer a few questions and we will generate your project configuration.</div>

<div class="wizard-container" id="wizard">
  <div class="wizard-progress">
    <div class="wizard-progress-bar" id="wizard-progress-bar" style="width:20%"></div>
  </div>
  <div class="wizard-steps">

    <!-- Step 1: Use Case -->
    <div class="wizard-step active" id="step-1">
      <div class="wizard-step-number">Step 1 of 5</div>
      <h2>What type of project is this?</h2>
      <p class="wizard-desc">This determines the level of formality and document types we recommend.</p>
      <div class="wizard-options" id="wiz-usecase">
        <button type="button" class="wizard-option" data-value="personal" onclick="wizSelect(this)">
          <div class="wizard-option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
          <div class="wizard-option-title">Personal</div>
          <div class="wizard-option-desc">Solo projects, notes, personal knowledge base. Minimal governance.</div>
        </button>
        <button type="button" class="wizard-option" data-value="business" onclick="wizSelect(this)">
          <div class="wizard-option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg></div>
          <div class="wizard-option-title">Business</div>
          <div class="wizard-option-desc">Team or company projects. Standard naming, versioning, and review cycles.</div>
        </button>
        <button type="button" class="wizard-option" data-value="both" onclick="wizSelect(this)">
          <div class="wizard-option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
          <div class="wizard-option-title">Both</div>
          <div class="wizard-option-desc">Mix of personal and business docs. Moderate governance with flexibility.</div>
        </button>
      </div>
      <div class="wizard-nav">
        <span></span>
        <button type="button" class="wizard-btn wizard-btn--next" id="btn-next-1" onclick="wizNext(2)" disabled>Next</button>
      </div>
    </div>

    <!-- Step 2: Industry -->
    <div class="wizard-step" id="step-2">
      <div class="wizard-step-number">Step 2 of 5</div>
      <h2>What industry or domain?</h2>
      <p class="wizard-desc">This selects the right document templates and naming patterns for your field.</p>
      <div class="wizard-options wizard-options--grid" id="wiz-industry">
        <button type="button" class="wizard-option wizard-option--compact" data-value="software" onclick="wizSelect(this)">
          <div class="wizard-option-title">Software / Technology</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="business" onclick="wizSelect(this)">
          <div class="wizard-option-title">Business / Consulting</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="legal" onclick="wizSelect(this)">
          <div class="wizard-option-title">Legal</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="scientific" onclick="wizSelect(this)">
          <div class="wizard-option-title">Scientific / Research</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="healthcare" onclick="wizSelect(this)">
          <div class="wizard-option-title">Healthcare</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="finance" onclick="wizSelect(this)">
          <div class="wizard-option-title">Finance</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="government" onclick="wizSelect(this)">
          <div class="wizard-option-title">Government / Defense</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact" data-value="general" onclick="wizSelect(this)">
          <div class="wizard-option-title">General / Other</div>
        </button>
      </div>
      <div class="wizard-nav">
        <button type="button" class="wizard-btn" onclick="wizBack(1)">Back</button>
        <button type="button" class="wizard-btn wizard-btn--next" id="btn-next-2" onclick="wizNext(3)" disabled>Next</button>
      </div>
    </div>

    <!-- Step 3: Compliance -->
    <div class="wizard-step" id="step-3">
      <div class="wizard-step-number">Step 3 of 5</div>
      <h2>Any compliance requirements?</h2>
      <p class="wizard-desc">Select all that apply. These add required document types and metadata rules. Skip if none.</p>
      <div class="wizard-options wizard-options--grid wizard-options--multi" id="wiz-compliance">
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="hipaa" onclick="wizToggle(this)">
          <div class="wizard-option-title">HIPAA</div>
          <div class="wizard-option-desc">Healthcare Privacy</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="gdpr" onclick="wizToggle(this)">
          <div class="wizard-option-title">GDPR</div>
          <div class="wizard-option-desc">EU Data Protection</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="iso_27001" onclick="wizToggle(this)">
          <div class="wizard-option-title">ISO 27001</div>
          <div class="wizard-option-desc">Information Security</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="sox" onclick="wizToggle(this)">
          <div class="wizard-option-title">SOX</div>
          <div class="wizard-option-desc">Financial Controls</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="pci_dss" onclick="wizToggle(this)">
          <div class="wizard-option-title">PCI DSS</div>
          <div class="wizard-option-desc">Payment Cards</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="soc2" onclick="wizToggle(this)">
          <div class="wizard-option-title">SOC 2</div>
          <div class="wizard-option-desc">Trust Services</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="dod_5200" onclick="wizToggle(this)">
          <div class="wizard-option-title">DoD 5200</div>
          <div class="wizard-option-desc">Classification</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="iso_9001" onclick="wizToggle(this)">
          <div class="wizard-option-title">ISO 9001</div>
          <div class="wizard-option-desc">Quality Mgmt</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="sec_finra" onclick="wizToggle(this)">
          <div class="wizard-option-title">SEC / FINRA</div>
          <div class="wizard-option-desc">Financial Records</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="ccpa" onclick="wizToggle(this)">
          <div class="wizard-option-title">CCPA</div>
          <div class="wizard-option-desc">CA Privacy</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="nist_csf" onclick="wizToggle(this)">
          <div class="wizard-option-title">NIST CSF</div>
          <div class="wizard-option-desc">Cybersecurity</div>
        </button>
        <button type="button" class="wizard-option wizard-option--compact wizard-option--toggle" data-value="none" onclick="wizToggle(this)">
          <div class="wizard-option-title">None</div>
          <div class="wizard-option-desc">No compliance</div>
        </button>
      </div>
      <div class="wizard-nav">
        <button type="button" class="wizard-btn" onclick="wizBack(2)">Back</button>
        <button type="button" class="wizard-btn wizard-btn--next" id="btn-next-3" onclick="wizNext(4)">Next</button>
      </div>
    </div>

    <!-- Step 4: Formality -->
    <div class="wizard-step" id="step-4">
      <div class="wizard-step-number">Step 4 of 5</div>
      <h2>How formal should documents be?</h2>
      <p class="wizard-desc">This controls headers, footers, metadata requirements, and review cycles.</p>
      <div class="wizard-options" id="wiz-formality">
        <button type="button" class="wizard-option" data-value="minimal" onclick="wizSelect(this)">
          <div class="wizard-option-title">Minimal</div>
          <div class="wizard-option-desc">Just file naming and version tracking. No headers, footers, or mandatory metadata.</div>
        </button>
        <button type="button" class="wizard-option" data-value="standard" onclick="wizSelect(this)">
          <div class="wizard-option-title">Standard</div>
          <div class="wizard-option-desc">Headers with org name, version tracking, 90-day review cycle. Good default for most teams.</div>
        </button>
        <button type="button" class="wizard-option" data-value="strict" onclick="wizSelect(this)">
          <div class="wizard-option-title">Strict</div>
          <div class="wizard-option-desc">Full headers/footers, classification banners, mandatory approvals, revision history, retention policies.</div>
        </button>
      </div>
      <div class="wizard-nav">
        <button type="button" class="wizard-btn" onclick="wizBack(3)">Back</button>
        <button type="button" class="wizard-btn wizard-btn--next" id="btn-next-4" onclick="wizNext(5)" disabled>Next</button>
      </div>
    </div>

    <!-- Step 5: Details -->
    <div class="wizard-step" id="step-5">
      <div class="wizard-step-number">Step 5 of 5</div>
      <h2>A few final details</h2>
      <p class="wizard-desc">Optional — you can always change these later in Settings.</p>
      <div class="wizard-fields">
        <div class="wizard-field">
          <label for="wiz-org">Organization Name</label>
          <input type="text" id="wiz-org" placeholder="e.g. Acme Corporation">
        </div>
        <div class="wizard-field">
          <label for="wiz-author">Default Author</label>
          <input type="text" id="wiz-author" placeholder="e.g. Jane Smith">
        </div>
        <div class="wizard-field">
          <label for="wiz-project">Project Name</label>
          <input type="text" id="wiz-project" placeholder="e.g. Q4 Product Launch" value="{_esc(project_name)}">
        </div>
      </div>
      <div class="wizard-nav">
        <button type="button" class="wizard-btn" onclick="wizBack(4)">Back</button>
        <button type="button" class="wizard-btn wizard-btn--next wizard-btn--finish" onclick="wizFinish()">Generate Configuration</button>
      </div>
    </div>

    <!-- Result -->
    <div class="wizard-step" id="step-result" style="display:none">
      <div class="wizard-step-number">Done!</div>
      <h2>Your configuration is ready</h2>
      <p class="wizard-desc">Copy this YAML block into the <code>project_config</code> section of your <code>REGISTRY.yaml</code>. Or use <a href="settings.html" style="color:var(--accent)">Settings</a> to fine-tune.</p>
      <pre class="settings-yaml visible" id="wizard-yaml"></pre>
      <div class="settings-actions" style="margin-top:16px">
        <button type="button" class="settings-btn settings-btn--primary" onclick="wizCopy()">Copy to Clipboard</button>
        <button type="button" class="settings-btn" onclick="wizRestart()">Start Over</button>
        <span class="settings-copied" id="wizard-copied">Copied!</span>
      </div>
      <div style="margin-top:20px;padding:16px;background:var(--surface-alt);border-radius:var(--radius-lg);font-size:13px;line-height:1.6">
        <strong>What to do next:</strong><br>
        1. Paste this into your REGISTRY.yaml under <code>project_config:</code><br>
        2. Run <code>python -m librarian site</code> to regenerate your site<br>
        3. Use <code>python -m librarian scaffold --list</code> to see available templates<br>
        4. Visit <a href="settings.html" style="color:var(--accent)">Settings</a> to fine-tune any option
      </div>
    </div>

  </div><!-- /wizard-steps -->
</div><!-- /wizard-container -->

<script>
var wizData = {{}};

function wizSelect(btn) {{
  var group = btn.parentElement;
  group.querySelectorAll('.wizard-option').forEach(function(b) {{ b.classList.remove('selected'); }});
  btn.classList.add('selected');
  wizData[group.id] = btn.getAttribute('data-value');
  // Enable the Next button for this step
  var stepEl = btn.closest('.wizard-step');
  var nextBtn = stepEl.querySelector('.wizard-btn--next');
  if (nextBtn) nextBtn.disabled = false;
}}

function wizToggle(btn) {{
  // For compliance: "none" clears others, selecting a compliance clears "none"
  var val = btn.getAttribute('data-value');
  var group = btn.parentElement;
  if (val === 'none') {{
    group.querySelectorAll('.wizard-option').forEach(function(b) {{ b.classList.remove('selected'); }});
    btn.classList.add('selected');
  }} else {{
    group.querySelector('[data-value="none"]').classList.remove('selected');
    btn.classList.toggle('selected');
  }}
  // Collect selected values
  var selected = [];
  group.querySelectorAll('.wizard-option.selected').forEach(function(b) {{
    selected.push(b.getAttribute('data-value'));
  }});
  wizData['wiz-compliance'] = selected;
}}

function wizNext(step) {{
  document.querySelectorAll('.wizard-step').forEach(function(s) {{ s.classList.remove('active'); }});
  document.getElementById('step-' + step).classList.add('active');
  var pct = Math.min(100, step * 20);
  document.getElementById('wizard-progress-bar').style.width = pct + '%';
}}

function wizBack(step) {{
  document.querySelectorAll('.wizard-step').forEach(function(s) {{ s.classList.remove('active'); }});
  document.getElementById('step-' + step).classList.add('active');
  var pct = Math.min(100, step * 20);
  document.getElementById('wizard-progress-bar').style.width = pct + '%';
}}

function wizFinish() {{
  var useCase = wizData['wiz-usecase'] || 'personal';
  var industry = wizData['wiz-industry'] || 'general';
  var compliance = wizData['wiz-compliance'] || [];
  var formality = wizData['wiz-formality'] || 'standard';
  var org = document.getElementById('wiz-org').value;
  var author = document.getElementById('wiz-author').value;
  var project = document.getElementById('wiz-project').value;

  // Map industry to preset
  var presetMap = {{
    'software': 'software', 'business': 'business', 'legal': 'legal',
    'scientific': 'scientific', 'healthcare': 'healthcare',
    'finance': 'finance', 'government': 'government', 'general': 'software'
  }};
  var preset = presetMap[industry] || 'software';

  // Map formality to naming template + governance settings
  var formalityMap = {{
    'minimal': {{ template: 'default', cycle: 0, retention: 0, hdr: false, ftr: false, strict: false,
                  metaOwner: false, metaApprover: false, metaReview: false, metaDist: false, metaRev: false }},
    'standard': {{ template: 'default', cycle: 90, retention: 0, hdr: true, ftr: false, strict: false,
                   metaOwner: true, metaApprover: false, metaReview: true, metaDist: false, metaRev: false }},
    'strict': {{ template: 'default', cycle: 365, retention: 2190, hdr: true, ftr: true, strict: true,
                 metaOwner: true, metaApprover: true, metaReview: true, metaDist: true, metaRev: true }}
  }};
  var fm = formalityMap[formality] || formalityMap['standard'];

  // Industry-specific naming template overrides
  if (industry === 'legal') fm.template = 'legal';
  else if (industry === 'scientific') fm.template = 'scientific';
  else if (industry === 'healthcare') fm.template = 'healthcare';
  else if (industry === 'finance') fm.template = 'finance';
  else if (industry === 'government') fm.template = 'corporate';

  function yq(v) {{
    var s = String(v);
    if (/[:\\#\\[\\]\\{{\\}},&*?|\\-<>=!%@'"]/.test(s) || s !== s.trim() || s === '') {{
      return "'" + s.replace(/'/g, "''") + "'";
    }}
    return s;
  }}

  var yaml = 'project_config:\\n';
  yaml += '  preset: ' + preset + '\\n';
  if (project) yaml += '  project_name: ' + yq(project) + '\\n';
  yaml += '  naming_rules:\\n';
  yaml += '    template: ' + fm.template + '\\n';
  if (author) yaml += '  default_author: ' + yq(author) + '\\n';
  if (fm.strict) yaml += '  categories:\\n    strict_mode: true\\n';

  // Compliance
  var compFiltered = compliance.filter(function(c) {{ return c !== 'none'; }});
  if (compFiltered.length) {{
    yaml += '  compliance_standards:\\n';
    compFiltered.forEach(function(c) {{ yaml += '    - ' + c + '\\n'; }});
  }}

  // Header
  if (fm.hdr) {{
    yaml += '  document_header:\\n';
    yaml += '    enabled: true\\n';
    if (org) yaml += '    organization: ' + yq(org) + '\\n';
    yaml += '    show_version: true\\n';
    yaml += '    show_date: true\\n';
    yaml += '    show_status: true\\n';
  }}

  // Footer
  if (fm.ftr) {{
    yaml += '  document_footer:\\n';
    yaml += '    enabled: true\\n';
  }}

  // Metadata
  if (fm.metaOwner || fm.metaApprover || fm.metaReview || fm.cycle || fm.retention) {{
    yaml += '  document_metadata:\\n';
    if (fm.metaOwner) yaml += '    require_owner: true\\n';
    if (fm.metaApprover) yaml += '    require_approver: true\\n';
    if (fm.metaReview) yaml += '    require_review_date: true\\n';
    if (fm.metaDist) yaml += '    require_distribution_list: true\\n';
    if (fm.metaRev) yaml += '    require_revision_history: true\\n';
    if (fm.cycle) yaml += '    review_cycle_days: ' + fm.cycle + '\\n';
    if (fm.retention) yaml += '    retention_period_days: ' + fm.retention + '\\n';
  }}

  document.getElementById('wizard-yaml').textContent = yaml;
  document.querySelectorAll('.wizard-step').forEach(function(s) {{ s.classList.remove('active'); s.style.display = 'none'; }});
  var result = document.getElementById('step-result');
  result.style.display = '';
  result.classList.add('active');
  document.getElementById('wizard-progress-bar').style.width = '100%';
}}

function wizCopy() {{
  var text = document.getElementById('wizard-yaml').textContent;
  navigator.clipboard.writeText(text).then(function() {{
    var msg = document.getElementById('wizard-copied');
    msg.classList.add('show');
    setTimeout(function() {{ msg.classList.remove('show'); }}, 1500);
  }});
}}

function wizRestart() {{
  wizData = {{}};
  document.querySelectorAll('.wizard-step').forEach(function(s) {{
    s.style.display = '';
    s.classList.remove('active');
    s.querySelectorAll('.wizard-option').forEach(function(b) {{ b.classList.remove('selected'); }});
    var nextBtn = s.querySelector('.wizard-btn--next');
    if (nextBtn) nextBtn.disabled = true;
  }});
  document.getElementById('step-result').style.display = 'none';
  document.getElementById('step-1').classList.add('active');
  document.getElementById('wizard-progress-bar').style.width = '20%';
  document.getElementById('btn-next-3').disabled = false; // compliance is optional
}}
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")
    return _page(
        "Setup Wizard",
        body,
        "wizard",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
        sidebar=sidebar,
    )


def _build_audit_page(manifest: "Manifest") -> str:
    """Build the Audit & Verify page (audit.html).

    Shows a unified view of document governance health:
    1. OODA audit results (unregistered, missing, naming violations, cross-refs)
    2. File integrity table (SHA-256 hashes, exists/missing, size)
    3. Operation log (recent activity from the hash-chained oplog)
    4. Manifest seal and verification status
    5. CLI commands for deeper forensics
    """
    from .audit import audit as run_audit
    from .oplog import verify_chain
    from .recommend import generate_recommendations

    snapshot = manifest.registry_snapshot
    config = snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")
    documents = snapshot.get("documents", [])
    repo_root = manifest.repo_root or "."

    # --- Run audit ---
    from .registry import Registry
    registry_path = manifest.registry_path or "docs/REGISTRY.yaml"
    try:
        registry = Registry.load(registry_path)
        report = run_audit(registry, repo_root)
    except Exception:
        report = None

    # --- File integrity data ---
    file_data: list[dict[str, Any]] = []
    for h in sorted(manifest.file_hashes, key=lambda x: x.filename):
        file_data.append({
            "filename": h.filename,
            "sha256": h.sha256,
            "size": h.size_bytes,
            "exists": h.exists,
        })
    file_json = _json_safe(file_data, indent=None)

    # --- Oplog data ---
    log_path = Path(repo_root) / "operator" / "librarian-audit.jsonl"
    if not log_path.exists():
        # Try docs/.librarian.log as fallback
        log_path = Path(repo_root) / "docs" / ".librarian.log"

    oplog_entries: list[dict[str, Any]] = []
    if log_path.exists():
        try:
            from .oplog import OpLogEntry
            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            for line in lines[-20:]:  # last 20 entries
                try:
                    entry = OpLogEntry.from_json_line(line.strip())
                    oplog_entries.append({
                        "ts": entry.timestamp,
                        "op": entry.operation,
                        "actor": entry.actor,
                        "files": entry.files[:3],  # limit for display
                        "commit": entry.commit_hash[:8] if entry.commit_hash else "",
                        "chained": bool(entry.prev_hash),
                    })
                except Exception:
                    pass
        except Exception:
            pass
    oplog_json = _json_safe(list(reversed(oplog_entries)), indent=None)

    # --- Chain verification ---
    chain_result = {"valid": True, "total_entries": 0, "chained_entries": 0, "error": ""}
    if log_path.exists():
        try:
            chain_result = verify_chain(log_path)
        except Exception:
            chain_result["error"] = "verification failed"

    chain_json = _json_safe(chain_result, indent=None)

    # --- Audit findings as JSON ---
    audit_data: dict[str, Any] = {
        "files_on_disk": len(report.on_disk) if report else 0,
        "registered": len(report.registered) if report else len(documents),
        "unregistered": list(report.unregistered) if report else [],
        "missing": list(report.missing) if report else [],
        "naming_violations": [
            {"file": f, "errors": errs}
            for f, errs in (report.naming_violations if report else [])
        ],
        "pending_cross_refs": list(report.pending_cross_refs) if report else [],
        "folder_suggestions": [
            {"group": s.group_name, "count": s.count, "suggestion": s.suggestion}
            for s in (report.folder_suggestions if report else [])
        ],
        "overdue_reviews": [
            r.to_dict() for r in (report.overdue_reviews if report else [])
        ],
        "oplog_locked": (report.oplog_locked if report else None),
        "oplog_path": (report.oplog_path if report else ""),
        "clean": report.clean if report else True,
    }
    audit_json = _json_safe(audit_data, indent=None)

    # --- Recommendations ---
    rec_data: list[dict[str, Any]] = []
    try:
        recs = generate_recommendations(registry)
        for r in recs:
            rec_data.append(r.to_dict())
    except Exception:
        pass
    rec_json = _json_safe(rec_data, indent=None)

    # --- Seal info ---
    seal = manifest.manifest_sha256 or "N/A"
    generated_at = manifest.generated_at or "N/A"

    # --- Status summary for KPI cards ---
    n_ok = sum(1 for h in manifest.file_hashes if h.exists)
    n_miss = sum(1 for h in manifest.file_hashes if not h.exists)
    n_unreg = len(audit_data["unregistered"])
    n_violations = len(audit_data["naming_violations"])
    n_pending = len(audit_data["pending_cross_refs"])
    n_overdue = len(audit_data["overdue_reviews"])
    oplog_locked_val = audit_data.get("oplog_locked")
    chain_ok = chain_result.get("valid", True)
    _check = "\u2713"
    _cross = "\u2717"
    _dash = "\u2013"
    chain_icon = _check if chain_ok else _cross
    if oplog_locked_val is True:
        oplog_icon = _check
        oplog_cls = "kpi-ok"
    elif oplog_locked_val is False:
        oplog_icon = _cross
        oplog_cls = "kpi-warn"
    else:
        oplog_icon = _dash
        oplog_cls = "kpi-ok"  # undetectable -> don't alarm

    body = f"""<h1>Audit &amp; Verify</h1>
<div class="subtitle">Document governance health report &mdash; generated {_esc(generated_at)}</div>

<!-- KPI Cards -->
<div class="kpi-row" style="margin-bottom:24px">
  <div class="kpi-card">
    <div class="kpi-value {'kpi-ok' if n_unreg == 0 else 'kpi-warn'}">{audit_data['registered']}</div>
    <div class="kpi-label">Registered</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value {'kpi-ok' if n_unreg == 0 else 'kpi-warn'}">{n_unreg}</div>
    <div class="kpi-label">Unregistered</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value {'kpi-ok' if n_miss == 0 else 'kpi-err'}">{n_miss}</div>
    <div class="kpi-label">Missing</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value {'kpi-ok' if n_violations == 0 else 'kpi-warn'}">{n_violations}</div>
    <div class="kpi-label">Naming Issues</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value {'kpi-ok' if n_overdue == 0 else 'kpi-warn'}">{n_overdue}</div>
    <div class="kpi-label">Overdue Reviews</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value {oplog_cls}">{oplog_icon}</div>
    <div class="kpi-label">Oplog Lock</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value {'kpi-ok' if chain_ok else 'kpi-err'}">{chain_icon}</div>
    <div class="kpi-label">Chain Integrity</div>
  </div>
</div>

<div class="audit-sections">

  <!-- Section 1: OODA Audit -->
  <div class="aud-section" id="aud-ooda">
    <div class="aud-section-header" onclick="toggleAudSection('aud-ooda')">
      <h2>OODA Audit</h2>
      <span class="aud-status {'aud-pass' if audit_data['clean'] else 'aud-fail'}">
        {"PASS" if audit_data['clean'] else "FINDINGS"}
      </span>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="aud-section-body">
      <div id="ooda-results"></div>
    </div>
  </div>

  <!-- Section 2: File Integrity -->
  <div class="aud-section" id="aud-integrity">
    <div class="aud-section-header" onclick="toggleAudSection('aud-integrity')">
      <h2>File Integrity</h2>
      <span class="aud-status {'aud-pass' if n_miss == 0 else 'aud-fail'}">
        {n_ok}/{len(manifest.file_hashes)} verified
      </span>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="aud-section-body">
      <div class="aud-controls">
        <input type="text" id="integrity-search" placeholder="Filter files..." oninput="filterIntegrity()">
        <label class="aud-toggle"><input type="checkbox" id="show-hashes" onchange="toggleHashes()"> Show full hashes</label>
      </div>
      <div id="integrity-table"></div>
    </div>
  </div>

  <!-- Section 3: Operation Log -->
  <div class="aud-section" id="aud-oplog">
    <div class="aud-section-header" onclick="toggleAudSection('aud-oplog')">
      <h2>Operation Log</h2>
      <span class="aud-status aud-info">{len(oplog_entries)} entries</span>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="aud-section-body">
      <div id="oplog-table"></div>
      <div class="aud-chain-status" id="chain-status"></div>
    </div>
  </div>

  <!-- Section 4: Manifest Seal -->
  <div class="aud-section" id="aud-seal">
    <div class="aud-section-header" onclick="toggleAudSection('aud-seal')">
      <h2>Manifest Seal</h2>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="aud-section-body">
      <div class="aud-seal-box">
        <div class="aud-seal-row">
          <span class="aud-seal-label">SHA-256 Seal</span>
          <code class="aud-seal-value" id="seal-full">{_esc(seal)}</code>
          <button class="mgr-btn mgr-btn--sm" onclick="copyText(document.getElementById('seal-full').textContent)">Copy</button>
        </div>
        <div class="aud-seal-row">
          <span class="aud-seal-label">Generated</span>
          <span>{_esc(generated_at)}</span>
        </div>
        <div class="aud-seal-row">
          <span class="aud-seal-label">Files Hashed</span>
          <span>{len(manifest.file_hashes)}</span>
        </div>
        <div class="aud-seal-row">
          <span class="aud-seal-label">Edges</span>
          <span>{manifest.total_edges}</span>
        </div>
        <p class="aud-seal-explain">
          The seal is a SHA-256 hash computed from the sorted <code>filename:sha256</code> pairs
          of every governed file. If any file is added, removed, or modified, this seal changes &mdash;
          making the manifest tamper-evident.
        </p>
      </div>
    </div>
  </div>

  <!-- Section 5: Recommendations -->
  <div class="aud-section" id="aud-recs">
    <div class="aud-section-header" onclick="toggleAudSection('aud-recs')">
      <h2>Recommendations</h2>
      <span class="aud-status aud-info" id="rec-count">0</span>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="aud-section-body">
      <div id="rec-results"></div>
    </div>
  </div>

  <!-- Section 6: CLI Commands -->
  <div class="aud-section" id="aud-cli">
    <div class="aud-section-header" onclick="toggleAudSection('aud-cli')">
      <h2>CLI Commands</h2>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="aud-section-body">
      <div class="aud-cli-grid">
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Run Full Audit</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml audit --recommend</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Export Audit as JSON</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml audit --recommend --json</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Generate Manifest</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml manifest -o manifest.json</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Generate Evidence Pack</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml evidence -o evidence.json</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Diff Two Manifests</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml diff old.json new.json</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">View Operation Log</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml log --last 20</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">List Overdue Reviews</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml review list --overdue</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Oplog Lock Status</div>
          <code>python -m librarian --registry docs/REGISTRY.yaml oplog status</code>
        </div>
        <div class="aud-cli-card" onclick="copyText(this.querySelector('code').textContent)">
          <div class="aud-cli-title">Enable Oplog Lock</div>
          <code>scripts/librarian-oplog-lock-20260414-V1.0.sh lock</code>
        </div>
      </div>
      <p class="aud-cli-hint">Click any card to copy the command.</p>
    </div>
  </div>

</div>

<script>
var AUDIT = {audit_json};
var FILES = {file_json};
var OPLOG = {oplog_json};
var CHAIN = {chain_json};
var RECS = {rec_json};

function toggleAudSection(id) {{
  document.getElementById(id).classList.toggle('collapsed');
}}

function copyText(text) {{
  if (navigator.clipboard) {{
    navigator.clipboard.writeText(text);
  }}
}}

// --- OODA Results ---
(function() {{
  var el = document.getElementById('ooda-results');
  var html = '';

  if (AUDIT.clean) {{
    html += '<div class="aud-ok-banner">\\u2713 All checks passed &mdash; no findings.</div>';
  }}

  if (AUDIT.unregistered.length) {{
    html += '<div class="aud-finding"><h3 class="aud-finding-title aud-finding--warn">Unregistered Files (' + AUDIT.unregistered.length + ')</h3>';
    html += '<p class="aud-finding-hint">Files on disk not in the registry. Use <a href="manage.html">Project Manager</a> to register them.</p>';
    html += '<ul class="aud-finding-list">';
    AUDIT.unregistered.forEach(function(f) {{ html += '<li><code>' + f + '</code></li>'; }});
    html += '</ul></div>';
  }}

  if (AUDIT.missing.length) {{
    html += '<div class="aud-finding"><h3 class="aud-finding-title aud-finding--err">Missing Files (' + AUDIT.missing.length + ')</h3>';
    html += '<p class="aud-finding-hint">Registered in REGISTRY.yaml but not found on disk.</p>';
    html += '<ul class="aud-finding-list">';
    AUDIT.missing.forEach(function(f) {{ html += '<li><code>' + f + '</code></li>'; }});
    html += '</ul></div>';
  }}

  if (AUDIT.naming_violations.length) {{
    html += '<div class="aud-finding"><h3 class="aud-finding-title aud-finding--warn">Naming Violations (' + AUDIT.naming_violations.length + ')</h3>';
    html += '<ul class="aud-finding-list">';
    AUDIT.naming_violations.forEach(function(v) {{
      html += '<li><code>' + v.file + '</code> &mdash; ' + v.errors.join('; ') + '</li>';
    }});
    html += '</ul></div>';
  }}

  if (AUDIT.pending_cross_refs.length) {{
    html += '<div class="aud-finding"><h3 class="aud-finding-title aud-finding--info">Pending Cross-References (' + AUDIT.pending_cross_refs.length + ')</h3>';
    html += '<ul class="aud-finding-list">';
    AUDIT.pending_cross_refs.forEach(function(r) {{ html += '<li><code>' + r + '</code></li>'; }});
    html += '</ul></div>';
  }}

  if (AUDIT.folder_suggestions.length) {{
    html += '<div class="aud-finding"><h3 class="aud-finding-title aud-finding--info">Folder Suggestions</h3>';
    html += '<ul class="aud-finding-list">';
    AUDIT.folder_suggestions.forEach(function(s) {{
      html += '<li><strong>' + s.group + '</strong> (' + s.count + ' files) &mdash; ' + s.suggestion + '</li>';
    }});
    html += '</ul></div>';
  }}

  if (AUDIT.overdue_reviews && AUDIT.overdue_reviews.length) {{
    html += '<div class="aud-finding"><h3 class="aud-finding-title aud-finding--warn">Overdue Reviews (' + AUDIT.overdue_reviews.length + ')</h3>';
    html += '<p class="aud-finding-hint">Documents whose <code>next_review</code> deadline has passed. Update via <code>librarian review set &lt;file&gt; --by YYYY-MM-DD</code>.</p>';
    html += '<table class="mgr-table"><thead><tr><th>Filename</th><th>Deadline</th><th style="text-align:right">Days Overdue</th></tr></thead><tbody>';
    AUDIT.overdue_reviews.forEach(function(r) {{
      html += '<tr><td class="mgr-filename">' + r.filename + '</td>';
      html += '<td style="font-family:var(--mono);font-size:11px">' + r.next_review + '</td>';
      html += '<td style="text-align:right;color:#92400e;font-weight:600">' + r.days_overdue + '</td></tr>';
    }});
    html += '</tbody></table></div>';
  }}

  if (!html) html = '<div class="aud-ok-banner">\\u2713 All checks passed.</div>';
  el.innerHTML = html;
}})();

// --- File Integrity Table ---
var showFull = false;
function renderIntegrity(filter) {{
  var el = document.getElementById('integrity-table');
  var q = (filter || '').toLowerCase();
  var html = '<table class="mgr-table"><thead><tr>';
  html += '<th style="width:24px"></th><th>Filename</th><th>SHA-256</th><th style="text-align:right">Size</th>';
  html += '</tr></thead><tbody>';
  var shown = 0;
  FILES.forEach(function(f) {{
    if (q && f.filename.toLowerCase().indexOf(q) < 0) return;
    var icon = f.exists ? '<span class="aud-dot aud-dot--ok">\\u2713</span>' : '<span class="aud-dot aud-dot--err">\\u2717</span>';
    var hash = showFull ? f.sha256 : f.sha256.substring(0, 16) + '...';
    var size = f.size > 1024 ? (f.size / 1024).toFixed(1) + ' KB' : f.size + ' B';
    html += '<tr' + (f.exists ? '' : ' class="aud-row--err"') + '>';
    html += '<td>' + icon + '</td>';
    html += '<td class="mgr-filename">' + f.filename + '</td>';
    html += '<td class="aud-hash" title="' + f.sha256 + '">' + hash + '</td>';
    html += '<td style="text-align:right;font-family:var(--mono);font-size:11px">' + size + '</td>';
    html += '</tr>';
    shown++;
  }});
  html += '</tbody></table>';
  if (shown === 0) html += '<div style="padding:16px;text-align:center;color:var(--text-muted)">No files match filter.</div>';
  el.innerHTML = html;
}}
function filterIntegrity() {{
  renderIntegrity(document.getElementById('integrity-search').value);
}}
function toggleHashes() {{
  showFull = document.getElementById('show-hashes').checked;
  filterIntegrity();
}}
renderIntegrity();

// --- Operation Log ---
(function() {{
  var el = document.getElementById('oplog-table');
  if (OPLOG.length === 0) {{
    el.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-style:italic">No operation log entries found.</div>';
    return;
  }}
  var html = '<table class="mgr-table"><thead><tr>';
  html += '<th>Timestamp</th><th>Operation</th><th>Actor</th><th>Files</th><th>Commit</th><th style="width:20px">\\u26d3</th>';
  html += '</tr></thead><tbody>';
  OPLOG.forEach(function(e) {{
    html += '<tr>';
    html += '<td style="font-family:var(--mono);font-size:11px;white-space:nowrap">' + e.ts + '</td>';
    html += '<td><span class="aud-op-badge aud-op--' + e.op + '">' + e.op + '</span></td>';
    html += '<td style="font-size:12px">' + e.actor + '</td>';
    html += '<td style="font-size:11px;font-family:var(--mono)">' + (e.files.length ? e.files.join(', ') : '&mdash;') + '</td>';
    html += '<td style="font-family:var(--mono);font-size:11px">' + (e.commit || '&mdash;') + '</td>';
    html += '<td style="text-align:center">' + (e.chained ? '\\u26d3' : '') + '</td>';
    html += '</tr>';
  }});
  html += '</tbody></table>';
  el.innerHTML = html;

  // Chain status
  var cs = document.getElementById('chain-status');
  if (CHAIN.total_entries === 0) {{
    cs.innerHTML = '<span class="aud-chain-info">No log entries to verify.</span>';
  }} else if (CHAIN.valid) {{
    cs.innerHTML = '<span class="aud-chain-ok">\\u2713 Hash chain intact &mdash; ' + CHAIN.chained_entries + '/' + CHAIN.total_entries + ' entries chained.</span>';
  }} else {{
    cs.innerHTML = '<span class="aud-chain-broken">\\u2717 Chain broken: ' + CHAIN.error + '</span>';
  }}
}})();

// --- Recommendations ---
(function() {{
  var el = document.getElementById('rec-results');
  var badge = document.getElementById('rec-count');
  badge.textContent = RECS.length;

  if (RECS.length === 0) {{
    el.innerHTML = '<div class="aud-ok-banner">No recommendations &mdash; project is well-covered.</div>';
    return;
  }}

  // Group by category
  var groups = {{}};
  var order = ['core', 'recommended', 'cross_ref', 'maturity', 'compliance'];
  var labels = {{core: 'Core Templates', recommended: 'Recommended', cross_ref: 'Cross-Reference Gaps', maturity: 'Maturity Progression', compliance: 'Compliance'}};
  RECS.forEach(function(r) {{
    var cat = r.category || 'other';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(r);
  }});

  var html = '';
  order.forEach(function(cat) {{
    if (!groups[cat]) return;
    html += '<div class="aud-rec-group">';
    html += '<h3 class="aud-rec-cat">' + (labels[cat] || cat) + ' (' + groups[cat].length + ')</h3>';
    html += '<ul class="aud-finding-list">';
    groups[cat].forEach(function(r) {{
      html += '<li><code>' + r.template_id + '</code> &mdash; ' + r.reason + '</li>';
    }});
    html += '</ul></div>';
  }});
  el.innerHTML = html;
}})();
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Audit",
        body,
        "audit",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
        sidebar=sidebar,
    )


def _build_manage_page(manifest: "Manifest") -> str:
    """Build the Project Manager page (manage.html).

    Provides four client-side tools for managing project documents:
    1. Unregistered Files — files on disk not yet in the registry
    2. Register Existing File — manual form for any file
    3. Create Folder — generate mkdir commands for new directories
    4. Scaffold from Template — generate scaffold CLI commands
    """
    from .templates import discover_templates, CROSS_CUTTING

    snapshot = manifest.registry_snapshot
    config = snapshot.get("project_config", {})
    project_name = config.get("project_name", "Librarian")
    active_preset = config.get("preset", "")
    documents = snapshot.get("documents", [])
    custom_dir = config.get("custom_templates_dir", None)

    # Compute unregistered files from manifest data
    registered_names = {d.get("filename", "") for d in documents}
    exempt = set(config.get("infrastructure_exempt", [
        "REGISTRY.yaml", "README.md", "CLAUDE.md", ".gitignore",
    ]))
    on_disk = {h.filename for h in manifest.file_hashes if h.exists}
    unregistered = sorted(on_disk - registered_names - exempt)
    unreg_json = _json_safe(unregistered, indent=None)

    # Existing folders for reference
    folders = set()
    for doc in documents:
        p = doc.get("path", "")
        if "/" in p:
            folders.add("/".join(p.split("/")[:-1]))
    for h in manifest.file_hashes:
        if "/" in h.filename:
            folders.add("/".join(h.filename.split("/")[:-1]))
    folder_list = sorted(folders)
    folder_json = _json_safe(folder_list, indent=None)

    # Template data for scaffold section
    all_presets = [
        "software", "business", "legal", "scientific",
        "healthcare", "finance", "government",
    ]
    tmpl_data: list[dict[str, Any]] = []
    for preset in all_presets:
        for t in discover_templates(preset, custom_dir).values():
            # Deduplicate by template_id
            if not any(x["id"] == t.template_id for x in tmpl_data):
                tmpl_data.append({
                    "id": t.template_id,
                    "name": t.display_name,
                    "source": t.preset or preset,
                    "presets": [preset],
                })
            else:
                existing = next(x for x in tmpl_data if x["id"] == t.template_id)
                if preset not in existing["presets"]:
                    existing["presets"].append(preset)
    tmpl_json = _json_safe(tmpl_data, indent=None)

    # Existing tags for autocomplete
    all_tags = set()
    for doc in documents:
        for tag in doc.get("tags", []):
            all_tags.add(tag)
    tags_json = _json_safe(sorted(all_tags), indent=None)

    # Status options
    statuses = ["active", "draft", "superseded", "archived"]

    body = f"""<h1>Project Manager</h1>
<div class="subtitle">Add files, create folders, and scaffold new documents</div>

<div class="mgr-sections">

  <!-- Section 1: Unregistered Files -->
  <div class="mgr-section" id="mgr-unreg">
    <div class="mgr-section-header" onclick="toggleMgrSection('mgr-unreg')">
      <span class="mgr-section-icon">&#9679;</span>
      <h2>Unregistered Files</h2>
      <span class="mgr-badge" id="unreg-count">{len(unregistered)}</span>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="mgr-section-body">
      <p class="mgr-hint">Files found on disk but not yet registered. Click a file to register it.</p>
      <div id="unreg-list"></div>
      <div id="unreg-empty" style="display:none;padding:20px;text-align:center;color:var(--text-muted);font-style:italic">
        All files are registered. Nothing to do here.
      </div>
    </div>
  </div>

  <!-- Section 2: Register Existing File -->
  <div class="mgr-section" id="mgr-register">
    <div class="mgr-section-header" onclick="toggleMgrSection('mgr-register')">
      <span class="mgr-section-icon">&#43;</span>
      <h2>Register Existing File</h2>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="mgr-section-body">
      <p class="mgr-hint">Manually register a file that already exists on disk.</p>
      <div class="mgr-form">
        <div class="mgr-row">
          <label>Filename</label>
          <input type="text" id="reg-filename" placeholder="e.g. design-spec-20260413-V1.0.md">
        </div>
        <div class="mgr-row">
          <label>Path (relative)</label>
          <input type="text" id="reg-path" placeholder="e.g. docs/design-spec-20260413-V1.0.md" list="reg-path-list">
          <datalist id="reg-path-list"></datalist>
        </div>
        <div class="mgr-row">
          <label>Status</label>
          <select id="reg-status">
            {"".join(f'<option value="{s}">{_esc(s.title())}</option>' for s in statuses)}
          </select>
        </div>
        <div class="mgr-row">
          <label>Description</label>
          <input type="text" id="reg-desc" placeholder="Brief description of the document">
        </div>
        <div class="mgr-row">
          <label>Tags</label>
          <input type="text" id="reg-tags" placeholder="Comma-separated: governance, phase-a" list="reg-tags-list">
          <datalist id="reg-tags-list"></datalist>
        </div>
        <div class="mgr-row mgr-row-btn">
          <button type="button" class="mgr-btn mgr-btn--primary" onclick="generateRegister()">Generate Command</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Section 3: Create Folder -->
  <div class="mgr-section" id="mgr-folder">
    <div class="mgr-section-header" onclick="toggleMgrSection('mgr-folder')">
      <span class="mgr-section-icon">&#128193;</span>
      <h2>Create Folder</h2>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="mgr-section-body">
      <p class="mgr-hint">Define new directories for your project structure.</p>
      <div class="mgr-form">
        <div class="mgr-row">
          <label>Folder Path</label>
          <input type="text" id="folder-path" placeholder="e.g. docs/security" list="folder-path-list">
          <datalist id="folder-path-list"></datalist>
        </div>
        <div class="mgr-row mgr-row-btn">
          <button type="button" class="mgr-btn mgr-btn--primary" onclick="generateMkdir()">Generate Command</button>
        </div>
        <div class="mgr-existing-folders" id="existing-folders"></div>
      </div>
    </div>
  </div>

  <!-- Section 4: Scaffold from Template -->
  <div class="mgr-section" id="mgr-scaffold">
    <div class="mgr-section-header" onclick="toggleMgrSection('mgr-scaffold')">
      <span class="mgr-section-icon">&#128196;</span>
      <h2>Scaffold from Template</h2>
      <span class="mgr-chevron">&#9660;</span>
    </div>
    <div class="mgr-section-body">
      <p class="mgr-hint">Create a new document from a template with proper naming, registration, and cross-references.</p>
      <div class="mgr-form">
        <div class="mgr-row">
          <label>Preset</label>
          <select id="scaf-preset" onchange="updateTemplateList()">
            {"".join(f'<option value="{_esc(p)}"{"selected" if p == active_preset else ""}>{_esc(p.title())}</option>' for p in all_presets)}
          </select>
        </div>
        <div class="mgr-row">
          <label>Template</label>
          <select id="scaf-template" onchange="updateScaffoldPreview()">
            <option value="">— select template —</option>
          </select>
        </div>
        <div class="mgr-row">
          <label>Title</label>
          <input type="text" id="scaf-title" placeholder="e.g. Q2 Security Assessment" oninput="updateScaffoldPreview()">
        </div>
        <div class="mgr-row">
          <label>Folder</label>
          <input type="text" id="scaf-folder" placeholder="e.g. docs/" value="docs/" list="scaf-folder-list">
          <datalist id="scaf-folder-list"></datalist>
        </div>
        <div class="mgr-row">
          <label>Author</label>
          <input type="text" id="scaf-author" placeholder="Optional author name">
        </div>
        <div id="scaf-preview" class="mgr-preview" style="display:none"></div>
        <div class="mgr-row mgr-row-btn">
          <button type="button" class="mgr-btn mgr-btn--primary" onclick="generateScaffold()">Generate Command</button>
          <button type="button" class="mgr-btn" onclick="generateScaffold(true)">Dry Run (preview only)</button>
        </div>
      </div>
    </div>
  </div>

</div>

<!-- Command Output Panel -->
<div id="mgr-output" class="mgr-output" style="display:none">
  <div class="mgr-output-header">
    <h3>Command</h3>
    <button type="button" class="mgr-btn mgr-btn--sm" onclick="copyCommand()">Copy</button>
    <button type="button" class="mgr-btn mgr-btn--sm" onclick="closeMgrOutput()">Close</button>
  </div>
  <pre id="mgr-output-cmd"></pre>
  <p class="mgr-output-hint">Paste this command into your terminal to execute.</p>
</div>

<script>
var UNREG = {unreg_json};
var FOLDERS = {folder_json};
var TEMPLATES = {tmpl_json};
var ALL_TAGS = {tags_json};

// Populate datalists
(function() {{
  var tagList = document.getElementById('reg-tags-list');
  ALL_TAGS.forEach(function(t) {{
    var o = document.createElement('option');
    o.value = t;
    tagList.appendChild(o);
  }});
  ['reg-path-list', 'folder-path-list', 'scaf-folder-list'].forEach(function(id) {{
    var dl = document.getElementById(id);
    FOLDERS.forEach(function(f) {{
      var o = document.createElement('option');
      o.value = f + '/';
      dl.appendChild(o);
    }});
  }});
}})();

// Section toggle
function toggleMgrSection(id) {{
  var el = document.getElementById(id);
  el.classList.toggle('collapsed');
}}

// --- Unregistered Files ---
function renderUnreg() {{
  var list = document.getElementById('unreg-list');
  var empty = document.getElementById('unreg-empty');
  if (UNREG.length === 0) {{
    list.style.display = 'none';
    empty.style.display = '';
    return;
  }}
  var html = '<table class="mgr-table"><thead><tr><th>Filename</th><th>Action</th></tr></thead><tbody>';
  for (var i = 0; i < UNREG.length; i++) {{
    var fn = UNREG[i];
    var safe = fn.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
    html += '<tr id="unreg-row-' + i + '">';
    html += '<td class="mgr-filename">' + safe + '</td>';
    html += '<td><button class="mgr-btn mgr-btn--sm mgr-btn--primary" onclick="quickRegister(' + i + ')">Register</button></td>';
    html += '</tr>';
  }}
  html += '</tbody></table>';
  list.innerHTML = html;
}}
renderUnreg();

function quickRegister(idx) {{
  var fn = UNREG[idx];
  // Pre-fill the register form
  document.getElementById('reg-filename').value = fn;
  // Guess path from filename
  document.getElementById('reg-path').value = fn;
  document.getElementById('reg-status').value = 'active';
  document.getElementById('reg-desc').value = '';
  document.getElementById('reg-tags').value = '';
  // Open register section, scroll to it
  var sect = document.getElementById('mgr-register');
  sect.classList.remove('collapsed');
  sect.scrollIntoView({{behavior: 'smooth', block: 'start'}});
  document.getElementById('reg-filename').focus();
}}

// --- Register Existing File ---
function generateRegister() {{
  var fn = document.getElementById('reg-filename').value.trim();
  if (!fn) {{ alert('Filename is required'); return; }}
  var path = document.getElementById('reg-path').value.trim() || fn;
  var status = document.getElementById('reg-status').value;
  var desc = document.getElementById('reg-desc').value.trim();
  var tags = document.getElementById('reg-tags').value.trim();

  var cmd = 'python -m librarian --registry docs/REGISTRY.yaml register';
  cmd += ' --filename ' + shellQuote(fn);
  cmd += ' --path ' + shellQuote(path);
  cmd += ' --status ' + status;
  if (desc) cmd += ' --description ' + shellQuote(desc);
  if (tags) {{
    tags.split(',').forEach(function(t) {{
      t = t.trim();
      if (t) cmd += ' --tag ' + shellQuote(t);
    }});
  }}
  showCommand(cmd);
}}

// --- Create Folder ---
function generateMkdir() {{
  var path = document.getElementById('folder-path').value.trim();
  if (!path) {{ alert('Folder path is required'); return; }}
  // Sanitize: no .., no leading /
  path = path.replace(/\\.\\./g, '').replace(/^\\/+/, '');
  var cmd = 'mkdir -p ' + shellQuote(path);
  showCommand(cmd);
}}

// Render existing folders
(function() {{
  var el = document.getElementById('existing-folders');
  if (FOLDERS.length === 0) {{ el.style.display = 'none'; return; }}
  var html = '<div class="mgr-folder-ref"><strong>Existing folders:</strong> ';
  html += FOLDERS.map(function(f) {{
    return '<code>' + f.replace(/</g, '&lt;') + '/</code>';
  }}).join(' ');
  html += '</div>';
  el.innerHTML = html;
}})();

// --- Scaffold from Template ---
function updateTemplateList() {{
  var preset = document.getElementById('scaf-preset').value;
  var sel = document.getElementById('scaf-template');
  var prev = sel.value;
  sel.innerHTML = '<option value="">\\u2014 select template \\u2014</option>';

  // Group by source
  var groups = {{}};
  TEMPLATES.forEach(function(t) {{
    if (t.presets.indexOf(preset) < 0) return;
    var src = t.source;
    if (!groups[src]) groups[src] = [];
    groups[src].push(t);
  }});

  var order = ['universal', 'security', 'compliance', preset, 'custom'];
  order.forEach(function(src) {{
    if (!groups[src]) return;
    var grp = document.createElement('optgroup');
    grp.label = src.charAt(0).toUpperCase() + src.slice(1);
    groups[src].forEach(function(t) {{
      var o = document.createElement('option');
      o.value = t.id;
      o.textContent = t.name + ' (' + t.id + ')';
      grp.appendChild(o);
    }});
    sel.appendChild(grp);
  }});

  // Try to restore previous selection
  if (prev) sel.value = prev;
  updateScaffoldPreview();
}}
updateTemplateList();

function updateScaffoldPreview() {{
  var tmplId = document.getElementById('scaf-template').value;
  var title = document.getElementById('scaf-title').value.trim();
  var prev = document.getElementById('scaf-preview');
  if (!tmplId) {{ prev.style.display = 'none'; return; }}

  var tmpl = TEMPLATES.find(function(t) {{ return t.id === tmplId; }});
  if (!tmpl) {{ prev.style.display = 'none'; return; }}

  // Generate expected filename
  var slug = tmplId;
  if (title) {{
    slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }}
  var today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  var expectedName = slug + '-' + today + '-V1.0.md';

  var html = '<div class="mgr-preview-inner">';
  html += '<div class="mgr-preview-row"><strong>Template:</strong> ' + tmpl.name + '</div>';
  html += '<div class="mgr-preview-row"><strong>Expected file:</strong> <code>' + expectedName + '</code></div>';
  html += '<div class="mgr-preview-row"><strong>Source:</strong> ' + tmpl.source + '</div>';
  html += '</div>';
  prev.innerHTML = html;
  prev.style.display = '';
}}

function generateScaffold(dryRun) {{
  var tmplId = document.getElementById('scaf-template').value;
  if (!tmplId) {{ alert('Select a template first'); return; }}
  var title = document.getElementById('scaf-title').value.trim();
  var folder = document.getElementById('scaf-folder').value.trim();
  var author = document.getElementById('scaf-author').value.trim();
  var preset = document.getElementById('scaf-preset').value;

  var cmd = 'python -m librarian --registry docs/REGISTRY.yaml scaffold';
  cmd += ' --template ' + shellQuote(tmplId);
  if (title) cmd += ' --title ' + shellQuote(title);
  if (folder) cmd += ' --folder ' + shellQuote(folder);
  if (author) cmd += ' --author ' + shellQuote(author);
  cmd += ' --preset ' + preset;
  if (dryRun) cmd += ' --dry-run';
  showCommand(cmd);
}}

// --- Shared helpers ---
function shellQuote(s) {{
  if (/^[a-zA-Z0-9_.\\/-]+$/.test(s)) return s;
  return "'" + s.replace(/'/g, "'\\''") + "'";
}}

function showCommand(cmd) {{
  var out = document.getElementById('mgr-output');
  document.getElementById('mgr-output-cmd').textContent = cmd;
  out.style.display = '';
  out.scrollIntoView({{behavior: 'smooth', block: 'nearest'}});
}}

function closeMgrOutput() {{
  document.getElementById('mgr-output').style.display = 'none';
}}

function copyCommand() {{
  var text = document.getElementById('mgr-output-cmd').textContent;
  if (navigator.clipboard) {{
    navigator.clipboard.writeText(text);
    var btn = document.querySelector('.mgr-output-header .mgr-btn--sm');
    var orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(function() {{ btn.textContent = orig; }}, 1500);
  }}
}}
</script>"""

    sidebar = _sidebar_html(documents, base_prefix="")

    return _page(
        "Manage",
        body,
        "manage",
        project_name=project_name,
        generated_at=manifest.generated_at,
        seal=manifest.manifest_sha256,
        has_dashboard=False,
        sidebar=sidebar,
    )


def _build_search_index(manifest: "Manifest") -> str:
    """Build the global search index JSON for the header search bar.

    Returns a JSON string with entries for documents, settings fields,
    site pages, and template catalog items.
    """
    entries: list[dict[str, str]] = []
    snapshot = manifest.registry_snapshot
    documents = snapshot.get("documents", [])

    # ── Documents ──────────────────────────────────────────────────────
    _date_re = re.compile(r"(\d{4})-?(\d{2})-?(\d{2})")
    for doc in documents:
        fn = doc.get("filename", "")
        title = doc.get("title", fn)
        status = doc.get("status", "")
        tags = doc.get("tags", [])
        # Extract a normalized YYYY-MM-DD date from registry field or filename
        raw_date = doc.get("date", "") or ""
        dm = _date_re.search(str(raw_date)) or _date_re.search(fn)
        norm_date = f"{dm.group(1)}-{dm.group(2)}-{dm.group(3)}" if dm else ""
        text_parts = [fn, title, status] + tags
        entry: dict[str, str] = {
            "category": "document",
            "title": title,
            "text": " ".join(text_parts).lower(),
            "href": f"docs/{fn}.html",
            "meta": status,
        }
        if norm_date:
            entry["date"] = norm_date
        entries.append(entry)

    # ── Settings fields ────────────────────────────────────────────────
    settings_items = [
        ("Preset", "Project Basics", "cfg-preset"),
        ("Organization", "Project Basics", "cfg-hdr-org"),
        ("Default Author", "Project Basics", "cfg-author"),
        ("Review Cycle", "Project Basics", "cfg-meta-cycle"),
        ("Naming Template", "Naming Convention", "cfg-template"),
        ("Separator", "Naming Convention", "cfg-sep"),
        ("Case", "Naming Convention", "cfg-case"),
        ("Date Format", "Naming Convention", "cfg-date"),
        ("Version Format", "Naming Convention", "cfg-ver"),
        ("Domain Prefix", "Naming Convention", "cfg-domain"),
        ("Tracked Directories", "Folder Categories", "folders"),
        ("Forbidden Words", "Tags Taxonomy", "forbidden"),
        ("Exempt Files", "Tags Taxonomy", "exempt"),
        ("Tags Taxonomy", "Tags Taxonomy", "tags"),
        ("Category Strictness", "Governance", "strictness"),
        ("Default Author", "Governance", "author"),
        ("Classification Banner", "Governance", "classification"),
        ("Header Enabled", "Document Header / Footer", "cfg-hdr-enabled"),
        ("Header Organization", "Document Header / Footer", "cfg-hdr-org"),
        ("Logo URL", "Document Header / Footer", "cfg-hdr-logo"),
        ("Classification Banner", "Document Header / Footer", "cfg-hdr-banner"),
        ("Document ID Prefix", "Document Header / Footer", "cfg-hdr-prefix"),
        ("Show Version", "Document Header / Footer", "cfg-hdr-ver"),
        ("Show Date", "Document Header / Footer", "cfg-hdr-date"),
        ("Show Status", "Document Header / Footer", "cfg-hdr-status"),
        ("Footer Copyright", "Document Header / Footer", "footer"),
        ("Footer Custom Text", "Document Header / Footer", "footer-custom"),
        ("Legal Disclaimer", "Document Header / Footer", "disclaimer"),
        ("Require Author", "Required Metadata", "metadata"),
        ("Require Reviewer", "Required Metadata", "metadata"),
        ("Require Revision History", "Required Metadata", "metadata"),
        ("Review Cycle Days", "Required Metadata", "metadata"),
        ("Retention Period Days", "Required Metadata", "metadata"),
        # Compliance standards
        ("HIPAA", "Compliance Standards", "hipaa"),
        ("GDPR", "Compliance Standards", "gdpr"),
        ("ISO 27001", "Compliance Standards", "iso27001"),
        ("SOX", "Compliance Standards", "sox"),
        ("SOC 2", "Compliance Standards", "soc2"),
        ("DoD 5200", "Compliance Standards", "dod5200"),
        ("PCI DSS", "Compliance Standards", "pci-dss"),
        ("NIST CSF", "Compliance Standards", "nist-csf"),
        ("ISO 9001", "Compliance Standards", "iso9001"),
        ("CCPA", "Compliance Standards", "ccpa"),
        ("FERPA", "Compliance Standards", "ferpa"),
        ("FedRAMP", "Compliance Standards", "fedramp"),
    ]
    for label, section, field_id in settings_items:
        entries.append({
            "category": "setting",
            "title": label,
            "text": f"{label} {section} {field_id}".lower(),
            "href": f"settings.html#cfg-{field_id}" if field_id.startswith("cfg-") else "settings.html",
            "meta": section,
        })

    # ── Site pages ─────────────────────────────────────────────────────
    pages = [
        ("Home", "Document registry and overview", "index.html"),
        ("Folder Structure", "Tree view of project directories", "tree.html"),
        ("Cross-Reference Graph", "Dependency graph visualization", "graph.html"),
        ("Template Catalog", "Browse available document templates", "templates.html"),
        ("Settings", "Project configuration and compliance", "settings.html"),
        ("Setup Wizard", "Guided project setup questionnaire", "wizard.html"),
        ("Project Manager", "Add files, create folders, scaffold documents", "manage.html"),
        ("Audit & Verify", "OODA audit file integrity operation log seal recommendations", "audit.html"),
    ]
    for title, desc, href in pages:
        entries.append({
            "category": "page",
            "title": title,
            "text": f"{title} {desc}".lower(),
            "href": href,
            "meta": "",
        })

    # ── Templates ──────────────────────────────────────────────────────
    try:
        from .templates import discover_templates
        pc = snapshot.get("project_config", {})
        preset = pc.get("preset", "software")
        tmps = discover_templates(preset=preset or "software")
        for tid, tmpl in tmps.items():
            tags = " ".join(tmpl.suggested_tags) if tmpl.suggested_tags else ""
            entries.append({
                "category": "template",
                "title": tmpl.display_name,
                "text": f"{tid} {tmpl.display_name} {tmpl.description} {tags}".lower(),
                "href": f"templates.html#tmpl-{tid}",
                "meta": tmpl.preset,
            })
    except Exception:
        pass  # templates not available

    return _json_safe(entries, separators=(",", ":"))


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
        dashboard_path: Deprecated — ignored. Standalone dashboards are
            generated separately via ``librarian dashboard``.

    Returns:
        The resolved output directory path.
    """
    global _SEARCH_INDEX_JSON  # noqa: PLW0603

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Build global search index before any pages
    _SEARCH_INDEX_JSON = _build_search_index(manifest)

    # Assets
    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "style.css").write_text(SITE_CSS, encoding="utf-8")

    # Index (Home)
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

    # Templates catalog page
    (out / "templates.html").write_text(_build_templates_page(manifest), encoding="utf-8")

    # Setup wizard page
    (out / "wizard.html").write_text(_build_wizard_page(manifest), encoding="utf-8")

    # Audit & Verify page
    (out / "audit.html").write_text(_build_audit_page(manifest), encoding="utf-8")

    # Project Manager page
    (out / "manage.html").write_text(_build_manage_page(manifest), encoding="utf-8")

    return out.resolve()
