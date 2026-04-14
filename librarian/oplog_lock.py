"""OS-level append-only enforcement for the operation log (Phase 7.5).

The oplog stores plaintext JSON entries with optional SHA-256 hash chaining.
The hash chain is *detect-only* — an attacker with write access to the log
file can modify any entry and recompute the chain forward to produce a
structurally-valid but semantically-false log.

Kernel-enforced append-only flags close that gap. When set:

* macOS: ``chflags uappend <file>`` — only opens with ``O_APPEND`` succeed;
  random-offset writes and truncation return ``EPERM``.
* Linux: ``chattr +a <file>`` (requires root) — same semantics; supported
  on ext*, xfs, btrfs; not on tmpfs, NTFS, many network filesystems.

The librarian's existing :func:`librarian.oplog.append` already uses
``open(path, "a")`` which maps to ``O_APPEND`` on POSIX, so normal operation
is unaffected once the flag is set.

This module provides *detection* and user-facing instructions only.
Applying the flag is out of band — it lives in ``scripts/librarian-oplog-lock-*.sh``
because Linux requires sudo, which we do not want to gate library calls on.

Detection semantics:

* ``True`` — file exists and the OS append-only flag is set.
* ``False`` — file exists and the flag is NOT set.
* ``None`` — undetectable (unsupported OS, missing probe tool,
  file does not exist, or permission denied on stat).

``None`` is treated as advisory in the audit — we don't fail, we just don't
have information. This keeps the audit usable on Windows, CI containers,
and any environment where attribute probes are restricted.
"""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
from pathlib import Path


__all__ = [
    "platform_support",
    "is_append_only",
    "lock_instructions",
    "unlock_instructions",
]


def platform_support() -> str:
    """Return which append-only mechanism applies on this host.

    Returns one of ``"macos"``, ``"linux"``, or ``"unsupported"``.
    """
    sysname = platform.system()
    if sysname == "Darwin":
        return "macos"
    if sysname == "Linux":
        return "linux"
    return "unsupported"


def is_append_only(path: str | Path) -> bool | None:
    """Detect whether *path* has the OS append-only flag set.

    Returns ``True`` / ``False`` / ``None`` per module docstring semantics.
    Never raises.
    """
    p = Path(path)
    if not p.exists():
        return None

    plat = platform_support()
    if plat == "macos":
        return _is_append_only_macos(p)
    if plat == "linux":
        return _is_append_only_linux(p)
    return None


def _is_append_only_macos(p: Path) -> bool | None:
    """macOS: check ``st_flags & UF_APPEND``.

    ``stat.UF_APPEND`` is the BSD user-append flag (value 0x00000004).
    Available in Python's stat module on all POSIX builds, but only
    meaningful on Darwin / BSD kernels.
    """
    uf_append = getattr(stat, "UF_APPEND", 0x00000004)
    try:
        flags = os.stat(p).st_flags  # type: ignore[attr-defined]
    except (OSError, AttributeError):
        return None
    return bool(flags & uf_append)


def _is_append_only_linux(p: Path) -> bool | None:
    """Linux: shell out to ``lsattr`` and parse for the ``a`` flag.

    ``lsattr`` ships with e2fsprogs; present by default on every mainstream
    Linux distro. If it's missing or returns non-zero (e.g., unsupported
    filesystem), we return ``None`` — undetectable, not absent.

    Output format (one line per file):
        ``----i---a------- /path/to/file``
    We look for ``a`` anywhere in the attribute column (everything before the
    first run of whitespace).
    """
    lsattr = shutil.which("lsattr")
    if not lsattr:
        return None
    try:
        result = subprocess.run(
            [lsattr, "-d", str(p)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on whitespace — attribute column is first token.
        attr_col = line.split(None, 1)[0]
        # Only look at characters up to any dashes/zeros; 'a' indicates append-only.
        return "a" in attr_col
    return None


def lock_instructions(path: str | Path) -> str:
    """Return a human-readable command the user should run to apply the flag.

    Intended for CLI output and audit-page hints. Does NOT execute.
    """
    p = Path(path).resolve()
    plat = platform_support()
    if plat == "macos":
        return f"chflags uappend {p}"
    if plat == "linux":
        return f"sudo chattr +a {p}"
    return "(append-only lock not supported on this OS)"


def unlock_instructions(path: str | Path) -> str:
    """Return a human-readable command the user should run to remove the flag.

    Needed for log rotation, archival, or clean uninstall.
    """
    p = Path(path).resolve()
    plat = platform_support()
    if plat == "macos":
        return f"chflags nouappend {p}"
    if plat == "linux":
        return f"sudo chattr -a {p}"
    return "(append-only lock not supported on this OS)"
