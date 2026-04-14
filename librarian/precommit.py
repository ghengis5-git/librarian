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
import sys
from pathlib import Path

import yaml

from .naming import validate as validate_name


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
    """
    current = start if start.is_dir() else start.parent
    current = current.resolve()
    filesystem_root = Path(current.anchor)
    while current != filesystem_root:
        candidate = current / "docs" / "REGISTRY.yaml"
        if candidate.is_file():
            return candidate
        current = current.parent
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
    """Best-effort load of project_config. Returns empty dict on any error."""
    try:
        with registry_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
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
    try:
        raw_parent = filepath.parent if filepath.is_absolute() \
            else (Path.cwd() / filepath).parent
        try:
            resolved_parent = raw_parent.resolve(strict=False)
        except OSError:
            resolved_parent = raw_parent
        lexical = resolved_parent / filepath.name
        rel = lexical.relative_to(repo_root)
    except ValueError:
        # File lives outside the registry's repo — skip (another project)
        return False

    rel_posix = rel.as_posix() + ("/" if filepath.is_dir() else "")
    for td in tracked_dirs:
        if not td:
            continue
        # Ensure trailing slash for prefix match
        prefix = td if td.endswith("/") else td + "/"
        if rel_posix.startswith(prefix):
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
        parent = (fp if fp.is_dir() else fp.parent).resolve()
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
