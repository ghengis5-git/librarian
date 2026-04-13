"""Recommendations engine — deterministic gap analysis for document registries.

Rules (applied in order):
  1. Preset baseline — core/recommended templates expected for the preset.
  2. Cross-reference pull — if doc A exists and declares cross-refs to B, C,
     and C is missing, recommend C.
  3. Maturity progression — if a template's ``requires`` prerequisites are
     all present, recommend the template itself.
  4. Compliance triggers — if compliance flags are active in project_config,
     pull in the corresponding security/compliance templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .templates import discover_templates, DocumentTemplate


# ── Preset expectations ─────────────────────────────────────────────────────
# "core"        — docs most projects in this preset need
# "recommended" — common but not essential
# "conditional" — keyed by a trigger (compliance flag, tag, etc.)

PRESET_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "software": {
        "core": ["technical-architecture", "project-plan"],
        "recommended": [
            "security-assessment", "runbook", "test-plan",
            "architecture-decision-record", "api-specification",
        ],
    },
    "business": {
        "core": ["strategic-plan", "project-management-plan"],
        "recommended": [
            "cost-analysis", "risk-assessment",
            "competitor-analysis", "stakeholder-analysis",
            "business-case", "executive-summary",
        ],
    },
    "legal": {
        "core": ["legal-review", "contract-summary"],
        "recommended": [
            "regulatory-compliance-checklist", "nda-tracker",
            "patent-review", "ip-landscape",
        ],
    },
    "scientific": {
        "core": ["scientific-foundation", "experiment-protocol"],
        "recommended": [
            "data-management-plan", "literature-review",
            "lab-notebook-entry",
        ],
    },
    "healthcare": {
        "core": ["clinical-protocol", "hipaa-risk-assessment"],
        "recommended": [
            "quality-improvement-plan", "policy-document",
            "incident-report", "credentialing-checklist",
        ],
    },
    "finance": {
        "core": ["due-diligence-report", "compliance-review"],
        "recommended": [
            "investment-memo", "audit-finding",
            "risk-assessment-finance", "regulatory-filing-checklist",
        ],
    },
    "government": {
        "core": ["policy-directive", "standard-operating-procedure"],
        "recommended": [
            "memorandum", "acquisition-plan",
            "security-plan", "after-action-report",
        ],
    },
}

# Map compliance flags → template IDs that should be recommended when active
COMPLIANCE_TEMPLATES: dict[str, list[str]] = {
    "hipaa": [
        "hipaa-risk-assessment", "data-classification-policy",
        "incident-response-plan", "access-control-matrix",
    ],
    "dod_5200": [
        "data-classification-policy", "security-plan",
        "access-control-matrix", "threat-model",
    ],
    "iso_9001": [
        "audit-readiness-checklist", "vendor-risk-assessment",
    ],
    "iso_27001": [
        "iso27001-statement-of-applicability", "security-architecture-review",
        "threat-model", "access-control-matrix",
        "audit-readiness-checklist",
    ],
    "sec_finra": [
        "sox-controls-matrix", "audit-readiness-checklist",
        "compliance-review", "vendor-risk-assessment",
    ],
}


# ── Recommendation dataclass ────────────────────────────────────────────────

@dataclass
class Recommendation:
    """A single document recommendation."""

    template_id: str
    display_name: str
    priority: str  # "core", "recommended", "cross_ref", "compliance", "maturity"
    reason: str  # "preset_baseline", "cross_ref_gap", "maturity_progression", "compliance_trigger"
    referenced_by: list[str] = field(default_factory=list)
    scaffold_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "template_id": self.template_id,
            "display_name": self.display_name,
            "priority": self.priority,
            "reason": self.reason,
        }
        if self.referenced_by:
            d["referenced_by"] = self.referenced_by
        d["scaffold_command"] = (
            self.scaffold_command
            or f"python -m librarian scaffold --template {self.template_id}"
        )
        return d


@dataclass
class RecommendationReport:
    """Full recommendations output."""

    preset: str
    registered_count: int
    recommendations: list[Recommendation] = field(default_factory=list)

    @property
    def core(self) -> list[Recommendation]:
        return [r for r in self.recommendations if r.priority == "core"]

    @property
    def recommended(self) -> list[Recommendation]:
        return [r for r in self.recommendations if r.priority == "recommended"]

    @property
    def cross_ref_gaps(self) -> list[Recommendation]:
        return [r for r in self.recommendations if r.priority == "cross_ref"]

    @property
    def compliance(self) -> list[Recommendation]:
        return [r for r in self.recommendations if r.priority == "compliance"]

    @property
    def maturity(self) -> list[Recommendation]:
        return [r for r in self.recommendations if r.priority == "maturity"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset": self.preset,
            "registered_count": self.registered_count,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


# ── Engine ──────────────────────────────────────────────────────────────────

def generate_recommendations(
    registry_documents: list[dict[str, Any]],
    project_config: dict[str, Any] | None = None,
) -> RecommendationReport:
    """Analyse a registry and return gap recommendations.

    Parameters
    ----------
    registry_documents:
        The ``documents`` list from REGISTRY.yaml.
    project_config:
        The ``project_config`` block from REGISTRY.yaml.
    """
    pc = project_config or {}
    preset = pc.get("preset", "")

    # Build the set of template IDs that are "present" in the registry.
    # We match by checking if a template_id appears as a substring of any
    # registered filename (same heuristic as scaffold cross-ref wiring).
    present_ids = _extract_present_ids(registry_documents, preset, pc)

    report = RecommendationReport(
        preset=preset,
        registered_count=len(registry_documents),
    )

    # Deduplicate: track which template_ids we've already recommended
    seen: set[str] = set()

    # ── Rule 1: Preset baseline ──────────────────────────────────────
    expectations = PRESET_EXPECTATIONS.get(preset, {})
    templates = discover_templates(preset=preset)

    for tid in expectations.get("core", []):
        if tid not in present_ids and tid not in seen:
            tmpl = templates.get(tid)
            name = tmpl.display_name if tmpl else tid
            report.recommendations.append(Recommendation(
                template_id=tid,
                display_name=name,
                priority="core",
                reason="preset_baseline",
            ))
            seen.add(tid)

    for tid in expectations.get("recommended", []):
        if tid not in present_ids and tid not in seen:
            tmpl = templates.get(tid)
            name = tmpl.display_name if tmpl else tid
            report.recommendations.append(Recommendation(
                template_id=tid,
                display_name=name,
                priority="recommended",
                reason="preset_baseline",
            ))
            seen.add(tid)

    # ── Rule 2: Cross-reference pull ─────────────────────────────────
    for tid in present_ids:
        tmpl = templates.get(tid)
        if not tmpl:
            continue
        for ref_id in tmpl.typical_cross_refs:
            if ref_id not in present_ids and ref_id not in seen:
                ref_tmpl = templates.get(ref_id)
                name = ref_tmpl.display_name if ref_tmpl else ref_id
                # Find all present templates that reference this missing one
                referencing = _find_referencers(ref_id, present_ids, templates)
                report.recommendations.append(Recommendation(
                    template_id=ref_id,
                    display_name=name,
                    priority="cross_ref",
                    reason="cross_ref_gap",
                    referenced_by=referencing,
                ))
                seen.add(ref_id)

    # ── Rule 3: Maturity progression ─────────────────────────────────
    for tid, tmpl in templates.items():
        if tid in present_ids or tid in seen:
            continue
        if not tmpl.requires:
            continue
        # All prerequisites present → recommend this template
        if all(req in present_ids for req in tmpl.requires):
            report.recommendations.append(Recommendation(
                template_id=tid,
                display_name=tmpl.display_name,
                priority="maturity",
                reason="maturity_progression",
                referenced_by=list(tmpl.requires),
            ))
            seen.add(tid)

    # ── Rule 4: Compliance triggers ──────────────────────────────────
    compliance_flags = pc.get("compliance_standards", [])
    if isinstance(compliance_flags, list):
        for flag in compliance_flags:
            for tid in COMPLIANCE_TEMPLATES.get(flag, []):
                if tid not in present_ids and tid not in seen:
                    tmpl = templates.get(tid)
                    name = tmpl.display_name if tmpl else tid
                    report.recommendations.append(Recommendation(
                        template_id=tid,
                        display_name=name,
                        priority="compliance",
                        reason="compliance_trigger",
                    ))
                    seen.add(tid)

    return report


def _extract_present_ids(
    documents: list[dict[str, Any]],
    preset: str,
    project_config: dict[str, Any],
) -> set[str]:
    """Determine which template IDs are represented in the registry.

    Matching strategy: a template_id is "present" if any registered
    document's filename contains the template_id as a substring AND
    the document is not superseded.
    """
    templates = discover_templates(
        preset=preset,
        custom_dir=project_config.get("custom_templates_dir"),
    )
    all_ids = set(templates.keys())
    present: set[str] = set()

    for doc in documents:
        if doc.get("status") == "superseded":
            continue
        fname = doc.get("filename", "")
        for tid in all_ids:
            if tid in fname:
                present.add(tid)

    return present


def _find_referencers(
    target_id: str,
    present_ids: set[str],
    templates: dict[str, DocumentTemplate],
) -> list[str]:
    """Find all present templates whose typical_cross_refs include target_id."""
    result: list[str] = []
    for tid in sorted(present_ids):
        tmpl = templates.get(tid)
        if tmpl and target_id in tmpl.typical_cross_refs:
            result.append(tid)
    return result


# ── Formatter ───────────────────────────────────────────────────────────────

def format_recommendations(report: RecommendationReport) -> str:
    """Format a RecommendationReport as a human-readable string."""
    lines: list[str] = []
    bar = "=" * 60

    lines.append(bar)
    preset_label = f"'{report.preset}'" if report.preset else "(no preset)"
    lines.append(
        f" RECOMMENDATIONS — Based on {preset_label} preset, "
        f"{report.registered_count} registered docs"
    )
    lines.append(bar)
    lines.append("")

    if not report.recommendations:
        lines.append("  No recommendations — all expected documents are present.")
        lines.append(bar)
        return "\n".join(lines)

    # Core
    core = report.core
    if core:
        lines.append(f" CORE (expected for this preset, not yet created):")
        for r in core:
            lines.append(f'   !  {r.template_id:35s}  "{r.display_name}"')
            if r.referenced_by:
                lines.append(
                    f"      -> Referenced by: {', '.join(r.referenced_by)}"
                )
            lines.append(
                f"      -> Run: python -m librarian scaffold --template {r.template_id}"
            )
        lines.append("")

    # Recommended
    recommended = report.recommended
    if recommended:
        lines.append(f" RECOMMENDED (common for this preset):")
        for r in recommended:
            lines.append(f'   ~  {r.template_id:35s}  "{r.display_name}"')
        lines.append("")

    # Cross-ref gaps
    xref = report.cross_ref_gaps
    if xref:
        lines.append(f" CROSS-REFERENCE GAPS:")
        for r in xref:
            refs = ", ".join(r.referenced_by) if r.referenced_by else "unknown"
            lines.append(
                f"   ~  {r.template_id:35s}  Referenced by {refs} but not in registry"
            )
        lines.append("")

    # Maturity
    maturity = report.maturity
    if maturity:
        lines.append(f" MATURITY PROGRESSION:")
        for r in maturity:
            prereqs = ", ".join(r.referenced_by) if r.referenced_by else ""
            lines.append(
                f'   ~  {r.template_id:35s}  "{r.display_name}"'
            )
            if prereqs:
                lines.append(f"      -> Prerequisites met: {prereqs}")
        lines.append("")

    # Compliance
    compliance = report.compliance
    if compliance:
        lines.append(f" COMPLIANCE:")
        for r in compliance:
            lines.append(f'   ~  {r.template_id:35s}  "{r.display_name}"')
        lines.append("")
    else:
        lines.append(" COMPLIANCE:")
        lines.append(
            "   (no compliance standards selected — configure via Settings or project_config)"
        )
        lines.append("")

    lines.append(bar)
    return "\n".join(lines)
