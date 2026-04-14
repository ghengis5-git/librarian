"""Librarian — document governance, version control, and registry management."""

__version__ = "0.7.4"

from .audit import AuditReport, FolderSuggestion, audit, format_report
from .config import (
    LibrarianConfig,
    NamingConfig,
    CategoryConfig,
    HeaderConfig,
    FooterConfig,
    MetadataRequirements,
    PRESETS,
    NAMING_TEMPLATES,
    load_config,
    list_presets,
    list_naming_templates,
)
from .dashboard import render as render_dashboard, write_dashboard
from .diffaudit import DiffReport, diff_manifests, format_diff
from .evidence import EvidencePack, generate_evidence, write_evidence, verify_evidence, SigningError
from .manifest import (
    DependencyEdge,
    FileHash,
    Manifest,
    generate as generate_manifest,
    write_manifest,
)
from .naming import ParsedName, ValidationResult, parse_filename, validate
from .oplog import OpLogEntry, append as oplog_append, log_operation, read_log, format_log, verify_chain
from .oplog_lock import (
    is_append_only,
    lock_instructions,
    platform_support,
    unlock_instructions,
)
from .registry import Registry
from .review import (
    OverdueReview,
    ReviewDateError,
    compute_overdue,
    compute_upcoming,
    format_review_date,
    parse_review_date,
)
from .recommend import (
    PRESET_EXPECTATIONS,
    COMPLIANCE_TEMPLATES,
    Recommendation,
    RecommendationReport,
    generate_recommendations,
    format_recommendations,
)
from .sitegen import generate_site
from .templates import (
    DocumentTemplate,
    TemplateRenderError,
    render_template,
    discover_templates,
    load_template,
    list_templates,
    build_context,
)
from .versioning import Version, bump_filename, parse_version

__all__ = [
    "__version__",
    # config
    "LibrarianConfig",
    "NamingConfig",
    "CategoryConfig",
    "HeaderConfig",
    "FooterConfig",
    "MetadataRequirements",
    "PRESETS",
    "NAMING_TEMPLATES",
    "load_config",
    "list_presets",
    "list_naming_templates",
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
    "SigningError",
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
    "verify_chain",
    # oplog_lock (Phase 7.5)
    "is_append_only",
    "lock_instructions",
    "platform_support",
    "unlock_instructions",
    # recommend
    "PRESET_EXPECTATIONS",
    "COMPLIANCE_TEMPLATES",
    "Recommendation",
    "RecommendationReport",
    "generate_recommendations",
    "format_recommendations",
    # registry
    "Registry",
    # review
    "OverdueReview",
    "ReviewDateError",
    "compute_overdue",
    "compute_upcoming",
    "format_review_date",
    "parse_review_date",
    # sitegen
    "generate_site",
    # templates
    "DocumentTemplate",
    "TemplateRenderError",
    "render_template",
    "discover_templates",
    "load_template",
    "list_templates",
    "build_context",
    # versioning
    "Version",
    "bump_filename",
    "parse_version",
]
