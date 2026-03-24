"""
constants.py — Organization branding, color palette, fonts, and page geometry.

All organization-specific values live here so that rebranding or
environment-specific overrides require changes in exactly one file.

Color values are expressed as RGBColor objects for direct use with python-docx.
Page dimensions are expressed in twips (1/1440 inch) for use in sectPr XML,
and EMU (English Metric Unit) for python-docx section properties.
    1 inch  = 1440 twips
    1 twip  = 635 EMU
    1 point = 20 twips
"""

from docx.shared import RGBColor

# ── Color palette ─────────────────────────────────────────────────────────────
# Dark navy used for cover title, heading H1, revision table header
BLUE_DARK  = RGBColor(0x1F, 0x4E, 0x79)

# Mid blue used for heading H2, revision/body table header backgrounds
BLUE_MID   = RGBColor(0x2E, 0x75, 0xB6)

# Teal used for TOC section heading (matches reference image)
TEAL       = RGBColor(0x17, 0x67, 0x6B)

# Link/URL blue used for hyperlink-style runs and cover-page URL
BLUE_LINK  = RGBColor(0x17, 0x50, 0x8D)

# Gray used for footer page-number text
GRAY_TEXT  = RGBColor(0x59, 0x59, 0x59)

# Standard black for body text
BLACK      = RGBColor(0x00, 0x00, 0x00)

# Dark navy for cover-page copyright block (matches reference image footer)
DARK_NAVY  = RGBColor(0x1A, 0x2F, 0x4A)

# ── Typography ────────────────────────────────────────────────────────────────
FONT_BODY  = "Calibri"
FONT_TITLE = "Calibri"

# ── Organization identity (defaults) ─────────────────────────────────────────
# These values appear on the cover page and in document footers.
# Override per-document via the `org:` front matter key, or change these
# defaults to match your organization.
ORG_NAME  = "Acme Corp"
ORG_DEPT  = "Enterprise Architecture"
ORG_ADDR1 = "123 Main Street"
ORG_ADDR2 = "Anytown, USA"
ORG_URL   = "www.example.com"

# ── Page geometry ─────────────────────────────────────────────────────────────
# US Letter dimensions in twips (used in raw sectPr XML and EMU calculations).
# Multiply by 635 to convert to EMU for python-docx section.page_width/height.
PAGE_W_TWIPS = 12240   # 8.5 inches
PAGE_H_TWIPS = 15840   # 11.0 inches

# Standard margin for cover page (0.75").
# Body/TOC/revision sections use 1.0" margins set directly in builder.py.
COVER_MARGIN_TWIPS = 1080   # 0.75 inches

# Twips-to-EMU conversion factor.
# Stored as a named constant to make section.page_width = Emu(W * TWIPS_TO_EMU) readable.
TWIPS_TO_EMU = 635

# ── Table cell styling ───────────────────────────────────────────────────────
# Internal cell padding in twips (1 pt = 20 twips).
# Vertical margins (top/bottom) control row height; horizontal (left/right)
# control the breathing room between border and text. Word default is 108
# twips (~5.4 pt) for left/right. These values produce compact, scannable rows.
TABLE_CELL_MARGIN_V = 36    # 1.8 pt — top and bottom
TABLE_CELL_MARGIN_H = 72    # 3.6 pt — left and right (half the Word default)
