"""Naming convention validator tests."""

from librarian.naming import parse_filename, validate


class TestParseFilename:
    def test_canonical(self):
        p = parse_filename("research-20260411-V1.0.md")
        assert p is not None
        assert p.stem == "research"
        assert p.date == "20260411"
        assert p.major == 1
        assert p.minor == 0
        assert p.ext == "md"
        assert p.version == "V1.0"
        assert p.filename == "research-20260411-V1.0.md"

    def test_multi_word_stem(self):
        p = parse_filename("my-long-stem-name-20260411-V2.5.yaml")
        assert p is not None
        assert p.stem == "my-long-stem-name"
        assert p.major == 2
        assert p.minor == 5
        assert p.ext == "yaml"

    def test_invalid_date_rejected(self):
        # Month 13 — must be rejected
        assert parse_filename("stem-20261301-V1.0.md") is None

    def test_missing_version_rejected(self):
        assert parse_filename("stem-20260411.md") is None

    def test_missing_date_rejected(self):
        assert parse_filename("stem-V1.0.md") is None


class TestValidate:
    def test_happy_path(self):
        r = validate("research-20260411-V1.0.md")
        assert r.valid
        assert r.parsed is not None
        assert not r.errors

    def test_forbidden_word_in_stem(self):
        r = validate("my-file-20260411-V1.0.md")
        assert not r.valid
        assert any("forbidden" in e for e in r.errors)

    def test_missing_date_error(self):
        r = validate("research.md")
        assert not r.valid
        assert any("date" in e for e in r.errors)

    def test_missing_version_error(self):
        r = validate("research-20260411.md")
        assert not r.valid
        assert any("version" in e for e in r.errors)

    def test_exempt_bypass(self):
        r = validate("README.md", exempt={"README.md"})
        assert r.valid
        assert not r.errors
