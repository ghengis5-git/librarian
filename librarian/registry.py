"""REGISTRY.yaml read/write and document CRUD.

Naive read-modify-write; safe for single-user single-process use.
Cross-process locking is out of scope for Phase A — add filelock in Phase C
if we ever need concurrent write safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .config import LibrarianConfig, load_config
from .yaml_errors import YamlParseError, load_yaml


@dataclass
class Registry:
    """In-memory representation of REGISTRY.yaml."""

    path: Path
    data: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------ load/save
    @classmethod
    def load(cls, path: str | Path) -> "Registry":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"registry not found: {path}")
        # Use load_yaml for friendly parse errors (line/column + caret).
        # Propagates as YamlParseError so callers can catch it without
        # depending on PyYAML's exception hierarchy.
        data = load_yaml(path) or {}
        return cls(path=path, data=data)

    def save(self) -> None:
        with self.path.open("w") as f:
            yaml.safe_dump(
                self.data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    # ------------------------------------------------------------ config
    @property
    def project_config(self) -> dict[str, Any]:
        return self.data.get("project_config", {})

    @property
    def infrastructure_exempt(self) -> frozenset[str]:
        naming_rules = self.project_config.get("naming_rules", {})
        return frozenset(naming_rules.get("infrastructure_exempt", []))

    @property
    def tracked_dirs(self) -> list[str]:
        return self.project_config.get("tracked_dirs", ["docs/"])

    def get_config(self, preset: str = "") -> LibrarianConfig:
        """Build a fully resolved LibrarianConfig from this registry's project_config."""
        return load_config(project_config=self.project_config, preset=preset)

    # ------------------------------------------------------------ documents
    @property
    def documents(self) -> list[dict[str, Any]]:
        return self.data.setdefault("documents", [])

    def get_document(self, filename: str) -> dict[str, Any] | None:
        for doc in self.documents:
            if doc.get("filename") == filename:
                return doc
        return None

    def add_document(self, entry: dict[str, Any]) -> None:
        if "filename" not in entry:
            raise ValueError("document entry must have 'filename'")
        if self.get_document(entry["filename"]):
            raise ValueError(f"document already registered: {entry['filename']}")
        self.documents.append(entry)
        self.update_meta()

    def supersede(self, old_filename: str, new_filename: str) -> None:
        old = self.get_document(old_filename)
        if old is None:
            raise ValueError(f"document not registered: {old_filename}")
        new = self.get_document(new_filename)
        if new is None:
            raise ValueError(f"new version not registered: {new_filename}")
        old["status"] = "superseded"
        old["superseded_by"] = new_filename
        new.setdefault("supersedes", []).append(old_filename)
        self.update_meta()

    # ------------------------------------------------------------ meta
    def update_meta(self) -> None:
        meta = self.data.setdefault("registry_meta", {})
        docs = self.documents
        meta["total_documents"] = len(docs)
        meta["active"] = sum(1 for d in docs if d.get("status") == "active")
        meta["draft"] = sum(1 for d in docs if d.get("status") == "draft")
        meta["superseded"] = sum(1 for d in docs if d.get("status") == "superseded")
        meta["last_updated"] = date.today().strftime("%Y-%m-%d")
