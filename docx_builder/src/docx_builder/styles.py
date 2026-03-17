"""
styles.py — Heading style application.

Headings are styled directly via XML rather than relying on named Word styles.
This ensures consistent rendering regardless of the base document template
and avoids style inheritance surprises.

Style map:
  H1: 16pt bold, BLUE_DARK (#1F4E79), 240pt space before
  H2: 13pt bold, BLUE_MID  (#2E75B6), 180pt space before
  H3: 11pt bold, BLACK     (#000000), 120pt space before
"""

from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from .constants import BLUE_DARK, BLUE_MID, BLACK, FONT_TITLE
from .xml_helpers import set_run_color, para_spacing


def apply_heading_style(doc, para, level: int):
    """
    Apply Heading formatting to an existing paragraph.

    Sets the paragraph style name (Heading1/2/3) for TOC field compatibility,
    then applies font size, color, and spacing directly to override
    any inherited style defaults.

    Args:
        doc:   python-docx Document (unused directly but kept for API consistency)
        para:  the paragraph to style
        level: heading level (1, 2, or 3)
    """
    # Apply named heading style so the native TOC field can discover headings
    pPr    = para._p.get_or_add_pPr()
    pStyle = OxmlElement('w:pStyle')
    style_map = {1: 'Heading1', 2: 'Heading2', 3: 'Heading3'}
    pStyle.set(qn('w:val'), style_map.get(level, 'Heading1'))
    pPr.insert(0, pStyle)

    # Font size and color by level
    size_map   = {1: 16,        2: 13,      3: 11}
    color_map  = {1: BLUE_DARK, 2: BLUE_MID, 3: BLACK}
    before_map = {1: 240,       2: 180,     3: 120}

    para_spacing(para, before=before_map.get(level, 120), after=80)

    for run in para.runs:
        run.bold      = True
        run.font.name = FONT_TITLE
        run.font.size = Pt(size_map.get(level, 11))
        set_run_color(run, color_map.get(level, BLACK))
