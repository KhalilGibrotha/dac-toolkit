"""
builder.py — Document orchestration: assembles all sections into a final DOCX.

build_document() is the single public entry point. It:
  1. Reads and parses the input Markdown file
  2. Creates a python-docx Document
  3. Builds Section 1 (cover page)
  4. Builds Section 2 (TOC)
  5. Builds Section 3 (revision history)
  6. Builds Section 4 (body content)
  7. Saves the document
  8. Applies a post-save fixup for a python-docx XML bug (see below)

POST-SAVE FIXUP — w:zoom
------------------------
python-docx emits <w:zoom/> in word/settings.xml without the required
w:percent attribute, which causes Word to display a repair warning or
refuse to open the file. The fixup patches the ZIP archive in-place after
saving to inject w:percent="100". This step is not optional and must
remain at the end of build_document().
"""

import os
import re
import shutil
import zipfile
import tempfile

import mistune
from docx import Document
from docx.shared import Inches
from docx.enum.section import WD_SECTION

from .metadata import parse_front_matter, extract_headings
from .cover_page import build_cover_page, remove_page_border
from .toc import build_toc_page
from .revision_history import build_revision_table
from .sections import add_section_break, add_body_footer
from .cover_page import set_toc_page_numbering_start
from .markdown_parser import HtmlToDocx, extract_md_tables, render_md_table
from .diagrams import extract_mermaid_fences, render_diagram


def build_document(
    md_path: str,
    logo_path: str | None = None,
    output_path: str | None = None,
    org_overrides: dict | None = None,
) -> str:
    """
    Convert a Markdown + YAML front matter file to a styled DOCX.

    Args:
        md_path:        Path to the input .md file.
        logo_path:      Optional path to a logo image (PNG or JPG).
                        If not provided or the file doesn't exist, org name
                        is rendered as text on the cover page.
        output_path:    Optional output .docx path.
                        Defaults to the input path with .docx extension.
        org_overrides:  Optional dict of org identity values (name, dept,
                        addr1, addr2, url) loaded from --org YAML file.
                        Merged into meta['org'], overriding front matter.

    Returns:
        The path to the saved .docx file.
    """
    # ── 1. Read and parse input ───────────────────────────────────────────────
    with open(md_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    meta, body_md = parse_front_matter(raw)

    # Merge org overrides: CLI --org flag takes precedence over front matter org: block
    if org_overrides:
        existing_org = meta.get('org') or {}
        existing_org.update(org_overrides)
        meta['org'] = existing_org
    headings_for_toc = extract_headings(body_md)

    # ── 2. Create document ────────────────────────────────────────────────────
    doc = Document()

    # Remove the default empty paragraph python-docx inserts on creation
    for para in doc.paragraphs:
        para._p.getparent().remove(para._p)

    # ── 3. Section 1: Cover page ──────────────────────────────────────────────
    build_cover_page(doc, meta, logo_path)

    # ── 4. Section 2: Table of Contents ──────────────────────────────────────
    toc_section = add_section_break(doc, WD_SECTION.NEW_PAGE)
    toc_section.top_margin    = Inches(1.0)
    toc_section.bottom_margin = Inches(1.0)
    toc_section.left_margin   = Inches(1.0)
    toc_section.right_margin  = Inches(1.0)

    toc_section.header.is_linked_to_previous = False
    toc_section.footer.is_linked_to_previous = False
    remove_page_border(toc_section)
    set_toc_page_numbering_start(toc_section, start=1)

    build_toc_page(doc, headings_for_toc)

    # ── 5. Section 3: Revision history ───────────────────────────────────────
    rev_section = add_section_break(doc, WD_SECTION.NEW_PAGE)
    rev_section.top_margin    = Inches(1.0)
    rev_section.bottom_margin = Inches(1.0)
    rev_section.left_margin   = Inches(1.0)
    rev_section.right_margin  = Inches(1.0)

    rev_section.header.is_linked_to_previous = False
    remove_page_border(rev_section)

    build_revision_table(doc, meta)

    # ── 6. Section 4: Body content ────────────────────────────────────────────
    body_section = add_section_break(doc, WD_SECTION.NEW_PAGE)
    body_section.top_margin    = Inches(1.0)
    body_section.bottom_margin = Inches(1.0)
    body_section.left_margin   = Inches(1.0)
    body_section.right_margin  = Inches(1.0)

    body_section.header.is_linked_to_previous = False
    remove_page_border(body_section)
    add_body_footer(body_section, meta)

    # Directory of the source .md file — used to resolve relative image paths
    # in ![alt](path) references inside HtmlToDocx.
    md_src_dir = os.path.dirname(os.path.abspath(md_path))

    # Step 1: Extract inline Mermaid fences before mistune sees them.
    #         Replaces each ```mermaid block with a __MERMAID_N__ placeholder.
    body_md_no_mermaid, mermaid_data_list = extract_mermaid_fences(body_md)

    # Step 2: Extract GFM tables (no doc writes yet).
    #         Replaces each pipe table with a __TABLE_N__ placeholder.
    body_md_processed, table_data_list = extract_md_tables(body_md_no_mermaid)

    # Step 3: Render all body segments in source order.
    #         Tables → render_md_table, diagrams → render_diagram (PNG embed),
    #         text → mistune → HtmlToDocx.  The temp directory holds diagram
    #         PNGs for the lifetime of the build and is cleaned up on exit.
    md_to_html = mistune.create_markdown()
    segments   = re.split(r'(__(?:TABLE|MERMAID)_\d+__)', body_md_processed)

    # Single walker instance so heading counters persist across all text
    # segments (tables and diagrams split the text but must not reset numbering).
    walker = HtmlToDocx(doc, md_src_dir=md_src_dir)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for seg in segments:
            tbl_match = re.match(r'__TABLE_(\d+)__',   seg.strip())
            mmd_match = re.match(r'__MERMAID_(\d+)__', seg.strip())
            if tbl_match:
                render_md_table(doc, table_data_list[int(tbl_match.group(1))])
            elif mmd_match:
                render_diagram(doc, mermaid_data_list[int(mmd_match.group(1))], tmp_dir)
            elif seg.strip():
                html_fragment = md_to_html(seg)
                walker.feed(html_fragment)

    # ── 7. Save ───────────────────────────────────────────────────────────────
    if output_path is None:
        base        = os.path.splitext(md_path)[0]
        output_path = f"{base}.docx"

    doc.save(output_path)

    # ── 8. Post-save fixup: patch <w:zoom/> in settings.xml ──────────────────
    # python-docx emits <w:zoom/> without the required w:percent attribute.
    # Word may refuse to open or warn about the file without this fix.
    # We patch the ZIP archive in-place rather than modifying python-docx internals.
    _fix_zoom_attribute(output_path)

    print(f"Saved: {output_path}")
    return output_path


def _fix_zoom_attribute(docx_path: str):
    """
    Patch word/settings.xml inside the DOCX ZIP to add w:percent="100" to
    any <w:zoom> element that is missing the attribute.

    This corrects a known python-docx bug. The fix is applied by rewriting
    the ZIP rather than modifying the Document object, which avoids
    triggering further python-docx serialization.
    """
    tmp = docx_path + '.tmp'
    with zipfile.ZipFile(docx_path, 'r') as zin, \
         zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/settings.xml':
                data = data.replace(
                    b'<w:zoom/>',
                    b'<w:zoom w:percent="100"/>'
                ).replace(
                    b'<w:zoom w:val=',
                    b'<w:zoom w:percent="100" w:val='
                )
                # Handle bare <w:zoom> without closing slash or w:percent
                data = re.sub(
                    rb'<w:zoom(?!\s+w:percent)(\s*/>|(?=\s+w:val))',
                    lambda m: b'<w:zoom w:percent="100"' + (b'/>' if m.group(1).strip() == b'/>' else b''),
                    data
                )
            zout.writestr(item, data)
    shutil.move(tmp, docx_path)
