"""Naming convention validator for librarian-managed documents.

Canonical format: descriptive-name-YYYYMMDD-VX.Y.ext

Rules:
- descriptive-name: lowercase, hyphen-separated, no forbidden words as tokens
- YYYYMMDD: 8-digit calendar date (must parse as real date)
- VX.Y: major.minor version with literal V prefix
- .ext: lowercase extension
- Exempt files (listed in REGISTRY.yaml project_config.infrastructure_exempt)
  bypass the convention entirely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Canonical filename regex: stem-YYYYMMDD-VX.Y.ext
CANONICAL_RE = re.compile(
    r"^(?P<stem>[a-z0-9][a-z0-9-]*[a-z0-9])"
    r"-(?P<date>\d{8})"
    r"-V(?P<major>\d+)\.(?P<minor>\d+)"
    r"\.(?P<ext>[a-z0-9]+)$"
)

# Forbidden stem tokens (hyphen-split). Inherited from PRISM hook.
FORBIDDEN_WORDS = frozenset({"file", "download", "output", "document"})


@dataclass
class ParsedName:
    stem: str
    date: str  # YYYYMMDD
    major: int
    minor: int
    ext: str

    @property
    def version(self) -> str:
        return f"V{self.major}.{self.minor}"

    @property
    def filename(self) -> str:
        return f"{self.stem}-{self.date}-{self.version}.{self.ext}"


@dataclass
class ValidationResult:
    valid: bool
    filename: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parsed: ParsedName | None = None

    def __bool__(self) -> bool:
        return self.valid


def parse_filename(name: str) -> ParsedName | None:
    """Parse a filename into its canonical components.

    Returns None if the filename does not match the canonical pattern
    or if the date component does not resolve to a real calendar date.
    """
    m = CANONICAL_RE.match(name)
    if not m:
        return None
    date_str = m.group("date")
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return None
    return ParsedName(
        stem=m.group("stem"),
        date=date_str,
        major=int(m.group("major")),
        minor=int(m.group("minor")),
        ext=m.group("ext"),
    )


def validate(
    name: str,
    exempt: frozenset[str] | set[str] = frozenset(),
    forbidden: frozenset[str] | set[str] = FORBIDDEN_WORDS,
) -> ValidationResult:
    """Validate a filename against the canonical naming convention.

    Args:
        name: basename to validate (path components are stripped defensively)
        exempt: set of filenames that bypass the convention
        forbidden: set of hyphen-split tokens disallowed in the stem

    Returns:
        ValidationResult with valid flag, errors list, and (if parseable)
        the parsed form.
    """
    name = Path(name).name
    result = ValidationResult(valid=True, filename=name)

    if name in exempt:
        return result

    parsed = parse_filename(name)
    if parsed is None:
        if not re.search(r"\d{8}", name):
            result.errors.append("missing YYYYMMDD date")
        if not re.search(r"V\d+\.\d+", name):
            result.errors.append("missing VX.Y version suffix")
        if "." not in name:
            result.errors.append("missing file extension")
        if not result.errors:
            result.errors.append("does not match canonical pattern")
        result.valid = False
        return result

    tokens = set(parsed.stem.split("-"))
    bad = tokens & set(forbidden)
    if bad:
        result.errors.append(f"forbidden token(s) in stem: {sorted(bad)}")
        result.valid = False

    result.parsed = parsed
    return result
