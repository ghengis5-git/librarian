"""CLI entry point for the librarian. Run via `python -m librarian <command>`."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from .audit import audit, format_report
from .recommend import generate_recommendations, format_recommendations
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
from .evidence import generate_evidence, write_evidence, verify_evidence, SigningError
from .manifest import generate as generate_manifest, write_manifest
from .naming import parse_filename
from .oplog import log_operation, read_log, read_log_since, format_log
from .oplog_lock import (
    is_append_only,
    lock_instructions,
    platform_support,
    unlock_instructions,
)
from .registry import Registry
from .review import (
    ReviewDateError,
    compute_overdue,
    compute_upcoming,
    format_review_date,
    parse_review_date,
)
from .sitegen import generate_site
from .templates import discover_templates, load_template, list_templates, build_context
from .templates._base import render_template
from .versioning import bump_filename

DEFAULT_REGISTRY = "docs/REGISTRY.yaml"


def _find_registry(explicit: str | None, repo_root: Path) -> Path:
    if explicit:
        return Path(explicit)
    return repo_root / DEFAULT_REGISTRY


# ------------------------------------------------------------------ commands


def cmd_audit(args: argparse.Namespace) -> int:
    import json as _json

    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)

    # Phase 8.1: allow project_config.audit_config.folder_threshold to
    # override the default (15). Projects with intentionally heavy self-
    # documentation (the librarian itself is one) can raise this bound
    # instead of being forced to reorganize into subdirs.
    audit_cfg = (reg.project_config or {}).get("audit_config", {}) or {}
    folder_threshold = audit_cfg.get("folder_threshold")
    if isinstance(folder_threshold, int) and folder_threshold > 0:
        report = audit(reg, repo_root, folder_threshold=folder_threshold)
    else:
        report = audit(reg, repo_root)

    if args.recommend:
        rec_report = generate_recommendations(
            registry_documents=reg.documents,
            project_config=reg.project_config,
        )
        if args.json:
            # JSON output: combine audit summary + recommendations
            output = {
                "audit": {
                    "files_on_disk": len(report.on_disk),
                    "registered": len(report.registered),
                    "unregistered": report.unregistered,
                    "missing": report.missing,
                    "naming_violations": [
                        {"file": n, "errors": e}
                        for n, e in report.naming_violations
                    ],
                    "pending_cross_refs": report.pending_cross_refs,
                    "overdue_reviews": [
                        r.to_dict() for r in report.overdue_reviews
                    ],
                    "oplog_locked": report.oplog_locked,
                    "oplog_path": report.oplog_path,
                    "clean": report.clean,
                },
                "recommendations": rec_report.to_dict(),
            }
            print(_json.dumps(output, indent=2))
        else:
            print(format_report(report))
            print()
            print(format_recommendations(rec_report))
    else:
        if args.json:
            output = {
                "audit": {
                    "files_on_disk": len(report.on_disk),
                    "registered": len(report.registered),
                    "unregistered": report.unregistered,
                    "missing": report.missing,
                    "naming_violations": [
                        {"file": n, "errors": e}
                        for n, e in report.naming_violations
                    ],
                    "pending_cross_refs": report.pending_cross_refs,
                    "overdue_reviews": [
                        r.to_dict() for r in report.overdue_reviews
                    ],
                    "oplog_locked": report.oplog_locked,
                    "oplog_path": report.oplog_path,
                    "clean": report.clean,
                },
            }
            print(_json.dumps(output, indent=2))
        else:
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

    # Parse optional --review-by up front so we reject bad input before write.
    review_by: str | None = None
    if getattr(args, "review_by", None):
        try:
            review_by = format_review_date(parse_review_date(args.review_by))
        except ReviewDateError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

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
    if review_by:
        entry["next_review"] = review_by
    reg.add_document(entry)
    reg.save()
    print(f"Registered: {filename}")
    if review_by:
        print(f"  next_review: {review_by}")

    # Log the operation
    details = {"version": args.version, "status": args.status}
    if review_by:
        details["next_review"] = review_by
    log_operation(
        "register",
        files=[filename],
        details=details,
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

    # --review-by / --clear-review: update the inherited next_review field.
    # Mutual exclusion is enforced by argparse.
    review_override: str | None = None
    clear_review = bool(getattr(args, "clear_review", False))
    if getattr(args, "review_by", None):
        try:
            review_override = format_review_date(parse_review_date(args.review_by))
        except ReviewDateError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

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

    # next_review handling: default is inherit (already in dict(old));
    # --clear-review strips it; --review-by overwrites it.
    if clear_review:
        new_entry.pop("next_review", None)
    elif review_override:
        new_entry["next_review"] = review_override

    reg.add_document(new_entry)
    reg.supersede(args.filename, new_filename)
    reg.save()
    print(f"Bumped: {args.filename} -> {new_filename}")
    if "next_review" in new_entry:
        print(f"  next_review: {new_entry['next_review']}")
    elif clear_review:
        print("  next_review: cleared")
    print("Note: librarian does NOT create the new file on disk.")
    print("      Copy the old file to the new name manually, then edit.")

    # Log the operation
    details: dict[str, Any] = {"old": args.filename, "new": new_filename, "major": args.major}
    if review_override:
        details["next_review"] = review_override
    elif clear_review:
        details["next_review_cleared"] = True
    log_operation(
        "bump",
        files=[args.filename, new_filename],
        details=details,
        repo_root=repo_root,
    )
    return 0


# ------------------------------------------------------------------ review
#
# `librarian review` groups three actions on the optional ``next_review``
# field:
#
#     review set <filename> --by <YYYY-MM-DD>
#     review clear <filename>
#     review list [--overdue | --upcoming [--within-days N]]
#
# Rationale: the flag-on-existing-command path (register/bump --review-by)
# handles the creation flow well, but editing a deadline after the fact
# or surveying review state across the whole registry benefits from a
# dedicated verb. See docstring in librarian/review.py for the full design.


def cmd_review(args: argparse.Namespace) -> int:
    sub = getattr(args, "review_action", None)
    if sub == "set":
        return _review_set(args)
    if sub == "clear":
        return _review_clear(args)
    if sub == "list":
        return _review_list(args)
    print("Error: no review subcommand. Use: set | clear | list", file=sys.stderr)
    return 2


def _review_set(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)
    doc = reg.get_document(args.filename)
    if doc is None:
        print(f"Not registered: {args.filename}", file=sys.stderr)
        return 1
    try:
        new_date = format_review_date(parse_review_date(args.by))
    except ReviewDateError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if new_date is None:
        print("Error: --by is required", file=sys.stderr)
        return 2

    prior = doc.get("next_review")
    doc["next_review"] = new_date
    doc["updated"] = date.today().strftime("%Y-%m-%d")
    reg.update_meta()
    reg.save()

    action = "set" if not prior else "updated"
    print(f"Review deadline {action}: {args.filename} -> {new_date}")
    if prior and prior != new_date:
        print(f"  (was: {prior})")

    log_operation(
        "review",
        files=[args.filename],
        details={"action": "set", "next_review": new_date, "previous": prior},
        repo_root=repo_root,
    )
    return 0


def _review_clear(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)
    doc = reg.get_document(args.filename)
    if doc is None:
        print(f"Not registered: {args.filename}", file=sys.stderr)
        return 1
    prior = doc.pop("next_review", None)
    doc["updated"] = date.today().strftime("%Y-%m-%d")
    reg.update_meta()
    reg.save()

    if prior is None:
        print(f"No review deadline was set: {args.filename}")
    else:
        print(f"Review deadline cleared: {args.filename} (was {prior})")

    log_operation(
        "review",
        files=[args.filename],
        details={"action": "clear", "previous": prior},
        repo_root=repo_root,
    )
    return 0


def _review_list(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)
    reg = Registry.load(reg_path)
    today = date.today()

    overdue_only = bool(getattr(args, "overdue", False))
    upcoming_only = bool(getattr(args, "upcoming", False))
    within = int(getattr(args, "within_days", 30) or 30)

    overdue = compute_overdue(reg.documents, today=today)
    upcoming = compute_upcoming(reg.documents, today=today, within_days=within)

    # Build full-coverage view when neither filter is on.
    all_with_deadline: list[tuple[str, str, int]] = []
    if not overdue_only and not upcoming_only:
        for doc in reg.documents:
            status = doc.get("status")
            raw = doc.get("next_review")
            if status not in {"active", "draft"} or raw in (None, ""):
                continue
            try:
                d = parse_review_date(raw)
            except ReviewDateError:
                continue
            if d is None:
                continue
            delta = (d - today).days
            all_with_deadline.append((doc.get("filename", "?"),
                                       format_review_date(d) or "", delta))
        all_with_deadline.sort(key=lambda r: (r[2], r[0]))

    def _row(fn: str, deadline: str, delta: int) -> str:
        if delta < 0:
            tag = f"OVERDUE by {-delta}d"
        elif delta == 0:
            tag = "due today"
        else:
            tag = f"in {delta}d"
        return f"  {deadline}  {fn:50s}  {tag}"

    if overdue_only:
        if not overdue:
            print("No overdue reviews.")
            return 0
        print(f"Overdue reviews ({len(overdue)}):")
        for r in overdue:
            print(_row(r.filename, format_review_date(r.next_review) or "?",
                      -r.days_overdue))
        return 0

    if upcoming_only:
        if not upcoming:
            print(f"No reviews upcoming within {within} days.")
            return 0
        print(f"Upcoming reviews (next {within} days, {len(upcoming)}):")
        for r in upcoming:
            deadline = format_review_date(r.next_review) or "?"
            # days_overdue field carries -delta; flip for display
            print(_row(r.filename, deadline, -r.days_overdue))
        return 0

    # Default list: everything with a deadline, overdue first.
    if not all_with_deadline:
        print("No documents have a next_review deadline set.")
        return 0
    print(f"Documents with review deadlines ({len(all_with_deadline)}):")
    for fn, deadline, delta in all_with_deadline:
        print(_row(fn, deadline, delta))
    return 0


def cmd_oplog(args: argparse.Namespace) -> int:
    """Phase 7.5 — inspect the OS-level append-only flag on the oplog file."""
    repo_root = Path(args.repo or ".").resolve()
    log_path = repo_root / "operator" / "librarian-audit.jsonl"

    sub = getattr(args, "oplog_action", None)
    if sub != "status":
        print("Error: no oplog subcommand. Use: status", file=sys.stderr)
        print("  (To apply/remove the lock, run "
              "scripts/librarian-oplog-lock-20260414-V1.0.sh.)",
              file=sys.stderr)
        return 2

    plat = platform_support()
    locked = is_append_only(log_path)

    print(f"Oplog file:   {log_path}")
    print(f"Platform:     {plat}")
    if not log_path.exists():
        print("State:        missing (log has not been created yet)")
        print("Hint:         run any librarian operation (e.g., audit) to create it.")
        return 0
    if locked is True:
        print("State:        locked — kernel-enforced append-only")
        print("Removal:      " + unlock_instructions(log_path))
        return 0
    if locked is False:
        print("State:        unlocked — detect-only hash chain only")
        print("Apply:        " + lock_instructions(log_path))
        print("              (or: scripts/librarian-oplog-lock-20260414-V1.0.sh lock)")
        return 0
    # None
    print("State:        undetectable")
    print("Reason:       append-only flags are not supported or not probeable on "
          "this platform/filesystem.")
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

    # Read evidence_signing from project_config (feature flag)
    signing_mode = reg.project_config.get("evidence_signing", "off")

    try:
        pack = generate_evidence(reg, repo_root, evidence_signing=signing_mode)
    except SigningError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output:
        out = write_evidence(pack, args.output)
        print(f"Evidence pack written to: {out}")
    else:
        print(pack.to_json())

    dirty_str = " (DIRTY)" if pack.git_dirty else ""
    signed_str = "  |  Signed: YES" if pack.signature.get("signed") else ""
    sys.stderr.write(
        f"\n  Project: {pack.project_name}"
        f"  |  Commit: {pack.git_commit_hash[:8] or 'N/A'}{dirty_str}"
        f"  |  Seal: {pack.manifest_json_sha256[:16]}..."
        f"{signed_str}\n"
    )

    # Log the operation
    log_operation(
        "evidence",
        files=[args.output] if args.output else [],
        details={
            "commit": pack.git_commit_hash[:8],
            "seal": pack.manifest_json_sha256[:16],
            "dirty": pack.git_dirty,
            "signed": bool(pack.signature.get("signed")),
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

    # Dashboard is no longer bundled into the site by default —
    # use `librarian dashboard` for a standalone portable file.
    site_dir = generate_site(manifest, output_dir)

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


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Scaffold a new document from a template."""
    repo_root = Path(args.repo or ".").resolve()
    reg_path = _find_registry(args.registry, repo_root)

    # Load registry and config
    try:
        reg = Registry.load(reg_path)
        pc = reg.project_config
    except FileNotFoundError:
        if not args.list and not args.list_all:
            print(f"Registry not found: {reg_path}", file=sys.stderr)
            return 1
        pc = {}
        reg = None

    preset = pc.get("preset", args.preset or "")
    custom_dir = pc.get("custom_templates_dir", None)

    # --list: show templates for this preset
    if args.list:
        templates = list_templates(preset=preset, custom_dir=custom_dir)
        if not templates:
            print("No templates found.")
            return 0
        print(f"Available templates (preset: {preset or 'universal'}):\n")
        for t in templates:
            print(f"  {t['id']:35s}  {t['name']}")
            if t['description']:
                print(f"  {'':35s}  {t['description']}")
            print()
        return 0

    # --list-all: show all templates across all presets
    if args.list_all:
        all_presets = ["universal", "software", "business", "legal", "scientific",
                       "healthcare", "finance", "government", "security", "compliance"]
        seen: set[str] = set()
        for p in all_presets:
            templates = discover_templates(preset=p, custom_dir=custom_dir)
            new_ids = sorted(set(templates.keys()) - seen)
            if new_ids:
                print(f"\n  [{p}]")
                for tid in new_ids:
                    t = templates[tid]
                    print(f"    {tid:35s}  {t.display_name}")
                    seen.add(tid)
        print()
        return 0

    # Require --template
    if not args.template:
        print("Error: --template is required (or use --list to see available templates).",
              file=sys.stderr)
        return 1

    # Resolve template
    tmpl = load_template(args.template, preset=preset, custom_dir=custom_dir)
    if tmpl is None:
        print(f"Template not found: {args.template}", file=sys.stderr)
        print(f"Run: python -m librarian scaffold --list", file=sys.stderr)
        return 1

    # Build context
    ctx = build_context(project_config=pc)

    # Apply overrides
    title = args.title or tmpl.display_name
    ctx["title"] = title
    if args.author:
        ctx["author"] = args.author

    # Render the template body
    rendered = tmpl.render(ctx)

    # Build the filename using naming convention
    nr = pc.get("naming_rules", {})
    sep = nr.get("separator", "-")
    date_fmt = nr.get("date_format", "YYYYMMDD")
    version_fmt = nr.get("version_format", "VX.Y")

    today = date.today()
    if date_fmt == "YYYY-MM-DD":
        date_str = today.strftime("%Y-%m-%d")
    elif date_fmt == "off":
        date_str = ""
    else:
        date_str = today.strftime("%Y%m%d")

    if version_fmt == "vX.Y":
        ver_str = "v1.0"
    elif version_fmt == "X.Y":
        ver_str = "1.0"
    else:
        ver_str = "V1.0"

    # Build filename parts — sanitize template_id to prevent path traversal
    stem = re.sub(r"[^a-z0-9-]", "", tmpl.template_id.lower())
    if not stem:
        print("Error: template_id contains no valid characters.", file=sys.stderr)
        return 1
    parts = [stem]
    if date_str:
        parts.append(date_str)
    parts.append(ver_str)
    filename = sep.join(parts) + ".md"

    # Determine output folder — sanitize to prevent path traversal
    folder = args.folder or tmpl.suggested_folder or "docs/"
    if not folder.endswith("/"):
        folder += "/"
    out_dir = (repo_root / folder).resolve()
    out_path = out_dir / filename

    # Security: ensure output path is under repo_root
    try:
        out_path.resolve().relative_to(repo_root)
    except ValueError:
        print(f"Error: output path escapes repo root: {folder}", file=sys.stderr)
        return 1

    # --dry-run: show what would be created
    if args.dry_run:
        print(f"[dry-run] Would create: {out_path.relative_to(repo_root)}")
        print(f"  Template:  {tmpl.template_id}")
        print(f"  Title:     {title}")
        print(f"  Tags:      {', '.join(tmpl.suggested_tags)}")
        if tmpl.typical_cross_refs:
            print(f"  X-refs:    {', '.join(tmpl.typical_cross_refs)}")
        print(f"\n--- Preview (first 20 lines) ---\n")
        for line in rendered.splitlines()[:20]:
            print(line)
        if len(rendered.splitlines()) > 20:
            print(f"  ... ({len(rendered.splitlines()) - 20} more lines)")
        return 0

    # Refuse to overwrite existing files
    if out_path.exists():
        print(f"Error: file already exists: {out_path.relative_to(repo_root)}", file=sys.stderr)
        print("  Bump the existing version or remove the file first.", file=sys.stderr)
        return 1

    # Write the file
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")

    # Register in REGISTRY.yaml (unless --no-register)
    if not args.no_register and reg is not None:
        # Validate --review-by (if provided) before any disk write.
        review_by: str | None = None
        if getattr(args, "review_by", None):
            try:
                review_by = format_review_date(parse_review_date(args.review_by))
            except ReviewDateError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

        rel_path = str(out_path.relative_to(repo_root))
        entry = {
            "filename": filename,
            "title": title,
            "description": tmpl.description,
            "status": "draft",
            "version": "V1.0",
            "created": today.strftime("%Y-%m-%d"),
            "updated": today.strftime("%Y-%m-%d"),
            "author": ctx.get("author", ""),
            "classification": ctx.get("classification", "INTERNAL"),
            "tags": list(tmpl.suggested_tags),
            "path": rel_path,
            "infrastructure_exempt": False,
        }
        if review_by:
            entry["next_review"] = review_by

        # Add cross-references for targets that already exist in registry
        xrefs = []
        for ref_id in tmpl.typical_cross_refs:
            # Check if a document with this template_id in its filename exists
            for doc in reg.documents:
                doc_fn = doc.get("filename", "")
                if ref_id in doc_fn:
                    xrefs.append(doc_fn)
                    break
        if xrefs:
            entry["cross_references"] = xrefs

        try:
            reg.add_document(entry)
            reg.save()
        except ValueError as e:
            print(f"Warning: could not register — {e}", file=sys.stderr)

        # Log the operation
        log_operation(
            "scaffold",
            files=[filename],
            details={
                "template": tmpl.template_id,
                "title": title,
                "tags": tmpl.suggested_tags,
            },
            repo_root=repo_root,
        )

    # Print summary
    print(f"Created: {out_path.relative_to(repo_root)}")
    print(f"  Title:    {title}")
    print(f"  Status:   draft")
    print(f"  Tags:     {', '.join(tmpl.suggested_tags)}")

    if tmpl.typical_cross_refs:
        print(f"  X-refs:   {', '.join(tmpl.typical_cross_refs)}")

    # Show recommended companions
    if tmpl.recommended_with:
        existing = {d.get("filename", "") for d in (reg.documents if reg else [])}
        missing = [r for r in tmpl.recommended_with
                   if not any(r in fn for fn in existing)]
        if missing:
            print(f"\n  Recommended companions (not yet in registry):")
            for m in missing:
                print(f"    - {m}")
            print(f"\n  Run: python -m librarian scaffold --template <name>")

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

    # Naming-enforcement hook opt-in (middle-option: ship disabled, project-gated)
    enforce_hook: bool
    if args.enable_hook:
        enforce_hook = True
    elif args.no_hook:
        enforce_hook = False
    elif sys.stdin.isatty() and sys.stdout.isatty():
        prompt = (
            "\nLibrarian can block writes to files whose names don't match\n"
            "  descriptive-name-YYYYMMDD-VX.Y.ext\n"
            "Enable naming-enforcement hook for this project? [y/N]: "
        )
        try:
            ans = input(prompt).strip().lower()
        except EOFError:
            ans = ""
        enforce_hook = ans in ("y", "yes")
    else:
        enforce_hook = False

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
        # Middle-option hook gate: plugin ships hook disabled globally; this flag
        # lets a project opt in once the hook is enabled in hooks/hooks.json.
        "enforce_naming_hook": enforce_hook,
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

    # Naming-enforcement hook status message
    if enforce_hook:
        print("  Hook:      ENABLED in project config. To activate globally,")
        print("             edit <plugin>/hooks/hooks.json and rename")
        print("             '_PreToolUse' → 'PreToolUse'.")
    else:
        print("  Hook:      disabled (run `librarian init --force --enable-hook` to opt in)")

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
    p_audit.add_argument("--recommend", action="store_true",
                         help="include document gap recommendations")
    p_audit.add_argument("--json", action="store_true",
                         help="output as JSON instead of text")
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
    p_reg.add_argument("--review-by", dest="review_by", metavar="YYYY-MM-DD",
                       help="schedule a next_review deadline for this document")
    p_reg.set_defaults(func=cmd_register)

    # --- bump
    p_bump = sub.add_parser("bump", help="Bump a document version")
    p_bump.add_argument("filename", help="current filename to bump")
    p_bump.add_argument("--major", action="store_true", help="bump major, reset minor to 0")
    bump_review = p_bump.add_mutually_exclusive_group()
    bump_review.add_argument(
        "--review-by", dest="review_by", metavar="YYYY-MM-DD",
        help="override the inherited next_review deadline on the new version",
    )
    bump_review.add_argument(
        "--clear-review", action="store_true",
        help="drop next_review from the new version (do not inherit)",
    )
    p_bump.set_defaults(func=cmd_bump)

    # --- review (set / clear / list)
    p_review = sub.add_parser(
        "review",
        help="Manage per-document review deadlines (next_review field)",
    )
    review_sub = p_review.add_subparsers(dest="review_action")
    p_rset = review_sub.add_parser("set", help="set or update a review deadline")
    p_rset.add_argument("filename", help="registered filename")
    p_rset.add_argument("--by", required=True, metavar="YYYY-MM-DD",
                        help="ISO 8601 date when this document is next due for review")
    p_rclear = review_sub.add_parser("clear", help="remove the review deadline")
    p_rclear.add_argument("filename", help="registered filename")
    p_rlist = review_sub.add_parser("list", help="list documents with review deadlines")
    p_rlist_mode = p_rlist.add_mutually_exclusive_group()
    p_rlist_mode.add_argument("--overdue", action="store_true",
                              help="only docs whose deadline has passed")
    p_rlist_mode.add_argument("--upcoming", action="store_true",
                              help="only docs due within the next --within-days")
    p_rlist.add_argument("--within-days", dest="within_days", type=int, default=30,
                         help="window for --upcoming (default: 30)")
    p_review.set_defaults(func=cmd_review)

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
    p_site.set_defaults(func=cmd_site)

    # --- oplog (Phase 7.5)
    p_oplog = sub.add_parser(
        "oplog",
        help="Inspect the operation-log append-only lock state",
    )
    oplog_sub = p_oplog.add_subparsers(dest="oplog_action")
    oplog_sub.add_parser(
        "status",
        help="show whether the oplog file is kernel-enforced append-only",
    )
    p_oplog.set_defaults(func=cmd_oplog)

    # --- log (Phase C)
    p_log = sub.add_parser("log", help="View the operation log")
    p_log.add_argument("--log-path", help="explicit path to the JSONL log file")
    p_log.add_argument("--since", help="show entries from this ISO timestamp onward")
    p_log.add_argument("--last", type=int, help="show only the last N entries")
    p_log.set_defaults(func=cmd_log)

    # --- scaffold (Phase G)
    p_scaffold = sub.add_parser("scaffold", help="Create a new document from a template")
    p_scaffold.add_argument("--template", help="template ID (e.g., project-plan, readme)")
    p_scaffold.add_argument("--title", help="override the document title")
    p_scaffold.add_argument("--folder", help="override the output folder")
    p_scaffold.add_argument("--author", help="override the default author")
    p_scaffold.add_argument("--preset", help="preset for template resolution")
    p_scaffold.add_argument("--list", action="store_true", help="list templates for the project's preset")
    p_scaffold.add_argument("--list-all", action="store_true", help="list all templates across all presets")
    p_scaffold.add_argument("--dry-run", action="store_true", help="preview without writing files")
    p_scaffold.add_argument("--no-register", action="store_true", help="create file but skip registry entry")
    p_scaffold.add_argument("--review-by", dest="review_by", metavar="YYYY-MM-DD",
                            help="schedule a next_review deadline for the new document")
    p_scaffold.set_defaults(func=cmd_scaffold)

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
    p_init.add_argument("--enable-hook", action="store_true",
                        help="opt into naming-enforcement PreToolUse hook (sets enforce_naming_hook: true)")
    p_init.add_argument("--no-hook", action="store_true",
                        help="skip the hook opt-in prompt (sets enforce_naming_hook: false)")
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
