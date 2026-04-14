"""OODA audit — files on disk vs registered."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .naming import validate as validate_name
from .oplog_lock import is_append_only, platform_support
from .registry import Registry
from .review import OverdueReview, compute_overdue

DEFAULT_SKIP_DIRS = frozenset(
    {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "dist"}
)

# When any single folder or logical group exceeds this count, suggest splitting.
DEFAULT_FOLDER_THRESHOLD = 15


@dataclass
class FolderSuggestion:
    """A recommendation to reorganize documents into a subfolder."""

    group_type: str  # "directory" | "tag" | "status"
    group_name: str  # e.g. "docs" or "phase-a"
    count: int
    suggestion: str  # human-readable recommendation


@dataclass
class AuditReport:
    registered: set[str] = field(default_factory=set)
    on_disk: set[str] = field(default_factory=set)
    unregistered: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    naming_violations: list[tuple[str, list[str]]] = field(default_factory=list)
    pending_cross_refs: list[str] = field(default_factory=list)
    folder_suggestions: list[FolderSuggestion] = field(default_factory=list)
    # Phase 7.2 — documents whose next_review deadline has passed.
    # Severity: warn (like folder_suggestions, this does NOT flip
    # AuditReport.clean to False today; keep report.clean semantics
    # stable for existing consumers).
    overdue_reviews: list[OverdueReview] = field(default_factory=list)

    # Phase 7.5 — OS-level append-only flag state on the oplog file.
    # True  = kernel-enforced append-only (tamper-resistant)
    # False = no OS protection (detect-only via hash chain)
    # None  = undetectable (unsupported OS, missing tools, no log yet)
    # Advisory only — does NOT flip `clean`. Surfaced in the audit
    # report and on the Audit page as informational.
    oplog_locked: bool | None = None
    oplog_path: str = ""  # resolved path used for the lock probe

    @property
    def clean(self) -> bool:
        # folder_suggestions and overdue_reviews are advisory — they don't
        # fail the audit. This preserves the exit-code contract for existing
        # automation that relies on `audit` returning 0 for compliant repos.
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


def audit(
    registry: Registry,
    repo_root: str | Path,
    *,
    folder_threshold: int = DEFAULT_FOLDER_THRESHOLD,
) -> AuditReport:
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
    # they may be archived or intentionally removed).  Also check the
    # registered *path* for files that live outside tracked_dirs (e.g.
    # README.md at the project root).
    for name in sorted(report.registered - report.on_disk):
        doc = registry.get_document(name)
        if doc and doc.get("status") == "superseded":
            continue
        # Check if the file actually exists via its registered path
        doc_path = doc.get("path", "") if doc else ""
        if doc_path and (repo_root / doc_path).exists():
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

    # Folder density analysis
    report.folder_suggestions = _analyze_folder_density(
        registry, threshold=folder_threshold
    )

    # Phase 7.2 — overdue review deadlines
    report.overdue_reviews = compute_overdue(registry.documents)

    # Phase 7.5 — oplog append-only detection
    oplog_path = repo_root / "operator" / "librarian-audit.jsonl"
    report.oplog_path = str(oplog_path)
    report.oplog_locked = is_append_only(oplog_path)

    return report


def _analyze_folder_density(
    registry: Registry,
    *,
    threshold: int = DEFAULT_FOLDER_THRESHOLD,
) -> list[FolderSuggestion]:
    """Check document groupings and suggest splits when groups are too large."""
    suggestions: list[FolderSuggestion] = []
    documents = registry.documents

    if not documents:
        return suggestions

    # 1. Check by directory — most actionable
    by_dir: dict[str, list[str]] = defaultdict(list)
    for doc in documents:
        path = doc.get("path", doc.get("filename", ""))
        parent = str(PurePosixPath(path).parent) if "/" in path else "."
        by_dir[parent].append(doc.get("filename", ""))

    for dirname, files in sorted(by_dir.items()):
        if len(files) > threshold:
            suggestions.append(
                FolderSuggestion(
                    group_type="directory",
                    group_name=dirname,
                    count=len(files),
                    suggestion=(
                        f'Directory "{dirname}" has {len(files)} documents '
                        f"(threshold: {threshold}). Consider splitting by "
                        f"status or topic into subdirectories."
                    ),
                )
            )

    # 2. Check by tag — suggest tag-based folders
    by_tag: dict[str, list[str]] = defaultdict(list)
    for doc in documents:
        for tag in doc.get("tags") or []:
            by_tag[tag].append(doc.get("filename", ""))

    for tag, files in sorted(by_tag.items()):
        if len(files) > threshold:
            suggestions.append(
                FolderSuggestion(
                    group_type="tag",
                    group_name=tag,
                    count=len(files),
                    suggestion=(
                        f'Tag "{tag}" spans {len(files)} documents '
                        f"(threshold: {threshold}). Consider grouping "
                        f'"{tag}" documents into a dedicated folder.'
                    ),
                )
            )

    return suggestions


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

    if report.folder_suggestions:
        lines.append(f"-- Folder suggestions ({len(report.folder_suggestions)}) --")
        for fs in report.folder_suggestions:
            lines.append(f"  ~ {fs.suggestion}")
        lines.append("")

    if report.overdue_reviews:
        lines.append(f"-- Overdue reviews ({len(report.overdue_reviews)}) --")
        for rev in report.overdue_reviews:
            lines.append(
                f"  ~ {rev.filename}  (due {rev.next_review.isoformat()}, "
                f"{rev.days_overdue}d overdue)"
            )
        lines.append("")

    # Phase 7.5 — oplog lock status line. Informational, one line.
    if report.oplog_locked is True:
        lines.append("  Oplog lock: ENABLED (kernel-enforced append-only)")
    elif report.oplog_locked is False:
        lines.append(
            "  Oplog lock: disabled (detect-only hash chain). "
            "Enable: scripts/librarian-oplog-lock-20260414-V1.0.sh lock"
        )
    # None = undetectable — stay silent to avoid noise on Windows/CI

    if report.clean:
        lines.append("  OK: all clean.")
    lines.append(bar)
    return "\n".join(lines)
