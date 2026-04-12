"""CLI entry point for the librarian. Run via `python -m librarian <command>`."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .audit import audit, format_report
from .manifest import generate as generate_manifest, write_manifest
from .naming import parse_filename
from .registry import Registry
from .versioning import bump_filename

DEFAULT_REGISTRY = "docs/REGISTRY.yaml"


def _find_registry(explicit: str | None, repo_root: Path) -> Path:
    if explicit:
        return Path(explicit)
    return repo_root / DEFAULT_REGISTRY


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
    import sys as _sys
    _sys.stderr.write(
        f"\n  Registered: {manifest.total_registered}"
        f"  |  On disk: {manifest.total_on_disk}"
        f"  |  Hashed: {manifest.total_hashed}"
        f"  |  Edges: {manifest.total_edges}\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="librarian", description="Document governance CLI")
    p.add_argument("--repo", help="repo root (default: cwd)")
    p.add_argument("--registry", help=f"registry path (default: {DEFAULT_REGISTRY})")
    sub = p.add_subparsers(dest="command", required=True)

    p_audit = sub.add_parser("audit", help="Run OODA audit")
    p_audit.set_defaults(func=cmd_audit)

    p_status = sub.add_parser("status", help="Show registry counts")
    p_status.set_defaults(func=cmd_status)

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

    p_bump = sub.add_parser("bump", help="Bump a document version")
    p_bump.add_argument("filename", help="current filename to bump")
    p_bump.add_argument("--major", action="store_true", help="bump major, reset minor to 0")
    p_bump.set_defaults(func=cmd_bump)

    p_manifest = sub.add_parser("manifest", help="Generate manifest (JSON + SHA-256 + graph)")
    p_manifest.add_argument("-o", "--output", help="write to file instead of stdout")
    p_manifest.add_argument("--no-snapshot", action="store_true", help="omit registry snapshot")
    p_manifest.add_argument("--no-hashes", action="store_true", help="omit SHA-256 file hashes")
    p_manifest.add_argument("--no-graph", action="store_true", help="omit dependency graph")
    p_manifest.set_defaults(func=cmd_manifest)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
