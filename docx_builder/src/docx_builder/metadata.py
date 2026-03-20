"""
metadata.py — YAML front matter parsing and validation.

Extracts structured metadata from the --- delimited YAML block at the top
of a Markdown source file. If no front matter is present, returns an empty
dict and leaves the full text as body content.

Expected front matter keys (all optional, defaults applied at render time):
    title           : str   — document title; supports \\n for multi-line
    department      : str   — department or org unit
    status          : str   — "Draft" | "In Review" | "Accepted" | "Rejected" | "Retired"
                              | "Proposed" | "Informational"
                              Only "Draft" produces a DRAFT watermark in DOCX output.
                              "Informational" is for meeting notes and informal captures
                              with no review cycle.
    version         : str   — e.g. "1.0"
    date            : str   — e.g. "2026-03-13"
    author          : str   — primary author name
    owner           : str   — document owner name
    audience        : list  — list of audience strings
    related_docs    : list  — list of related document references
    revision_history: list  — list of revision dicts (version/date/author/description)
    org             : dict  — optional org identity overrides for the cover footer
        name  : str — organisation name   (default: constants.ORG_NAME)
        dept  : str — department / unit   (default: constants.ORG_DEPT)
        addr1 : str — street address      (default: constants.ORG_ADDR1)
        addr2 : str — city / state / zip  (default: constants.ORG_ADDR2)
        url   : str — website URL         (default: constants.ORG_URL)

    Example org override (omit to use the compiled-in defaults):
        org:
          name:  "Acme Corporation"
          dept:  "Platform Engineering"
          addr1: "123 Main Street"
          addr2: "Springfield, IL"
          url:   "www.acme.example.com"
"""

import re
import yaml


class HeadingNumberer:
    """
    Tracks hierarchical section counters and formats numbered heading text.

    Counters reset on promotion: advancing an H1 resets H2 and H3;
    advancing an H2 resets H3.

    Output format:
        H1  ->  "1 \u2014 Title"
        H2  ->  "1.1 \u2014 Title"
        H3  ->  "1.1.1 \u2014 Title"

    Used by both extract_headings() (pre-scan for static TOC) and
    HtmlToDocx (body rendering), so numbering is identical in both places.
    """

    def __init__(self):
        self._counters = [0, 0, 0]   # index 0 = H1, 1 = H2, 2 = H3

    def format(self, level: int, text: str) -> str:
        """Advance the counter for `level` and return the numbered heading string."""
        idx = level - 1
        self._counters[idx] += 1
        # Reset all deeper counters
        for i in range(idx + 1, 3):
            self._counters[i] = 0

        if level == 1:
            prefix = f"{self._counters[0]}"
        elif level == 2:
            prefix = f"{self._counters[0]}.{self._counters[1]}"
        else:
            prefix = f"{self._counters[0]}.{self._counters[1]}.{self._counters[2]}"

        return f"{prefix} \u2014 {text}"


def parse_front_matter(raw_text: str) -> tuple[dict, str]:
    """
    Split raw file text into (metadata dict, body markdown string).

    If the file begins with a YAML front matter block (--- delimited),
    parse it and return (meta, body). Otherwise return ({}, full_text).

    Args:
        raw_text: full contents of the .md file as a string

    Returns:
        (meta, body_md) where meta is a dict and body_md is the markdown
        content after the front matter block.
    """
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw_text, re.DOTALL)
    if fm_match:
        meta    = yaml.safe_load(fm_match.group(1)) or {}
        body_md = raw_text[fm_match.end():]
        return meta, body_md
    return {}, raw_text


def extract_headings(body_md: str) -> list[tuple]:
    """
    Pre-scan markdown source for headings (h1-h3) to populate the static
    TOC fallback entries before the document is fully rendered.

    Returns a list of (level: int, numbered_text: str, page: None) tuples.
    Heading text is pre-numbered using HeadingNumberer so it matches what
    HtmlToDocx will write into the document body.
    page is always None here; Word fills in actual page numbers on open.

    Args:
        body_md: the markdown body (after front matter has been removed)
    """
    heading_scan = re.findall(r'^(#{1,3})\s+(.+)$', body_md, re.MULTILINE)
    numberer = HeadingNumberer()
    return [(len(h), numberer.format(len(h), t.strip()), None) for h, t in heading_scan]
