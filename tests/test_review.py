"""Tests for the next_review field and the librarian.review module (Phase 7.2).

Covers:
    * Date parsing (parse_review_date, format_review_date, ReviewDateError)
    * Overdue computation (compute_overdue + status filtering)
    * Upcoming-window computation (compute_upcoming)
    * AuditReport integration (overdue_reviews populated; clean unaffected)
    * Audit text + JSON output
    * CLI: register --review-by, bump --review-by, bump --clear-review,
      scaffold --review-by, and the dedicated `review set/clear/list`
      subcommand.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

import pytest
import yaml

# Project root — needed because subprocess.run(cwd=tmp_path) loses the
# implicit sys.path entry pytest adds. We pass it via PYTHONPATH so
# `python -m librarian` resolves regardless of where librarian was
# installed (or whether it was installed at all).
_REPO_ROOT = Path(__file__).resolve().parents[1]

from librarian.audit import audit, format_report
from librarian.registry import Registry
from librarian.review import (
    OverdueReview,
    ReviewDateError,
    compute_overdue,
    compute_upcoming,
    format_review_date,
    parse_review_date,
)


# --------------------------------------------------------------------------- #
# parse_review_date / format_review_date                                       #
# --------------------------------------------------------------------------- #


class TestParseReviewDate:
    def test_parses_iso_string(self):
        assert parse_review_date("2026-12-31") == date(2026, 12, 31)

    def test_strips_whitespace(self):
        assert parse_review_date("  2026-04-14  ") == date(2026, 4, 14)

    def test_none_passthrough(self):
        assert parse_review_date(None) is None

    def test_empty_string_is_none(self):
        assert parse_review_date("") is None
        assert parse_review_date("   ") is None

    def test_date_passthrough(self):
        d = date(2026, 7, 1)
        assert parse_review_date(d) == d

    @pytest.mark.parametrize("bad", [
        "2026/12/31",     # wrong separator
        "12-31-2026",     # US format
        "2026-13-01",     # invalid month
        "2026-12-32",     # invalid day
        "Dec 31 2026",    # natural language
        "2026",           # year only
        "tomorrow",
    ])
    def test_rejects_malformed(self, bad):
        with pytest.raises(ReviewDateError):
            parse_review_date(bad)

    def test_rejects_unsupported_type(self):
        with pytest.raises(ReviewDateError):
            parse_review_date(20261231)  # type: ignore[arg-type]


class TestFormatReviewDate:
    def test_formats_date(self):
        assert format_review_date(date(2026, 12, 31)) == "2026-12-31"

    def test_none_passthrough(self):
        assert format_review_date(None) is None


# --------------------------------------------------------------------------- #
# compute_overdue                                                              #
# --------------------------------------------------------------------------- #


@pytest.fixture
def today():
    return date(2026, 4, 14)


@pytest.fixture
def docs():
    return [
        {"filename": "very-overdue.md", "status": "active",
         "next_review": "2025-01-01"},
        {"filename": "barely-overdue.md", "status": "active",
         "next_review": "2026-04-13"},
        {"filename": "due-today.md", "status": "active",
         "next_review": "2026-04-14"},
        {"filename": "soon.md", "status": "active",
         "next_review": "2026-04-30"},
        {"filename": "far-future.md", "status": "active",
         "next_review": "2027-12-31"},
        {"filename": "no-deadline.md", "status": "active"},
        {"filename": "draft-overdue.md", "status": "draft",
         "next_review": "2026-01-01"},
        {"filename": "superseded-overdue.md", "status": "superseded",
         "next_review": "2025-01-01"},
        {"filename": "archived-overdue.md", "status": "archived",
         "next_review": "2025-01-01"},
        {"filename": "malformed.md", "status": "active",
         "next_review": "next quarter"},
    ]


class TestComputeOverdue:
    def test_returns_overdue_only(self, docs, today):
        result = compute_overdue(docs, today=today)
        names = [r.filename for r in result]
        assert "very-overdue.md" in names
        assert "barely-overdue.md" in names
        assert "draft-overdue.md" in names

    def test_excludes_due_today(self, docs, today):
        # "due-today" has next_review == today; not overdue yet.
        result = compute_overdue(docs, today=today)
        assert "due-today.md" not in [r.filename for r in result]

    def test_excludes_future(self, docs, today):
        result = compute_overdue(docs, today=today)
        for fn in ("soon.md", "far-future.md"):
            assert fn not in [r.filename for r in result]

    def test_excludes_no_deadline(self, docs, today):
        result = compute_overdue(docs, today=today)
        assert "no-deadline.md" not in [r.filename for r in result]

    def test_excludes_superseded_and_archived(self, docs, today):
        result = compute_overdue(docs, today=today)
        names = [r.filename for r in result]
        assert "superseded-overdue.md" not in names
        assert "archived-overdue.md" not in names

    def test_silent_skip_malformed_by_default(self, docs, today):
        # Default strict=False — malformed dates do not raise.
        result = compute_overdue(docs, today=today)
        assert "malformed.md" not in [r.filename for r in result]

    def test_strict_raises_on_malformed(self, docs, today):
        with pytest.raises(ReviewDateError):
            compute_overdue(docs, today=today, strict=True)

    def test_sorted_most_overdue_first(self, docs, today):
        result = compute_overdue(docs, today=today)
        days = [r.days_overdue for r in result]
        assert days == sorted(days, reverse=True)

    def test_days_overdue_correct(self, docs, today):
        by_name = {r.filename: r.days_overdue for r in compute_overdue(docs, today=today)}
        assert by_name["barely-overdue.md"] == 1  # 4/14 - 4/13 = 1d
        # very-overdue: 2026-04-14 - 2025-01-01 = 468d
        assert by_name["very-overdue.md"] == (date(2026, 4, 14) - date(2025, 1, 1)).days

    def test_to_dict_shape(self, docs, today):
        first = compute_overdue(docs, today=today)[0]
        d = first.to_dict()
        assert set(d.keys()) == {"filename", "next_review", "days_overdue"}
        assert d["next_review"] == first.next_review.isoformat()


class TestComputeUpcoming:
    def test_finds_within_window(self, docs, today):
        # within 30 days from 2026-04-14: due-today (0d), soon (16d).
        # Not very-overdue, not far-future.
        result = compute_upcoming(docs, today=today, within_days=30)
        names = [r.filename for r in result]
        assert "soon.md" in names
        assert "due-today.md" in names
        assert "far-future.md" not in names
        assert "very-overdue.md" not in names

    def test_excludes_overdue(self, docs, today):
        result = compute_upcoming(docs, today=today, within_days=30)
        # overdue items should NOT appear in upcoming
        assert "very-overdue.md" not in [r.filename for r in result]

    def test_window_boundary(self, today):
        # Day exactly at window edge is included.
        d = (today.toordinal() + 30)
        target = date.fromordinal(d)
        docs_local = [
            {"filename": "edge.md", "status": "active",
             "next_review": target.isoformat()},
        ]
        result = compute_upcoming(docs_local, today=today, within_days=30)
        assert [r.filename for r in result] == ["edge.md"]

    def test_sorted_soonest_first(self, docs, today):
        result = compute_upcoming(docs, today=today, within_days=60)
        # days_overdue is negated for upcoming; sorting by it ascending
        # = soonest first.
        deadlines = [r.next_review for r in result]
        assert deadlines == sorted(deadlines)


# --------------------------------------------------------------------------- #
# AuditReport integration                                                      #
# --------------------------------------------------------------------------- #


def _write_registry(tmp_path: Path, docs: list[dict]) -> Path:
    registry = {
        "project_config": {"project_name": "test", "tracked_dirs": ["docs/"]},
        "documents": docs,
    }
    p = tmp_path / "REGISTRY.yaml"
    p.write_text(yaml.safe_dump(registry, sort_keys=False))
    (tmp_path / "docs").mkdir(exist_ok=True)
    # Materialise files so the audit doesn't flag them as missing.
    for d in docs:
        path = tmp_path / d.get("path", f"docs/{d['filename']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# " + d["filename"])
    return p


class TestAuditIntegration:
    def test_audit_report_populates_overdue(self, tmp_path):
        docs = [
            {"filename": "stale-doc-20260101-V1.0.md", "status": "active",
             "next_review": "2025-01-01",
             "path": "docs/stale-doc-20260101-V1.0.md"},
            {"filename": "fresh-doc-20260101-V1.0.md", "status": "active",
             "next_review": "2030-01-01",
             "path": "docs/fresh-doc-20260101-V1.0.md"},
        ]
        reg_path = _write_registry(tmp_path, docs)
        reg = Registry.load(reg_path)
        report = audit(reg, tmp_path)
        names = [r.filename for r in report.overdue_reviews]
        assert "stale-doc-20260101-V1.0.md" in names
        assert "fresh-doc-20260101-V1.0.md" not in names

    def test_overdue_does_not_flip_clean(self, tmp_path):
        # Phase 7.2 contract: overdue_reviews are advisory like
        # folder_suggestions — they should not change report.clean.
        docs = [
            {"filename": "stale-doc-20260101-V1.0.md", "status": "active",
             "next_review": "2025-01-01",
             "path": "docs/stale-doc-20260101-V1.0.md"},
        ]
        reg_path = _write_registry(tmp_path, docs)
        reg = Registry.load(reg_path)
        report = audit(reg, tmp_path)
        assert report.overdue_reviews
        assert report.clean is True

    def test_format_report_includes_overdue(self, tmp_path):
        docs = [
            {"filename": "stale-doc-20260101-V1.0.md", "status": "active",
             "next_review": "2025-01-01",
             "path": "docs/stale-doc-20260101-V1.0.md"},
        ]
        reg_path = _write_registry(tmp_path, docs)
        reg = Registry.load(reg_path)
        report = audit(reg, tmp_path)
        text = format_report(report)
        assert "Overdue reviews" in text
        assert "stale-doc-20260101-V1.0.md" in text
        assert "overdue" in text.lower()


# --------------------------------------------------------------------------- #
# CLI: register / bump / scaffold flags + review subcommand                    #
# --------------------------------------------------------------------------- #


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_REPO_ROOT}{os.pathsep}{existing_pp}" if existing_pp else str(_REPO_ROOT)
    )
    return subprocess.run(
        [sys.executable, "-m", "librarian", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def cli_repo(tmp_path: Path) -> Path:
    """A minimal repo with a registry the CLI can mutate."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "REGISTRY.yaml").write_text(textwrap.dedent("""\
        project_config:
          project_name: test
          tracked_dirs:
          - docs/
          default_author: Tester
          default_classification: INTERNAL
          naming_rules:
            separator: '-'
            case: lowercase
            infrastructure_exempt:
            - REGISTRY.yaml
        documents: []
    """))
    return tmp_path


class TestCLIRegisterReviewBy:
    def test_register_with_review_by_persists_field(self, cli_repo):
        (cli_repo / "docs" / "guide-20260101-V1.0.md").write_text("# guide")
        result = _run_cli(
            "register", "docs/guide-20260101-V1.0.md",
            "--review-by", "2026-12-31",
            cwd=cli_repo,
        )
        assert result.returncode == 0, result.stderr
        assert "next_review: 2026-12-31" in result.stdout
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        entry = reg["documents"][0]
        assert entry["next_review"] == "2026-12-31"

    def test_register_without_review_by_omits_field(self, cli_repo):
        (cli_repo / "docs" / "guide-20260101-V1.0.md").write_text("# guide")
        result = _run_cli(
            "register", "docs/guide-20260101-V1.0.md",
            cwd=cli_repo,
        )
        assert result.returncode == 0
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        assert "next_review" not in reg["documents"][0]

    def test_register_rejects_bad_date(self, cli_repo):
        (cli_repo / "docs" / "guide-20260101-V1.0.md").write_text("# guide")
        result = _run_cli(
            "register", "docs/guide-20260101-V1.0.md",
            "--review-by", "next quarter",
            cwd=cli_repo,
        )
        assert result.returncode != 0
        assert "expected YYYY-MM-DD" in result.stderr


class TestCLIBumpReviewBy:
    def _seed(self, cli_repo: Path) -> None:
        (cli_repo / "docs" / "guide-20260101-V1.0.md").write_text("# guide")
        _run_cli(
            "register", "docs/guide-20260101-V1.0.md",
            "--review-by", "2026-12-31",
            cwd=cli_repo,
        )

    def test_bump_inherits_review_by_default(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli("bump", "guide-20260101-V1.0.md", cwd=cli_repo)
        assert result.returncode == 0, result.stderr
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        new = next(d for d in reg["documents"] if d["version"] == "V1.1")
        assert new["next_review"] == "2026-12-31"

    def test_bump_review_by_overrides(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli(
            "bump", "guide-20260101-V1.0.md",
            "--review-by", "2027-06-30",
            cwd=cli_repo,
        )
        assert result.returncode == 0, result.stderr
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        new = next(d for d in reg["documents"] if d["version"] == "V1.1")
        assert new["next_review"] == "2027-06-30"

    def test_bump_clear_review_drops_field(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli(
            "bump", "guide-20260101-V1.0.md",
            "--clear-review",
            cwd=cli_repo,
        )
        assert result.returncode == 0, result.stderr
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        new = next(d for d in reg["documents"] if d["version"] == "V1.1")
        assert "next_review" not in new

    def test_bump_review_by_and_clear_are_mutually_exclusive(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli(
            "bump", "guide-20260101-V1.0.md",
            "--review-by", "2027-01-01",
            "--clear-review",
            cwd=cli_repo,
        )
        assert result.returncode != 0
        assert "not allowed with" in result.stderr or "argument" in result.stderr


class TestCLIReviewSubcommand:
    def _seed(self, cli_repo: Path) -> None:
        (cli_repo / "docs" / "guide-20260101-V1.0.md").write_text("# guide")
        _run_cli("register", "docs/guide-20260101-V1.0.md", cwd=cli_repo)

    def test_review_set_adds_field(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli(
            "review", "set", "guide-20260101-V1.0.md",
            "--by", "2026-12-31",
            cwd=cli_repo,
        )
        assert result.returncode == 0, result.stderr
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        assert reg["documents"][0]["next_review"] == "2026-12-31"

    def test_review_set_updates_existing(self, cli_repo):
        self._seed(cli_repo)
        _run_cli("review", "set", "guide-20260101-V1.0.md",
                 "--by", "2026-12-31", cwd=cli_repo)
        result = _run_cli("review", "set", "guide-20260101-V1.0.md",
                          "--by", "2027-06-30", cwd=cli_repo)
        assert result.returncode == 0, result.stderr
        assert "(was: 2026-12-31)" in result.stdout
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        assert reg["documents"][0]["next_review"] == "2027-06-30"

    def test_review_set_unknown_doc(self, cli_repo):
        result = _run_cli(
            "review", "set", "no-such-doc.md",
            "--by", "2026-12-31",
            cwd=cli_repo,
        )
        assert result.returncode == 1
        assert "Not registered" in result.stderr

    def test_review_set_rejects_bad_date(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli(
            "review", "set", "guide-20260101-V1.0.md",
            "--by", "tomorrow",
            cwd=cli_repo,
        )
        assert result.returncode != 0
        assert "expected YYYY-MM-DD" in result.stderr

    def test_review_clear_removes_field(self, cli_repo):
        self._seed(cli_repo)
        _run_cli("review", "set", "guide-20260101-V1.0.md",
                 "--by", "2026-12-31", cwd=cli_repo)
        result = _run_cli(
            "review", "clear", "guide-20260101-V1.0.md", cwd=cli_repo,
        )
        assert result.returncode == 0
        reg = yaml.safe_load((cli_repo / "docs/REGISTRY.yaml").read_text())
        assert "next_review" not in reg["documents"][0]

    def test_review_clear_when_none_set(self, cli_repo):
        self._seed(cli_repo)
        result = _run_cli(
            "review", "clear", "guide-20260101-V1.0.md", cwd=cli_repo,
        )
        assert result.returncode == 0
        assert "No review deadline was set" in result.stdout

    def test_review_list_default(self, cli_repo):
        self._seed(cli_repo)
        # add second doc
        (cli_repo / "docs" / "other-20260101-V1.0.md").write_text("# other")
        _run_cli("register", "docs/other-20260101-V1.0.md", cwd=cli_repo)
        _run_cli("review", "set", "guide-20260101-V1.0.md",
                 "--by", "2030-01-01", cwd=cli_repo)
        _run_cli("review", "set", "other-20260101-V1.0.md",
                 "--by", "2025-01-01", cwd=cli_repo)
        result = _run_cli("review", "list", cwd=cli_repo)
        assert result.returncode == 0
        # Most-overdue first by default sort
        assert result.stdout.find("other-20260101-V1.0.md") < result.stdout.find("guide-20260101-V1.0.md")

    def test_review_list_overdue_only(self, cli_repo):
        self._seed(cli_repo)
        _run_cli("review", "set", "guide-20260101-V1.0.md",
                 "--by", "2030-01-01", cwd=cli_repo)
        result = _run_cli("review", "list", "--overdue", cwd=cli_repo)
        assert result.returncode == 0
        assert "No overdue reviews" in result.stdout

    def test_review_list_empty(self, cli_repo):
        result = _run_cli("review", "list", cwd=cli_repo)
        assert result.returncode == 0
        assert "No documents have a next_review deadline" in result.stdout


class TestCLIAuditJSON:
    def test_audit_json_includes_overdue_reviews(self, cli_repo):
        (cli_repo / "docs" / "guide-20260101-V1.0.md").write_text("# guide")
        _run_cli(
            "register", "docs/guide-20260101-V1.0.md",
            "--review-by", "2025-01-01",
            cwd=cli_repo,
        )
        result = _run_cli("audit", "--json", cwd=cli_repo)
        assert result.returncode == 0, result.stderr
        # JSON may have leading/trailing noise; isolate the JSON object.
        payload = json.loads(result.stdout)
        overdue = payload["audit"]["overdue_reviews"]
        assert overdue
        assert overdue[0]["filename"] == "guide-20260101-V1.0.md"
        assert overdue[0]["next_review"] == "2025-01-01"
        assert overdue[0]["days_overdue"] > 0
