"""Librarian — document governance, version control, and registry management."""

__version__ = "0.5.0"

from .audit import AuditReport, FolderSuggestion, audit, format_report
from .dashboard import render as render_dashboard, write_dashboard
from .diffaudit import DiffReport, diff_manifests, format_diff
from .evidence import EvidencePack, generate_evidence, write_evidence, verify_evidence
from .manifest import (
    DependencyEdge,
    FileHash,
    Manifest,
    generate as generate_manifest,
    write_manifest,
)
from .naming import ParsedName, ValidationResult, parse_filename, validate
from .oplog import OpLogEntry, append as oplog_append, log_operation, read_log, format_log
from .registry import Registry
from .sitegen import generate_site
from .versioning import Version, bump_filename, parse_version

__all__ = [
    "__version__",
    # dashboard
    "render_dashboard",
    "write_dashboard",
    # audit
    "AuditReport",
    "FolderSuggestion",
    "audit",
    "format_report",
    # diffaudit
    "DiffReport",
    "diff_manifests",
    "format_diff",
    # evidence
    "EvidencePack",
    "generate_evidence",
    "write_evidence",
    "verify_evidence",
    # manifest
    "DependencyEdge",
    "FileHash",
    "Manifest",
    "generate_manifest",
    "write_manifest",
    # naming
    "ParsedName",
    "ValidationResult",
    "parse_filename",
    "validate",
    # oplog
    "OpLogEntry",
    "oplog_append",
    "log_operation",
    "read_log",
    "format_log",
    # registry
    "Registry",
    # sitegen
    "generate_site",
    # versioning
    "Version",
    "bump_filename",
    "parse_version",
]
