"""Hyperlink emission and URL normalization.

Two things are under test: that normalize_href makes the right call about
what can become a live link, and that a rendered DOCX actually carries
hyperlink relationships. The second matters because link styling alone
(blue + underline) looks identical in Word whether or not the text is
clickable - which is how the builder shipped styled-but-inert links.
"""
import re
import zipfile

import pytest

from docx_builder.markdown_parser import normalize_href


class TestNormalizeHref:
    @pytest.mark.parametrize("url", [
        "https://example.com/docs/guide",
        "http://example.com",
        "mailto:someone@example.com",
        "ftp://files.example.com/pub",
    ])
    def test_absolute_schemes_pass_through(self, url):
        assert normalize_href(url) == url

    @pytest.mark.parametrize("ref", [
        "../patterns/foo.md",          # relative sibling
        "docs/guide.md",               # relative child
        "./thing.md",
        "#overview",                   # bare fragment
        "",
        None,
    ])
    def test_non_absolute_refs_are_not_linked(self, ref):
        assert normalize_href(ref) is None

    @pytest.mark.parametrize("scheme", [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<script>",
    ])
    def test_unsafe_schemes_are_not_linked(self, scheme):
        assert normalize_href(scheme) is None

    def test_existing_percent_escapes_are_preserved(self):
        """The double-encoding trap: %20 must not become %2520."""
        url = "https://example.com/sites/Shared%20Documents/Forms/AllItems.aspx"
        assert normalize_href(url) == url
        assert "%2520" not in normalize_href(url)

    def test_raw_spaces_are_encoded(self):
        out = normalize_href("https://example.com/Shared Documents/file.docx")
        assert out == "https://example.com/Shared%20Documents/file.docx"

    def test_query_and_fragment_survive(self):
        url = "https://example.com/s?a=1&b=2#frag"
        assert normalize_href(url) == url

    def test_non_ascii_is_percent_encoded(self):
        out = normalize_href("https://example.com/café")
        assert out == "https://example.com/caf%C3%A9"

    def test_surrounding_whitespace_is_stripped(self):
        assert normalize_href("  https://example.com  ") == "https://example.com"


def _hyperlink_targets(docx_path):
    """External hyperlink relationship targets in a .docx.

    Word stores link targets in document.xml.rels, not in the body XML, so
    this reads the relationships directly rather than trusting run styling.
    """
    targets = []
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if not name.endswith(".rels"):
                continue
            for m in re.finditer(
                rb'Type="[^"]*hyperlink"[^>]*Target="([^"]+)"', z.read(name)
            ):
                targets.append(m.group(1).decode())
    return targets


class TestRenderedDocx:
    def test_absolute_link_becomes_a_relationship(self, tmp_path):
        from docx_builder.builder import build_document

        md = tmp_path / "doc.md"
        md.write_text(
            "---\n"
            "title: Link Test\n"
            "doc_type: reference\n"
            "status: Draft\n"
            "version: '0.1'\n"
            "author: Test\n"
            "date: 2026-08-03\n"
            "---\n\n"
            "# Heading\n\n"
            "An [external reference](https://example.com/spec) and a\n"
            "[relative one](../other/doc.md) in one paragraph.\n",
            encoding="utf-8",
        )
        out = tmp_path / "doc.docx"
        build_document(str(md), output_path=str(out))

        targets = _hyperlink_targets(out)
        assert "https://example.com/spec" in targets, \
            "absolute link did not produce a hyperlink relationship"
        assert not any("other/doc.md" in t for t in targets), \
            "relative link should not become a relationship in phase 1"

    def test_link_in_table_cell(self, tmp_path):
        """Table cells take a separate code path from body text.

        Before this was wired, a linked cell rendered the raw markdown
        source - '[label](https://...)' - visibly, to the reader.
        """
        from docx import Document
        from docx_builder.builder import build_document

        md = tmp_path / "tbl.md"
        md.write_text(
            "---\n"
            "title: Table Link Test\n"
            "doc_type: reference\n"
            "status: Draft\n"
            "version: '0.1'\n"
            "author: Test\n"
            "date: 2026-08-03\n"
            "---\n\n"
            "# Heading\n\n"
            "| Item | Reference |\n"
            "|---|---|\n"
            "| Alpha | [Vendor KCS 12345](https://example.com/solutions/12345) |\n"
            "| Beta  | [Sibling doc](../other/doc.md) |\n",
            encoding="utf-8",
        )
        out = tmp_path / "tbl.docx"
        build_document(str(md), output_path=str(out))

        assert "https://example.com/solutions/12345" in _hyperlink_targets(out)

        cells = [c.text for t in Document(out).tables for r in t.rows for c in r.cells]
        joined = " | ".join(cells)
        assert "Vendor KCS 12345" in joined, "link label missing from the table"
        assert "](" not in joined, f"raw markdown leaked into a cell: {joined}"
        assert "Sibling doc" in joined, "relative link label should still render"
