"""OODA audit — files on disk vs registered."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .naming import validate as validate_name
from .registry import Registry

DEFAULT_SKIP_DIRS = frozenset(
    {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "dist"}
)


@dataclass
class AuditReport:
    registered: set[str] = field(default_factory=set)
    on_disk: set[str] = field(default_factory=set)
    unregistered: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    naming_violations: list[tuple[str, list[str]]] = field(default_factory=list)
    pending_cross_refs: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not (
            self.unregistered
            or self.missing
            or self.naming_violations
            or self.pending_cross_refs
        )


def _walk_tracked(
    repo_root: Path,
    tracked_dirs: list[str],
    skip_dirs: frozenset[str] | set[str] = DEFAULT_SKIP_DIRS,
) -> set[Path]:
    """Walk tracked directories and return relative file paths, skipping SKIP_DIRS."""
    result: set[Path] = set()
    for td in tracked_dirs:
        base = repo_root / td
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(repo_root)
            if any(part in skip_dirs for part in rel.parts):
                continue
            result.add(rel)
    return result


def audit(registry: Registry, repo_root: str | Path) -> AuditReport:
    """Produce an audit report for the repo under the given registry."""
    repo_root = Path(repo_root)
    report = AuditReport()

    for doc in registry.documents:
        fname = doc.get("filename")
        if fname:
            report.registered.add(fname)

    disk_paths = _walk_tracked(repo_root, registry.tracked_dirs)
    for rel in disk_paths:
        report.on_disk.add(rel.name)

    exempt = registry.infrastructure_exempt

    # Unregistered: on disk but not in registry, excluding exempt
    for name in sorted(report.on_disk - report.registered):
        if name in exempt:
            continue
        report.unregistered.append(name)

    # Missing: in registry but not on disk (superseded entries excluded —
    # they may be archived or intentionally removed)
    for name in sorted(report.registered - report.on_disk):
        doc = registry.get_document(name)
        if doc and doc.get("status") == "superseded":
            continue
        report.missing.append(name)

    # Naming violations — every on-disk file, exempt bypasses
    for rel in sorted(disk_paths):
        v = validate_name(rel.name, exempt=exempt)
        if not v.valid:
            report.naming_violations.append((rel.name, list(v.errors)))

    # Pending cross-references declared in registry_meta
    meta = registry.data.get("registry_meta", {})
    pending_count = meta.get("pending_cross_reference_updates", 0)
    if pending_count:
        for doc in registry.documents:
            xrefs = doc.get("cross_references", []) or []
            for xref in xrefs:
                if isinstance(xref, dict) and xref.get("status") == "pending":
                    report.pending_cross_refs.append(
                        f"{doc.get('filename', '?')} -> {xref.get('target', '?')}"
                    )

    return report


def format_report(report: AuditReport) -> str:
    """Format an AuditReport as a human-readable string."""
    lines: list[str] = []
    bar = "=" * 55
    lines.append(bar)
    lines.append("  Librarian OODA Audit")
    lines.append(bar)
    lines.append("")
    lines.append(f"  Files on disk:  {len(report.on_disk)}")
    lines.append(f"  Registered:     {len(report.registered)}")
    lines.append("")

    if report.unregistered:
        lines.append(f"-- Unregistered files ({len(report.unregistered)}) --")
        for name in report.unregistered:
            lines.append(f"  ! {name}")
        lines.append("")

    if report.missing:
        lines.append(f"-- Missing from disk ({len(report.missing)}) --")
        for name in report.missing:
            lines.append(f"  ! {name}")
        lines.append("")

    if report.naming_violations:
        lines.append(f"-- Naming violations ({len(report.naming_violations)}) --")
        for name, errors in report.naming_violations:
            lines.append(f"  ! {name}")
            for err in errors:
                lines.append(f"      {err}")
        lines.append("")

    if report.pending_cross_refs:
        lines.append(f"-- Pending cross-refs ({len(report.pending_cross_refs)}) --")
        for x in report.pending_cross_refs:
            lines.append(f"  ! {x}")
        lines.append("")

    if report.clean:
        lines.append("  OK: all clean.")
    lines.append(bar)
    return "\n".join(lines)
