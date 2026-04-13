# Phase D Implementation Plan — Dashboard V3.0

## Scope

Build `python -m librarian dashboard` that renders a single-file HTML dashboard
from a project's manifest JSON. The dashboard provides: KPI summary cards,
searchable/filterable document table, version timeline, and interactive
cross-reference graph.

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Graph library | cytoscape.js (~80KB) | Built-in layouts (hierarchical, force), pan/zoom/select. Better fit for dependency viz than raw d3-force. |
| Search | Lunr.js (~8KB) | Client-side full-text, prefix matching, zero server. Standard for static sites. |
| Data injection | Embedded JSON | CLI replaces `__MANIFEST_DATA__` placeholder in template. Single file, zero fetch, works offline, fastest load. |
| Styling | CSS custom properties, no framework | Zero dependencies. Dark/light toggle via `prefers-color-scheme` + manual override. |
| Template location | `dashboard/librarian-dashboard-template-YYYYMMDD-V3.0.html` | Per buildout plan. |

## File Changes

### New files
1. `librarian/dashboard.py` — template loader, manifest injection, HTML writer
2. `dashboard/librarian-dashboard-template-20260412-V3.0.html` — the template
3. `tests/test_dashboard.py` — tests for the dashboard module

### Modified files
4. `librarian/__main__.py` — add `dashboard` subcommand
5. `librarian/__init__.py` — export dashboard module, bump to v0.4.0

## Template Structure (single HTML file)

```
<html>
  <head>
    <style>  /* ~400 lines: tokens, layout, components */  </style>
  </head>
  <body>
    <header>  Project name + generation timestamp + theme toggle  </header>
    <section id="kpi">  KPI cards: total, active, draft, superseded, violations, pending xrefs  </section>
    <section id="search">  Lunr search bar + filter chips (status, format, tags)  </section>
    <section id="table">  Sortable document table: name, version, status, date, tags  </section>
    <section id="timeline">  Horizontal timeline of document versions by date  </section>
    <section id="graph">  cytoscape.js dependency graph (cross-refs, supplements, supersedes)  </section>
    <footer>  Generator version + manifest SHA-256 seal  </footer>

    <script>/* Lunr.js inlined (~8KB) */</script>
    <script>/* cytoscape.js inlined (~80KB) */</script>
    <script>
      const MANIFEST = __MANIFEST_DATA__;
      // ~300 lines: init search, build table, render timeline, render graph
    </script>
  </body>
</html>
```

## dashboard.py Module

```python
def render(manifest: Manifest, template_path: Path | None = None) -> str:
    """Inject manifest JSON into the HTML template. Returns rendered HTML string."""

def write_dashboard(manifest: Manifest, output_path: Path, template_path: Path | None = None) -> Path:
    """Render and write to disk. Returns resolved output path."""

DEFAULT_TEMPLATE  # Path to bundled template in dashboard/
```

## CLI Subcommand

```
python -m librarian dashboard [--registry PATH] [-o output.html] [--template PATH]
```

- Default output: `docs/diagrams/librarian-dashboard-YYYYMMDD-V3.0.html`
- Default template: bundled `dashboard/librarian-dashboard-template-*.html`
- Generates manifest internally (calls `generate_manifest`), then renders

## Dashboard Features

### 1. KPI Cards
- Total documents, Active, Draft, Superseded, Naming violations, Pending cross-refs
- Sourced from `registry_meta` in the manifest snapshot
- Color-coded: green (clean), amber (warnings), red (violations)

### 2. Search (Lunr)
- Indexes: filename, title, description, tags
- Instant results as-you-type
- Highlights matching terms in the table

### 3. Filter UI
- Status chips: Active | Draft | Superseded (toggle)
- Format chips: md | yaml | json (toggle)
- Tag dropdown or chip cloud from `tags_taxonomy`
- Filters compose with search (AND logic)

### 4. Document Table
- Columns: filename, title, version, status, date, format, tags
- Click-to-sort on any column
- Row click expands detail panel (description, path, cross-refs, hash)

### 5. Timeline
- X-axis: dates from document `created`/`updated` fields
- Dots represent document versions, colored by status
- Hover shows filename + version
- CSS-only (no chart library needed for this)

### 6. Cross-Reference Graph
- Nodes: documents (colored by status)
- Edges: cross_references (solid), supplements (dashed), supersedes (dotted)
- cytoscape.js with `cose` (force-directed) layout, switchable to `breadthfirst`
- Click node highlights connected edges and dims others
- Node label: filename (truncated), tooltip: full title + version

## Test Plan

| Test | What it verifies |
|---|---|
| `test_render_injects_manifest` | `__MANIFEST_DATA__` replaced with valid JSON |
| `test_render_produces_valid_html` | Output contains `<html>`, `</html>`, `<script>` |
| `test_write_dashboard_creates_file` | File written to disk at expected path |
| `test_default_template_exists` | Bundled template file is present |
| `test_cli_dashboard_runs` | `python -m librarian dashboard` exits 0 |
| `test_cli_dashboard_output_flag` | `-o` writes to specified path |
| `test_manifest_data_accessible_in_html` | The injected JSON parses back to the original manifest dict |
| `test_empty_registry` | Dashboard renders without errors on 0 documents |
| `test_large_registry` | Dashboard renders with 50+ synthetic documents |

## Execution Order

1. Create `dashboard/` directory
2. Build the HTML template (largest deliverable — layout, CSS, inlined JS libs, app JS)
3. Build `librarian/dashboard.py` (template loading + manifest injection)
4. Add `dashboard` subcommand to `__main__.py`
5. Write `tests/test_dashboard.py`
6. Run full test suite (128 existing + ~9 new)
7. Render dashboard against librarian's own manifest and visually verify

## Payload Budget

| Component | Est. size |
|---|---|
| cytoscape.js (minified) | ~80KB |
| Lunr.js (minified) | ~8KB |
| CSS + app JS | ~15KB |
| Template HTML | ~5KB |
| Manifest JSON (10 docs) | ~8KB |
| **Total** | **~116KB** |

Well within the 10MB budget. Even at scale (40 docs + full-text corpus), estimate ~500KB.

## Out of Scope (Phase D)

- Server-side rendering or live reload
- Full-text document body indexing (Lunr indexes metadata only in V3.0)
- Vector search (Phase F)
- Static site generator (Phase E)
- Dark mode as default (respects system preference, defaults light)
