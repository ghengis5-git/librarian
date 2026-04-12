"""Librarian — document governance, version control, and registry management."""

__version__ = "0.3.0"

from .audit import AuditReport, audit, format_report
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
from .versioning import Version, bump_filename, parse_version

__all__ = [
    "__version__",
    # audit
    "AuditReport",
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
    # versioning
    "Version",
    "bump_filename",
    "parse_version",
]
