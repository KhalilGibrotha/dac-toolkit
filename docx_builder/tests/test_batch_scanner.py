"""
tests/test_batch_scanner.py — Scanner behavior, focused on the empty-render note.

Run with: python -m pytest tests/ from the docx_builder directory.
"""

import os
import textwrap

from docx_builder.batch_config import load_config
from docx_builder.batch_scanner import scan


NOTE_MARKER = "none with YAML front matter"


def _repo(tmp_path, files: dict[str, str], skip_retired: bool = True):
    """Build a minimal scannable repo and return its loaded BatchConfig."""
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    for rel, body in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
    config = tmp_path / "docx-build.yml"
    config.write_text(
        "export_root: exports/\n"
        "scan:\n  - docs/\n"
        f"options:\n  skip_retired: {'true' if skip_retired else 'false'}\n",
        encoding="utf-8",
    )
    return load_config(str(config))


def _notes(warnings):
    return [w for w in warnings if NOTE_MARKER in w]


DOC_RETIRED = """
    ---
    title: "Old"
    doc_type: "overview"
    status: "Retired"
    version: "0.1"
    ---

    # Old
    """

DOC_VALID = """
    ---
    title: "Current"
    doc_type: "overview"
    status: "Draft"
    version: "0.1"
    ---

    # Current
    """

DOC_MISSING_FIELDS = """
    ---
    title: "Incomplete"
    ---

    # Incomplete
    """

NO_FRONT_MATTER = """
    # Just a note

    No front matter here.
    """


def test_note_fires_when_nothing_has_front_matter(tmp_path):
    config = _repo(tmp_path, {"docs/notes.md": NO_FRONT_MATTER})
    docs, warnings = scan(config)
    assert docs == []
    assert len(_notes(warnings)) == 1


def test_note_silent_when_a_retired_doc_supplied_front_matter(tmp_path):
    # Empty render, but front matter exists — telling the user to add it is wrong.
    config = _repo(tmp_path, {
        "docs/notes.md": NO_FRONT_MATTER,
        "docs/old.md": DOC_RETIRED,
    })
    docs, warnings = scan(config)
    assert docs == []
    assert _notes(warnings) == []


def test_note_silent_when_front_matter_failed_validation(tmp_path):
    # The doc is skipped for missing required fields, not for lacking front matter.
    config = _repo(tmp_path, {
        "docs/notes.md": NO_FRONT_MATTER,
        "docs/incomplete.md": DOC_MISSING_FIELDS,
    })
    docs, warnings = scan(config)
    assert docs == []
    assert _notes(warnings) == []
    assert any("missing front matter" in w for w in warnings)


def test_note_silent_when_something_rendered(tmp_path):
    config = _repo(tmp_path, {
        "docs/notes.md": NO_FRONT_MATTER,
        "docs/current.md": DOC_VALID,
    })
    docs, warnings = scan(config)
    assert len(docs) == 1
    assert _notes(warnings) == []


def test_note_spans_two_lines(tmp_path):
    config = _repo(tmp_path, {"docs/notes.md": NO_FRONT_MATTER})
    _, warnings = scan(config)
    assert "\n" in _notes(warnings)[0]
