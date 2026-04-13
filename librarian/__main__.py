"""CLI entry point for the librarian. Run via `python -m librarian <command>`."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .audit import audit, format_report
from .config import (
    PRESETS,
    NAMING_TEMPLATES,
    LibrarianConfig,
    load_config,
    list_presets,
    list_naming_templates,
)
from .dashboard import render as render_dashboard, write_dashboard
from .diffaudit import diff_manifests, format_diff
from .evidence import generate_evidence, write_evidence, verify_evidence
from .manifest import generate as generate_manifest, write_manifest
from .naming import parse_filename
from .oplog import log_operation, read_log, read_log_since, format_log
from .registry import Registry
from .sitegen import generate_site
from .versioning import bump_filename

DEFAULT_REGISTRY = "docs/REGISTRY.yaml"


def _find_registry(explicit: str | None, repo_root: Path) -> Path:
    if explicit:
        return Path(explicit)
    return repo_root / DEFAULT_REGISTRY


# ------------------------------------------------------------------ commands


def cmd_audit(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)
    report = audit(reg, repo_root)
    print(format_report(report))
    return 0 if report.clean else 1


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)
    meta = reg.data.get("registry_meta", {})
    print(f"Total:              {meta.get('total_documents', 0)}")
    print(f"Active:             {meta.get('active', 0)}")
    print(f"Draft:              {meta.get('draft', 0)}")
    print(f"Superseded:         {meta.get('superseded', 0)}")
    print(f"Pending cross-refs: {meta.get('pending_cross_reference_updates', 0)}")
    print(f"Last updated:       {meta.get('last_updated', 'unknown')}")
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    target = Path(args.path)
    filename = target.name

    if reg.get_document(filename):
        print(f"Already registered: {filename}", file=sys.stderr)
        return 1

    if target.is_absolute():
        try:
            path_field = str(target.relative_to(repo_root))
        except ValueError:
            path_field = str(target)
    else:
        path_field = str(target)

    entry = {
        "filename": filename,
        "title": args.title or filename,
        "description": args.description or "",
        "status": args.status,
        "version": args.version,
        "created": date.today().strftime("%Y-%m-%d"),
        "updated": date.today().strftime("%Y-%m-%d"),
        "author": args.author or reg.project_config.get("default_author", "unknown"),
        "classification": args.classification
        or reg.project_config.get("default_classification", "INTERNAL"),
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
        "path": path_field,
        "infrastructure_exempt": False,
    }
    reg.add_document(entry)
    reg.save()
    print(f"Registered: {filename}")

    # Log the operation
    log_operation(
        "register",
        files=[filename],
        details={"version": args.version, "status": args.status},
        repo_root=repo_root,
    )
    return 0


def cmd_bump(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    old = reg.get_document(args.filename)
    if old is None:
        print(f"Not registered: {args.filename}", file=sys.stderr)
        return 1

    new_filename = bump_filename(args.filename, major=args.major)
    new_parsed = parse_filename(new_filename)
    assert new_parsed is not None  # bump_filename guarantees canonical output

    new_entry = dict(old)
    new_entry["filename"] = new_filename
    new_entry["version"] = new_parsed.version
    new_entry["status"] = "active"
    new_entry["created"] = date.today().strftime("%Y-%m-%d")
    new_entry["updated"] = date.today().strftime("%Y-%m-%d")
    old_path = Path(old.get("path", ""))
    new_entry["path"] = str(old_path.with_name(new_filename)) if old_path.name else new_filename
    new_entry.pop("supersedes", None)
    new_entry.pop("superseded_by", None)

    reg.add_document(new_entry)
    reg.supersede(args.filename, new_filename)
    reg.save()
    print(f"Bumped: {args.filename} -> {new_filename}")
    print("Note: librarian does NOT create the new file on disk.")
    print("      Copy the old file to the new name manually, then edit.")

    # Log the operation
    log_operation(
        "bump",
        files=[args.filename, new_filename],
        details={"old": args.filename, "new": new_filename, "major": args.major},
        repo_root=repo_root,
    )
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    manifest = generate_manifest(
        reg,
        repo_root,
        include_snapshot=not args.no_snapshot,
        include_hashes=not args.no_hashes,
        include_graph=not args.no_graph,
    )

    if args.output:
        out = write_manifest(manifest, args.output)
        print(f"Manifest written to: {out}")
    else:
        print(manifest.to_json())

    # Summary to stderr so it does not pollute piped JSON
    sys.stderr.write(
        f"\n  Registered: {manifest.total_registered}"
        f"  |  On disk: {manifest.total_on_disk}"
        f"  |  Hashed: {manifest.total_hashed}"
        f"  |  Edges: {manifest.total_edges}\n"
    )

    # Log the operation
    log_operation(
        "manifest",
        files=[args.output] if args.output else [],
        details={
            "registered": manifest.total_registered,
            "hashed": manifest.total_hashed,
            "edges": manifest.total_edges,
        },
        repo_root=repo_root,
    )
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    pack = generate_evidence(reg, repo_root)

    if args.output:
        out = write_evidence(pack, args.output)
        print(f"Evidence pack written to: {out}")
    else:
        print(pack.to_json())

    dirty_str = " (DIRTY)" if pack.git_dirty else ""
    sys.stderr.write(
        f"\n  Project: {pack.project_name}"
        f"  |  Commit: {pack.git_commit_hash[:8] or 'N/A'}{dirty_str}"
        f"  |  Seal: {pack.manifest_json_sha256[:16]}...\n"
    )

    # Log the operation
    log_operation(
        "evidence",
        files=[args.output] if args.output else [],
        details={
            "commit": pack.git_commit_hash[:8],
            "seal": pack.manifest_json_sha256[:16],
            "dirty": pack.git_dirty,
        },
        repo_root=repo_root,
    )
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    report = diff_manifests(args.old, args.new)

    if args.json:
        print(report.to_json())
    else:
        print(format_diff(report))

    return 0 if not report.has_changes else 1


def cmd_log(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    log_path = repo_root / "operator" / "librarian-audit.jsonl"
    if args.log_path:
        log_path = Path(args.log_path)

    if args.since:
        entries = read_log_since(log_path, args.since)
    else:
        entries = read_log(log_path)

    if args.last:
        entries = entries[-args.last:]

    print(f"  Log: {log_path}")
    print(f"  Entries: {len(entries)}")
    print()
    print(format_log(entries))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    manifest = generate_manifest(reg, repo_root)

    template_path = Path(args.template) if args.template else None

    if args.output:
        out = write_dashboard(manifest, args.output, template_path=template_path)
    else:
        # Default output path
        out = write_dashboard(
            manifest,
            repo_root / "docs" / "diagrams" / "librarian-dashboard.html",
            template_path=template_path,
        )
    print(f"Dashboard written to: {out}")

    sys.stderr.write(
        f"\n  Documents: {manifest.total_registered}"
        f"  |  Edges: {manifest.total_edges}"
        f"  |  Seal: {manifest.manifest_sha256[:16]}...\n"
    )

    # Log the operation
    log_operation(
        "dashboard",
        files=[str(out)],
        details={
            "registered": manifest.total_registered,
            "edges": manifest.total_edges,
        },
        repo_root=repo_root,
    )
    return 0


def cmd_site(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    manifest = generate_manifest(reg, repo_root)

    output_dir = Path(args.output_dir) if args.output_dir else repo_root / "_site"

    # Optionally render dashboard and include it
    dashboard_path = None
    if not args.no_dashboard:
        dashboard_out = output_dir / "dashboard.html"
        dashboard_out.parent.mkdir(parents=True, exist_ok=True)
        template_path = Path(args.template) if args.template else None
        write_dashboard(manifest, dashboard_out, template_path=template_path)
        dashboard_path = dashboard_out

    site_dir = generate_site(manifest, output_dir, dashboard_path=dashboard_path)

    # Count pages
    pages = list(site_dir.rglob("*.html"))
    print(f"Site generated: {site_dir}")
    print(f"  Pages: {len(pages)}")

    sys.stderr.write(
        f"\n  Documents: {manifest.total_registered}"
        f"  |  Edges: {manifest.total_edges}"
        f"  |  Pages: {len(pages)}\n"
    )

    # Log the operation
    log_operation(
        "site",
        files=[str(site_dir)],
        details={
            "registered": manifest.total_registered,
            "pages": len(pages),
        },
        repo_root=repo_root,
    )
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new REGISTRY.yaml with a chosen preset."""
    import yaml as _yaml

    repo_root = Path(args.repo or ".").resolve()
    preset = args.preset or "minimal"

    if preset not in PRESETS:
        print(f"Unknown preset: {preset}", file=sys.stderr)
        print(f"Available: {', '.join(PRESETS)}", file=sys.stderr)
        return 1

    config = load_config(preset=preset)

    # Build project_config block
    naming_template = args.naming_template or "default"
    if naming_template in NAMING_TEMPLATES:
        nr = dict(NAMING_TEMPLATES[naming_template])
    else:
        nr = {"separator": "-", "case": "lowercase", "date_format": "YYYYMMDD", "version_format": "VX.Y"}

    nr["forbidden_words"] = config.naming.forbidden_words
    nr["infrastructure_exempt"] = [
        "REGISTRY.yaml", "README.md", "CLAUDE.md", ".gitignore",
    ]

    project_config = {
        "project_name": args.name or "My Project",
        "naming_convention": config.naming.human_pattern,
        "naming_rules": nr,
        "categories": {
            "strict_mode": config.categories.strict_mode,
            "folders": config.categories.folders,
            "labels": config.categories.labels,
        },
        "tags_taxonomy": config.tags_taxonomy,
        "tracked_dirs": config.tracked_dirs,
        "default_author": args.author or "",
        "default_classification": "INTERNAL",
        "classification_levels": ["INTERNAL", "CONFIDENTIAL", "PUBLIC"],
        "staleness_threshold_days": 90,
    }

    data = {
        "project_config": project_config,
        "documents": [],
        "registry_meta": {
            "total_documents": 0,
            "active": 0,
            "draft": 0,
            "superseded": 0,
            "last_updated": date.today().strftime("%Y-%m-%d"),
        },
    }

    out_path = Path(args.output) if args.output else repo_root / "docs" / "REGISTRY.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not args.force:
        print(f"Registry already exists: {out_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    with out_path.open("w") as f:
        _yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"Initialized registry: {out_path}")
    print(f"  Preset:    {preset}")
    print(f"  Naming:    {config.naming.human_pattern}")
    print(f"  Template:  {naming_template}")
    print(f"  Folders:   {len(config.categories.folders)}")
    print(f"  Tags:      {sum(len(v) for v in config.tags_taxonomy.values())} across {len(config.tags_taxonomy)} groups")

    # Create preset folders if requested
    if args.create_folders and config.categories.folders:
        docs_root = out_path.parent
        created = 0
        for folder in config.categories.folders:
            fp = docs_root / folder
            if not fp.exists():
                fp.mkdir(parents=True, exist_ok=True)
                created += 1
        print(f"  Created {created} category folders under {docs_root}")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Display resolved configuration or list presets/templates."""
    if args.list_presets:
        print("Available presets:")
        for p in list_presets():
            print(f"  {p['name']:15s}  {p['description']}")
        return 0

    if args.list_templates:
        print("Available naming templates:")
        for t in list_naming_templates():
            print(f"  {t['name']:15s}  {t['pattern']}")
        return 0

    # Show resolved config for current registry
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)

    try:
        reg = Registry.load(reg_path)
        config = reg.get_config(preset=args.preset or "")
    except FileNotFoundError:
        print(f"No registry found at {reg_path}. Showing defaults.", file=sys.stderr)
        config = load_config(preset=args.preset or "")

    print(f"Project:             {config.project_name}")
    print(f"Preset:              {config.preset or '(none)'}")
    print()
    print("─── Naming Convention ───")
    print(f"  Pattern:           {config.naming.human_pattern}")
    print(f"  Separator:         '{config.naming.separator}'")
    print(f"  Case:              {config.naming.case}")
    print(f"  Date format:       {config.naming.date_format}")
    print(f"  Version format:    {config.naming.version_format}")
    print(f"  Domain prefix:     {config.naming.domain_prefix}")
    print(f"  Forbidden words:   {', '.join(config.naming.forbidden_words)}")
    print(f"  Exempt files:      {len(config.naming.infrastructure_exempt)}")
    print()
    print("─── Categories ───")
    print(f"  Strict mode:       {config.categories.strict_mode}")
    print(f"  Folders:           {len(config.categories.folders)}")
    for f in config.categories.folders:
        label = config.categories.labels.get(f.rstrip("/"), "")
        label_str = f" — {label}" if label else ""
        print(f"    {f}{label_str}")
    print()
    print("─── Tags Taxonomy ───")
    for group, tags in config.tags_taxonomy.items():
        print(f"  {group}: {', '.join(tags)}")
    print()
    print("─── Tracking ───")
    print(f"  Tracked dirs:      {', '.join(config.tracked_dirs)}")
    print(f"  Staleness:         {config.staleness_threshold_days} days")
    return 0


# ------------------------------------------------------------------ parser


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="librarian", description="Document governance CLI")
    p.add_argument("--repo", help="repo root (default: cwd)")
    p.add_argument("--registry", help=f"registry path (default: {DEFAULT_REGISTRY})")
    sub = p.add_subparsers(dest="command", required=True)

    # --- audit
    p_audit = sub.add_parser("audit", help="Run OODA audit")
    p_audit.set_defaults(func=cmd_audit)

    # --- status
    p_status = sub.add_parser("status", help="Show registry counts")
    p_status.set_defaults(func=cmd_status)

    # --- register
    p_reg = sub.add_parser("register", help="Register a new document")
    p_reg.add_argument("path", help="path to the document")
    p_reg.add_argument("--title")
    p_reg.add_argument("--description")
    p_reg.add_argument("--status", default="draft", choices=["draft", "active"])
    p_reg.add_argument("--version", default="V1.0")
    p_reg.add_argument("--author")
    p_reg.add_argument("--classification")
    p_reg.add_argument("--tags", help="comma-separated")
    p_reg.set_defaults(func=cmd_register)

    # --- bump
    p_bump = sub.add_parser("bump", help="Bump a document version")
    p_bump.add_argument("filename", help="current filename to bump")
    p_bump.add_argument("--major", action="store_true", help="bump major, reset minor to 0")
    p_bump.set_defaults(func=cmd_bump)

    # --- manifest
    p_manifest = sub.add_parser("manifest", help="Generate manifest (JSON + SHA-256 + graph)")
    p_manifest.add_argument("-o", "--output", help="write to file instead of stdout")
    p_manifest.add_argument("--no-snapshot", action="store_true", help="omit registry snapshot")
    p_manifest.add_argument("--no-hashes", action="store_true", help="omit SHA-256 file hashes")
    p_manifest.add_argument("--no-graph", action="store_true", help="omit dependency graph")
    p_manifest.set_defaults(func=cmd_manifest)

    # --- evidence (Phase C)
    p_evidence = sub.add_parser("evidence", help="Generate IP evidence pack")
    p_evidence.add_argument("-o", "--output", help="write to file instead of stdout")
    p_evidence.set_defaults(func=cmd_evidence)

    # --- diff (Phase C)
    p_diff = sub.add_parser("diff", help="Diff two manifests")
    p_diff.add_argument("old", help="path to the old/baseline manifest JSON")
    p_diff.add_argument("new", help="path to the new/current manifest JSON")
    p_diff.add_argument("--json", action="store_true", help="output as JSON instead of text")
    p_diff.set_defaults(func=cmd_diff)

    # --- dashboard (Phase D)
    p_dash = sub.add_parser("dashboard", help="Generate HTML dashboard from manifest")
    p_dash.add_argument("-o", "--output", help="write to file (default: docs/diagrams/librarian-dashboard.html)")
    p_dash.add_argument("--template", help="path to template file or directory")
    p_dash.set_defaults(func=cmd_dashboard)

    # --- site (Phase E)
    p_site = sub.add_parser("site", help="Generate static HTML site from manifest")
    p_site.add_argument("-o", "--output-dir", help="output directory (default: _site/)")
    p_site.add_argument("--template", help="path to dashboard template file or directory")
    p_site.add_argument("--no-dashboard", action="store_true", help="omit dashboard page from site")
    p_site.set_defaults(func=cmd_site)

    # --- log (Phase C)
    p_log = sub.add_parser("log", help="View the operation log")
    p_log.add_argument("--log-path", help="explicit path to the JSONL log file")
    p_log.add_argument("--since", help="show entries from this ISO timestamp onward")
    p_log.add_argument("--last", type=int, help="show only the last N entries")
    p_log.set_defaults(func=cmd_log)

    # --- init
    p_init = sub.add_parser("init", help="Scaffold a new REGISTRY.yaml from a preset")
    p_init.add_argument("--name", help="project name")
    p_init.add_argument("--preset", default="minimal",
                        help="preset pack: software, business, accounting, minimal (default)")
    p_init.add_argument("--naming-template", default="default",
                        help="naming template: default, legal, engineering, corporate, dateless")
    p_init.add_argument("--author", help="default author name")
    p_init.add_argument("-o", "--output", help="output path (default: docs/REGISTRY.yaml)")
    p_init.add_argument("--force", action="store_true", help="overwrite existing registry")
    p_init.add_argument("--create-folders", action="store_true",
                        help="create category folders on disk")
    p_init.set_defaults(func=cmd_init)

    # --- config
    p_config = sub.add_parser("config", help="Show resolved configuration or list presets")
    p_config.add_argument("--list-presets", action="store_true", help="list available presets")
    p_config.add_argument("--list-templates", action="store_true", help="list naming templates")
    p_config.add_argument("--preset", help="apply a preset before showing config")
    p_config.set_defaults(func=cmd_config)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
