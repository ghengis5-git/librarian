"""Naming convention validator for librarian-managed documents.

Default format: descriptive-name-YYYYMMDD-VX.Y.ext

All format elements are configurable via NamingConfig:
- separator: - (default), _, .
- case: lowercase (default), mixed, uppercase
- date_format: YYYYMMDD (default), YYYY-MM-DD, off
- version_format: VX.Y (default), vX.Y, X.Y
- domain_prefix: False (default) — if True: domain-stem-date-VX.Y.ext

Rules:
- stem: separator-delimited, matching the configured case
- date: 8-digit or ISO date (must be a real calendar date), or absent if off
- version: major.minor with configured prefix
- ext: file extension
- Exempt files bypass the convention entirely
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import NamingConfig

# Canonical filename regex (default): stem-YYYYMMDD-VX.Y.ext
CANONICAL_RE = re.compile(
    r"^(?P<stem>[a-z0-9][a-z0-9-]*[a-z0-9])"
    r"-(?P<date>\d{8})"
    r"-V(?P<major>\d+)\.(?P<minor>\d+)"
    r"\.(?P<ext>[a-z0-9]+)$"
)

# Forbidden stem tokens (hyphen-split). Generic names that violate naming convention.
FORBIDDEN_WORDS = frozenset({"file", "download", "output", "document"})


@dataclass
class ParsedName:
    stem: str
    date: str  # YYYYMMDD, YYYY-MM-DD, or "" if date_format=off
    major: int
    minor: int
    ext: str
    domain: str = ""  # populated when domain_prefix is enabled

    @property
    def version(self) -> str:
        return f"V{self.major}.{self.minor}"

    @property
    def filename(self) -> str:
        parts = []
        if self.domain:
            parts.append(self.domain)
        parts.append(self.stem)
        if self.date:
            parts.append(self.date)
        parts.append(self.version)
        return "-".join(parts) + f".{self.ext}"

    def filename_with(self, separator: str = "-", version_format: str = "VX.Y") -> str:
        """Reconstruct filename with given separator and version format."""
        if version_format == "VX.Y":
            ver = f"V{self.major}.{self.minor}"
        elif version_format == "vX.Y":
            ver = f"v{self.major}.{self.minor}"
        else:
            ver = f"{self.major}.{self.minor}"

        parts = []
        if self.domain:
            parts.append(self.domain)
        parts.append(self.stem)
        if self.date:
            parts.append(self.date)
        parts.append(ver)
        return separator.join(parts) + f".{self.ext}"


@dataclass
class ValidationResult:
    valid: bool
    filename: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parsed: ParsedName | None = None

    def __bool__(self) -> bool:
        return self.valid


def _build_regex(config: "NamingConfig | None" = None) -> re.Pattern:
    """Build a compiled regex from a NamingConfig (or return CANONICAL_RE for defaults)."""
    if config is None:
        return CANONICAL_RE
    return re.compile(config.regex_pattern)


def _date_strptime_fmt(date_format: str) -> str | None:
    """Return the strptime format string for a date_format config value."""
    if date_format == "YYYYMMDD":
        return "%Y%m%d"
    elif date_format == "YYYY-MM-DD":
        return "%Y-%m-%d"
    return None  # off


def parse_filename(
    name: str,
    config: "NamingConfig | None" = None,
) -> ParsedName | None:
    """Parse a filename into its canonical components.

    Returns None if the filename does not match the configured pattern
    or if the date component does not resolve to a real calendar date.
    """
    regex = _build_regex(config)
    m = regex.match(name)
    if not m:
        return None

    groups = m.groupdict()
    date_str = groups.get("date", "")

    # Validate date if present
    if date_str:
        date_fmt_cfg = config.date_format if config else "YYYYMMDD"
        strp_fmt = _date_strptime_fmt(date_fmt_cfg)
        if strp_fmt:
            try:
                datetime.strptime(date_str, strp_fmt)
            except ValueError:
                return None

    return ParsedName(
        stem=groups.get("stem", ""),
        date=date_str,
        major=int(groups.get("major", "0")),
        minor=int(groups.get("minor", "0")),
        ext=groups.get("ext", ""),
        domain=groups.get("domain", ""),
    )


def validate(
    name: str,
    exempt: frozenset[str] | set[str] = frozenset(),
    forbidden: frozenset[str] | set[str] = FORBIDDEN_WORDS,
    config: "NamingConfig | None" = None,
) -> ValidationResult:
    """Validate a filename against the naming convention.

    Args:
        name: basename to validate (path components are stripped defensively)
        exempt: set of filenames that bypass the convention
        forbidden: set of hyphen-split tokens disallowed in the stem
        config: optional NamingConfig for non-default conventions

    Returns:
        ValidationResult with valid flag, errors list, and (if parseable)
        the parsed form.
    """
    name = Path(name).name
    result = ValidationResult(valid=True, filename=name)

    if name in exempt:
        return result

    # Use forbidden words from config if provided
    if config is not None and hasattr(config, "forbidden_words"):
        forbidden = frozenset(config.forbidden_words)

    parsed = parse_filename(name, config=config)
    if parsed is None:
        date_fmt = config.date_format if config else "YYYYMMDD"
        ver_fmt = config.version_format if config else "VX.Y"

        if date_fmt != "off" and not re.search(r"\d{4}", name):
            result.errors.append("missing date component")
        if ver_fmt == "VX.Y" and not re.search(r"V\d+\.\d+", name):
            result.errors.append("missing VX.Y version suffix")
        elif ver_fmt == "vX.Y" and not re.search(r"v\d+\.\d+", name):
            result.errors.append("missing vX.Y version suffix")
        elif ver_fmt == "X.Y" and not re.search(r"\d+\.\d+", name):
            result.errors.append("missing X.Y version suffix")
        if "." not in name:
            result.errors.append("missing file extension")
        if not result.errors:
            result.errors.append("does not match naming convention")
        result.valid = False
        return result

    sep = config.separator if config else "-"
    tokens = set(parsed.stem.split(sep)) if sep in parsed.stem else {parsed.stem}
    bad = tokens & set(forbidden)
    if bad:
        result.errors.append(f"forbidden token(s) in stem: {sorted(bad)}")
        result.valid = False

    result.parsed = parsed
    return result
