"""
xml_helpers.py — Low-level python-docx / lxml XML utility functions.

IMPORTANT — Schema ordering rules for Word XML
-----------------------------------------------
Word is strict about child-element ordering inside container elements.
Several functions below include comments explaining the required order.
Violating these orders causes Word to silently drop formatting or
(in extreme cases) refuse to open the file.

Summary of known constraints:
  - tcPr:  tcBorders must appear BEFORE w:shd
  - tblPr: tblBorders must appear BEFORE w:tblLook
  - pPr:   w:keepNext must appear before w:pBdr, w:spacing, and w:ind
  - pPr:   w:pBdr must appear before w:spacing and w:ind
  - pPr:   w:tabs must appear before w:spacing and w:ind

These are enforced by the helper functions below. Do not change the
insertion positions without verifying against the OOXML schema.
"""

from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import RGBColor
import docx


# ── Cell / table XML helpers ──────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    """Set cell background fill color. hex_color is a 6-char hex string, e.g. '1F4E79'."""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    existing = tcPr.find(qn('w:shd'))
    if existing is not None:
        tcPr.remove(existing)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    # shd always comes AFTER tcBorders in tcPr schema order
    tcPr.append(shd)


def set_cell_borders(cell, color: str = "CCCCCC", sz: int = 4):
    """
    Apply single-line borders to all four sides of a cell.
    sz is in 1/8-point units (4 = 0.5pt).

    tcBorders must be inserted BEFORE w:shd in tcPr — see schema note above.
    """
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    existing = tcPr.find(qn('w:tcBorders'))
    if existing is not None:
        tcPr.remove(existing)
    tcBorders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'),   'single')
        el.set(qn('w:sz'),    str(sz))
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        tcBorders.append(el)
    # Insert tcBorders before shd if shd is already present
    shd = tcPr.find(qn('w:shd'))
    if shd is not None:
        tcPr.insert(list(tcPr).index(shd), tcBorders)
    else:
        tcPr.append(tcBorders)


def set_table_border(table, color: str = "CCCCCC", sz: int = 4):
    """
    Apply single-line borders to all sides and interior gridlines of a table.
    tblBorders must appear BEFORE w:tblLook in tblPr — see schema note above.
    """
    tbl   = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    existing = tblPr.find(qn('w:tblBorders'))
    if existing is not None:
        tblPr.remove(existing)
    tblBorders = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'),   'single')
        el.set(qn('w:sz'),    str(sz))
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        tblBorders.append(el)
    # Insert before tblLook to satisfy schema ordering
    tblLook = tblPr.find(qn('w:tblLook'))
    if tblLook is not None:
        tblPr.insert(list(tblPr).index(tblLook), tblBorders)
    else:
        tblPr.append(tblBorders)


def set_col_width(table, col_idx: int, width_inches: float):
    """Force a specific column to the given width (overrides table auto-fit)."""
    for row in table.rows:
        row.cells[col_idx].width = Inches(width_inches)


def set_row_cant_split(row) -> None:
    """
    Prevent a table row from breaking across pages.

    Sets <w:cantSplit/> in the row's <w:trPr>. When applied to every row in a
    table, no single row will be split by a page break. Combined with
    set_para_keep_next() on cell paragraphs, this keeps small tables together
    on one page.
    """
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn('w:cantSplit')) is None:
        cant_split = OxmlElement('w:cantSplit')
        trPr.append(cant_split)


def set_para_keep_next(para) -> None:
    """
    Set <w:keepNext/> on a paragraph so Word keeps it on the same page as the
    following content.

    In the OOXML pPr schema, keepNext appears before pBdr, spacing, and ind —
    insert at index 0 to satisfy schema ordering. Idempotent: does nothing if
    keepNext is already present.
    """
    pPr = para._p.get_or_add_pPr()
    if pPr.find(qn('w:keepNext')) is None:
        keep_next = OxmlElement('w:keepNext')
        pPr.insert(0, keep_next)


# ── Paragraph / run XML helpers ───────────────────────────────────────────────

def set_run_color(run, rgb: RGBColor):
    """Set the font color of a run."""
    run.font.color.rgb = rgb


def no_space_paragraph(para):
    """Remove before/after spacing from a paragraph."""
    pPr     = para._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), '0')
    spacing.set(qn('w:after'),  '0')
    pPr.append(spacing)


def para_spacing(para, before: int = 0, after: int = 0, line: int = None):
    """
    Set paragraph spacing.
    before, after: values in twips (1 point = 20 twips).
    line: line spacing in twips (240 = single, 480 = double). None = Word default.
    """
    pf = para.paragraph_format
    pf.space_before = Pt(before / 20)
    pf.space_after  = Pt(after  / 20)
    if line is not None:
        pf.line_spacing = Pt(line / 20)


def set_paragraph_border_bottom(para, color: str = "2E75B6", sz: int = 6):
    """
    Add a bottom border rule to a paragraph (used for decorative rules under
    the logo and document title on the cover page).
    w:pBdr must appear before w:spacing and w:ind in pPr — inserted at index 0.
    sz is in 1/8-point units (6 = 0.75pt).
    """
    pPr  = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'),   'single')
    bottom.set(qn('w:sz'),    str(sz))
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), color)
    pBdr.append(bottom)
    pPr.insert(0, pBdr)


def add_page_break(doc):
    """Insert a hard page break paragraph into the document body."""
    para = doc.add_paragraph()
    para.clear()
    run = para.add_run()
    br  = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    run._r.append(br)
    return para
