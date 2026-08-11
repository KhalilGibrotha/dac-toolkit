"""
tests/test_table_layout.py — Unit tests for table column width allocation.

Run with: python -m pytest tests/ from the docx_builder directory.
Or: pip install pytest && pytest
"""

import pytest

from docx_builder.constants import (TABLE_COL_CHAR_CAP, TABLE_MIN_COL_IN,
                                    TABLE_TOTAL_WIDTH_IN)
from docx_builder.markdown_parser import _column_widths, _visible_len


# ── _visible_len ──────────────────────────────────────────────────────────────
#
# Width follows what the reader sees. Bids measured against raw markdown would
# buy inches for syntax that never draws.

def test_visible_len_strips_emphasis():
    assert _visible_len("**Recommended target**") == "Recommended target"
    assert _visible_len("*italic*") == "italic"
    assert _visible_len("`code`") == "code"


def test_visible_len_keeps_link_text_not_target():
    assert _visible_len("[the report](https://example.com/very/long/path)") \
        == "the report"


def test_visible_len_keeps_autolink_url():
    # A bare autolink renders as the URL, so the URL is what needs the width.
    assert _visible_len("<https://example.com/x>") == "https://example.com/x"


def test_visible_len_leaves_plain_text_alone():
    assert _visible_len("Satellite server to capsules") \
        == "Satellite server to capsules"


# ── _column_widths ────────────────────────────────────────────────────────────

def _widths(header, body):
    return _column_widths(header, body, len(header))


def test_narrow_column_yields_width_to_its_neighbours():
    header = ["#", "Rule", "Source"]
    body = [["1", "All automation executes from the platform; workstations "
                  "and the managed host are not execution points", "REQ-05"]]
    w = _widths(header, body)
    even = TABLE_TOTAL_WIDTH_IN / 3
    assert w[0] < even / 2, "a single-digit column must not claim an even share"
    assert w[1] > even, "the sentence column should gain what the counter gives up"


def test_widths_always_total_the_content_width():
    cases = [
        (["A", "B"], [["x", "y"]]),
        (["#", "Rule", "Source"], [["1", "a" * 200, "REQ-05"]]),
        (["One"], [["only one column"]]),
        (["a"] * 12, [["1"] * 12]),
    ]
    for header, body in cases:
        w = _widths(header, body)
        assert sum(w) == pytest.approx(TABLE_TOTAL_WIDTH_IN), header


def test_no_column_falls_below_the_floor():
    # A tiny column beside a very large one is where a floor gets violated.
    header = ["#", "Description"]
    body = [["1", "z" * 400]]
    w = _widths(header, body)
    assert min(w) >= TABLE_MIN_COL_IN - 1e-9


def test_runaway_cell_stops_bidding_at_the_cap():
    # Past the cap a cell wraps regardless, so doubling its length again must
    # not take more width from its neighbour.
    header = ["Short", "Long"]
    at_cap = _widths(header, [["ab", "z" * TABLE_COL_CHAR_CAP]])
    beyond = _widths(header, [["ab", "z" * (TABLE_COL_CHAR_CAP * 4)]])
    assert at_cap[1] == pytest.approx(beyond[1])


def test_long_word_is_not_broken_by_a_narrow_allocation():
    # A column whose cells are short overall but contain one long unbreakable
    # token still needs room for that token.
    header = ["Endpoint", "Note"]
    body = [["subscription-manager-register-endpoint", "ok"]]
    w = _widths(header, body)
    assert w[0] > w[1]


def test_all_tiny_columns_fall_back_to_an_even_split():
    # Nothing has surplus to fund a floor from; the even split must stand
    # rather than the allocator producing slivers or negative widths.
    header = ["a"] * 15
    w = _widths(header, [["1"] * 15])
    assert all(x == pytest.approx(TABLE_TOTAL_WIDTH_IN / 15) for x in w)


def test_header_text_counts_toward_the_bid():
    # A column with a long header and short cells still needs the header room.
    long_header = _widths(["Position under the support policy", "x"],
                          [["yes", "no"]])
    short_header = _widths(["Pos", "x"], [["yes", "no"]])
    assert long_header[0] > short_header[0]


def test_ragged_rows_do_not_raise():
    # Body rows shorter than the header are malformed markdown, but a build of
    # 100 documents must not abort on one of them.
    header = ["A", "B", "C"]
    w = _column_widths(header, [["only one"], ["two", "cells"]], 3)
    assert len(w) == 3
    assert sum(w) == pytest.approx(TABLE_TOTAL_WIDTH_IN)
