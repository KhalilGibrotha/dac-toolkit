"""
tests/test_lint_docx_constructs.py — Tests for the builder-unsupported
construct gate.

The gate exists because a pipe table indented inside a list item is legal
GFM, passes markdownlint, and still renders as literal pipe text in the
DOCX: the builder's table extractor only matches rows at column 0. These
tests pin the three shapes that matter (nested table flagged, top-level
table clean, ordinary list clean) plus the places a naive scan gets wrong:
pipes inside fenced code, pipes in front matter, and a table that follows
a list once the list has ended.

Run with: python -m pytest scripts/tests/ from the repo root.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "lint-docx-constructs.py"


def _load():
    spec = importlib.util.spec_from_file_location("lint_docx_constructs", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()

FRONT_MATTER = "---\ntitle: Fixture\nstatus: Draft\n---\n\n"

NESTED_TABLE = FRONT_MATTER + """# Checklist

1. Confirm the inputs.
2. Record the result:

   | Field | Value |
   |-------|-------|
   | Host  | web01 |

3. File the record.
"""

TOP_LEVEL_TABLE = FRONT_MATTER + """# Inventory

| Field | Value |
|-------|-------|
| Host  | web01 |
| Role  | app   |
"""

PLAIN_LIST = FRONT_MATTER + """# Steps

- First step.
- Second step, with a continuation paragraph
  that wraps onto an indented line.
  - A nested bullet.
- Third step.

1. Numbered.
2. Also numbered.
"""


def _line_numbers(text: str) -> list[int]:
    return [line_no for _, line_no, _ in MOD.find_issues(text)]


# ── The three shapes the issue names ─────────────────────────────────────────

def test_table_nested_in_list_item_is_flagged():
    issues = MOD.find_issues(NESTED_TABLE)
    assert len(issues) == 1
    severity, line_no, message = issues[0]
    assert severity == "ERROR"
    # Line 11 is the header row "   | Field | Value |" counted from the
    # top of the file, front matter included.
    assert line_no == 11
    assert "nested inside a list item" in message
    assert "item starts at line 9" in message


def test_top_level_table_is_clean():
    assert MOD.find_issues(TOP_LEVEL_TABLE) == []


def test_ordinary_list_is_clean():
    assert MOD.find_issues(PLAIN_LIST) == []


# ── Nesting variants ─────────────────────────────────────────────────────────

def test_bullet_list_nesting_is_flagged():
    text = FRONT_MATTER + """- Item one
- Item two

  | A | B |
  |---|---|
  | 1 | 2 |
"""
    assert _line_numbers(text) == [9]


def test_table_directly_under_item_text_is_flagged():
    # No blank line between the item and the table.
    text = FRONT_MATTER + """- Item
  | A | B |
  |---|---|
"""
    assert _line_numbers(text) == [7]


def test_deeply_nested_list_reports_innermost_item():
    text = FRONT_MATTER + """- Outer
  - Inner

    | A | B |
    |---|---|
"""
    issues = MOD.find_issues(text)
    assert len(issues) == 1
    assert "item starts at line 7" in issues[0][2]


def test_table_after_list_has_ended_is_clean():
    # A column-0 paragraph ends the list; the table that follows is top level.
    text = FRONT_MATTER + """- Item one
- Item two

Closing paragraph.

| A | B |
|---|---|
| 1 | 2 |
"""
    assert MOD.find_issues(text) == []


def test_indented_table_outside_a_list_is_flagged_separately():
    text = FRONT_MATTER + """# Heading

  | A | B |
  |---|---|
"""
    issues = MOD.find_issues(text)
    assert len(issues) == 1
    assert "Indented table" in issues[0][2]
    assert "nested" not in issues[0][2]


# ── Things that look like tables but are not ─────────────────────────────────

def test_pipes_in_fenced_code_inside_a_list_are_ignored():
    text = FRONT_MATTER + """- Run the query:

  ```sql
  | col | val |
  |-----|-----|
  ```

- Done.
"""
    assert MOD.find_issues(text) == []


def test_tilde_fence_is_honoured():
    text = FRONT_MATTER + """- Example:

  ~~~
  | col | val |
  |-----|-----|
  ~~~
"""
    assert MOD.find_issues(text) == []


def test_pipe_line_without_divider_is_not_a_table():
    text = FRONT_MATTER + """- Item

  | just | prose with pipes |
  and no divider row follows.
"""
    assert MOD.find_issues(text) == []


def test_front_matter_pipes_are_skipped():
    text = """---
title: Fixture
description: |
  | not | a table |
  |-----|---------|
---

Body.
"""
    assert MOD.find_issues(text) == []


# ── End-to-end: file discovery, output format, exit code ─────────────────────

def _run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(root), *extra],
        capture_output=True, text=True,
    )


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_cli_reports_file_and_line_and_exits_nonzero(tmp_path):
    _write(tmp_path, "docs/bad.md", NESTED_TABLE)
    _write(tmp_path, "docs/good.md", TOP_LEVEL_TABLE)
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "[ERROR] docs/bad.md:11:" in result.stdout
    assert "good.md" not in result.stdout
    assert "Checked 2 file(s). Errors: 1, Warnings: 0." in result.stdout


def test_cli_exits_zero_when_clean(tmp_path):
    _write(tmp_path, "docs/good.md", TOP_LEVEL_TABLE)
    _write(tmp_path, "docs/list.md", PLAIN_LIST)
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "Checked 2 file(s). Errors: 0, Warnings: 0." in result.stdout


def test_cli_skips_files_without_front_matter_and_skip_dirs(tmp_path):
    body = NESTED_TABLE[len(FRONT_MATTER):]
    _write(tmp_path, "notes.md", body)
    _write(tmp_path, "README.md", NESTED_TABLE)
    _write(tmp_path, "exports/old.md", NESTED_TABLE)
    _write(tmp_path, "templates/t.md", NESTED_TABLE)
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "Checked 0 file(s)." in result.stdout


def test_cli_include_templates(tmp_path):
    _write(tmp_path, "templates/t.md", NESTED_TABLE)
    result = _run(tmp_path, "--include-templates")
    assert result.returncode == 1
    assert "[ERROR] templates/t.md:11:" in result.stdout
