"""Version bump logic for librarian-managed documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .naming import parse_filename


@dataclass(frozen=True)
class Version:
    major: int
    minor: int

    def __str__(self) -> str:
        return f"V{self.major}.{self.minor}"

    def bump_minor(self) -> "Version":
        return Version(self.major, self.minor + 1)

    def bump_major(self) -> "Version":
        return Version(self.major + 1, 0)


def parse_version(s: str) -> Version:
    """Parse 'VX.Y' into a Version. Raises ValueError if malformed."""
    if not s.startswith("V"):
        raise ValueError(f"version must start with V: {s!r}")
    try:
        major_str, minor_str = s[1:].split(".", 1)
        return Version(int(major_str), int(minor_str))
    except (ValueError, IndexError) as e:
        raise ValueError(f"malformed version {s!r}: {e}") from e


def bump_filename(
    old_filename: str,
    major: bool = False,
    new_date: str | None = None,
) -> str:
    """Produce the next-version filename from an old canonical filename.

    Args:
        old_filename: current filename, must match canonical pattern
        major: if True, bump major and reset minor to 0
        new_date: override YYYYMMDD; if None, uses today

    Returns:
        New filename string. Caller is responsible for creating the file.

    Raises:
        ValueError: if old_filename is not canonical
    """
    parsed = parse_filename(old_filename)
    if parsed is None:
        raise ValueError(f"not a canonical filename: {old_filename!r}")

    old_version = Version(parsed.major, parsed.minor)
    new_version = old_version.bump_major() if major else old_version.bump_minor()
    date_str = new_date or date.today().strftime("%Y%m%d")

    return f"{parsed.stem}-{date_str}-{new_version}.{parsed.ext}"
