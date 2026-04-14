"""Document-review deadlines (`next_review` field).

A governed document can carry an optional ``next_review: YYYY-MM-DD`` field
in its registry entry. When that date is in the past, the document is
"overdue for review" — surfaced on the Audit page as a KPI card and in
the ``audit`` CLI output.

This module is the single source of truth for:
    * parsing review dates (strict ISO 8601 ``YYYY-MM-DD``)
    * computing the set of overdue documents for a given registry
    * the severity tier (warn) attached to overdue findings

Design notes (Phase 7.2, chosen variant A3+B1+C1+D1):

    * A3  — both CLI flag (``--review-by``) on register/bump/scaffold
            AND a dedicated ``librarian review`` subcommand.
    * B1  — explicit-only: the project preset never auto-applies a
            default cadence. Whatever the user sets is what sticks.
    * C1  — absolute ISO dates only (``2026-12-31``). No relative
            parsing; that can be layered on later without breaking
            the stored format.
    * D1  — overdue = warning severity. Treated like an audit finding
            but does not change the overall audit exit code today
            (matches how folder suggestions behave).

Thread-safety: none of these functions mutate shared state. All inputs
are value-typed (``datetime.date``, plain dicts).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable


# --------------------------------------------------------------------------- #
# Parsing                                                                      #
# --------------------------------------------------------------------------- #


class ReviewDateError(ValueError):
    """Raised when a review date string is malformed or out of range."""


def parse_review_date(value: str | date | None) -> date | None:
    """Parse an ISO 8601 ``YYYY-MM-DD`` string into a ``date``.

    Returns ``None`` if *value* is ``None`` or an empty string.
    Raises :class:`ReviewDateError` on malformed input.

    Accepts a ``date`` instance as a passthrough so callers don't have to
    gate on the type themselves.
    """
    if value is None:
        return None
    if isinstance(value, date):
        # datetime is a date subclass; normalise to plain date
        return date(value.year, value.month, value.day)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return datetime.strptime(stripped, "%Y-%m-%d").date()
        except ValueError as e:
            raise ReviewDateError(
                f"invalid review date {stripped!r}: expected YYYY-MM-DD"
            ) from e
    raise ReviewDateError(
        f"unsupported review date type {type(value).__name__}: {value!r}"
    )


def format_review_date(value: date | None) -> str | None:
    """Render a ``date`` as the canonical ``YYYY-MM-DD`` string (or ``None``)."""
    if value is None:
        return None
    return value.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# Overdue computation                                                          #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class OverdueReview:
    """A single overdue-review finding."""

    filename: str
    next_review: date
    days_overdue: int  # strictly positive

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "next_review": format_review_date(self.next_review),
            "days_overdue": self.days_overdue,
        }


# Statuses that are eligible for review-deadline tracking. Superseded and
# archived docs are intentionally excluded — their deadlines are moot.
_ELIGIBLE_STATUSES: frozenset[str] = frozenset({"active", "draft"})


def compute_overdue(
    documents: Iterable[dict[str, Any]],
    today: date | None = None,
    *,
    strict: bool = False,
) -> list[OverdueReview]:
    """Return the list of documents whose ``next_review`` has passed.

    Sorted most-overdue first. ``today`` defaults to :func:`date.today`.

    * ``strict=False`` (default): malformed ``next_review`` values are
      silently skipped. Useful for the audit page — a typo in one entry
      shouldn't blow up the whole report.
    * ``strict=True``: malformed values raise :class:`ReviewDateError`.
      Useful in unit tests and in CLI commands that need to be loud.
    """
    if today is None:
        today = date.today()

    out: list[OverdueReview] = []
    for doc in documents:
        if doc.get("status") not in _ELIGIBLE_STATUSES:
            continue
        raw = doc.get("next_review")
        if raw in (None, ""):
            continue
        try:
            deadline = parse_review_date(raw)
        except ReviewDateError:
            if strict:
                raise
            continue
        if deadline is None or deadline >= today:
            continue
        filename = doc.get("filename") or "?"
        out.append(
            OverdueReview(
                filename=filename,
                next_review=deadline,
                days_overdue=(today - deadline).days,
            )
        )

    out.sort(key=lambda r: (-r.days_overdue, r.filename))
    return out


def compute_upcoming(
    documents: Iterable[dict[str, Any]],
    today: date | None = None,
    *,
    within_days: int = 30,
    strict: bool = False,
) -> list[OverdueReview]:
    """Docs with a review deadline ``0 <= delta <= within_days`` away.

    Uses the same ``OverdueReview`` dataclass for convenience; the
    ``days_overdue`` field is negated (≤0) to indicate days *remaining*.
    Caller is expected to interpret the sign (or call this only for
    upcoming work). Sorted soonest-first.
    """
    if today is None:
        today = date.today()

    out: list[OverdueReview] = []
    for doc in documents:
        if doc.get("status") not in _ELIGIBLE_STATUSES:
            continue
        raw = doc.get("next_review")
        if raw in (None, ""):
            continue
        try:
            deadline = parse_review_date(raw)
        except ReviewDateError:
            if strict:
                raise
            continue
        if deadline is None:
            continue
        delta = (deadline - today).days
        if 0 <= delta <= within_days:
            filename = doc.get("filename") or "?"
            out.append(
                OverdueReview(
                    filename=filename,
                    next_review=deadline,
                    days_overdue=-delta,  # negative = days-remaining
                )
            )

    # days_overdue is stored as -delta for upcoming; sort by delta ascending
    # (= soonest-first) which means -days_overdue ascending.
    out.sort(key=lambda r: (-r.days_overdue, r.filename))
    return out


__all__ = [
    "ReviewDateError",
    "OverdueReview",
    "parse_review_date",
    "format_review_date",
    "compute_overdue",
    "compute_upcoming",
]
