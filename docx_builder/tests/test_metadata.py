"""
tests/test_metadata.py — Unit tests for YAML front matter parsing.

Run with: python -m pytest tests/ from the docx_builder directory.
Or: pip install pytest && pytest
"""

import pytest
from docx_builder.metadata import parse_front_matter, extract_headings


# ── parse_front_matter ────────────────────────────────────────────────────────

def test_parse_front_matter_basic():
    raw = """\
---
title: "Test Document"
status: "Draft"
version: "1.0"
---

## Overview

Some content here.
"""
    meta, body = parse_front_matter(raw)
    assert meta['title']   == "Test Document"
    assert meta['status']  == "Draft"
    assert meta['version'] == "1.0"
    assert "## Overview" in body
    assert "---" not in body


def test_parse_front_matter_no_front_matter():
    raw = "## Just markdown\n\nNo front matter here."
    meta, body = parse_front_matter(raw)
    assert meta == {}
    assert body == raw


def test_parse_front_matter_list_fields():
    raw = """\
---
audience:
  - Platform Engineering
  - Architecture Review Board
related_docs:
  - "Network Design v1.0"
---
"""
    meta, body = parse_front_matter(raw)
    assert isinstance(meta['audience'], list)
    assert len(meta['audience']) == 2
    assert "Platform Engineering" in meta['audience']
    assert isinstance(meta['related_docs'], list)


def test_parse_front_matter_revision_history():
    raw = """\
---
revision_history:
  - version: "1.0"
    date: "2026-03-14"
    author: "A. Smith"
    description: "Initial draft"
  - version: "1.1"
    date: "2026-03-20"
    author: "B. Jones"
    description: "Incorporated review feedback"
---
"""
    meta, _ = parse_front_matter(raw)
    revs = meta['revision_history']
    assert len(revs) == 2
    assert revs[0]['version'] == "1.0"
    assert revs[1]['author']  == "B. Jones"


def test_parse_front_matter_empty_block():
    raw = "---\n---\n\nContent."
    meta, body = parse_front_matter(raw)
    assert meta == {}
    assert "Content." in body


# ── extract_headings ──────────────────────────────────────────────────────────

def test_extract_headings_basic():
    body = """\
## Overview

Some text.

### Background

More text.

## Architecture

Final section.
"""
    headings = extract_headings(body)
    assert len(headings) == 3
    # Text is now numbered; H2 with no preceding H1 gets counter 0.N
    assert headings[0][0] == 2
    assert headings[0][1].endswith("Overview")
    assert headings[1][0] == 3
    assert headings[1][1].endswith("Background")
    assert headings[2][0] == 2
    assert headings[2][1].endswith("Architecture")


def test_extract_headings_h1():
    body = "# Top Level\n\n## Sub\n"
    headings = extract_headings(body)
    assert headings[0][0] == 1
    assert headings[1][0] == 2


def test_extract_headings_none():
    body = "No headings here.\n\nJust paragraphs."
    headings = extract_headings(body)
    assert headings == []


def test_extract_headings_strips_whitespace():
    body = "##  Heading with extra space  \n"
    headings = extract_headings(body)
    # Text is numbered; verify the title portion (after the em dash) is trimmed
    assert headings[0][1].endswith("Heading with extra space")
