"""Configuration system for librarian — defaults, presets, and project overrides.

Layered config:
1. Built-in defaults (DEFAULTS dict)
2. Preset packs (software, business, accounting, minimal)
3. REGISTRY.yaml project_config overrides

The merge rule is simple: project_config keys override defaults.
Lists are replaced wholesale (not appended).
Nested dicts are merged recursively.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ── Built-in defaults ──────────────────────────────────────────────────────

DEFAULTS: dict[str, Any] = {
    "project_name": "Untitled Project",
    "naming_convention": "{stem}{sep}{date}{sep}V{major}.{minor}.{ext}",
    "naming_rules": {
        "separator": "-",
        "case": "lowercase",           # lowercase | mixed | uppercase
        "date_format": "YYYYMMDD",     # YYYYMMDD | YYYY-MM-DD | off
        "version_format": "VX.Y",      # VX.Y | vX.Y | X.Y
        "domain_prefix": False,        # if True: domain-stem-date-VX.Y.ext
        "forbidden_words": ["file", "download", "output", "document"],
        "infrastructure_exempt": [],
    },
    "categories": {
        "strict_mode": False,
        "folders": [],
        "labels": {},
    },
    "tags_taxonomy": {},
    "tracked_dirs": ["docs/"],
    "default_author": "",
    "default_classification": "",
    "classification_levels": [],
    "staleness_threshold_days": 90,
    "document_header": {
        "enabled": False,
        "organization": "",
        "classification_banner": "",        # shown top+bottom of every page
        "document_id_prefix": "",           # e.g. "DOC-", "PROJ-", "POL-"
        "show_version": True,
        "show_date": True,
        "show_status": True,
        "show_page_numbers": True,          # "Page X of Y"
    },
    "document_footer": {
        "enabled": False,
        "classification_banner": "",        # repeated at bottom
        "distribution_statement": "",       # e.g. "Distribution A: Public release"
        "retention_notice": "",             # e.g. "Retain for 7 years per policy X"
        "copyright_notice": "",             # e.g. "(c) 2026 Acme Corp"
        "custom_text": "",
    },
    "document_metadata": {
        "require_owner": False,             # document must have an owner/responsible party
        "require_approver": False,          # document must have an approver field
        "require_review_date": False,       # next_review date required
        "require_distribution_list": False, # must specify who receives the doc
        "require_revision_history": False,  # must include change log
        "retention_period_days": 0,         # 0 = no auto-retention
        "review_cycle_days": 0,             # 0 = no auto-review cycle
    },
}


# ── Preset packs ───────────────────────────────────────────────────────────

PRESETS: dict[str, dict[str, Any]] = {
    "software": {
        "categories": {
            "folders": [
                "docs/",
                "specs/",
                "schemas/",
                "examples/",
                "tests/",
                "architecture/",
                "runbooks/",
                "decisions/",
            ],
            "labels": {
                "docs": "Documentation",
                "specs": "Technical Specifications",
                "schemas": "Data Schemas",
                "examples": "Examples & Samples",
                "tests": "Test Documentation",
                "architecture": "Architecture Decisions",
                "runbooks": "Operational Runbooks",
                "decisions": "Decision Records",
            },
        },
        "tags_taxonomy": {
            "domain": [
                "governance", "infrastructure", "architecture",
                "operational", "security", "api", "frontend",
                "backend", "devops", "data",
            ],
            "type": [
                "technical-spec", "design-doc", "adr", "runbook",
                "schema", "example", "readme", "changelog",
                "project-plan", "report", "postmortem",
            ],
        },
        "tracked_dirs": ["docs/", "specs/", "schemas/", "architecture/"],
    },
    "business": {
        "categories": {
            "folders": [
                "finance/",
                "legal/",
                "hr/",
                "compliance/",
                "operations/",
                "marketing/",
                "executive/",
                "procurement/",
                "corporate-governance/",
                "risk-management/",
            ],
            "labels": {
                "finance": "Finance & Treasury",
                "legal": "Legal & Contracts",
                "hr": "Human Resources",
                "compliance": "Compliance & Regulatory",
                "operations": "Operations",
                "marketing": "Marketing & Communications",
                "executive": "Executive & Board",
                "procurement": "Procurement & Vendor Management",
                "corporate-governance": "Corporate Governance",
                "risk-management": "Risk Management",
            },
        },
        "tags_taxonomy": {
            "domain": [
                "finance", "legal", "hr", "compliance",
                "operations", "marketing", "executive",
                "procurement", "risk", "strategy",
            ],
            "type": [
                "policy", "procedure", "contract", "agreement",
                "memo", "report", "presentation", "proposal",
                "minutes", "charter", "sop", "template",
            ],
        },
        "tracked_dirs": [
            "finance/", "legal/", "hr/", "compliance/",
            "operations/", "executive/",
        ],
    },
    "accounting": {
        "categories": {
            "folders": [
                "accounts-receivable/",
                "accounts-payable/",
                "general-ledger/",
                "tax/",
                "audit/",
                "financial-statements/",
                "budgets/",
                "payroll/",
                "treasury/",
                "fixed-assets/",
                "cost-accounting/",
                "regulatory-filings/",
            ],
            "labels": {
                "accounts-receivable": "Accounts Receivable (A/R)",
                "accounts-payable": "Accounts Payable (A/P)",
                "general-ledger": "General Ledger (G/L)",
                "tax": "Tax Returns & Compliance",
                "audit": "Audit & Assurance",
                "financial-statements": "Financial Statements",
                "budgets": "Budgets & Forecasts",
                "payroll": "Payroll & Benefits",
                "treasury": "Treasury & Cash Management",
                "fixed-assets": "Fixed Assets & Depreciation",
                "cost-accounting": "Cost Accounting",
                "regulatory-filings": "Regulatory Filings (SEC, GAAP, IFRS)",
            },
        },
        "tags_taxonomy": {
            "domain": [
                "accounts-receivable", "accounts-payable", "general-ledger",
                "tax", "audit", "financial-reporting", "budgeting",
                "payroll", "treasury", "fixed-assets", "cost-accounting",
                "regulatory",
            ],
            "type": [
                "invoice", "receipt", "statement", "reconciliation",
                "journal-entry", "trial-balance", "tax-return",
                "audit-report", "budget", "forecast", "variance-analysis",
                "bank-statement", "aging-report", "depreciation-schedule",
            ],
            "period": [
                "monthly", "quarterly", "annual", "ytd", "fiscal-year",
            ],
        },
        "tracked_dirs": [
            "accounts-receivable/", "accounts-payable/", "general-ledger/",
            "tax/", "audit/", "financial-statements/", "budgets/",
        ],
    },
    "government": {
        "categories": {
            "folders": [
                "policies/",
                "procedures/",
                "directives/",
                "memoranda/",
                "reports/",
                "plans/",
                "agreements/",
                "correspondence/",
                "forms/",
                "technical-data/",
                "training/",
                "audit-findings/",
            ],
            "labels": {
                "policies": "Policies & Regulations",
                "procedures": "Standard Operating Procedures (SOPs)",
                "directives": "Directives & Instructions",
                "memoranda": "Memoranda & Notices",
                "reports": "Reports & Assessments",
                "plans": "Plans & Strategies",
                "agreements": "Agreements & MOUs",
                "correspondence": "Official Correspondence",
                "forms": "Forms & Templates",
                "technical-data": "Technical Data Packages",
                "training": "Training Materials",
                "audit-findings": "Audit Findings & Corrective Actions",
            },
        },
        "tags_taxonomy": {
            "domain": [
                "policy", "operations", "security", "compliance",
                "acquisitions", "logistics", "personnel", "finance",
                "training", "communications", "legal", "technical",
            ],
            "type": [
                "policy", "sop", "directive", "memorandum", "report",
                "plan", "agreement", "mou", "moa", "form", "briefing",
                "assessment", "finding", "corrective-action", "waiver",
            ],
            "classification": [
                "unclassified", "cui", "confidential",
                "secret", "top-secret",
            ],
        },
        "classification_levels": [
            "UNCLASSIFIED",
            "CUI",
            "CONFIDENTIAL",
            "SECRET",
            "TOP SECRET",
        ],
        "tracked_dirs": [
            "policies/", "procedures/", "directives/",
            "memoranda/", "reports/", "plans/",
        ],
        "document_header": {
            "enabled": True,
            "organization": "",
            "classification_banner": "UNCLASSIFIED",
            "document_id_prefix": "DOC-",
            "show_version": True,
            "show_date": True,
            "show_status": True,
            "show_page_numbers": True,
        },
        "document_footer": {
            "enabled": True,
            "classification_banner": "UNCLASSIFIED",
            "distribution_statement": "Distribution A: Approved for public release; distribution unlimited.",
            "retention_notice": "",
            "copyright_notice": "",
            "custom_text": "",
        },
        "document_metadata": {
            "require_owner": True,
            "require_approver": True,
            "require_review_date": True,
            "require_distribution_list": True,
            "require_revision_history": True,
            "retention_period_days": 2555,
            "review_cycle_days": 365,
        },
    },
    "scientific": {
        "categories": {
            "folders": [
                "manuscripts/",
                "datasets/",
                "protocols/",
                "analysis/",
                "figures/",
                "supplementary/",
                "literature/",
                "grants/",
                "presentations/",
                "lab-notebooks/",
                "ethics-irb/",
                "raw-data/",
            ],
            "labels": {
                "manuscripts": "Manuscripts & Drafts",
                "datasets": "Processed Datasets",
                "protocols": "Protocols & Methods",
                "analysis": "Analysis Scripts & Results",
                "figures": "Figures & Visualizations",
                "supplementary": "Supplementary Materials",
                "literature": "Literature & References",
                "grants": "Grant Proposals & Reports",
                "presentations": "Conference Presentations",
                "lab-notebooks": "Lab Notebooks & Field Notes",
                "ethics-irb": "Ethics / IRB Approvals",
                "raw-data": "Raw Data (Unprocessed)",
            },
        },
        "naming_rules": {
            "separator": "_",
            "case": "mixed",
            "date_format": "YYYY-MM-DD",
            "version_format": "vX.Y",
            "domain_prefix": True,
        },
        "tags_taxonomy": {
            "domain": [
                "experiment", "analysis", "manuscript", "protocol",
                "dataset", "literature-review", "grant", "ethics",
                "field-work", "computational", "statistical",
            ],
            "type": [
                "manuscript", "preprint", "protocol", "dataset",
                "analysis-script", "figure", "supplementary",
                "grant-proposal", "progress-report", "irb-application",
                "lab-notebook", "poster", "slide-deck", "thesis-chapter",
            ],
            "status": [
                "in-preparation", "submitted", "under-review",
                "revision-requested", "accepted", "published", "archived",
            ],
        },
        "tracked_dirs": [
            "manuscripts/", "datasets/", "protocols/",
            "analysis/", "grants/",
        ],
        "document_header": {
            "enabled": True,
            "organization": "",
            "classification_banner": "",
            "document_id_prefix": "",
            "show_version": True,
            "show_date": True,
            "show_status": True,
            "show_page_numbers": True,
        },
        "document_metadata": {
            "require_owner": True,           # PI / corresponding author
            "require_approver": False,
            "require_review_date": True,     # submission / revision deadline
            "require_distribution_list": False,
            "require_revision_history": True,
            "retention_period_days": 3650,   # 10 years per NIH/NSF data retention
            "review_cycle_days": 180,
        },
    },
    "finance": {
        "categories": {
            "folders": [
                "regulatory-filings/",
                "client-reports/",
                "compliance/",
                "risk-management/",
                "trading-records/",
                "audit-trail/",
                "policies/",
                "fund-documents/",
                "correspondence/",
                "board-materials/",
                "marketing-materials/",
                "due-diligence/",
            ],
            "labels": {
                "regulatory-filings": "Regulatory Filings (SEC, FINRA, CFTC)",
                "client-reports": "Client Reports & Statements",
                "compliance": "Compliance & KYC/AML",
                "risk-management": "Risk Management & Controls",
                "trading-records": "Trading Records & Confirmations",
                "audit-trail": "Audit Trail & Examinations",
                "policies": "Policies & Procedures (WSPs)",
                "fund-documents": "Fund Documents & Offering Memos",
                "correspondence": "Client Correspondence",
                "board-materials": "Board & Committee Materials",
                "marketing-materials": "Marketing & Advertising Review",
                "due-diligence": "Due Diligence & Research",
            },
        },
        "naming_rules": {
            "separator": "-",
            "case": "lowercase",
            "date_format": "YYYYMMDD",
            "version_format": "VX.Y",
            "domain_prefix": True,
        },
        "tags_taxonomy": {
            "domain": [
                "regulatory", "compliance", "trading", "risk",
                "client", "fund", "audit", "operations",
                "legal", "marketing", "board", "research",
            ],
            "type": [
                "filing", "report", "statement", "confirmation",
                "policy", "procedure", "memo", "review",
                "prospectus", "offering-memo", "adr", "kyc-form",
                "aml-report", "sar", "ctr", "audit-finding",
            ],
            "retention": [
                "3-year", "5-year", "6-year", "7-year", "permanent",
            ],
        },
        "tracked_dirs": [
            "regulatory-filings/", "compliance/", "policies/",
            "client-reports/", "audit-trail/", "risk-management/",
        ],
        "document_header": {
            "enabled": True,
            "organization": "",
            "classification_banner": "CONFIDENTIAL",
            "document_id_prefix": "",
            "show_version": True,
            "show_date": True,
            "show_status": True,
            "show_page_numbers": True,
        },
        "document_footer": {
            "enabled": True,
            "classification_banner": "CONFIDENTIAL",
            "distribution_statement": "Internal Use Only — Not for Public Distribution",
            "retention_notice": "",
            "copyright_notice": "",
            "custom_text": "SEC Rule 17a-4 / FINRA Rule 4511 retention applies",
        },
        "document_metadata": {
            "require_owner": True,
            "require_approver": True,
            "require_review_date": True,
            "require_distribution_list": True,
            "require_revision_history": True,
            "retention_period_days": 2190,    # 6 years per FINRA 4511
            "review_cycle_days": 365,
        },
        "classification_levels": [
            "PUBLIC",
            "INTERNAL USE ONLY",
            "CONFIDENTIAL",
            "RESTRICTED",
        ],
    },
    "healthcare": {
        "categories": {
            "folders": [
                "policies/",
                "procedures/",
                "clinical-protocols/",
                "compliance/",
                "quality-assurance/",
                "patient-forms/",
                "training/",
                "incident-reports/",
                "audit/",
                "credentialing/",
                "pharmacy/",
                "infection-control/",
            ],
            "labels": {
                "policies": "Organizational Policies",
                "procedures": "Standard Operating Procedures",
                "clinical-protocols": "Clinical Protocols & Guidelines",
                "compliance": "HIPAA / Regulatory Compliance",
                "quality-assurance": "Quality Assurance & Improvement",
                "patient-forms": "Patient Forms & Consent",
                "training": "Staff Training & Competencies",
                "incident-reports": "Incident / Event Reports",
                "audit": "Audit & Accreditation",
                "credentialing": "Credentialing & Privileging",
                "pharmacy": "Pharmacy & Formulary",
                "infection-control": "Infection Prevention & Control",
            },
        },
        "naming_rules": {
            "separator": "-",
            "case": "lowercase",
            "date_format": "YYYYMMDD",
            "version_format": "VX.Y",
            "domain_prefix": True,
        },
        "tags_taxonomy": {
            "domain": [
                "clinical", "administrative", "compliance", "quality",
                "pharmacy", "nursing", "radiology", "laboratory",
                "surgery", "emergency", "behavioral-health", "it",
            ],
            "type": [
                "policy", "procedure", "protocol", "guideline",
                "form", "consent", "order-set", "care-plan",
                "incident-report", "audit-finding", "training-material",
                "competency-checklist", "credentialing-file",
            ],
            "regulatory": [
                "hipaa", "joint-commission", "cms", "osha",
                "state-doh", "clia", "emtala", "hitech",
            ],
        },
        "tracked_dirs": [
            "policies/", "procedures/", "clinical-protocols/",
            "compliance/", "quality-assurance/",
        ],
        "classification_levels": [
            "PUBLIC",
            "INTERNAL USE ONLY",
            "CONFIDENTIAL",
            "PHI - RESTRICTED",
        ],
        "document_header": {
            "enabled": True,
            "organization": "",
            "classification_banner": "CONFIDENTIAL",
            "document_id_prefix": "POL-",
            "show_version": True,
            "show_date": True,
            "show_status": True,
            "show_page_numbers": True,
        },
        "document_footer": {
            "enabled": True,
            "classification_banner": "CONFIDENTIAL",
            "distribution_statement": "Internal Use Only — Contains Protected Health Information",
            "retention_notice": "Retain per facility records retention schedule",
            "copyright_notice": "",
            "custom_text": "HIPAA Privacy Rule (45 CFR Part 164) applies to all PHI",
        },
        "document_metadata": {
            "require_owner": True,
            "require_approver": True,
            "require_review_date": True,
            "require_distribution_list": True,
            "require_revision_history": True,
            "retention_period_days": 2190,    # 6 years per HIPAA
            "review_cycle_days": 365,         # annual review typical
        },
    },
    "legal": {
        "categories": {
            "folders": [
                "matters/",
                "contracts/",
                "pleadings/",
                "correspondence/",
                "corporate/",
                "compliance/",
                "intellectual-property/",
                "litigation/",
                "templates/",
                "research/",
                "closing-binders/",
                "discovery/",
            ],
            "labels": {
                "matters": "Client Matters & Case Files",
                "contracts": "Contracts & Agreements",
                "pleadings": "Pleadings & Court Filings",
                "correspondence": "Correspondence & Letters",
                "corporate": "Corporate Governance & Entity Records",
                "compliance": "Compliance & Regulatory",
                "intellectual-property": "Intellectual Property",
                "litigation": "Litigation & Dispute Resolution",
                "templates": "Templates & Precedents",
                "research": "Legal Research & Memoranda",
                "closing-binders": "Closing Binders & Deal Records",
                "discovery": "Discovery & Document Productions",
            },
        },
        "naming_rules": {
            "separator": "-",
            "case": "mixed",
            "date_format": "YYYY-MM-DD",
            "version_format": "VX.Y",
            "domain_prefix": True,
        },
        "tags_taxonomy": {
            "domain": [
                "corporate", "litigation", "regulatory", "ip",
                "real-estate", "employment", "tax", "m-and-a",
                "bankruptcy", "environmental", "securities", "privacy",
            ],
            "type": [
                "contract", "amendment", "pleading", "motion",
                "brief", "memorandum", "opinion-letter", "due-diligence",
                "closing-checklist", "term-sheet", "engagement-letter",
                "nda", "msa", "sow", "power-of-attorney",
            ],
            "privilege": [
                "attorney-client", "work-product", "non-privileged",
            ],
        },
        "tracked_dirs": [
            "matters/", "contracts/", "pleadings/",
            "corporate/", "compliance/",
        ],
        "classification_levels": [
            "PUBLIC FILING",
            "CONFIDENTIAL",
            "ATTORNEY-CLIENT PRIVILEGED",
            "ATTORNEY WORK PRODUCT",
        ],
        "document_header": {
            "enabled": True,
            "organization": "",
            "classification_banner": "CONFIDENTIAL",
            "document_id_prefix": "",
            "show_version": True,
            "show_date": True,
            "show_status": True,
            "show_page_numbers": True,
        },
        "document_footer": {
            "enabled": True,
            "classification_banner": "CONFIDENTIAL",
            "distribution_statement": "",
            "retention_notice": "",
            "copyright_notice": "",
            "custom_text": "Privileged and Confidential — Do Not Distribute Without Authorization",
        },
        "document_metadata": {
            "require_owner": True,
            "require_approver": True,
            "require_review_date": False,
            "require_distribution_list": True,
            "require_revision_history": True,
            "retention_period_days": 2555,    # 7 years typical
            "review_cycle_days": 0,
        },
    },
    "minimal": {
        "categories": {
            "folders": [],
            "labels": {},
        },
        "tags_taxonomy": {},
        "tracked_dirs": ["docs/"],
    },
}


# ── Named naming templates ─────────────────────────────────────────────────

NAMING_TEMPLATES: dict[str, dict[str, Any]] = {
    "default": {
        "separator": "-",
        "case": "lowercase",
        "date_format": "YYYYMMDD",
        "version_format": "VX.Y",
        "domain_prefix": False,
    },
    "legal": {
        "separator": "-",
        "case": "mixed",
        "date_format": "YYYY-MM-DD",
        "version_format": "VX.Y",
        "domain_prefix": True,
    },
    "engineering": {
        "separator": "-",
        "case": "lowercase",
        "date_format": "YYYYMMDD",
        "version_format": "vX.Y",
        "domain_prefix": False,
    },
    "corporate": {
        "separator": "_",
        "case": "mixed",
        "date_format": "YYYYMMDD",
        "version_format": "VX.Y",
        "domain_prefix": True,
    },
    "dateless": {
        "separator": "-",
        "case": "lowercase",
        "date_format": "off",
        "version_format": "VX.Y",
        "domain_prefix": False,
    },
    "scientific": {
        "separator": "_",
        "case": "mixed",
        "date_format": "YYYY-MM-DD",
        "version_format": "vX.Y",
        "domain_prefix": True,
    },
    "healthcare": {
        "separator": "-",
        "case": "lowercase",
        "date_format": "YYYYMMDD",
        "version_format": "VX.Y",
        "domain_prefix": True,
    },
    "finance": {
        "separator": "-",
        "case": "lowercase",
        "date_format": "YYYYMMDD",
        "version_format": "VX.Y",
        "domain_prefix": True,
    },
}


# ── Config dataclass ───────────────────────────────────────────────────────

@dataclass
class NamingConfig:
    """Resolved naming convention settings."""
    separator: str = "-"
    case: str = "lowercase"             # lowercase | mixed | uppercase
    date_format: str = "YYYYMMDD"       # YYYYMMDD | YYYY-MM-DD | off
    version_format: str = "VX.Y"        # VX.Y | vX.Y | X.Y
    domain_prefix: bool = False
    forbidden_words: list[str] = field(default_factory=lambda: list(DEFAULTS["naming_rules"]["forbidden_words"]))
    infrastructure_exempt: list[str] = field(default_factory=list)

    @property
    def regex_pattern(self) -> str:
        """Build a regex pattern string from the current config."""
        sep = _re_escape(self.separator)
        if self.case == "lowercase":
            stem = r"[a-z0-9][a-z0-9{sep}]*[a-z0-9]".format(sep=sep)
        elif self.case == "uppercase":
            stem = r"[A-Z0-9][A-Z0-9{sep}]*[A-Z0-9]".format(sep=sep)
        else:  # mixed
            stem = r"[a-zA-Z0-9][a-zA-Z0-9{sep}]*[a-zA-Z0-9]".format(sep=sep)

        if self.date_format == "YYYYMMDD":
            date_part = r"\d{8}"
        elif self.date_format == "YYYY-MM-DD":
            date_part = r"\d{4}-\d{2}-\d{2}"
        else:  # off
            date_part = None

        if self.version_format == "VX.Y":
            ver_part = r"V(?P<major>\d+)\.(?P<minor>\d+)"
        elif self.version_format == "vX.Y":
            ver_part = r"v(?P<major>\d+)\.(?P<minor>\d+)"
        else:  # X.Y
            ver_part = r"(?P<major>\d+)\.(?P<minor>\d+)"

        ext_part = r"\.(?P<ext>[a-zA-Z0-9]+)"

        if self.domain_prefix:
            stem = f"(?P<domain>[a-zA-Z0-9]+){sep}(?P<stem>{stem})"
        else:
            stem = f"(?P<stem>{stem})"

        parts = [f"^{stem}"]
        if date_part:
            parts.append(f"(?P<date>{date_part})")
        parts.append(ver_part)

        pattern = sep.join(parts) + ext_part + "$"
        return pattern

    @property
    def human_pattern(self) -> str:
        """Human-readable naming pattern string."""
        sep = self.separator
        parts = []
        if self.domain_prefix:
            parts.append("domain")
        parts.append("descriptive-name")
        if self.date_format != "off":
            parts.append(self.date_format)
        parts.append(self.version_format)
        return sep.join(parts) + ".ext"


@dataclass
class CategoryConfig:
    """Resolved folder category settings."""
    strict_mode: bool = False
    folders: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class HeaderConfig:
    """Document header settings (top of every page)."""
    enabled: bool = False
    organization: str = ""
    classification_banner: str = ""
    document_id_prefix: str = ""
    show_version: bool = True
    show_date: bool = True
    show_status: bool = True
    show_page_numbers: bool = True


@dataclass
class FooterConfig:
    """Document footer settings (bottom of every page)."""
    enabled: bool = False
    classification_banner: str = ""
    distribution_statement: str = ""
    retention_notice: str = ""
    copyright_notice: str = ""
    custom_text: str = ""


@dataclass
class MetadataRequirements:
    """Required metadata fields for document governance."""
    require_owner: bool = False
    require_approver: bool = False
    require_review_date: bool = False
    require_distribution_list: bool = False
    require_revision_history: bool = False
    retention_period_days: int = 0
    review_cycle_days: int = 0


@dataclass
class LibrarianConfig:
    """Fully resolved configuration."""
    project_name: str = "Untitled Project"
    naming: NamingConfig = field(default_factory=NamingConfig)
    categories: CategoryConfig = field(default_factory=CategoryConfig)
    header: HeaderConfig = field(default_factory=HeaderConfig)
    footer: FooterConfig = field(default_factory=FooterConfig)
    metadata: MetadataRequirements = field(default_factory=MetadataRequirements)
    tags_taxonomy: dict[str, list[str]] = field(default_factory=dict)
    tracked_dirs: list[str] = field(default_factory=lambda: ["docs/"])
    default_author: str = ""
    default_classification: str = ""
    classification_levels: list[str] = field(default_factory=list)
    staleness_threshold_days: int = 90
    preset: str = ""  # which preset was applied, if any


# ── Merge logic ────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Lists are replaced, dicts are merged."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _re_escape(s: str) -> str:
    """Escape a character for use in a regex character class or literal."""
    special = r"\.^$*+?{}[]|()"
    return "".join(f"\\{c}" if c in special else c for c in s)


# ── Config loading ─────────────────────────────────────────────────────────

def load_defaults(preset: str = "") -> dict[str, Any]:
    """Load built-in defaults, optionally merged with a preset pack."""
    result = copy.deepcopy(DEFAULTS)
    if preset and preset in PRESETS:
        result = _deep_merge(result, PRESETS[preset])
    return result


def load_config(
    project_config: dict[str, Any] | None = None,
    preset: str = "",
) -> LibrarianConfig:
    """Build a fully resolved LibrarianConfig from defaults + preset + overrides.

    Args:
        project_config: the project_config block from REGISTRY.yaml (or None)
        preset: optional preset name to apply before project overrides

    Returns:
        Fully resolved LibrarianConfig.
    """
    merged = load_defaults(preset)

    # Handle naming template shortcut — apply template to defaults BEFORE
    # user overrides, so user-supplied values win over template values,
    # but template values win over built-in defaults.
    pc = project_config or {}
    user_nr = pc.get("naming_rules", {})
    template_name = user_nr.pop("template", None) if isinstance(user_nr, dict) else None
    if template_name and template_name in NAMING_TEMPLATES:
        template = copy.deepcopy(NAMING_TEMPLATES[template_name])
        merged["naming_rules"] = _deep_merge(merged.get("naming_rules", {}), template)

    if pc:
        merged = _deep_merge(merged, pc)

    # Build NamingConfig
    nr = merged.get("naming_rules", {})
    naming = NamingConfig(
        separator=nr.get("separator", "-"),
        case=nr.get("case", "lowercase"),
        date_format=nr.get("date_format", "YYYYMMDD"),
        version_format=nr.get("version_format", "VX.Y"),
        domain_prefix=nr.get("domain_prefix", False),
        forbidden_words=nr.get("forbidden_words", list(DEFAULTS["naming_rules"]["forbidden_words"])),
        infrastructure_exempt=nr.get("infrastructure_exempt", []),
    )

    # Build CategoryConfig
    cats = merged.get("categories", {})
    categories = CategoryConfig(
        strict_mode=cats.get("strict_mode", False),
        folders=cats.get("folders", []),
        labels=cats.get("labels", {}),
    )

    # Build HeaderConfig
    hdr = merged.get("document_header", {})
    header = HeaderConfig(
        enabled=hdr.get("enabled", False),
        organization=hdr.get("organization", ""),
        classification_banner=hdr.get("classification_banner", ""),
        document_id_prefix=hdr.get("document_id_prefix", ""),
        show_version=hdr.get("show_version", True),
        show_date=hdr.get("show_date", True),
        show_status=hdr.get("show_status", True),
        show_page_numbers=hdr.get("show_page_numbers", True),
    )

    # Build FooterConfig
    ftr = merged.get("document_footer", {})
    footer = FooterConfig(
        enabled=ftr.get("enabled", False),
        classification_banner=ftr.get("classification_banner", ""),
        distribution_statement=ftr.get("distribution_statement", ""),
        retention_notice=ftr.get("retention_notice", ""),
        copyright_notice=ftr.get("copyright_notice", ""),
        custom_text=ftr.get("custom_text", ""),
    )

    # Build MetadataRequirements
    meta = merged.get("document_metadata", {})
    metadata = MetadataRequirements(
        require_owner=meta.get("require_owner", False),
        require_approver=meta.get("require_approver", False),
        require_review_date=meta.get("require_review_date", False),
        require_distribution_list=meta.get("require_distribution_list", False),
        require_revision_history=meta.get("require_revision_history", False),
        retention_period_days=meta.get("retention_period_days", 0),
        review_cycle_days=meta.get("review_cycle_days", 0),
    )

    return LibrarianConfig(
        project_name=merged.get("project_name", "Untitled Project"),
        naming=naming,
        categories=categories,
        header=header,
        footer=footer,
        metadata=metadata,
        tags_taxonomy=merged.get("tags_taxonomy", {}),
        tracked_dirs=merged.get("tracked_dirs", ["docs/"]),
        default_author=merged.get("default_author", ""),
        default_classification=merged.get("default_classification", ""),
        classification_levels=merged.get("classification_levels", []),
        staleness_threshold_days=merged.get("staleness_threshold_days", 90),
        preset=preset,
    )


def load_defaults_file(path: str | Path) -> dict[str, Any]:
    """Load a librarian-defaults.yaml file from disk."""
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r") as f:
        data = yaml.safe_load(f) or {}
    return data


def list_presets() -> list[dict[str, str]]:
    """Return available preset packs with descriptions."""
    descriptions = {
        "software": "Software/tech projects — docs, specs, schemas, architecture, runbooks",
        "business": "Corporate/enterprise — finance, legal, HR, compliance, operations, executive",
        "accounting": "Accounting/financial — A/R, A/P, G/L, tax, audit, financial statements, budgets",
        "government": "Government/military — policies, SOPs, directives, DoD 5200.01 classification markings",
        "scientific": "Research/academic — manuscripts, datasets, protocols, IRB, NIH/NSF 10-year retention",
        "finance": "Financial services — SEC/FINRA compliance, trading records, 6-year WORM retention",
        "healthcare": "Healthcare/clinical — HIPAA, Joint Commission, clinical protocols, PHI protections",
        "legal": "Law firm/legal dept — matters, contracts, pleadings, privilege markings, Bates numbering",
        "minimal": "Empty slate — no preset categories, user defines everything",
    }
    return [
        {"name": name, "description": descriptions.get(name, "")}
        for name in PRESETS
    ]


def list_naming_templates() -> list[dict[str, str]]:
    """Return available naming templates with their patterns."""
    result = []
    for name, rules in NAMING_TEMPLATES.items():
        nc = NamingConfig(**{k: v for k, v in rules.items() if k in NamingConfig.__dataclass_fields__})
        result.append({"name": name, "pattern": nc.human_pattern})
    return result
