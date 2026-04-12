"""Version bump tests."""

import pytest

from librarian.versioning import Version, bump_filename, parse_version


class TestVersion:
    def test_str(self):
        assert str(Version(1, 3)) == "V1.3"

    def test_bump_minor(self):
        assert Version(1, 3).bump_minor() == Version(1, 4)

    def test_bump_major_resets_minor(self):
        assert Version(1, 3).bump_major() == Version(2, 0)


class TestParseVersion:
    def test_parse(self):
        assert parse_version("V1.3") == Version(1, 3)

    def test_no_v_prefix_raises(self):
        with pytest.raises(ValueError):
            parse_version("1.3")

    def test_malformed_raises(self):
        with pytest.raises(ValueError):
            parse_version("Vfoo.bar")


class TestBumpFilename:
    def test_minor_bump(self):
        result = bump_filename("research-20260101-V1.0.md", new_date="20260411")
        assert result == "research-20260411-V1.1.md"

    def test_major_bump(self):
        result = bump_filename(
            "research-20260101-V1.3.md", major=True, new_date="20260411"
        )
        assert result == "research-20260411-V2.0.md"

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            bump_filename("not-canonical.md")

    def test_preserves_stem_and_ext(self):
        result = bump_filename(
            "multi-word-stem-name-20260101-V1.0.yaml", new_date="20260411"
        )
        assert result == "multi-word-stem-name-20260411-V1.1.yaml"
