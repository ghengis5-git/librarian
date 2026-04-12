"""Librarian — document governance, version control, and registry management."""

__version__ = "0.2.0"

from .audit import AuditReport, audit, format_report
from .manifest import (
    DependencyEdge,
    FileHash,
    Manifest,
    generate as generate_manifest,
    write_manifest,
)
from .naming import ParsedName, ValidationResult, parse_filename, validate
from .registry import Registry
from .versioning import Version, bump_filename, parse_version

__all__ = [
    "__version__",
    "AuditReport",
    "audit",
    "format_report",
    "DependencyEdge",
    "FileHash",
    "Manifest",
    "generate_manifest",
    "write_manifest",
    "ParsedName",
    "ValidationResult",
    "parse_filename",
    "validate",
    "Registry",
    "Version",
    "bump_filename",
    "parse_version",
]
