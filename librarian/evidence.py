"""IP evidence pack — tamper-evident snapshot for patent filings and trade-secret claims.

An evidence pack bundles:
1. The full manifest (portable JSON + SHA-256 hashes + dependency graph)
2. A git commit hash anchoring the snapshot to version control
3. A generation timestamp
4. A pack-level SHA-256 seal computed over the manifest JSON
5. (Optional) A git commit signature when ``evidence_signing`` is enabled

The pack is self-verifiable: re-generate the manifest, re-compute the seal,
and compare.  Any file modification, addition, or removal between pack
generation and verification will produce a different seal.

**Signing** (feature flag): when ``evidence_signing`` is set to ``"gpg"``
or ``"ssh"`` in ``project_config``, the evidence pack captures the HEAD
commit's cryptographic signature.  This anchors the pack to an externally
verifiable identity (the key owner) without any network call.  If signing
is enabled but git is not configured for it, generation fails with a clear
error.  When set to ``"off"`` (the default), the pack works exactly as
before — SHA-256 seal only.

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
    generator_version: str = "0.7.0"

    # Anchors
    git_commit_hash: str = ""
    git_branch: str = ""
    git_dirty: bool = False  # True if working tree has uncommitted changes

    # Manifest
    manifest: dict[str, Any] = field(default_factory=dict)

    # Seal: SHA-256 of the deterministic manifest JSON
    manifest_json_sha256: str = ""

    # Signature (optional — populated when evidence_signing is gpg/ssh)
    signature: dict[str, Any] = field(default_factory=dict)

    # Metadata
    generated_at: str = ""
    registry_path: str = ""
    repo_root: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = {
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
        if self.signature:
            result["signature"] = self.signature
        return result

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


# ------------------------------------------------------------------ signing


def _git_signing_configured(repo_root: Path) -> dict[str, str]:
    """Check if git commit signing is configured. Returns config details."""
    info: dict[str, str] = {}
    for key in ("commit.gpgsign", "gpg.format", "user.signingkey"):
        try:
            result = subprocess.run(
                ["git", "config", "--get", key],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                info[key] = result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return info


def _git_verify_commit(repo_root: Path, commit_hash: str) -> dict[str, Any]:
    """Verify a git commit's signature. Returns signature details.

    Uses two separate git calls:
    1. ``git log -1 --format=%G?|%GS|%GK|%GT`` for structured fields
    2. The signature banner is ignored (it appears on stderr or mixed
       into stdout before the format output with --show-signature).

    Works for both GPG and SSH signatures.
    """
    if not commit_hash:
        return {"signed": False, "reason": "no commit hash"}

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%G?|%GS|%GK|%GT", commit_hash],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"signed": False, "reason": "git not available or timed out"}

    if result.returncode != 0:
        return {"signed": False, "reason": f"git log failed: {result.stderr.strip()[:200]}"}

    # Output is a single line: "G|signer|key_id|trust_model"
    # Take the last non-empty line to skip any banner text
    raw_lines = result.stdout.strip().splitlines()
    if not raw_lines:
        return {"signed": False, "reason": "empty git output"}

    output_line = raw_lines[-1].strip()
    parts = output_line.split("|", 3)
    if len(parts) < 4:
        return {"signed": False, "reason": f"unexpected git format: {output_line[:80]}"}

    status_code = parts[0].strip()
    signer = parts[1].strip()
    key_id = parts[2].strip()
    trust_model = parts[3].strip()

    if status_code == "N":
        return {"signed": False, "reason": "commit is not signed"}

    return {
        "signed": True,
        "status": status_code,
        "status_description": {
            "G": "good signature",
            "B": "bad signature",
            "U": "good signature, untrusted key",
            "X": "good signature, expired",
            "Y": "good signature, expired key",
            "R": "good signature, revoked key",
            "E": "cannot verify (missing key)",
        }.get(status_code, f"unknown ({status_code})"),
        "signer": signer,
        "key_id": key_id,
        "trust_model": trust_model or "gpg",
        "commit": commit_hash,
    }


class SigningError(Exception):
    """Raised when evidence_signing is enabled but signing is not configured."""
    pass


def _require_signing(repo_root: Path, mode: str) -> dict[str, Any]:
    """Validate that signing is properly configured for the requested mode.

    Args:
        repo_root: project root
        mode: "gpg" or "ssh"

    Returns:
        Signature details dict if HEAD is signed.

    Raises:
        SigningError: if signing is not configured or HEAD is unsigned.
    """
    # Check git config
    config = _git_signing_configured(repo_root)
    gpg_sign = config.get("commit.gpgsign", "false").lower()
    gpg_format = config.get("gpg.format", "openpgp")

    if gpg_sign != "true":
        raise SigningError(
            f"evidence_signing is '{mode}' but git commit signing is not enabled.\n"
            f"  Run: git config commit.gpgsign true\n"
            f"  And: git config user.signingkey <your-key-id>"
        )

    # Validate format matches requested mode
    if mode == "ssh" and gpg_format != "ssh":
        raise SigningError(
            f"evidence_signing is 'ssh' but gpg.format is '{gpg_format}'.\n"
            f"  Run: git config gpg.format ssh\n"
            f"  And: git config user.signingkey <path-to-ssh-key>"
        )
    if mode == "gpg" and gpg_format == "ssh":
        raise SigningError(
            f"evidence_signing is 'gpg' but gpg.format is 'ssh'.\n"
            f"  Run: git config gpg.format openpgp\n"
            f"  Or change evidence_signing to 'ssh' in project_config."
        )

    # Verify HEAD is signed
    commit = _git_commit_hash(repo_root)
    sig_info = _git_verify_commit(repo_root, commit)

    if not sig_info.get("signed"):
        reason = sig_info.get("reason", "unknown")
        raise SigningError(
            f"evidence_signing is '{mode}' but HEAD commit is not signed ({reason}).\n"
            f"  Ensure your latest commit was signed:\n"
            f"    git commit -S -m \"your message\"\n"
            f"  Or enable auto-signing:\n"
            f"    git config commit.gpgsign true"
        )

    return sig_info


# ------------------------------------------------------------------ main entry


def generate_evidence(
    registry: Registry,
    repo_root: str | Path,
    *,
    evidence_signing: str = "off",
) -> EvidencePack:
    """Generate an IP evidence pack from a Registry and repo root.

    This function:
    1. Generates a full manifest (all three types)
    2. Reads git state (commit, branch, dirty flag)
    3. Computes a SHA-256 seal over the manifest JSON
    4. (Optional) Captures git commit signature if evidence_signing != "off"
    5. Bundles everything into an EvidencePack

    Args:
        registry: loaded Registry instance
        repo_root: path to the project root
        evidence_signing: "off" (default), "gpg", or "ssh"

    Returns:
        An EvidencePack dataclass ready for serialization.

    Raises:
        SigningError: if evidence_signing is enabled but not properly configured.
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

    # Signing (optional)
    signature: dict[str, Any] = {}
    signing_mode = evidence_signing.strip().lower() if evidence_signing else "off"
    if signing_mode in ("gpg", "ssh"):
        signature = _require_signing(repo_root, signing_mode)

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
        signature=signature,
    )


def write_evidence(pack: EvidencePack, output_path: str | Path) -> Path:
    """Write the evidence pack to a JSON file. Returns the resolved path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pack.to_json(), encoding="utf-8")
    return output_path.resolve()


def verify_evidence(pack_path: str | Path, registry: Registry, repo_root: str | Path) -> dict[str, Any]:
    """Verify an evidence pack against the current state.

    Re-generates the manifest and compares the seal.  If the pack
    contains a signature block, also verifies the commit signature.

    Returns a dict with:
        valid: bool — True if the seal matches
        pack_seal: str — the seal stored in the pack
        current_seal: str — the seal computed from current state
        pack_commit: str — git commit in the pack
        current_commit: str — current HEAD commit
        drift_detected: bool — True if any hash differs
        signature_valid: bool | None — None if no signature, True/False otherwise
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

    result = {
        "valid": pack_seal == current_seal,
        "pack_seal": pack_seal,
        "current_seal": current_seal,
        "pack_commit": pack_commit,
        "current_commit": current_commit,
        "drift_detected": pack_seal != current_seal,
        "signature_valid": None,
    }

    # Verify signature if present
    pack_sig = pack_data.get("signature", {})
    if pack_sig and pack_sig.get("signed"):
        sig_commit = pack_sig.get("commit", "")
        if sig_commit:
            current_sig = _git_verify_commit(repo_root, sig_commit)
            result["signature_valid"] = current_sig.get("signed", False)

    return result
