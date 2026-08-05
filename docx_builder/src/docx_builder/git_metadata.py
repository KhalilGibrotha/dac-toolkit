"""
git_metadata.py — Derive document authorship from git rather than front matter.

A hand-maintained `author:` field is wrong the moment somebody else edits the
document, and nothing detects it. Git already records who changed what and
when, so the revision table can read the fact instead of a copy of it.

Two modes:

  * Default. A document with no `revision_history:` gets one auto-generated
    row, and the author and date on that row come from the file's most recent
    commit. Front matter supplies the fallback when git cannot answer.

  * `revision_history: auto`. Rows are generated from the file's commit
    history, newest first, capped by REVISION_LIMIT. Use this where the
    document genuinely wants a changelog.

An explicit `revision_history:` list still wins over both. Curating the
history by hand stays available; it is just no longer the only option.

Display names come from the commit email, because a corporate address encodes
the name: `first.last@example.org` yields `First Last`. Addresses that carry
no name (noreply forms, bare handles) fall back to the git author name, then
to front matter. An `authors:` map in org.yaml overrides any of it for
identities the pattern cannot reach.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# How many commits `revision_history: auto` renders. A document with 200
# commits does not want a 200-row table before its first heading.
REVISION_LIMIT = 10

# Addresses that identify an account rather than a person. Matching one means
# the email cannot supply a display name.
_OPAQUE_EMAIL = re.compile(
    r"(noreply|no-reply|users\.noreply\.github\.com|\[bot\]|actions@github)",
    re.IGNORECASE,
)

# first.last@domain or first.middle.last@domain — the corporate form.
_DOTTED_LOCAL = re.compile(r"^([A-Za-z]+(?:[.\-_][A-Za-z]+)+)@")


def display_name_from_email(email: str) -> str | None:
    """Turn a corporate address into a display name, or None if it cannot.

    `alex.gambino@ncsecu.org` -> `Alex Gambino`.

    Returns None rather than guessing when the local part carries no
    separator, because `agambino@example.org` has no recoverable split point
    and inventing one produces a name that is confidently wrong.
    """
    if not email or _OPAQUE_EMAIL.search(email):
        return None
    m = _DOTTED_LOCAL.match(email.strip())
    if not m:
        return None
    parts = re.split(r"[.\-_]", m.group(1))
    return " ".join(p.capitalize() for p in parts if p)


def _git(args: list[str], cwd: Path) -> str | None:
    """Run git, returning stdout, or None if git cannot answer.

    Every failure mode is the same answer here: no history available, use the
    fallback. A document must still render outside a checkout - in a release
    tarball, or a container that mounted only the sources.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _resolve_name(email: str, git_name: str, overrides: dict) -> str:
    """Best available display name for one commit identity.

    Overrides are checked against both the email and the git author name, so
    a historical identity can be mapped by whichever of the two is stable.
    Commits predating a corporate git config carry neither a usable address
    nor a real name, and the override map is the only way to reach them.
    """
    if email and email.lower() in overrides:
        return overrides[email.lower()]
    if git_name and git_name.lower() in overrides:
        return overrides[git_name.lower()]
    from_email = display_name_from_email(email)
    if from_email:
        return from_email
    return git_name or ""


def contributors(md_path: str, author_overrides: dict | None = None,
                 max_named: int = 2) -> str:
    """Who wrote this document, most prolific first.

    The author column names contributors rather than the last committer.
    Attributing a document to whoever touched it last means a typo fix - or a
    repo-wide line-ending normalization - silently reassigns authorship, which
    is exactly the inaccuracy this is meant to remove.

    Caps at max_named because the column is 1.5 inches wide; beyond that it
    reports the overflow rather than wrapping to five lines.
    """
    history = commit_history(md_path, limit=200, author_overrides=author_overrides)
    if not history:
        return ""
    counts: dict[str, int] = {}
    for row in history:
        name = row["author"]
        if name:
            counts[name] = counts.get(name, 0) + 1
    if not counts:
        return ""
    ranked = sorted(counts, key=lambda n: (-counts[n], n))
    if len(ranked) <= max_named:
        return ", ".join(ranked)
    return f"{', '.join(ranked[:max_named])} +{len(ranked) - max_named}"


def commit_history(md_path: str, limit: int = REVISION_LIMIT,
                   author_overrides: dict | None = None) -> list[dict]:
    """Commits that touched this file, newest first.

    Each entry: {date, author, subject}. Empty list when git cannot answer,
    which callers treat as "fall back to front matter" rather than as an
    error.
    """
    path = Path(md_path).resolve()
    if not path.exists():
        return []
    overrides = {k.lower(): v for k, v in (author_overrides or {}).items()}

    # %x1f is a unit separator: commit subjects contain almost anything, and
    # splitting on a character a human can type is how a subject with a pipe
    # or a tab corrupts the parse.
    # --follow traverses renames. Without it a moved or renamed document
    # shows only the commits made under its CURRENT path, so the table
    # attributes it to whoever renamed it and drops the original authors -
    # the same class of error as crediting a line-ending pass. It requires
    # exactly one pathspec, which is what is passed here.
    out = _git(
        ["log", "--follow", f"-{max(1, limit)}", "--date=short",
         "--format=%ad%x1f%ae%x1f%an%x1f%s", "--", path.name],
        path.parent,
    )
    if not out:
        return []

    rows = []
    for line in out.splitlines():
        fields = line.split("\x1f")
        if len(fields) != 4:
            continue
        date, email, git_name, subject = fields
        rows.append({
            "date": date,
            "author": _resolve_name(email, git_name, overrides),
            "subject": subject,
        })
    return rows


def revision_rows(md_path: str, meta: dict) -> list[dict] | None:
    """Rows for the revision table, or None to use the caller's own default.

    Resolution order, most explicit first:

      1. `revision_history:` as a list — the author curated it, leave it alone
      2. `revision_history: auto` — generate a changelog from git
      3. no revision_history — one row, with author and date taken from the
         last commit and everything else from front matter
    """
    declared = meta.get("revision_history")
    overrides = (meta.get("org") or {}).get("authors") or meta.get("authors") or {}

    if isinstance(declared, list) and declared:
        # Curated by hand, and it stays that way: a row reading "Records the
        # 2026-07-27 engineering decision" is editorial content no commit
        # subject reproduces. The one thing git adds is filling a row whose
        # author was left BLANK, so a curator can write version, date and
        # description and let authorship resolve itself.
        if all(str(r.get("author", "")).strip() for r in declared):
            return None
        names = contributors(md_path, author_overrides=overrides)
        if not names:
            return None
        return [
            {**row, "author": row.get("author") or names}
            for row in declared
        ]

    history = commit_history(md_path, author_overrides=overrides)

    if isinstance(declared, str) and declared.strip().lower() == "auto":
        if not history:
            return None
        return [
            {
                "version": "",
                "date": row["date"],
                "author": row["author"],
                "description": row["subject"],
            }
            for row in history
        ]

    # Default: one row, with only the author taken from git.
    #
    # The DATE deliberately stays with front matter. `date:` means the last
    # SUBSTANTIVE revision - a human judgement - while git's newest commit
    # includes typo fixes and repo-wide reformatting. A line-ending
    # normalization pass should not advance a document's revision date.
    if not history:
        return None
    names = contributors(md_path, author_overrides=overrides)
    if not names:
        return None
    status = str(meta.get("status", "")).lower()
    return [{
        "version": meta.get("version", "1.0"),
        "date": str(meta.get("date", "")),
        "author": names,
        "description": "Initial draft" if status == "draft" else "Initial release",
    }]


def resolve_owner(meta: dict) -> str:
    """Document owner: front matter first, then the org default.

    Owner names a team rather than a person, so it belongs in org.yaml where
    one edit sets it for every document. A document that genuinely differs -
    one owned by another team - overrides it in its own front matter.
    """
    own = meta.get("owner")
    if own:
        return str(own)
    org = meta.get("org") or {}
    return str(org.get("owner", "") or "")
