"""IP evidence pack — tamper-evident snapshot for patent filings and trade-secret claims.

An evidence pack bundles:
1. The full manifest (portable JSON + SHA-256 hashes + dependency graph)
2. A git commit hash anchoring the snapshot to version control
3. A generation timestamp
4. A pack-level SHA-256 seal computed over the manifest JSON

The pack is self-verifiable: re-generate the manifest, re-compute the seal,
and compare.  Any file modification, addition, or removal between pack
generation and verification will produce a different seal.

The pack is written as a single JSON file suitable for archival, email
attachment, or submission as exhibit material.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import Manifest, generate as generate_manifest
from .registry import Registry


# ------------------------------------------------------------------ data model


@dataclass
class EvidencePack:
    """A tamper-evident evidence snapshot."""

    # Identity
    pack_id: str = ""  # ISO timestamp used as unique ID
    project_name: str = ""
    generator_version: str = "0.3.0"

    # Anchors
    git_commit_hash: str = ""
    git_branch: str = ""
    git_dirty: bool = False  # True if working tree has uncommitted changes

    # Manifest
    manifest: dict[str, Any] = field(default_factory=dict)

    # Seal: SHA-256 of the deterministic manifest JSON
    manifest_json_sha256: str = ""

    # Metadata
    generated_at: str = ""
    registry_path: str = ""
    repo_root: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_pack": {
                "pack_id": self.pack_id,
                "project_name": self.project_name,
                "generator_version": self.generator_version,
                "generated_at": self.generated_at,
                "repo_root": self.repo_root,
                "registry_path": self.registry_path,
            },
            "git_anchor": {
                "commit_hash": self.git_commit_hash,
                "branch": self.git_branch,
                "dirty": self.git_dirty,
            },
            "manifest": self.manifest,
            "seal": {
                "manifest_json_sha256": self.manifest_json_sha256,
                "algorithm": "SHA-256",
                "note": "Computed over the deterministic JSON serialization of the manifest (sorted keys). Re-generate the manifest and re-hash to verify.",
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)


# ------------------------------------------------------------------ git helpers


def _git_commit_hash(repo_root: Path) -> str:
    """Get the current HEAD commit hash, or empty string if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _git_branch(repo_root: Path) -> str:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _git_is_dirty(repo_root: Path) -> bool:
    """Check if the working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(result.stdout.strip()) if result.returncode == 0 else False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ------------------------------------------------------------------ main entry


def generate_evidence(
    registry: Registry,
    repo_root: str | Path,
) -> EvidencePack:
    """Generate an IP evidence pack from a Registry and repo root.

    This function:
    1. Generates a full manifest (all three types)
    2. Reads git state (commit, branch, dirty flag)
    3. Computes a SHA-256 seal over the manifest JSON
    4. Bundles everything into an EvidencePack

    Args:
        registry: loaded Registry instance
        repo_root: path to the project root

    Returns:
        An EvidencePack dataclass ready for serialization.
    """
    repo_root = Path(repo_root).resolve()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate manifest
    manifest = generate_manifest(registry, repo_root)
    manifest_dict = manifest.to_dict()
    manifest_json = manifest.to_json()

    # Compute seal over manifest JSON
    seal = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()

    # Read git state
    commit = _git_commit_hash(repo_root)
    branch = _git_branch(repo_root)
    dirty = _git_is_dirty(repo_root)

    project_name = registry.project_config.get("project_name", "unknown")

    return EvidencePack(
        pack_id=now,
        project_name=project_name,
        generated_at=now,
        repo_root=str(repo_root),
        registry_path=str(registry.path),
        git_commit_hash=commit,
        git_branch=branch,
        git_dirty=dirty,
        manifest=manifest_dict,
        manifest_json_sha256=seal,
    )


def write_evidence(pack: EvidencePack, output_path: str | Path) -> Path:
    """Write the evidence pack to a JSON file. Returns the resolved path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pack.to_json(), encoding="utf-8")
    return output_path.resolve()


def verify_evidence(pack_path: str | Path, registry: Registry, repo_root: str | Path) -> dict[str, Any]:
    """Verify an evidence pack against the current state.

    Re-generates the manifest and compares the seal.

    Returns a dict with:
        valid: bool — True if the seal matches
        pack_seal: str — the seal stored in the pack
        current_seal: str — the seal computed from current state
        pack_commit: str — git commit in the pack
        current_commit: str — current HEAD commit
        drift_detected: bool — True if any hash differs
    """
    pack_path = Path(pack_path)
    pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
    repo_root = Path(repo_root).resolve()

    pack_seal = pack_data.get("seal", {}).get("manifest_json_sha256", "")
    pack_commit = pack_data.get("git_anchor", {}).get("commit_hash", "")

    # Re-generate manifest
    current_manifest = generate_manifest(registry, repo_root)
    current_json = current_manifest.to_json()
    current_seal = hashlib.sha256(current_json.encode("utf-8")).hexdigest()
    current_commit = _git_commit_hash(repo_root)

    return {
        "valid": pack_seal == current_seal,
        "pack_seal": pack_seal,
        "current_seal": current_seal,
        "pack_commit": pack_commit,
        "current_commit": current_commit,
        "drift_detected": pack_seal != current_seal,
    }
