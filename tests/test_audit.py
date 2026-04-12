"""Audit report tests."""

from librarian.audit import audit
from librarian.registry import Registry


class TestAuditClean:
    def test_baseline_state_is_clean(self, temp_repo, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        report = audit(reg, temp_repo)
        assert report.clean
        # docs/ contains the baseline + REGISTRY.yaml; both appear in on_disk
        assert "baseline-doc-20260101-V1.0.md" in report.on_disk
        assert "REGISTRY.yaml" in report.on_disk


class TestAuditUnregistered:
    def test_detects_unregistered(self, temp_repo, temp_registry_path):
        (temp_repo / "docs" / "orphan-20260411-V1.0.md").write_text("# orphan\n")
        reg = Registry.load(temp_registry_path)
        report = audit(reg, temp_repo)
        assert not report.clean
        assert "orphan-20260411-V1.0.md" in report.unregistered


class TestAuditMissing:
    def test_detects_missing(self, temp_repo, temp_registry_path):
        (temp_repo / "docs" / "baseline-doc-20260101-V1.0.md").unlink()
        reg = Registry.load(temp_registry_path)
        report = audit(reg, temp_repo)
        assert not report.clean
        assert "baseline-doc-20260101-V1.0.md" in report.missing

    def test_superseded_missing_is_not_flagged(self, temp_repo, temp_registry_path):
        # Mark the baseline as superseded and delete it — should NOT flag
        reg = Registry.load(temp_registry_path)
        reg.add_document(
            {
                "filename": "baseline-doc-20260411-V1.1.md",
                "status": "active",
                "path": "docs/baseline-doc-20260411-V1.1.md",
            }
        )
        reg.supersede(
            "baseline-doc-20260101-V1.0.md",
            "baseline-doc-20260411-V1.1.md",
        )
        reg.save()
        (temp_repo / "docs" / "baseline-doc-20260101-V1.0.md").unlink()
        # Need to also create the new file on disk so it isn't flagged missing
        (temp_repo / "docs" / "baseline-doc-20260411-V1.1.md").write_text("# v1.1\n")

        reg2 = Registry.load(temp_registry_path)
        report = audit(reg2, temp_repo)
        assert "baseline-doc-20260101-V1.0.md" not in report.missing


class TestAuditNamingViolations:
    def test_detects_naming_violation(self, temp_repo, temp_registry_path):
        (temp_repo / "docs" / "badname.md").write_text("# bad\n")
        reg = Registry.load(temp_registry_path)
        report = audit(reg, temp_repo)
        assert not report.clean
        assert any(name == "badname.md" for name, _ in report.naming_violations)

    def test_exempt_bypasses_naming(self, temp_repo, temp_registry_path):
        # README.md is in the exempt list from SAMPLE_REGISTRY
        (temp_repo / "docs" / "README.md").write_text("# readme\n")
        reg = Registry.load(temp_registry_path)
        report = audit(reg, temp_repo)
        assert not any(name == "README.md" for name, _ in report.naming_violations)
        assert "README.md" not in report.unregistered
