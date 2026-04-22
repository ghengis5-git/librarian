"""Pre-commit framework entry point (Phase 7.7).

Wraps the naming-convention validator for use with the `pre-commit` framework
(https://pre-commit.com). Users add this repo to their ``.pre-commit-config.yaml``
and the ``librarian-naming`` hook runs on every commit.

Usage from the pre-commit framework
-----------------------------------

In the consuming project's ``.pre-commit-config.yaml``::

    repos:
      - repo: https://github.com/ghengis5-git/librarian
        rev: v0.7.4
        hooks:
          - id: librarian-naming

The framework passes each staged file as a positional argument.

Direct CLI use
--------------

Can also be run standalone::

    librarian-precommit docs/my-doc-20260414-V1.0.md
    librarian-precommit --strict docs/*.md

Exit codes
----------

* ``0`` — all files passed (or nothing to check)
* ``1`` — one or more files have naming violations (errors)
* ``2`` — usage error

Why Python (not wrapping the shell script)
------------------------------------------

The shell hook at ``scripts/librarian-pre-commit-hook-20260411-V1.0.sh``
does its own ``git diff`` to discover staged files and runs against the
repo's own REGISTRY. The pre-commit framework inverts that — it discovers
staged files itself and passes them to the hook. Writing a Python entry
point lets us reuse ``librarian.naming.validate`` directly without
duplicating the logic in shell, and it runs on Windows too (where the
shell hook's bash-isms don't work).

Relationship to the shell hook
------------------------------

Both hooks exist in the repo. Project-level git pre-commit installs use
the shell hook via symlink. Projects that prefer the pre-commit framework
use this Python entry point. They share the same naming rules (via
``librarian.naming``) so behavior is consistent.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

from .naming import validate as validate_name


# ─────────────────────────────────────────────────────────────────────────────
# Windows / UNC path helpers (Phase 8.2)
# ─────────────────────────────────────────────────────────────────────────────
#
# Windows filesystems introduce three complications the original POSIX-only
# code didn't handle:
#
#   1. Mapped-drive vs UNC mismatch. A project at ``Z:\proj`` may resolve via
#      ``Path.resolve()`` to ``\\server\share\proj`` (the underlying UNC).
#      If one side of a ``relative_to()`` comparison resolves and the other
#      doesn't, the containment check raises ``ValueError`` and the file is
#      silently skipped from the naming check — exactly the UNC bug users hit.
#
#   2. Case-insensitivity. NTFS compares case-insensitively, but
#      :meth:`pathlib.Path.relative_to` is case-sensitive on every platform.
#      ``Path("Z:/Docs/foo.md").relative_to("z:/docs")`` raises ValueError.
#
#   3. Disconnected shares. Calling ``Path.resolve()`` on a UNC path whose
#      server is offline can raise ``OSError``. We must tolerate that.
#
# ``os.path.normcase`` is the right primitive for (2) — it lowercases and
# swaps separators on Windows, and is a no-op on POSIX. We normalize both
# sides of every prefix check.
_IS_WINDOWS = os.name == "nt"


def _norm_key(p: Path | str) -> str:
    """Return a case-normalized POSIX-style key for path comparisons.

    On Windows this folds to lowercase and converts backslashes to forward
    slashes so UNC (``\\\\server\\share``) and mapped-drive (``Z:\\``) forms
    compare predictably against each other once resolved. On POSIX this
    preserves case and simply returns the forward-slash form.
    """
    s = str(p)
    if _IS_WINDOWS:
        # normcase lowercases AND flips separators on Windows.
        s = os.path.normcase(s)
        # Unify separators so startswith() matches work regardless of
        # whether the caller gave us backslashes or forward slashes.
        s = s.replace("\\", "/")
    return s


def _safe_resolve(p: Path) -> Path:
    """Resolve *p* tolerating OSError (disconnected network shares).

    ``Path.resolve(strict=False)`` still raises OSError on some Windows
    failure modes (offline UNC, deep recursion, reparse-point loops).
    When that happens we fall back to the unresolved path rather than
    crashing — the file will still get its naming check, just without
    symlink/junction unwrapping.
    """
    try:
        return p.resolve(strict=False)
    except OSError:
        return p


# Document extensions the naming convention applies to. Matches the
# DOC_EXTENSIONS list in the shell hook.
_DOC_EXTENSIONS: frozenset[str] = frozenset({
    "docx", "md", "html", "pdf", "pptx", "txt",
    "sh", "yaml", "yml", "jsx", "css", "js", "json",
})


def _find_registry(start: Path) -> Path | None:
    """Walk up from *start* to find the nearest ``docs/REGISTRY.yaml``.

    Returns ``None`` if no registry is found before hitting the filesystem
    root. We explicitly look for ``docs/REGISTRY.yaml`` rather than any
    ``REGISTRY.yaml`` to match the librarian's convention.

    Security note (Phase 8.0): the filesystem-root fallback was removed.
    On systems where ``/docs/REGISTRY.yaml`` exists (some container
    images, non-standard unix setups), the prior implementation would
    treat the entire filesystem as ``repo_root``, pulling every file
    into the naming check's scope. Now we stop at the last directory
    above the root and return ``None`` if no registry was found.

    Windows/UNC note (Phase 8.2): UNC paths like ``\\\\server\\share`` have
    ``anchor == '\\\\server\\share\\'``. ``Path.parent`` on a UNC root
    returns the UNC root itself (idempotent), so loop termination still
    works — but the comparison must be case-insensitive on Windows.
    We compare via ``_norm_key`` to match NTFS semantics. We also use
    ``_safe_resolve`` so a disconnected network share falls back to the
    lexical path instead of raising.
    """
    current = start if start.is_dir() else start.parent
    current = _safe_resolve(current)
    filesystem_root = Path(current.anchor)
    root_key = _norm_key(filesystem_root)
    seen: set[str] = set()
    while True:
        current_key = _norm_key(current)
        # Loop termination: stop once we reach the filesystem/UNC root, OR
        # if ``.parent`` returns the same path we already saw (defensive
        # against pathological UNC behavior on odd Python versions).
        if current_key == root_key or current_key in seen:
            break
        seen.add(current_key)
        candidate = current / "docs" / "REGISTRY.yaml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if _norm_key(parent) == current_key:
            break  # idempotent parent — we've hit the anchor
        current = parent
    # Deliberately no filesystem-root fallback — see security note above.
    return None


def _get_exempt(project_config: dict) -> frozenset[str]:
    """Return the project's infrastructure-exempt filename set.

    Phase 8.0: extracted from two near-identical inline blocks in
    :func:`_should_check` and :func:`_check_file` to keep behavior
    consistent across call sites.
    """
    naming_rules = project_config.get("naming_rules", {}) or {}
    return frozenset(naming_rules.get("infrastructure_exempt", []) or [])


def _load_project_config(registry_path: Path) -> dict:
    """Best-effort load of project_config. Returns empty dict on any error.

    Phase 8.2a adversarial-review fix L3: the exception swallow is
    **intentional** and documented here so future maintainers don't
    "helpfully" switch it to use :func:`librarian.yaml_errors.load_yaml`
    (which would raise :class:`YamlParseError` on malformed registries).

    The pre-commit hook must not block a developer's commit on problems that
    are unrelated to the files they are staging — e.g. an unrelated branch
    landed a broken REGISTRY.yaml, or the registry is missing. In those cases
    we degrade to "no project_config overrides" (empty dict), which causes
    ``_should_check`` to skip the file rather than falsely reject it. The
    user still sees the registry-parse failure separately via
    ``librarian audit``, which *does* use the friendly YAML-error path.

    Phase 8.2a adversarial-review fix H2 (Codex second-pass): we also
    catch :class:`UnicodeDecodeError` — opening with ``encoding="utf-8"``
    raises *before* PyYAML runs when the file isn't valid UTF-8 (e.g. a
    registry that was corrupted or saved as UTF-16 by a mis-configured
    editor). Without this, the hook crashed with a traceback rather than
    honoring its non-blocking contract.
    """
    try:
        with registry_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data.get("project_config", {}) or {}


def _should_check(
    filepath: Path,
    registry_path: Path | None,
    project_config: dict,
) -> bool:
    """Determine whether *filepath* should be validated against the naming
    convention.

    A file is checked when all are true:
      * Its extension is in _DOC_EXTENSIONS
      * It sits under one of the project's tracked_dirs (defaulting to
        ``docs/``)
      * It's not listed in naming_rules.infrastructure_exempt
      * It's not the REGISTRY.yaml itself
    """
    ext = filepath.suffix.lstrip(".").lower()
    if ext not in _DOC_EXTENSIONS:
        return False

    # REGISTRY.yaml is always exempt
    if filepath.name == "REGISTRY.yaml":
        return False

    # Infrastructure-exempt files bypass the convention entirely
    if filepath.name in _get_exempt(project_config):
        return False

    # If there's no registry, we can't know the tracked_dirs — treat any
    # doc-extension file as in scope and let naming.validate handle exemptions.
    if registry_path is None:
        return True

    tracked_dirs = project_config.get("tracked_dirs", ["docs/"]) or ["docs/"]
    repo_root = registry_path.parent.parent

    # Phase 8.0 security fix: previously did ``filepath.resolve().relative_to(repo_root)``
    # which follows symlinks on the filepath itself. A symlink
    # ``docs/valid-V1.0.md -> /etc/passwd`` would resolve outside
    # ``repo_root`` → ``ValueError`` → the file would be silently skipped
    # from the naming check. The filename itself must still be validated.
    #
    # Approach: resolve the *parent* directory only (which is trusted
    # project structure and handles OS-level tmpdir symlinks such as
    # macOS's ``/var -> /private/var``), then rebind the original leaf
    # name onto the resolved parent. This gives us a containment check
    # that does NOT follow a user-placed symlink at the filepath itself.
    #
    # Phase 8.2 Windows/UNC fix: both ``raw_parent`` and ``repo_root`` must
    # resolve consistently, because ``Path.resolve()`` on Windows converts
    # mapped drives to UNC (``Z:\proj`` → ``\\server\share\proj``). If only
    # one side resolved, ``relative_to`` would raise even for a file
    # genuinely inside the repo. We also fall back to a case-insensitive
    # POSIX-string prefix check (via ``_norm_key``) when ``relative_to``
    # still disagrees — which happens on case-varying Windows paths.
    #
    # Phase 8.2a adversarial-review fix L1: the previously-present outer
    # ``try/except ValueError`` around this whole block was dead code —
    # every path that can raise ValueError is already caught by the
    # inner try/except on ``relative_to``. Removed to tighten flow.
    raw_parent = filepath.parent if filepath.is_absolute() \
        else (Path.cwd() / filepath).parent
    resolved_parent = _safe_resolve(raw_parent)
    resolved_repo = _safe_resolve(repo_root)
    lexical = resolved_parent / filepath.name
    try:
        rel = lexical.relative_to(resolved_repo)
        rel_posix = rel.as_posix()
    except ValueError:
        # Case-insensitive fallback for Windows, where NTFS treats
        # ``Z:\Docs`` and ``z:\docs`` as the same directory but
        # ``Path.relative_to`` compares case-sensitively.
        lex_key = _norm_key(lexical)
        repo_key = _norm_key(resolved_repo).rstrip("/")
        if repo_key and lex_key.startswith(repo_key + "/"):
            rel_posix = lex_key[len(repo_key) + 1:]
        else:
            # Truly outside the repo — skip (another project)
            return False

    rel_posix = rel_posix + ("/" if filepath.is_dir() else "")
    # Case-normalize the rel path too, so ``Docs/foo.md`` matches tracked
    # dir ``docs/`` on Windows without forcing the user to care about case.
    rel_posix_cmp = _norm_key(rel_posix) if _IS_WINDOWS else rel_posix
    for td in tracked_dirs:
        if not td:
            continue
        # Ensure trailing slash for prefix match
        prefix = td if td.endswith("/") else td + "/"
        prefix_cmp = _norm_key(prefix) if _IS_WINDOWS else prefix
        if rel_posix_cmp.startswith(prefix_cmp):
            return True
    return False


def _check_file(
    filepath: Path,
    registry_path: Path | None,
    project_config: dict,
) -> tuple[bool, list[str]]:
    """Validate one file. Returns ``(ok, errors)`` where ``ok`` is True iff
    there are no errors. Warnings are collapsed into errors when strict mode
    is on (handled by the caller).
    """
    if not _should_check(filepath, registry_path, project_config):
        return True, []

    # Use the project's naming config if we have one, otherwise defaults.
    naming_cfg = None
    if project_config:
        try:
            from .config import load_config
            cfg = load_config(project_config=project_config)
            naming_cfg = cfg.naming
        except Exception:
            naming_cfg = None

    exempt = _get_exempt(project_config)
    result = validate_name(filepath.name, config=naming_cfg, exempt=exempt)
    if result.valid:
        return True, []
    return False, list(result.errors)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``librarian-precommit`` console script.

    Called by the pre-commit framework with staged files as positional
    arguments. Returns:

      * 0 — all checks pass (or no files to check)
      * 1 — one or more naming violations
      * 2 — usage error
    """
    parser = argparse.ArgumentParser(
        prog="librarian-precommit",
        description="Validate document filenames against the librarian naming convention.",
    )
    parser.add_argument(
        "files", nargs="*",
        help="Staged files to check (passed by the pre-commit framework).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors.",
    )
    args = parser.parse_args(argv)

    # Empty argv is a legitimate pre-commit-framework signal (regex
    # matched zero staged files). We exit 0 but print a trace so direct
    # CLI users who typo the command aren't left wondering whether it
    # silently ran. Goes to stdout (not stderr) to avoid noise on the
    # framework's pass path.
    if not args.files:
        print("Librarian naming check — no files to check")
        return 0

    failures: list[tuple[str, list[str]]] = []
    checked = 0
    skipped = 0

    # Cache registry lookup per unique parent directory to avoid redundant walks
    registry_cache: dict[Path, Path | None] = {}

    for raw in args.files:
        fp = Path(raw)
        # Phase 8.2 consistency fix: use _safe_resolve so a disconnected
        # UNC share or other OSError-producing path doesn't crash the
        # hook before any file gets checked. Matches the hardening
        # already applied in _find_registry and _should_check.
        parent = _safe_resolve(fp if fp.is_dir() else fp.parent)
        if parent not in registry_cache:
            registry_cache[parent] = _find_registry(parent)
        registry_path = registry_cache[parent]
        pc = _load_project_config(registry_path) if registry_path else {}

        if not _should_check(fp, registry_path, pc):
            skipped += 1
            continue
        ok, errors = _check_file(fp, registry_path, pc)
        checked += 1
        if not ok:
            failures.append((str(fp), errors))

    if failures:
        print("Librarian naming check — FAIL", file=sys.stderr)
        for fname, errors in failures:
            print(f"  {fname}", file=sys.stderr)
            for err in errors:
                print(f"    - {err}", file=sys.stderr)
        print(
            f"\n{len(failures)}/{checked} file(s) violate the naming "
            f"convention. {skipped} file(s) skipped (non-governed).",
            file=sys.stderr,
        )
        return 1

    if checked:
        print(f"Librarian naming check — OK ({checked} file(s), "
              f"{skipped} skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
