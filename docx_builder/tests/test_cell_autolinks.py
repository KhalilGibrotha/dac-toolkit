"""
tests/test_cell_autolinks.py — Inline markdown inside table cells.

Table cells are extracted before mistune runs, so cell inline markdown is
parsed by _INLINE_MD_RE rather than by the HTML walker. Anything the walker
handles has to be handled again here or it renders as raw source.

Run with: python -m pytest tests/ from the docx_builder directory.
"""

import pytest

from docx_builder.markdown_parser import _INLINE_MD_RE


def _kinds(text):
    """Sequence of (kind, matched-text) for the inline constructs found."""
    out = []
    for m in _INLINE_MD_RE.finditer(text):
        if m.group("auto"):
            out.append(("auto", m.group("aurl")))
        elif m.group("link"):
            out.append(("link", m.group("lurl")))
        else:
            out.append(("style", m.group(0)))
    return out


# ── Autolinks ─────────────────────────────────────────────────────────────────

def test_autolink_is_recognised():
    assert _kinds("<https://example.com/repo>") == \
        [("auto", "https://example.com/repo")]


def test_autolink_target_excludes_the_brackets():
    # The reported defect: angle brackets rendered literally in the cell.
    kinds = _kinds("See <https://example.com/x> for detail")
    assert kinds == [("auto", "https://example.com/x")]
    assert "<" not in kinds[0][1] and ">" not in kinds[0][1]


@pytest.mark.parametrize("scheme", ["https", "http", "mailto", "ftp"])
def test_common_schemes_autolink(scheme):
    text = f"<{scheme}:target>"
    assert _kinds(text) == [("auto", f"{scheme}:target")]


def test_angle_brackets_without_a_scheme_are_left_alone():
    # Placeholder prose is common in these documents; swallowing it as a link
    # would be worse than the defect being fixed.
    assert _kinds("Set <environment> before running") == []
    assert _kinds("<name>") == []


def test_autolink_does_not_swallow_following_text():
    kinds = _kinds("<https://example.com> and <https://example.org>")
    assert kinds == [("auto", "https://example.com"),
                     ("auto", "https://example.org")]


# ── Regressions on constructs that already worked ────────────────────────────

def test_inline_link_still_wins_over_autolink():
    assert _kinds("[label](https://example.com)") == \
        [("link", "https://example.com")]


def test_link_destination_keeps_balanced_parentheses():
    assert _kinds("[x](https://example.com/Function_(mathematics))") == \
        [("link", "https://example.com/Function_(mathematics)")]


def test_code_and_emphasis_still_match():
    kinds = _kinds("`code` and **bold** and *italic*")
    assert [k for k, _ in kinds] == ["style", "style", "style"]
