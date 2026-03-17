"""
markdown_parser.py — Markdown to python-docx paragraph conversion.

Pipeline:
  1. extract_mermaid_fences() (diagrams.py) — extract ```mermaid blocks,
                          replace with __MERMAID_N__ placeholders.
  2. extract_md_tables()  — extract GFM-style pipe tables, render them as
                          docx tables, and replace them with placeholders
                          in the markdown text.
  3. mistune renders remaining markdown to HTML.
  4. HtmlToDocx (HTMLParser subclass) walks the HTML and emits paragraphs.

Why the multi-stage approach:
  Mermaid fences and pipe tables must be extracted before mistune sees them
  so they can be rendered with full control over styling and placement.
  Diagrams and tables are rendered inline during the segment loop in
  builder.py, so they appear in the correct document position.

Supported markdown elements:
  Block:  h1–h3, p, ul (unordered), ol (ordered), blockquote, pre/code, hr
  Inline: strong, em, code, a (hyperlink text only, no live URL in DOCX)
  Images: ![alt text](relative/path/to/image.png) — resolved relative to
          the source .md file's directory (PNG, JPG, GIF, TIFF, BMP)
  Tables: GFM pipe tables with header / alignment divider / body rows

Elements not supported (rendered as plain text or ignored):
  - h4–h6 (treated as h3)
  - Nested blockquotes beyond one level
  - HTML inside markdown (stripped)
  - SVG images (export to PNG before referencing)
  - Cover logo (handled separately in cover_page.py)
"""

import os
import re
from html.parser import HTMLParser

from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import RGBColor

from .constants import BLUE_LINK, BLACK, FONT_BODY, GRAY_TEXT
from .xml_helpers import (
    set_run_color, para_spacing,
    set_cell_bg, set_cell_borders, set_table_border,
    set_paragraph_border_bottom,
)
from .styles import apply_heading_style
from .metadata import HeadingNumberer


def _strip_html(text: str) -> str:
    """Remove HTML tags for plain text extraction."""
    return re.sub(r'<[^>]+>', '', text or '').strip()


# ── HTML → docx walker ────────────────────────────────────────────────────────

class HtmlToDocx(HTMLParser):
    """
    Walk mistune-rendered HTML and emit python-docx paragraphs into `doc`.

    Headings are collected in self.headings as (level, text, None) tuples
    for use by the TOC builder.

    State tracking:
      _tag_stack     : stack of (tag, attrs_dict) for active open tags
      _list_stack    : stack of ('ul'|'ol', [counter]) for nested lists
      _current_para  : the paragraph currently being built
      _in_pre        : True while inside a <pre> block
      _pre_buf       : accumulates raw text inside <pre>
      _in_blockquote : True while inside <blockquote>
    """

    def __init__(self, doc, md_src_dir: str | None = None):
        super().__init__()
        self.doc        = doc
        self.headings   = []   # (level, numbered_text, None)
        # Directory of the source .md file, used to resolve relative image paths.
        # Defaults to the current working directory if not provided.
        self.md_src_dir = md_src_dir or os.getcwd()

        self._current_para   = None
        self._tag_stack      = []
        self._list_stack     = []
        self._in_pre         = False
        self._pre_buf        = []
        self._in_blockquote  = False
        self._skip_tags      = {'html', 'body', 'head'}
        self._heading_numberer = HeadingNumberer()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _current_tags(self):
        return {t for t, _ in self._tag_stack}

    def _flush_para(self):
        self._current_para = None

    def _ensure_para(self, before=60, after=80):
        if self._current_para is None:
            self._current_para = self.doc.add_paragraph()
            para_spacing(self._current_para, before=before, after=after)
        return self._current_para

    def _add_run(self, text, bold=False, italic=False, code=False, link=False):
        if not text:
            return
        para = self._ensure_para()
        run  = para.add_run(text)
        run.font.name = "Courier New" if code else FONT_BODY
        run.font.size = Pt(9) if code else Pt(10)
        run.bold      = bold
        run.italic    = italic
        if link:
            set_run_color(run, BLUE_LINK)
            run.underline = True
        elif code:
            set_run_color(run, RGBColor(0x1F, 0x1F, 0x1F))
        else:
            set_run_color(run, BLACK)

    def _handle_img(self, attrs_dict: dict) -> None:
        """
        Embed an image referenced by an <img src="..." alt="..."> tag.

        src is resolved relative to self.md_src_dir so that relative paths
        in the markdown (e.g. ../../diagrams/exported/foo.png) work correctly.
        alt text is rendered as a small italic caption below the image.

        Missing or unresolvable paths emit a styled warning paragraph instead
        of raising an exception, so the build always completes.

        Supported formats: PNG, JPG/JPEG, GIF, TIFF, BMP.
        SVG is not supported by python-docx — export to PNG first.
        """
        src = attrs_dict.get('src', '').strip()
        alt = attrs_dict.get('alt', '').strip()

        if not src:
            return

        # Resolve relative paths from the source .md file's directory
        img_path = src if os.path.isabs(src) else \
            os.path.normpath(os.path.join(self.md_src_dir, src))

        self._flush_para()

        if os.path.isfile(img_path):
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para_spacing(p, before=120, after=40)
            p.add_run().add_picture(img_path, width=Inches(DIAGRAM_DEFAULT_WIDTH_IN))
            if alt:
                cap = self.doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para_spacing(cap, before=0, after=120)
                run           = cap.add_run(alt)
                run.italic    = True
                run.font.name = FONT_BODY
                run.font.size = Pt(9)
                set_run_color(run, GRAY_TEXT)
        else:
            # Image not found — warn without crashing
            p   = self.doc.add_paragraph()
            para_spacing(p, before=60, after=60)
            run = p.add_run(f'[Image not found: {src}]')
            run.italic    = True
            run.font.name = FONT_BODY
            run.font.size = Pt(10)
            set_run_color(run, RGBColor(0xCC, 0x00, 0x00))

    # ── HTMLParser callbacks ──────────────────────────────────────────────────

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # img is a void element — handle fully here without touching the tag
        # stack.  HTMLParser may call handle_starttag + handle_endtag for
        # self-closing <img/>, but since we never push img onto _tag_stack
        # the subsequent handle_endtag is harmless (stack check will miss).
        if tag == 'img':
            self._handle_img(attrs_dict)
            return

        self._tag_stack.append((tag, attrs_dict))

        if tag in self._skip_tags:
            return

        if tag in ('h1', 'h2', 'h3'):
            self._flush_para()
            self._current_para = self.doc.add_paragraph()

        elif tag == 'p':
            self._flush_para()
            if self._in_blockquote:
                self._current_para = self.doc.add_paragraph()
                para_spacing(self._current_para, before=60, after=60)
                self._current_para.paragraph_format.left_indent = Inches(0.5)
            else:
                self._current_para = self.doc.add_paragraph()
                para_spacing(self._current_para, before=60, after=80)

        elif tag in ('ul', 'ol'):
            self._list_stack.append((tag, [0]))

        elif tag == 'li':
            self._flush_para()
            depth   = len(self._list_stack)
            ordered = self._list_stack[-1][0] == 'ol' if self._list_stack else False
            if ordered:
                self._list_stack[-1][1][0] += 1
                prefix = f"{self._list_stack[-1][1][0]}."
            else:
                prefix = "\u2022"   # bullet

            indent_left_in    = (360 * depth) / 1440
            indent_hanging_in = 360 / 1440

            self._current_para = self.doc.add_paragraph()
            para_spacing(self._current_para, before=40, after=40)
            self._current_para.paragraph_format.left_indent      = Inches(indent_left_in + indent_hanging_in)
            self._current_para.paragraph_format.first_line_indent = Inches(-indent_hanging_in)
            run = self._current_para.add_run(f"{prefix}\t")
            run.font.name = FONT_BODY
            run.font.size = Pt(10)

        elif tag == 'blockquote':
            self._in_blockquote = True

        elif tag == 'pre':
            self._in_pre  = True
            self._pre_buf = []

        elif tag == 'hr':
            p = self.doc.add_paragraph()
            set_paragraph_border_bottom(p, color="CCCCCC", sz=4)
            para_spacing(p, before=120, after=120)
            self._flush_para()

    def handle_endtag(self, tag):
        if self._tag_stack and self._tag_stack[-1][0] == tag:
            self._tag_stack.pop()

        if tag in ('h1', 'h2', 'h3'):
            if self._current_para:
                level    = int(tag[1])
                raw_text = ''.join(r.text for r in self._current_para.runs)
                numbered = self._heading_numberer.format(level, raw_text)
                # Replace paragraph content with the numbered heading text
                # so the heading in the document body and the TOC field match.
                self._current_para.clear()
                self._current_para.add_run(numbered)
                apply_heading_style(self.doc, self._current_para, level)
                self.headings.append((level, numbered, None))
            self._flush_para()

        elif tag == 'p':
            self._flush_para()

        elif tag in ('ul', 'ol'):
            if self._list_stack:
                self._list_stack.pop()
            self._flush_para()

        elif tag == 'li':
            self._flush_para()

        elif tag == 'blockquote':
            self._in_blockquote = False
            self._flush_para()

        elif tag == 'pre':
            self._in_pre = False
            text = ''.join(self._pre_buf)
            p    = self.doc.add_paragraph()
            para_spacing(p, before=60, after=60)
            # Light gray background for code blocks via raw XML shading
            from docx.oxml import OxmlElement as _OxmlElement
            from docx.oxml.ns import qn as _qn
            pPr = p._p.get_or_add_pPr()
            shd = _OxmlElement('w:shd')
            shd.set(_qn('w:val'),   'clear')
            shd.set(_qn('w:color'), 'auto')
            shd.set(_qn('w:fill'),  'F2F2F2')
            pPr.append(shd)
            run = p.add_run(text)
            run.font.name = "Courier New"
            run.font.size = Pt(9)
            set_run_color(run, RGBColor(0x1F, 0x1F, 0x1F))
            self._flush_para()

    def handle_data(self, data):
        if not data:
            return

        if self._in_pre:
            self._pre_buf.append(data)
            return

        # Don't create a new paragraph just for inter-element whitespace when
        # no paragraph is open (e.g. whitespace inside <p>...</p> after an
        # embedded <img> has already flushed _current_para).
        if data.strip() == '' and self._current_para is None:
            return

        tags = self._current_tags()

        # Ignore whitespace-only text between block-level elements
        if data.strip() == '' and not (tags & {'p', 'li', 'h1', 'h2', 'h3',
                                               'strong', 'em', 'code', 'a',
                                               'blockquote'}):
            return

        bold   = 'strong' in tags
        italic = 'em'     in tags or self._in_blockquote
        code   = 'code'   in tags and 'pre' not in tags
        link   = 'a'      in tags

        self._add_run(data, bold=bold, italic=italic, code=code, link=link)


# ── GFM table extraction ──────────────────────────────────────────────────────

def extract_md_tables(md_text: str) -> tuple[str, list[dict]]:
    """
    Extract GFM pipe tables from markdown without touching the document.

    Returns (processed_text, table_data_list) where:
      - processed_text has each table replaced by a __TABLE_N__ placeholder
      - table_data_list[N] is a dict with all data needed to render table N

    Call render_md_table(doc, table_data) for each placeholder encountered
    while iterating segments in order. This keeps tables and body text
    interleaved correctly in the final document.

    Table styling applied by render_md_table:
      - Header row: BLUE_MID (#2E75B6) background, white text
      - Body rows:  alternating white / light gray (#F2F2F2)
      - Column widths: evenly distributed across 8" content width
      - Alignment: derived from GFM divider row (:---:, ---:, :---)
    """
    table_re = re.compile(
        r'(?m)^(\|.+\|\n)(\|[-| :]+\|\n)((?:\|.+\|\n?)*)',
        re.MULTILINE
    )
    tables: list[dict] = []

    def extract_table(m):
        header_row  = [c.strip() for c in m.group(1).strip().split('|') if c.strip()]
        divider_row = [c.strip() for c in m.group(2).strip().split('|') if c.strip()]
        body_rows   = []
        for line in m.group(3).strip().splitlines():
            row = [c.strip() for c in line.strip().split('|') if c.strip()]
            if row:
                body_rows.append(row)

        idx = len(tables)
        tables.append({
            'header_row':  header_row,
            'divider_row': divider_row,
            'body_rows':   body_rows,
        })
        return f'\n__TABLE_{idx}__\n'

    processed = table_re.sub(extract_table, md_text)
    return processed, tables


def render_md_table(doc, table_data: dict) -> None:
    """
    Render a single parsed GFM table into the document at the current position.

    Called from builder.py while iterating body segments in order so that
    each table lands immediately after the preceding paragraph — not all
    tables first followed by all text (the old broken behaviour).
    """
    header_row  = table_data['header_row']
    divider_row = table_data['divider_row']
    body_rows   = table_data['body_rows']

    # Derive alignment from divider cells
    alignments = []
    for cell in divider_row:
        if cell.startswith(':') and cell.endswith(':'):
            alignments.append(WD_ALIGN_PARAGRAPH.CENTER)
        elif cell.endswith(':'):
            alignments.append(WD_ALIGN_PARAGRAPH.RIGHT)
        else:
            alignments.append(WD_ALIGN_PARAGRAPH.LEFT)

    n_cols = len(header_row)
    col_w  = 8.0 / n_cols   # distribute evenly across 8" content width

    table = doc.add_table(rows=1, cols=n_cols)
    table.style     = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_table_border(table, color="CCCCCC", sz=4)

    # Header row
    hdr = table.rows[0]
    for i, col_text in enumerate(header_row):
        cell = hdr.cells[i]
        cell.width = Inches(col_w)
        set_cell_bg(cell, "2E75B6")
        set_cell_borders(cell, color="CCCCCC", sz=4)
        p   = cell.paragraphs[0]
        p.alignment = alignments[i] if i < len(alignments) else WD_ALIGN_PARAGRAPH.LEFT
        para_spacing(p, before=60, after=60)
        run = p.add_run(col_text)
        run.bold      = True
        run.font.name = FONT_BODY
        run.font.size = Pt(10)
        set_run_color(run, RGBColor(0xFF, 0xFF, 0xFF))

    # Body rows
    for ridx, body_row in enumerate(body_rows):
        row  = table.add_row()
        fill = "F2F2F2" if ridx % 2 == 1 else "FFFFFF"
        for i in range(n_cols):
            cell = row.cells[i]
            cell.width = Inches(col_w)
            set_cell_bg(cell, fill)
            set_cell_borders(cell, color="CCCCCC", sz=4)
            p   = cell.paragraphs[0]
            p.alignment = alignments[i] if i < len(alignments) else WD_ALIGN_PARAGRAPH.LEFT
            para_spacing(p, before=60, after=60)
            val = body_row[i] if i < len(body_row) else ''
            run = p.add_run(val)
            run.font.name = FONT_BODY
            run.font.size = Pt(10)
            set_run_color(run, BLACK)

    doc.add_paragraph()   # spacer after table
