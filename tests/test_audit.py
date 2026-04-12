"""Audit report tests."""

from librarian.audit import audit, format_report, FolderSuggestion, _analyze_folder_density
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


class TestFolderSuggestions:
    """Tests for auto-folder density analysis."""

    def _make_registry(self, tmp_path, docs):
        """Helper to build a registry with N documents."""
        import yaml

        data = {
            "registry_meta": {"total_documents": len(docs)},
            "project_config": {
                "project_name": "Test",
                "tracked_dirs": ["docs"],
                "infrastructure_exempt": ["REGISTRY.yaml"],
            },
            "documents": docs,
        }
        reg_path = tmp_path / "docs" / "REGISTRY.yaml"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(yaml.dump(data, sort_keys=False))
        return Registry.load(str(reg_path))

    def test_no_suggestions_below_threshold(self, tmp_path):
        docs = [
            {"filename": f"doc-{i:02d}-20260101-V1.0.md", "status": "active",
             "path": f"docs/doc-{i:02d}-20260101-V1.0.md", "tags": ["core"]}
            for i in range(5)
        ]
        reg = self._make_registry(tmp_path, docs)
        suggestions = _analyze_folder_density(reg, threshold=15)
        assert suggestions == []

    def test_directory_suggestion_at_threshold(self, tmp_path):
        docs = [
            {"filename": f"doc-{i:02d}-20260101-V1.0.md", "status": "active",
             "path": f"docs/doc-{i:02d}-20260101-V1.0.md", "tags": []}
            for i in range(20)
        ]
        reg = self._make_registry(tmp_path, docs)
        suggestions = _analyze_folder_density(reg, threshold=15)
        dir_sugs = [s for s in suggestions if s.group_type == "directory"]
        assert len(dir_sugs) == 1
        assert dir_sugs[0].group_name == "docs"
        assert dir_sugs[0].count == 20

    def test_tag_suggestion_at_threshold(self, tmp_path):
        docs = [
            {"filename": f"doc-{i:02d}-20260101-V1.0.md", "status": "active",
             "path": f"docs/doc-{i:02d}-20260101-V1.0.md", "tags": ["phase-a"]}
            for i in range(18)
        ]
        reg = self._make_registry(tmp_path, docs)
        suggestions = _analyze_folder_density(reg, threshold=15)
        tag_sugs = [s for s in suggestions if s.group_type == "tag"]
        assert len(tag_sugs) == 1
        assert tag_sugs[0].group_name == "phase-a"

    def test_custom_threshold(self, tmp_path):
        docs = [
            {"filename": f"doc-{i:02d}-20260101-V1.0.md", "status": "active",
             "path": f"docs/doc-{i:02d}-20260101-V1.0.md", "tags": []}
            for i in range(6)
        ]
        reg = self._make_registry(tmp_path, docs)
        # Low threshold triggers suggestion
        suggestions = _analyze_folder_density(reg, threshold=5)
        assert len(suggestions) >= 1
        # High threshold does not
        suggestions = _analyze_folder_density(reg, threshold=50)
        assert suggestions == []

    def test_suggestions_advisory_not_fail(self, tmp_path):
        """Folder suggestions should not make the audit report 'not clean'."""
        docs = [
            {"filename": f"doc-{i:02d}-20260101-V1.0.md", "status": "active",
             "path": f"docs/doc-{i:02d}-20260101-V1.0.md", "tags": []}
            for i in range(20)
        ]
        reg = self._make_registry(tmp_path, docs)
        # Create matching files on disk
        (tmp_path / "docs").mkdir(exist_ok=True)
        for doc in docs:
            (tmp_path / doc["path"]).write_text(f"# {doc['filename']}\n")
        report = audit(reg, tmp_path, folder_threshold=15)
        assert len(report.folder_suggestions) >= 1
        # Audit should still be "clean" because suggestions are advisory
        # (there may be unregistered files from REGISTRY.yaml, so check suggestions don't affect clean)
        assert report.folder_suggestions  # has suggestions
        # The clean property does NOT check folder_suggestions
        has_violations = bool(
            report.unregistered or report.missing
            or report.naming_violations or report.pending_cross_refs
        )
        if not has_violations:
            assert report.clean

    def test_format_report_includes_suggestions(self, tmp_path):
        docs = [
            {"filename": f"doc-{i:02d}-20260101-V1.0.md", "status": "active",
             "path": f"docs/doc-{i:02d}-20260101-V1.0.md", "tags": []}
            for i in range(20)
        ]
        reg = self._make_registry(tmp_path, docs)
        (tmp_path / "docs").mkdir(exist_ok=True)
        for doc in docs:
            (tmp_path / doc["path"]).write_text(f"# {doc['filename']}\n")
        report = audit(reg, tmp_path, folder_threshold=15)
        text = format_report(report)
        assert "Folder suggestions" in text
        assert "threshold: 15" in text

    def test_empty_registry_no_suggestions(self, tmp_path):
        reg = self._make_registry(tmp_path, [])
        suggestions = _analyze_folder_density(reg)
        assert suggestions == []

    def test_multiple_directories(self, tmp_path):
        docs = []
        for folder in ["docs", "specs"]:
            for i in range(20):
                docs.append({
                    "filename": f"{folder}-{i:02d}-20260101-V1.0.md",
                    "status": "active",
                    "path": f"{folder}/{folder}-{i:02d}-20260101-V1.0.md",
                    "tags": [],
                })
        reg = self._make_registry(tmp_path, docs)
        suggestions = _analyze_folder_density(reg, threshold=15)
        dir_sugs = [s for s in suggestions if s.group_type == "directory"]
        assert len(dir_sugs) == 2
        names = {s.group_name for s in dir_sugs}
        assert names == {"docs", "specs"}
