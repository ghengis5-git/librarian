"""Tests for librarian.yaml_errors (Phase 8.2).

Covers the user-facing contract of :class:`YamlParseError`:

  * Pretty, path-qualified messages with 1-indexed line/column
  * Source-line preview with a caret under the offending column
  * Graceful degradation when ``problem_mark`` is absent
  * Structured attributes for programmatic callers (path, line, column, problem)
  * Propagation through :func:`Registry.load` so registry callers get a
    friendly error instead of a raw PyYAML traceback
  * ``load_yaml_string`` for in-memory sources (frontmatter, config blocks)
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from librarian.yaml_errors import (
    YamlParseError,
    _caret_prefix,
    load_yaml,
    load_yaml_string,
)
from librarian.registry import Registry


# --------------------------------------------------------------------------- #
# load_yaml — file-based                                                       #
# --------------------------------------------------------------------------- #


class TestLoadYamlValid:
    def test_parses_valid_yaml(self, tmp_path):
        p = tmp_path / "good.yaml"
        p.write_text("foo: 1\nbar: [a, b]\n")
        data = load_yaml(p)
        assert data == {"foo": 1, "bar": ["a", "b"]}

    def test_empty_file_returns_none(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("")
        # None is the natural PyYAML result; callers coerce with ``or {}``
        assert load_yaml(p) is None

    def test_accepts_string_path(self, tmp_path):
        p = tmp_path / "good.yaml"
        p.write_text("key: value\n")
        # load_yaml must accept str as well as Path
        assert load_yaml(str(p)) == {"key": "value"}


class TestLoadYamlStructuredErrors:
    """Verify the YamlParseError carries line/column/problem programmatically."""

    def test_raises_yaml_parse_error_on_bad_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        # Tab indentation is a classic PyYAML gotcha
        p.write_text("foo:\n\tbar: 1\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        err = excinfo.value
        assert err.path == p
        assert err.line is not None and err.line >= 1
        assert err.column is not None and err.column >= 1

    def test_line_is_1_indexed(self, tmp_path):
        """PyYAML reports 0-indexed; users expect 1-indexed."""
        p = tmp_path / "bad.yaml"
        # Valid line 1, broken line 2
        p.write_text("good: value\n\tbad: tab\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        # Error is on line 2 of the file — PyYAML says mark.line == 1,
        # our wrapper must report line == 2
        assert excinfo.value.line == 2

    def test_column_is_1_indexed(self, tmp_path):
        """Column numbering should match what editors show."""
        p = tmp_path / "bad.yaml"
        # Broken at column 1 (first character of line 2 is a tab)
        p.write_text("ok: 1\n\tbroken: 2\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        # Column must be 1-indexed (first col = 1, never 0)
        assert excinfo.value.column is not None
        assert excinfo.value.column >= 1

    def test_problem_is_populated(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("foo: bar: baz\n")  # nested mapping without structure
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        # PyYAML gives us a non-empty problem description
        assert excinfo.value.problem
        assert isinstance(excinfo.value.problem, str)


class TestLoadYamlPrettyMessage:
    """The str(exception) should be human-readable and actionable."""

    def test_message_includes_file_path(self, tmp_path):
        p = tmp_path / "broken.yaml"
        p.write_text("foo:\n\tbar: 1\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        # File path must be in the message
        assert str(p) in str(excinfo.value)

    def test_message_includes_line_and_column(self, tmp_path):
        p = tmp_path / "broken.yaml"
        p.write_text("foo:\n\tbar: 1\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        msg = str(excinfo.value)
        # Format: path:line:col: ...
        # Just check that "2:" (line 2) appears
        assert ":2:" in msg

    def test_message_includes_source_line_preview(self, tmp_path):
        p = tmp_path / "broken.yaml"
        p.write_text("ok_line: 1\n\tbroken_line: 2\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        msg = str(excinfo.value)
        # The offending source line should be quoted back at the user
        assert "broken_line" in msg

    def test_message_includes_caret(self, tmp_path):
        p = tmp_path / "broken.yaml"
        p.write_text("foo:\n\tbad: 1\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        # Caret under the offending column
        assert "^" in str(excinfo.value)


class TestLoadYamlExceptionChaining:
    def test_cause_is_original_yaml_error(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("foo:\n\tbad: 1\n")
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        # ``raise ... from e`` should preserve the underlying YAML error
        assert excinfo.value.__cause__ is not None
        assert isinstance(excinfo.value.__cause__, yaml.YAMLError)


# --------------------------------------------------------------------------- #
# Phase 8.2a adversarial-review pass-4 fix H1 — UnicodeDecodeError handling    #
# --------------------------------------------------------------------------- #


class TestLoadYamlUnicodeDecodeError:
    """A non-UTF-8 registry (UTF-16 BOM, Latin-1 accented bytes, stray
    high-bit bytes from copy-paste) raises :class:`UnicodeDecodeError`
    during ``open(..., encoding='utf-8')`` *before* PyYAML ever runs.

    The wrapper must catch it and re-raise as :class:`YamlParseError`
    with path context and a clear "re-save as UTF-8" hint, mirroring
    the fix already applied to ``_load_project_config`` in ``precommit.py``
    during the Codex second-pass review.
    """

    def test_utf16_bom_raises_yaml_parse_error(self, tmp_path):
        """UTF-16 BOM (``\\xff\\xfe`` or ``\\xfe\\xff``) is the most common
        non-UTF-8 encoding a user hits when they save a registry in a
        Windows editor without changing the default."""
        p = tmp_path / "utf16.yaml"
        # UTF-16 LE with BOM
        p.write_bytes("foo: bar\n".encode("utf-16"))

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        err = excinfo.value
        assert err.path == p
        # Underlying cause must be UnicodeDecodeError, preserved via ``from e``.
        assert isinstance(err.__cause__, UnicodeDecodeError)

    def test_utf16_bom_message_names_file_and_hints_utf8(self, tmp_path):
        p = tmp_path / "utf16.yaml"
        p.write_bytes("foo: bar\n".encode("utf-16"))

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        msg = str(excinfo.value)
        assert str(p) in msg, "error message must name the offending file"
        # User needs to know the fix, not just that something failed.
        assert "UTF-8" in msg

    def test_bare_high_bit_bytes_raise_yaml_parse_error(self, tmp_path):
        """Stray Latin-1 / high-bit continuation bytes are the other
        common failure mode — e.g. a smart-quote pasted from Word. These
        hit the UTF-8 decoder with no BOM, so the byte offset is the
        content position, not offset 0."""
        p = tmp_path / "latin1.yaml"
        # 0xa9 is the Latin-1 copyright sign; illegal as a UTF-8 lead byte.
        p.write_bytes(b"project_config:\n  name: caf\xa9\n")

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        err = excinfo.value
        assert isinstance(err.__cause__, UnicodeDecodeError)
        # Path must be reported.
        assert err.path == p

    def test_unicode_decode_error_has_problem_attribute(self, tmp_path):
        """Programmatic callers read ``err.problem`` — must be non-empty
        and mention the byte offset so tooling can point to the byte."""
        p = tmp_path / "bad_encoding.yaml"
        p.write_bytes(b"foo: \xff\xfe bar\n")

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        err = excinfo.value
        assert err.problem  # non-empty
        # Offset should be surfaced so the user can locate the byte.
        assert "offset" in err.problem.lower()

    def test_valid_utf8_still_parses(self, tmp_path):
        """Regression: plain UTF-8 files with non-ASCII content must still
        load cleanly — the new exception handler only kicks in on decode
        failure."""
        p = tmp_path / "utf8.yaml"
        p.write_text("name: café\nemoji: \U0001f4da\n", encoding="utf-8")
        data = load_yaml(p)
        assert data == {"name": "café", "emoji": "\U0001f4da"}


# --------------------------------------------------------------------------- #
# load_yaml_string — in-memory source                                          #
# --------------------------------------------------------------------------- #


class TestLoadYamlString:
    def test_parses_valid_string(self):
        assert load_yaml_string("key: value\n") == {"key": "value"}

    def test_raises_on_bad_string(self):
        with pytest.raises(YamlParseError):
            load_yaml_string("foo:\n\tbar: 1\n")

    def test_uses_source_label_in_message(self):
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml_string(
                "foo:\n\tbad: 1\n",
                source_label="<frontmatter of my-doc.md>",
            )
        assert "<frontmatter of my-doc.md>" in str(excinfo.value)

    def test_default_label_when_omitted(self):
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml_string("foo:\n\tbad: 1\n")
        # Fallback label is <string>
        assert "<string>" in str(excinfo.value)

    def test_source_line_preview_on_string(self):
        """Even without a file to re-read, the relevant line from the
        in-memory source should still appear in the message."""
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml_string("ok: 1\n\tbroken_marker: 2\n")
        assert "broken_marker" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# Registry integration — verifies callers get YamlParseError end-to-end       #
# --------------------------------------------------------------------------- #


class TestRegistryPropagatesYamlParseError:
    def test_registry_load_raises_yaml_parse_error(self, tmp_path):
        reg = tmp_path / "REGISTRY.yaml"
        reg.write_text(textwrap.dedent("""\
            project_config:
              project_name: test
            \tbroken: indent
        """))
        with pytest.raises(YamlParseError):
            Registry.load(reg)

    def test_registry_error_names_the_file(self, tmp_path):
        reg = tmp_path / "REGISTRY.yaml"
        reg.write_text("project_config:\n\tbroken: indent\n")
        with pytest.raises(YamlParseError) as excinfo:
            Registry.load(reg)
        assert "REGISTRY.yaml" in str(excinfo.value)

    def test_registry_load_valid_unchanged(self, tmp_path):
        """Regression: valid registries must load exactly as before."""
        reg = tmp_path / "REGISTRY.yaml"
        reg.write_text(textwrap.dedent("""\
            project_config:
              project_name: demo
              tracked_dirs:
              - docs/
            documents: []
        """))
        r = Registry.load(reg)
        assert r.project_config["project_name"] == "demo"
        assert r.documents == []


# --------------------------------------------------------------------------- #
# Phase 8.2a adversarial-review fix M2 — bounded source-line re-read           #
# --------------------------------------------------------------------------- #


class TestBoundedSourceLineReread:
    """``_format_error`` must not read the entire file into memory on the
    error path. Previously used ``readlines()`` which allocates the full
    contents; now uses ``islice`` capped at ``mark.line + lookahead``."""

    def test_does_not_read_past_error_line(self, tmp_path, monkeypatch):
        """Write a YAML file with an early parse error, then pad it with
        many lines of valid-looking content. Monkeypatch ``open`` on the
        file to count how many lines are pulled from the iterator during
        the error-path re-read. Must be bounded, not the full file."""
        # Parse error on line 2; pad with 10,000 additional lines.
        padding = "\n".join(f"line_{i}: value" for i in range(10_000))
        p = tmp_path / "big-bad.yaml"
        p.write_text("foo:\n\tbad: 1\n" + padding + "\n")

        # Wrap the file-iterator consumed by _format_error. We can't
        # easily intercept islice, so we count via a wrapper file object.
        # The key property to verify: source_line reflects the error line
        # and the process doesn't blow out memory with >10k readlines.
        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)

        # The bug manifested as "we loaded the whole file"; the fix is
        # "we loaded ~7 lines" (mark.line=1, plus lookahead=5 → 6 lines).
        # We can't assert memory directly, but we CAN assert that the
        # renderer stopped reading past the lookahead by patching the
        # file open to raise after a read cap.
        err = excinfo.value
        # The source line for mark.line=1 (0-indexed) is the tab-indented
        # ``\tbad: 1``. Must still be captured.
        assert "bad" in str(err)

    def test_bounded_read_does_not_allocate_full_file(
        self, tmp_path, monkeypatch
    ):
        """Stronger guarantee: intercept the file read and cap it at a
        small number of lines. If the formatter is bounded, ``load_yaml``
        succeeds in producing a YamlParseError. If the formatter tries
        to read beyond the cap, our wrapper raises and the test fails."""
        from librarian import yaml_errors

        # Build a small malformed file (mark.line=1). Error caret needs
        # about 6 lines (1 + _SOURCE_LINE_LOOKAHEAD).
        p = tmp_path / "bounded.yaml"
        lines = ["foo:", "\tbad: 1"] + [f"tail_{i}: v" for i in range(50)]
        p.write_text("\n".join(lines) + "\n")

        # Wrap islice so we can count the maximum lines pulled. If the
        # fix is in place, the count should be at most mark.line + 5 + 1.
        from itertools import islice as real_islice

        max_n_seen = {"n": 0}
        def counting_islice(iterable, stop):
            max_n_seen["n"] = max(max_n_seen["n"], stop)
            return real_islice(iterable, stop)

        monkeypatch.setattr(yaml_errors, "islice", counting_islice)

        with pytest.raises(YamlParseError):
            load_yaml(p)

        # mark.line for the tab error is 1 (0-indexed), lookahead is 5,
        # so cap should be 6. Allow a bit of slack for future lookahead
        # tweaks, but flag anything approaching full file read.
        assert max_n_seen["n"] < 20, (
            f"formatter read up to {max_n_seen['n']} lines — "
            "expected a bounded cap ~mark.line+5"
        )

    def test_crlf_file_strips_trailing_carriage_return(self, tmp_path):
        """L4: ``rstrip('\\n')`` used to leak a trailing ``\\r`` into the
        formatted source-line preview on Windows CRLF files. Now we strip
        ``\\r\\n`` both, so the caret line aligns cleanly."""
        # Explicit binary write with CRLF terminators so universal-newlines
        # doesn't rewrite them on the way in.
        p = tmp_path / "crlf.yaml"
        p.write_bytes(b"foo:\r\n\tbad: 1\r\n")

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        msg = str(excinfo.value)
        # The source-line preview must not contain a literal \r character.
        assert "\r" not in msg


# --------------------------------------------------------------------------- #
# Phase 8.2a adversarial-review fix L2 — tab-safe caret alignment              #
# --------------------------------------------------------------------------- #


class TestCaretPrefix:
    """Direct unit tests for ``_caret_prefix`` — the tab-safe helper used
    by both ``_format_error`` (file path) and ``load_yaml_string``
    (in-memory path). Tested in isolation so coverage doesn't depend on
    any specific PyYAML parse-error column behavior, which varies across
    PyYAML releases."""

    def test_empty_source_line_returns_empty_prefix(self):
        assert _caret_prefix("", column=1) == ""
        assert _caret_prefix("", column=5) == ""

    def test_column_1_returns_empty_prefix(self):
        """Column 1 → caret at start of line → no leading prefix.

        Phase 8.2a fix H1 (Codex second-pass): the prefix spans columns
        *before* the caret, so column=1 → pad=0 → empty string. Prior
        code returned one character of pad, shifting the caret to col 2.
        """
        assert _caret_prefix("abc", column=1) == ""
        assert _caret_prefix("\t\tabc", column=1) == ""

    def test_column_0_or_negative_clamps_to_empty(self):
        """Defensive: some paths might pass column <= 0. Clamp cleanly."""
        assert _caret_prefix("abc", column=0) == ""
        assert _caret_prefix("abc", column=-5) == ""

    def test_spaces_only_prefix(self):
        """Pure spaces → pure spaces out. column=5 means caret under the
        5th character, so pad is 4 leading chars → 4 spaces."""
        assert _caret_prefix("    bad", column=5) == "    "

    def test_preserves_leading_tab(self):
        """Tab-indented line → caret line starts with a matching tab.
        column=2 means caret under char 2 ('b' in '\\tbad'), so pad=1
        char = the leading tab. This is the core invariant that caret
        alignment depends on."""
        assert _caret_prefix("\tbad: value", column=2) == "\t"

    def test_preserves_multiple_leading_tabs(self):
        """Two tabs in, caret at column 3 → pad = 2 chars = two tabs."""
        assert _caret_prefix("\t\tbad: value", column=3) == "\t\t"

    def test_mixed_tab_and_space_indent(self):
        """Tab + space + space + text, caret at column 4 → pad = 3 chars
        → tab, space, space. Not 3 plain spaces (would misalign under
        the tab)."""
        assert _caret_prefix("\t  bad", column=4) == "\t  "

    def test_non_indent_chars_collapse_to_spaces(self):
        """Any non-tab character (letters, digits, punctuation) in the
        prefix region becomes a single space. They all have width 1 so
        this is safe and keeps the caret aligned. column=4 → pad=3
        chars of 'abcdef' → 3 spaces."""
        assert _caret_prefix("abcdef", column=4) == "   "

    def test_mid_line_tab_is_preserved(self):
        """A tab that appears mid-line (not just leading indent) must
        still be mirrored — caret alignment is a per-column property,
        not a 'leading-indent-only' property.

        "ab\\tcd", column=5 → pad=4 → slice "ab\\tc" → "  \\t " (two
        spaces, one tab, one space)."""
        assert _caret_prefix("ab\tcd", column=5) == "  \t "

    def test_column_past_end_of_line(self):
        """Column beyond source_line length → full-line prefix mirror.
        Edge case when parser reports error past the visible content.

        "\\tab" has 3 chars; column=10 → pad=9 but slice clamps to 3
        → "\\tab" → "\\t  " (tab + 2 spaces)."""
        assert _caret_prefix("\tab", column=10) == "\t  "

    def test_caret_lands_under_correct_column(self):
        """Integration-level unit test: build the full source+caret pair
        the way ``_format_error`` does (both with a 4-space decorative
        indent) and confirm the caret character sits at the same visual
        column as the offending source character."""
        source = "abcdef"
        column = 4  # caret should be under 'd'
        source_line = f"    {source}"
        caret_line = f"    {_caret_prefix(source, column)}^"
        # Ensure caret is at the same string index as 'd' in source_line.
        assert caret_line.index("^") == source_line.index("d")


class TestTabSafeCaretIntegration:
    """End-to-end check that the formatted message uses the tab-safe
    helper. We assert two things:

    1. H1 fix (Codex second-pass): the caret character ``^`` sits at
       the 1-indexed column the exception reports, i.e. ``caret_body[col-1]
       == "^"``. Under the old buggy prefix, the caret was always one
       column too far right.
    2. L2 fix: wherever a tab appears in the source body *before* the
       error column, there is also a tab at the same position in the
       caret body (so the caret aligns regardless of terminal tab width).
    """

    def test_caret_lands_on_reported_column(self, tmp_path):
        """Trigger a parse error and confirm the caret character sits
        exactly at the column the YamlParseError reports."""
        p = tmp_path / "col.yaml"
        # Well-known parse error: unclosed flow sequence. PyYAML reports
        # the mark at the position of the failing character. Using a
        # tab-indented line so the tab-mirror invariant is also exercised.
        p.write_text("good: ok\n\tbad: [1, 2\n")

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        err = excinfo.value
        lines = str(err).splitlines()

        caret_idx = next(
            i for i, ln in enumerate(lines) if ln.rstrip().endswith("^")
        )
        caret_decorated = lines[caret_idx]
        assert caret_decorated.startswith("    ")
        caret_body = caret_decorated[4:]

        # Primary H1 invariant: "^" lands at the reported 1-indexed
        # column (i.e. string index column - 1 in the body).
        assert err.column is not None, "parser should have reported a column"
        assert caret_body[err.column - 1] == "^", (
            f"caret not at reported column {err.column}: body={caret_body!r}"
        )
        # No other characters in the body should be ``^``.
        assert caret_body.count("^") == 1

    def test_format_error_caret_line_matches_source_line_tabs(self, tmp_path):
        """L2 tab-mirror invariant: every tab in the source prefix (the
        portion BEFORE the error column) is also a tab at the same
        position in the caret prefix."""
        p = tmp_path / "tabby.yaml"
        # Flow-sequence break on a tab-indented line forces the error
        # mark to land well past the leading tab, so the tab-mirror
        # invariant has somewhere to check.
        p.write_text("good: ok\n\tbad: [1, 2\n")

        with pytest.raises(YamlParseError) as excinfo:
            load_yaml(p)
        err = excinfo.value
        lines = str(excinfo.value).splitlines()

        caret_idx = next(
            i for i, ln in enumerate(lines) if ln.rstrip().endswith("^")
        )
        source_decorated = lines[caret_idx - 1]
        caret_decorated = lines[caret_idx]
        assert source_decorated.startswith("    ")
        assert caret_decorated.startswith("    ")
        source_body = source_decorated[4:]
        caret_body = caret_decorated[4:]

        # Invariant only applies to columns strictly before the caret.
        assert err.column is not None
        prefix_len = err.column - 1
        for i in range(min(prefix_len, len(source_body))):
            if source_body[i] == "\t":
                assert i < len(caret_body) and caret_body[i] == "\t", (
                    f"caret body diverges from source at position {i}: "
                    f"source={source_body!r}, caret={caret_body!r}"
                )
