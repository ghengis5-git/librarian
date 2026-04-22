"""Friendly YAML parse error reporting.

PyYAML raises ``yaml.MarkedYAMLError`` (parent of ``ScannerError``,
``ParserError``, ``ConstructorError``) with a ``problem_mark`` attribute
exposing line and column. Letting that exception propagate gives the user
a raw Python traceback that doesn't tell them which file failed, which
line to look at, or what the problematic character was.

This module wraps :func:`yaml.safe_load` and re-raises as
:class:`YamlParseError` with a formatted message that:

  * Names the offending file
  * Shows 1-indexed line and column (PyYAML reports 0-indexed)
  * Quotes the problematic line
  * Prints a caret (``^``) under the column the parser tripped on

Design notes
------------

* We expose ``YamlParseError`` rather than subclassing ``yaml.YAMLError``
  so callers can ``except YamlParseError`` without importing PyYAML.
* The original exception is chained via ``raise ... from e`` so tracebacks
  still show the underlying parser state when debugging.
* Best-effort read of the source line — if the file has already been
  truncated, moved, or re-encoded between the parse attempt and the
  re-read, we skip the line preview gracefully.
"""

from __future__ import annotations

from itertools import islice
from pathlib import Path
from typing import Any

import yaml


# Cap for source-line re-read on error path (Phase 8.2a adversarial-review
# fix M2). Without this cap, a malformed multi-gigabyte YAML file would
# force the error formatter to allocate the full contents into memory just
# to render a single source-line preview. We only ever need the line the
# parser tripped on plus a small window of context, so we read at most
# ``mark.line + _SOURCE_LINE_LOOKAHEAD`` lines via ``itertools.islice``.
# The lookahead is tiny — we don't currently render trailing context, but
# leaving room future-proofs the formatter without compromising the cap.
_SOURCE_LINE_LOOKAHEAD = 5


def _caret_prefix(source_line: str, column: int) -> str:
    """Build the indentation prefix for the caret marker line.

    Phase 8.2a adversarial-review fix L2: tab-safe caret. When the source
    line starts with tabs (or contains tabs before the error column), a
    pure-space prefix misaligns the caret in any terminal that renders
    tabs at width != 1. We mirror the tab characters from the source line
    so that both lines indent by the same visual amount; every other
    character (including normal spaces) becomes a space, which is safe
    because spaces have known width 1.

    Phase 8.2a adversarial-review fix H1 (Codex second-pass): the caret
    sits *under* the offending column, so the prefix spans the columns
    **before** it — i.e. ``column - 1`` characters, not ``column``. The
    earlier ``source_line[:max(column, 0)]`` slice included the offending
    character in the pad, shifting every caret one column to the right.
    A column=1 error now correctly yields an empty prefix (caret flush
    left under the first character).

    :param source_line: The source line being annotated (without trailing
        newline).
    :param column: 1-indexed column where the caret should land. Values
        <= 1 yield an empty prefix (caret at column 1).
    """
    # pad_chars = columns *before* the target column. For column=1 this
    # is 0 (empty prefix → caret at column 1); for column=N it is N-1.
    pad_chars = max(column - 1, 0)
    return "".join(
        c if c == "\t" else " "
        for c in source_line[:pad_chars]
    )


class YamlParseError(Exception):
    """Raised when a YAML file fails to parse.

    Instances carry the original :class:`yaml.YAMLError` in ``__cause__``
    (via ``raise from``) plus structured attributes for programmatic use:

    :ivar path: Absolute path to the YAML file.
    :ivar line: 1-indexed line number of the parse error (``None`` if
        PyYAML did not report a mark).
    :ivar column: 1-indexed column number (``None`` if unavailable).
    :ivar problem: Short description of what the parser objected to.
    """

    def __init__(
        self,
        path: Path,
        line: int | None,
        column: int | None,
        problem: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.path = path
        self.line = line
        self.column = column
        self.problem = problem


def _format_error(path: Path, err: yaml.YAMLError) -> tuple[int | None, int | None, str, str]:
    """Turn a ``yaml.YAMLError`` into (line, column, problem, pretty_message)."""
    # MarkedYAMLError exposes ``problem``, ``problem_mark``, and optionally
    # ``context``/``context_mark``. Plain ``yaml.YAMLError`` does not.
    mark = getattr(err, "problem_mark", None)
    context_mark = getattr(err, "context_mark", None)
    problem_desc = getattr(err, "problem", None) or "YAML parse error"
    context_desc = getattr(err, "context", None)

    if mark is None:
        # No structured location — fall back to str(err)
        return None, None, problem_desc, f"{path}: {problem_desc}"

    # PyYAML reports 0-indexed line/column; humans expect 1-indexed.
    line = mark.line + 1
    column = mark.column + 1

    # Read the source line for context. Best-effort — tolerate a file that
    # was edited/removed between parse and re-read.
    #
    # Phase 8.2a adversarial-review fix M2: bounded read. We only need
    # ``mark.line`` itself plus a tiny lookahead; reading the whole file via
    # ``readlines()`` would allocate O(filesize) on a malformed multi-GB
    # YAML just to render a caret preview. ``itertools.islice`` caps the
    # read at the first ``mark.line + _SOURCE_LINE_LOOKAHEAD`` lines.
    # Also strip ``\r\n`` (not just ``\n``) so CRLF files don't leak a
    # trailing ``\r`` into the formatted message.
    source_line = ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = list(islice(f, mark.line + _SOURCE_LINE_LOOKAHEAD))
        if 0 <= mark.line < len(lines):
            source_line = lines[mark.line].rstrip("\r\n")
    except OSError:
        source_line = ""

    # Build the pretty message.
    parts = [f"{path}:{line}:{column}: YAML parse error"]
    if context_desc:
        parts.append(f"  {context_desc}")
    parts.append(f"  {problem_desc}")
    if source_line:
        parts.append("")
        parts.append(f"    {source_line}")
        # Caret under the offending column (tab-safe — see _caret_prefix).
        parts.append(f"    {_caret_prefix(source_line, column)}^")
    if context_mark is not None and context_mark.line != mark.line:
        parts.append(
            f"  (note: related context at line {context_mark.line + 1}, "
            f"column {context_mark.column + 1})"
        )

    return line, column, problem_desc, "\n".join(parts)


def load_yaml(path: str | Path) -> Any:
    """Load a YAML file, raising :class:`YamlParseError` on parse failure.

    Returns the parsed data (or ``None`` for an empty file — callers
    typically coerce with ``... or {}``).

    Phase 8.2a adversarial-review fix H1 (pass 4): a non-UTF-8 registry
    (UTF-16 BOM, Latin-1 accented bytes, stray high-bit bytes from copy-
    paste) raises :class:`UnicodeDecodeError` during the ``open(..., 'r',
    encoding='utf-8')`` read, *before* PyYAML ever runs. Letting that
    propagate gave the user a raw Python traceback with no path context
    and no guidance — identical failure mode to the parse-error case this
    wrapper was built to fix. We now catch it, extract the byte offset
    and decode reason, and re-raise as a :class:`YamlParseError` with a
    clear "re-save as UTF-8 without BOM" hint.
    """
    p = Path(path)
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        line, column, problem, message = _format_error(p, e)
        raise YamlParseError(p, line, column, problem, message) from e
    except UnicodeDecodeError as e:
        problem = (
            f"Invalid UTF-8 byte at offset {e.start}: {e.reason}. "
            f"Re-save the file as UTF-8 without BOM."
        )
        message = (
            f"{p}: YAML encoding error\n"
            f"  {problem}"
        )
        raise YamlParseError(p, None, None, problem, message) from e


def load_yaml_string(source: str, source_label: str = "<string>") -> Any:
    """Load YAML from an in-memory string.

    :param source_label: Pseudo-path used in error messages — e.g.
        ``"<frontmatter of foo.md>"`` when parsing an embedded YAML block.
    """
    try:
        return yaml.safe_load(source)
    except yaml.YAMLError as e:
        # For in-memory sources we can't re-read the file, but we can
        # still snapshot the relevant source line from the string itself.
        mark = getattr(e, "problem_mark", None)
        problem = getattr(e, "problem", None) or "YAML parse error"
        if mark is None:
            message = f"{source_label}: {problem}"
            raise YamlParseError(Path(source_label), None, None, problem, message) from e

        line = mark.line + 1
        column = mark.column + 1
        lines = source.splitlines()
        source_line = lines[mark.line] if 0 <= mark.line < len(lines) else ""

        parts = [f"{source_label}:{line}:{column}: YAML parse error", f"  {problem}"]
        if source_line:
            parts.append("")
            parts.append(f"    {source_line}")
            # Tab-safe caret — shared helper with _format_error.
            parts.append(f"    {_caret_prefix(source_line, column)}^")
        message = "\n".join(parts)
        raise YamlParseError(Path(source_label), line, column, problem, message) from e
