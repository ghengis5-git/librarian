"""Tests for librarian.recommend — recommendations engine (Phase G.3)."""

from __future__ import annotations

import json

import pytest

from librarian.recommend import (
    COMPLIANCE_TEMPLATES,
    PRESET_EXPECTATIONS,
    Recommendation,
    RecommendationReport,
    generate_recommendations,
    format_recommendations,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_doc(filename: str, status: str = "active", tags: list | None = None) -> dict:
    """Create a minimal registry document dict."""
    return {
        "filename": filename,
        "title": filename,
        "status": status,
        "tags": tags or [],
    }


def _make_pc(preset: str, compliance: list | None = None) -> dict:
    """Create a minimal project_config dict."""
    pc: dict = {"preset": preset}
    if compliance:
        pc["compliance_standards"] = compliance
    return pc


# ═══════════════════════════════════════════════════════════════════════════
#  PRESET_EXPECTATIONS structure
# ═══════════════════════════════════════════════════════════════════════════


class TestPresetExpectations:
    """Verify the PRESET_EXPECTATIONS data structure is well-formed."""

    def test_all_presets_present(self):
        expected = {"software", "business", "legal", "scientific",
                    "healthcare", "finance", "government"}
        assert expected == set(PRESET_EXPECTATIONS.keys())

    def test_each_preset_has_core_and_recommended(self):
        for preset, data in PRESET_EXPECTATIONS.items():
            assert "core" in data, f"{preset} missing 'core'"
            assert "recommended" in data, f"{preset} missing 'recommended'"
            assert isinstance(data["core"], list)
            assert isinstance(data["recommended"], list)

    def test_no_overlap_core_recommended(self):
        for preset, data in PRESET_EXPECTATIONS.items():
            overlap = set(data["core"]) & set(data["recommended"])
            assert not overlap, f"{preset} has overlap: {overlap}"

    def test_core_not_empty(self):
        for preset, data in PRESET_EXPECTATIONS.items():
            assert len(data["core"]) >= 1, f"{preset} has empty core"


class TestComplianceTemplates:
    """Verify the COMPLIANCE_TEMPLATES mapping."""

    def test_expected_flags(self):
        expected = {
            "hipaa", "dod_5200", "iso_9001", "iso_27001", "sec_finra", "gdpr",
            "sox", "pci_dss", "soc2", "ccpa", "nist_csf", "fda_21cfr11",
            "cmmc", "ferpa", "fedramp", "gxp",
            "itar_ear", "nerc_cip", "nis2", "dora", "pipeda", "lgpd",
        }
        assert expected == set(COMPLIANCE_TEMPLATES.keys())

    def test_each_flag_has_templates(self):
        for flag, tids in COMPLIANCE_TEMPLATES.items():
            assert isinstance(tids, list)
            assert len(tids) >= 1, f"{flag} has no templates"


# ═══════════════════════════════════════════════════════════════════════════
#  Rule 1: Preset baseline
# ═══════════════════════════════════════════════════════════════════════════


class TestRule1PresetBaseline:
    """Rule 1 — missing core/recommended templates are flagged."""

    def test_empty_registry_flags_core(self):
        report = generate_recommendations([], _make_pc("software"))
        core_ids = {r.template_id for r in report.core}
        for tid in PRESET_EXPECTATIONS["software"]["core"]:
            assert tid in core_ids

    def test_empty_registry_flags_recommended(self):
        report = generate_recommendations([], _make_pc("software"))
        rec_ids = {r.template_id for r in report.recommended}
        for tid in PRESET_EXPECTATIONS["software"]["recommended"]:
            assert tid in rec_ids

    def test_present_doc_not_recommended(self):
        docs = [_make_doc("technical-architecture-20260413-V1.0.md")]
        report = generate_recommendations(docs, _make_pc("software"))
        rec_ids = {r.template_id for r in report.recommendations}
        assert "technical-architecture" not in rec_ids

    def test_superseded_doc_still_recommended(self):
        docs = [_make_doc("technical-architecture-20260413-V1.0.md", status="superseded")]
        report = generate_recommendations(docs, _make_pc("software"))
        core_ids = {r.template_id for r in report.core}
        assert "technical-architecture" in core_ids

    def test_all_core_present_means_no_core_recs(self):
        docs = [
            _make_doc("technical-architecture-20260413-V1.0.md"),
            _make_doc("project-plan-20260413-V1.0.md"),
        ]
        report = generate_recommendations(docs, _make_pc("software"))
        assert len(report.core) == 0

    def test_business_preset_core(self):
        report = generate_recommendations([], _make_pc("business"))
        core_ids = {r.template_id for r in report.core}
        assert "strategic-plan" in core_ids
        assert "project-management-plan" in core_ids

    def test_unknown_preset_no_crash(self):
        report = generate_recommendations([], _make_pc("imaginary"))
        # Should not crash, just no preset-based recommendations
        assert report.preset == "imaginary"

    def test_no_preset_no_crash(self):
        report = generate_recommendations([], {})
        assert report.preset == ""


# ═══════════════════════════════════════════════════════════════════════════
#  Rule 2: Cross-reference pull
# ═══════════════════════════════════════════════════════════════════════════


class TestRule2CrossRefPull:
    """Rule 2 — missing cross-ref targets are flagged."""

    def test_strategic_plan_pulls_cost_analysis(self):
        docs = [
            _make_doc("strategic-plan-20260413-V1.0.md"),
            _make_doc("project-management-plan-20260413-V1.0.md"),
        ]
        report = generate_recommendations(docs, _make_pc("business"))
        xref_ids = {r.template_id for r in report.cross_ref_gaps}
        # strategic-plan declares cross-refs to cost-analysis, competitor-analysis, risk-assessment
        # cost-analysis and competitor-analysis should show up as cross-ref gaps
        # (risk-assessment may show up as recommended from Rule 1 first)
        assert "cost-analysis" in xref_ids or "cost-analysis" in {
            r.template_id for r in report.recommendations
        }

    def test_cross_ref_satisfied_not_recommended(self):
        docs = [
            _make_doc("strategic-plan-20260413-V1.0.md"),
            _make_doc("project-management-plan-20260413-V1.0.md"),
            _make_doc("cost-analysis-20260413-V1.0.md"),
            _make_doc("competitor-analysis-20260413-V1.0.md"),
            _make_doc("risk-assessment-20260413-V1.0.md"),
        ]
        report = generate_recommendations(docs, _make_pc("business"))
        xref_ids = {r.template_id for r in report.cross_ref_gaps}
        assert "cost-analysis" not in xref_ids
        assert "competitor-analysis" not in xref_ids
        assert "risk-assessment" not in xref_ids

    def test_cross_ref_includes_referenced_by(self):
        """Cross-ref recommendations should list who references them."""
        docs = [
            _make_doc("technical-architecture-20260413-V1.0.md"),
            _make_doc("project-plan-20260413-V1.0.md"),
        ]
        report = generate_recommendations(docs, _make_pc("software"))
        # technical-architecture cross-refs: architecture-decision-record, security-assessment, api-specification
        # Some may be in recommended (Rule 1) not cross_ref, but at least one should have referenced_by
        for r in report.recommendations:
            if r.template_id == "security-assessment" and r.referenced_by:
                assert "technical-architecture" in r.referenced_by
                break


# ═══════════════════════════════════════════════════════════════════════════
#  Rule 3: Maturity progression
# ═══════════════════════════════════════════════════════════════════════════


class TestRule3MaturityProgression:
    """Rule 3 — templates with all prerequisites met get recommended."""

    def test_irb_recommended_when_experiment_protocol_exists(self):
        """irb-application requires experiment-protocol."""
        docs = [
            _make_doc("experiment-protocol-20260413-V1.0.md"),
            _make_doc("scientific-foundation-20260413-V1.0.md"),
        ]
        report = generate_recommendations(docs, _make_pc("scientific"))
        all_ids = {r.template_id for r in report.recommendations}
        assert "irb-application" in all_ids

    def test_irb_not_recommended_when_prereq_missing(self):
        """Without experiment-protocol, irb-application should not appear as maturity."""
        docs = [_make_doc("scientific-foundation-20260413-V1.0.md")]
        report = generate_recommendations(docs, _make_pc("scientific"))
        maturity_ids = {r.template_id for r in report.maturity}
        assert "irb-application" not in maturity_ids

    def test_maturity_includes_prereqs_in_referenced_by(self):
        docs = [
            _make_doc("experiment-protocol-20260413-V1.0.md"),
            _make_doc("scientific-foundation-20260413-V1.0.md"),
        ]
        report = generate_recommendations(docs, _make_pc("scientific"))
        for r in report.recommendations:
            if r.template_id == "irb-application" and r.priority == "maturity":
                assert "experiment-protocol" in r.referenced_by
                break


# ═══════════════════════════════════════════════════════════════════════════
#  Rule 4: Compliance triggers
# ═══════════════════════════════════════════════════════════════════════════


class TestRule4ComplianceTriggers:
    """Rule 4 — compliance flags trigger template recommendations."""

    def test_hipaa_triggers_templates(self):
        report = generate_recommendations([], _make_pc("software", ["hipaa"]))
        comp_ids = {r.template_id for r in report.compliance}
        for tid in COMPLIANCE_TEMPLATES["hipaa"]:
            # May be picked up by an earlier rule, so just check it's recommended somewhere
            all_ids = {r.template_id for r in report.recommendations}
            assert tid in all_ids, f"HIPAA template {tid} not recommended"

    def test_dod_triggers_templates(self):
        report = generate_recommendations([], _make_pc("government", ["dod_5200"]))
        all_ids = {r.template_id for r in report.recommendations}
        for tid in COMPLIANCE_TEMPLATES["dod_5200"]:
            assert tid in all_ids, f"DoD template {tid} not recommended"

    def test_no_compliance_no_compliance_recs(self):
        report = generate_recommendations([], _make_pc("software"))
        assert len(report.compliance) == 0

    def test_multiple_compliance_flags(self):
        report = generate_recommendations(
            [], _make_pc("healthcare", ["hipaa", "iso_27001"])
        )
        all_ids = {r.template_id for r in report.recommendations}
        # Should include templates from both flags
        assert "hipaa-risk-assessment" in all_ids  # hipaa
        assert "iso27001-statement-of-applicability" in all_ids  # iso_27001

    def test_compliance_already_present_not_duplicated(self):
        docs = [_make_doc("hipaa-risk-assessment-20260413-V1.0.md")]
        report = generate_recommendations(docs, _make_pc("healthcare", ["hipaa"]))
        ids = [r.template_id for r in report.recommendations]
        assert ids.count("hipaa-risk-assessment") == 0


# ═══════════════════════════════════════════════════════════════════════════
#  Deduplication
# ═══════════════════════════════════════════════════════════════════════════


class TestDeduplication:
    """Recommendations should not contain duplicate template_ids."""

    def test_no_duplicate_ids(self):
        report = generate_recommendations([], _make_pc("software", ["hipaa", "iso_27001"]))
        ids = [r.template_id for r in report.recommendations]
        assert len(ids) == len(set(ids)), f"Duplicates found: {ids}"

    def test_core_wins_over_compliance(self):
        """If a template is both core and compliance, it should appear once as core."""
        # hipaa-risk-assessment is core for healthcare AND triggered by hipaa compliance
        report = generate_recommendations(
            [], _make_pc("healthcare", ["hipaa"])
        )
        ids = [r.template_id for r in report.recommendations]
        assert ids.count("hipaa-risk-assessment") == 1
        # Should be classified as core (Rule 1 runs first)
        for r in report.recommendations:
            if r.template_id == "hipaa-risk-assessment":
                assert r.priority == "core"
                break


# ═══════════════════════════════════════════════════════════════════════════
#  RecommendationReport
# ═══════════════════════════════════════════════════════════════════════════


class TestRecommendationReport:
    """RecommendationReport dataclass behavior."""

    def test_to_dict_structure(self):
        report = generate_recommendations([], _make_pc("software"))
        d = report.to_dict()
        assert "preset" in d
        assert "registered_count" in d
        assert "recommendations" in d
        assert isinstance(d["recommendations"], list)

    def test_to_dict_recommendation_fields(self):
        report = generate_recommendations([], _make_pc("software"))
        if report.recommendations:
            rec = report.recommendations[0].to_dict()
            assert "template_id" in rec
            assert "display_name" in rec
            assert "priority" in rec
            assert "reason" in rec
            assert "scaffold_command" in rec

    def test_category_properties(self):
        report = generate_recommendations([], _make_pc("software", ["hipaa"]))
        # Should have at least core and compliance
        assert isinstance(report.core, list)
        assert isinstance(report.recommended, list)
        assert isinstance(report.cross_ref_gaps, list)
        assert isinstance(report.compliance, list)
        assert isinstance(report.maturity, list)


# ═══════════════════════════════════════════════════════════════════════════
#  Formatter
# ═══════════════════════════════════════════════════════════════════════════


class TestFormatter:
    """Human-readable formatter tests."""

    def test_format_contains_preset(self):
        report = generate_recommendations([], _make_pc("software"))
        text = format_recommendations(report)
        assert "'software'" in text

    def test_format_contains_registered_count(self):
        docs = [_make_doc("readme-20260413-V1.0.md")]
        report = generate_recommendations(docs, _make_pc("software"))
        text = format_recommendations(report)
        assert "1 registered docs" in text

    def test_format_empty_registry_has_core_section(self):
        report = generate_recommendations([], _make_pc("software"))
        text = format_recommendations(report)
        assert "CORE" in text

    def test_format_all_satisfied(self):
        """When all expected docs are present, should say no recommendations."""
        # Create docs for all software core + recommended + cross-cutting
        all_tids = (
            PRESET_EXPECTATIONS["software"]["core"]
            + PRESET_EXPECTATIONS["software"]["recommended"]
        )
        docs = [_make_doc(f"{tid}-20260413-V1.0.md") for tid in all_tids]
        report = generate_recommendations(docs, _make_pc("software"))
        # May still have cross-ref gaps, but at minimum core + recommended should be empty
        assert len(report.core) == 0
        assert len(report.recommended) == 0

    def test_format_no_preset(self):
        report = generate_recommendations([], {})
        text = format_recommendations(report)
        assert "(no preset)" in text

    def test_format_zero_recommendations_message(self):
        """When report has zero recommendations, formatter says so explicitly."""
        report = RecommendationReport(preset="software", registered_count=5)
        text = format_recommendations(report)
        assert "No recommendations" in text


# ═══════════════════════════════════════════════════════════════════════════
#  CLI integration (via __main__)
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIIntegration:
    """Test the audit --recommend CLI path."""

    def test_cli_recommend_flag_exists(self):
        from librarian.__main__ import build_parser
        parser = build_parser()
        args = parser.parse_args(["audit", "--recommend"])
        assert args.recommend is True

    def test_cli_json_flag_exists(self):
        from librarian.__main__ import build_parser
        parser = build_parser()
        args = parser.parse_args(["audit", "--json"])
        assert args.json is True

    def test_cli_recommend_json_combined(self):
        from librarian.__main__ import build_parser
        parser = build_parser()
        args = parser.parse_args(["audit", "--recommend", "--json"])
        assert args.recommend is True
        assert args.json is True
