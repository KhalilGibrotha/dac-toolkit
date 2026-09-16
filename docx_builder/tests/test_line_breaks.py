"""Soft breaks reflow; hard breaks and code blocks keep their lines.

A newline inside a Markdown paragraph is a soft break: the author wrapped the
source at some column and expects the rendered text to fill the page. mistune
keeps that newline as a literal "\\n" in the text node, and python-docx turns
a "\\n" inside a run into a <w:br/>. Unhandled, every wrapped source line
became a hard line break in Word, so body text stopped at the wrap column and
documents ran long. The fix collapses soft breaks to a space; this file pins
that down and guards the two places a line break is still meant to survive.
"""
import re
import zipfile

from docx_builder.builder import build_document

FRONT_MATTER = (
    "---\n"
    "title: Line Break Test\n"
    "doc_type: reference\n"
    "status: Draft\n"
    "version: '0.1'\n"
    "author: Test\n"
    "date: 2026-09-16\n"
    "---\n\n"
)


def _body_paragraphs(docx_path):
    """Body paragraphs of document.xml, tables stripped, as raw XML strings."""
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    body = re.search(r"<w:body>(.*)</w:body>", xml, re.S).group(1)
    body = re.sub(r"<w:tbl>.*?</w:tbl>", "", body, flags=re.S)
    return re.findall(r"<w:p[ >].*?</w:p>", body, re.S)


def _paragraph_with(paragraphs, needle):
    hits = [p for p in paragraphs if needle in p]
    assert len(hits) == 1, f"expected one paragraph containing {needle!r}"
    return hits[0]


def _text(paragraph_xml):
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", paragraph_xml))


def _render(tmp_path, markdown):
    md = tmp_path / "doc.md"
    md.write_text(FRONT_MATTER + markdown, encoding="utf-8")
    out = tmp_path / "doc.docx"
    build_document(str(md), output_path=str(out))
    return _body_paragraphs(out)


def test_wrapped_paragraph_reflows(tmp_path):
    paras = _render(
        tmp_path,
        "# Heading\n\n"
        "This paragraph is wrapped at a narrow column in the source\n"
        "so that it spans three lines, and the rendered text must\n"
        "fill the page instead of ending where each line ends.\n",
    )
    p = _paragraph_with(paras, "wrapped at a narrow column")
    assert "<w:br/>" not in p, "soft line break rendered as a hard break"
    assert _text(p) == (
        "This paragraph is wrapped at a narrow column in the source "
        "so that it spans three lines, and the rendered text must "
        "fill the page instead of ending where each line ends."
    )


def test_wrapped_list_item_reflows(tmp_path):
    paras = _render(
        tmp_path,
        "# Heading\n\n"
        "- A list item that is wrapped in the source across\n"
        "  two lines, with the continuation indented.\n"
        "- A second item.\n",
    )
    p = _paragraph_with(paras, "wrapped in the source across")
    assert "<w:br/>" not in p
    assert "across two lines" in _text(p)


def test_wrap_around_inline_markup_keeps_the_space(tmp_path):
    """The newline sits between a word and an inline element; collapsing it
    must leave one space, not glue the words together."""
    paras = _render(
        tmp_path,
        "# Heading\n\n"
        "Some words before\n"
        "*an emphasized phrase* and after.\n",
    )
    p = _paragraph_with(paras, "Some words before")
    assert "<w:br/>" not in p
    assert _text(p) == "Some words before an emphasized phrase and after."


def test_hard_break_survives(tmp_path):
    """A trailing backslash is an intentional hard break and must stay."""
    paras = _render(
        tmp_path,
        "# Heading\n\n"
        "First line of the stanza\\\n"
        "Second line of the stanza\n",
    )
    p = _paragraph_with(paras, "First line of the stanza")
    assert p.count("<w:br/>") == 1
    assert "Second line of the stanza" in _text(p)


def test_code_block_keeps_its_lines(tmp_path):
    paras = _render(
        tmp_path,
        "# Heading\n\n"
        "```\n"
        "line one\n"
        "line two\n"
        "```\n",
    )
    p = _paragraph_with(paras, "line one")
    assert "<w:br/>" in p, "code block lines collapsed onto one line"
    assert "line two" in _text(p)
