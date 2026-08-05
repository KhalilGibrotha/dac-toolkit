"""
tests/test_git_metadata.py — Authorship derived from git rather than front matter.

The revision table used to print whatever `author:` said, which is wrong the
moment somebody else edits the document and nothing detects it. These tests
pin the three behaviours that make the derived version trustworthy:

  * a display name is derived only when the address actually encodes one,
  * authorship reflects who wrote the document rather than who touched it
    last, so a typo fix cannot reassign it,
  * every failure mode falls back rather than raising, because a document
    must still render outside a git checkout.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from docx_builder.git_metadata import (
    commit_history,
    contributors,
    display_name_from_email,
    resolve_owner,
    revision_rows,
)


# ── display_name_from_email ──────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("alex.gambino@ncsecu.org", "Alex Gambino"),
        ("ALEX.GAMBINO@NCSECU.ORG", "Alex Gambino"),
        ("jane.q.public@example.org", "Jane Q Public"),
        ("mary-jane.watson@example.org", "Mary Jane Watson"),
        # No separator in the local part: there is no recoverable split point,
        # and inventing one produces a name that is confidently wrong.
        ("agambino@example.org", None),
        # Account identities, not people.
        ("khalilgibrotha@users.noreply.github.com", None),
        ("49699333+dependabot[bot]@users.noreply.github.com", None),
        ("actions@github.com", None),
        ("", None),
    ],
)
def test_display_name_from_email(email, expected):
    assert display_name_from_email(email) == expected


# ── graceful degradation ─────────────────────────────────────────────────────

def test_missing_file_returns_empty(tmp_path):
    assert commit_history(str(tmp_path / "nope.md")) == []


def test_outside_a_git_checkout_returns_empty(tmp_path):
    # A release tarball or a container mounting only sources: no .git, and the
    # document must still render.
    doc = tmp_path / "doc.md"
    doc.write_text("# hi\n")
    assert commit_history(str(doc)) == []
    assert revision_rows(str(doc), {"version": "1.0"}) is None


# ── against a real repository ────────────────────────────────────────────────

def _commit(repo: Path, name: str, email: str, message: str, path: Path, text: str):
    path.write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True,
                   capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-qm", message],
        check=True, capture_output=True,
        env={
            "PATH": __import__("os").environ.get("PATH", ""),
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        },
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    doc = tmp_path / "doc.md"
    # Two commits from one author, one from another. The MINORITY author
    # commits last, which is the case that catches last-committer logic.
    _commit(tmp_path, "Alex Gambino", "alex.gambino@ncsecu.org",
            "initial draft", doc, "# doc\n\nfirst\n")
    _commit(tmp_path, "Alex Gambino", "alex.gambino@ncsecu.org",
            "expand section", doc, "# doc\n\nfirst\nsecond\n")
    _commit(tmp_path, "Dana Scully", "dana.scully@ncsecu.org",
            "fix typo", doc, "# doc\n\nfirst\nsecond fixed\n")
    return tmp_path


def test_commit_history_is_newest_first(repo):
    rows = commit_history(str(repo / "doc.md"))
    assert [r["subject"] for r in rows] == [
        "fix typo", "expand section", "initial draft",
    ]
    assert rows[0]["author"] == "Dana Scully"


def test_contributors_ranked_by_volume_not_recency(repo):
    # Dana committed most recently; Alex wrote most of it. A typo fix must not
    # reassign authorship of the document.
    assert contributors(str(repo / "doc.md")) == "Alex Gambino, Dana Scully"


def test_contributors_overflow_is_reported_not_wrapped(repo):
    doc = repo / "doc.md"
    for who in ("Fox Mulder", "Walter Skinner"):
        first, last = who.lower().split()
        _commit(repo, who, f"{first}.{last}@ncsecu.org", f"edit by {who}",
                doc, f"# doc\n\n{who} was here\n")
    # 1.5-inch column: name two, count the rest.
    assert contributors(str(doc), max_named=2).endswith("+2")


def test_author_name_override_reaches_historical_identities(repo):
    doc = repo / "doc.md"
    _commit(repo, "oldhandle", "oldhandle@users.noreply.github.com",
            "legacy commit", doc, "# doc\n\nlegacy\n")
    # Without a mapping the handle is all that is available.
    assert "oldhandle" in contributors(str(doc), max_named=5)
    # Mapping by git author name reaches it.
    mapped = contributors(str(doc), author_overrides={"oldhandle": "Alex Gambino"},
                          max_named=5)
    assert "oldhandle" not in mapped
    assert "Alex Gambino" in mapped


# ── revision_rows resolution order ───────────────────────────────────────────

def test_curated_list_wins(repo):
    meta = {"revision_history": [{"version": "0.1", "author": "Someone"}]}
    assert revision_rows(str(repo / "doc.md"), meta) is None


def test_default_row_keeps_front_matter_date(repo):
    # `date:` means last SUBSTANTIVE revision - a human judgement. Git's newest
    # commit includes typo fixes and repo-wide reformatting, so a line-ending
    # normalization pass must not advance a document's revision date.
    meta = {"version": "0.3", "status": "Draft", "date": "2026-01-15",
            "author": "Stale Value"}
    rows = revision_rows(str(repo / "doc.md"), meta)
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-01-15"
    assert rows[0]["version"] == "0.3"
    assert rows[0]["author"] == "Alex Gambino, Dana Scully"
    assert rows[0]["description"] == "Initial draft"


def test_auto_mode_renders_a_changelog(repo):
    meta = {"revision_history": "auto", "version": "0.3"}
    rows = revision_rows(str(repo / "doc.md"), meta)
    assert len(rows) == 3
    # Here the per-row date IS the commit date, because each row is a commit.
    assert rows[0]["description"] == "fix typo"
    assert rows[0]["author"] == "Dana Scully"


def test_auto_mode_without_history_falls_back(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("# hi\n")
    assert revision_rows(str(doc), {"revision_history": "auto"}) is None


# ── owner resolution ─────────────────────────────────────────────────────────

def test_owner_prefers_front_matter():
    meta = {"owner": "Network Engineering", "org": {"owner": "Infra Arch"}}
    assert resolve_owner(meta) == "Network Engineering"


def test_owner_falls_back_to_org_default():
    assert resolve_owner({"org": {"owner": "Infra Arch"}}) == "Infra Arch"


def test_owner_empty_when_neither_set():
    assert resolve_owner({}) == ""
