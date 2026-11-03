#!/usr/bin/env python3
"""
Flag Markdown constructs that docx_builder cannot render.

Legal GitHub-flavored Markdown and builder-renderable Markdown are not the
same set. A construct can pass markdownlint, look right on GitHub, and still
come out of the DOCX render broken, and nobody learns that until a reader
opens the document. This check names the known gaps so the gate catches them
at source.

Current checks:

  nested-table    A pipe table indented inside a list item. The builder's
                  table extractor only matches rows that start at column 0,
                  so an indented table never reaches the table renderer and
                  its rows land in the list item as literal pipe text.

  indented-table  The same failure outside a list: a table indented for any
                  other reason (a stray leading space, a block quote) is
                  skipped by the extractor and renders as prose.

Scope matches lint-mermaid.py: Markdown files with YAML front matter, which
is what the builder renders. Fenced code blocks and front matter are skipped.

Usage:
    lint-docx-constructs.py [--path .] [--include-templates]

Exit codes: 0 = clean, 1 = at least one error.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
SKIP_DIRS = {".git", ".github", ".vale", "archive", "exports", "diagrams", "node_modules"}
SKIP_NAMES = {"README.md", "CLAUDE.md", "CONTRIBUTING.md", "CHANGELOG.md"}

# A list item: optional indent, a bullet or ordered marker, then at least one
# space (or end of line for an empty item).
LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[-*+]|\d{1,9}[.)])(?P<gap>[ \t]+|$)")

# A fence opener or closer. Three or more backticks or tildes, indented by
# any amount so fences inside list items are recognised too.
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")

# The divider row under a table header: cells of dashes with optional colons.
# This is what makes two pipe lines a table rather than prose with pipes.
DIVIDER_RE = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")

TAB_WIDTH = 4


def eligible_markdown_files(root: Path, include_templates: bool) -> list[Path]:
    results: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if path.name in SKIP_NAMES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not include_templates and "templates" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if FRONT_MATTER_RE.match(text):
            results.append(path)
    return results


def _indent_of(line: str) -> int:
    expanded = line.expandtabs(TAB_WIDTH)
    return len(expanded) - len(expanded.lstrip(" "))


def _is_table_header(line: str, next_line: str | None) -> bool:
    if next_line is None:
        return False
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    return bool(DIVIDER_RE.match(next_line.strip()))


def find_issues(text: str) -> list[tuple[str, int, str]]:
    """Return (severity, line_no, message) for every unsupported construct.

    Line numbers are 1-based and count from the top of the file, front
    matter included, so they match what an editor shows.
    """
    issues: list[tuple[str, int, str]] = []
    lines = text.splitlines()

    start = 0
    fm = FRONT_MATTER_RE.match(text)
    if fm:
        start = fm.group(0).count("\n")

    # Stack of (content_indent, item_line_no) for the list items that
    # enclose the current line. A line indented at least as far as the
    # innermost item's content continues that item.
    items: list[tuple[int, int]] = []
    fence_marker: str | None = None

    for idx in range(start, len(lines)):
        line = lines[idx]
        line_no = idx + 1
        stripped = line.strip()

        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_marker is None:
                fence_marker = marker[0] * 3
                continue
            if marker.startswith(fence_marker):
                fence_marker = None
                continue
        if fence_marker is not None:
            continue

        if not stripped:
            continue

        indent = _indent_of(line)
        while items and indent < items[-1][0]:
            items.pop()

        item = LIST_ITEM_RE.match(line)
        if item:
            content_indent = _indent_of(line) + len(item.group("marker")) + max(len(item.group("gap")), 1)
            items.append((content_indent, line_no))
            continue

        next_line = lines[idx + 1] if idx + 1 < len(lines) else None
        if indent > 0 and _is_table_header(line, next_line):
            if items:
                issues.append((
                    "ERROR",
                    line_no,
                    f"Table nested inside a list item (item starts at line {items[-1][1]}). "
                    "docx_builder only renders tables that start at column 0; the rows "
                    "will appear as literal pipe text. Move the table out of the list.",
                ))
            else:
                issues.append((
                    "ERROR",
                    line_no,
                    "Indented table. docx_builder only renders tables that start at "
                    "column 0; the rows will appear as literal pipe text.",
                ))

    return issues


def lint_file(path: Path, root: Path) -> list[tuple[str, int, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues = find_issues(text)
    if not issues:
        return []
    rel = path.relative_to(root).as_posix()
    return [(severity, line_no, f"{rel}:{line_no}: {message}") for severity, line_no, message in issues]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--path", default=".", help="Repo root to scan.")
    parser.add_argument("--include-templates", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    files = eligible_markdown_files(root, include_templates=args.include_templates)

    all_issues: list[tuple[str, int, str]] = []
    for path in files:
        all_issues.extend(lint_file(path, root))

    errors = 0
    warnings = 0
    for severity, _, message in all_issues:
        print(f"[{severity}] {message}")
        if severity == "ERROR":
            errors += 1
        else:
            warnings += 1

    print(f"\nChecked {len(files)} file(s). Errors: {errors}, Warnings: {warnings}.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
