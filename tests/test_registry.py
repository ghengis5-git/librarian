"""Registry CRUD tests."""

import pytest

from librarian.registry import Registry


class TestRegistryLoad:
    def test_load_valid(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        assert reg.project_config["project_name"] == "Test Project"
        assert len(reg.documents) == 1

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Registry.load(tmp_path / "nope.yaml")


class TestGetDocument:
    def test_found(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        doc = reg.get_document("baseline-doc-20260101-V1.0.md")
        assert doc is not None
        assert doc["status"] == "active"

    def test_not_found(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        assert reg.get_document("nonexistent.md") is None


class TestAddDocument:
    def test_add_updates_meta(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        reg.add_document(
            {
                "filename": "new-doc-20260411-V1.0.md",
                "status": "draft",
            }
        )
        assert reg.get_document("new-doc-20260411-V1.0.md") is not None
        assert reg.data["registry_meta"]["total_documents"] == 2
        assert reg.data["registry_meta"]["draft"] == 1
        assert reg.data["registry_meta"]["active"] == 1

    def test_duplicate_raises(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        with pytest.raises(ValueError):
            reg.add_document({"filename": "baseline-doc-20260101-V1.0.md"})

    def test_missing_filename_raises(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        with pytest.raises(ValueError):
            reg.add_document({"status": "draft"})


class TestSupersede:
    def test_supersede_flips_status(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        reg.add_document(
            {
                "filename": "baseline-doc-20260411-V1.1.md",
                "status": "active",
            }
        )
        reg.supersede(
            "baseline-doc-20260101-V1.0.md",
            "baseline-doc-20260411-V1.1.md",
        )
        old = reg.get_document("baseline-doc-20260101-V1.0.md")
        new = reg.get_document("baseline-doc-20260411-V1.1.md")
        assert old is not None and new is not None
        assert old["status"] == "superseded"
        assert old["superseded_by"] == "baseline-doc-20260411-V1.1.md"
        assert "baseline-doc-20260101-V1.0.md" in new["supersedes"]
        assert reg.data["registry_meta"]["superseded"] == 1
        assert reg.data["registry_meta"]["active"] == 1

    def test_supersede_missing_old_raises(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        reg.add_document(
            {"filename": "new-20260411-V1.0.md", "status": "active"}
        )
        with pytest.raises(ValueError):
            reg.supersede("nonexistent.md", "new-20260411-V1.0.md")


class TestSave:
    def test_round_trip(self, temp_registry_path):
        reg = Registry.load(temp_registry_path)
        reg.add_document(
            {"filename": "round-trip-20260411-V1.0.md", "status": "draft"}
        )
        reg.save()
        reg2 = Registry.load(temp_registry_path)
        assert reg2.get_document("round-trip-20260411-V1.0.md") is not None
        assert reg2.data["registry_meta"]["total_documents"] == 2
