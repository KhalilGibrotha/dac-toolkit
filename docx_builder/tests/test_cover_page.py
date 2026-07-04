import base64
import tempfile
import unittest
import zipfile
from pathlib import Path

from docx_builder.builder import build_document


_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAusB9Wn0w6sAAAAASUVORK5CYII="
)


class CoverPageTests(unittest.TestCase):
    def test_build_document_embeds_logo_image(self):
        markdown = """\
---
title: "Logo Test"
department: "Enterprise Architecture"
status: "Draft"
---

# Logo Test

Body paragraph.
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            md_path = tmp_path / "logo-test.md"
            logo_path = tmp_path / "logo.png"
            output_path = tmp_path / "logo-test.docx"

            md_path.write_text(markdown, encoding="utf-8")
            logo_path.write_bytes(base64.b64decode(_PNG_BASE64))

            build_document(
                str(md_path),
                logo_path=str(logo_path),
                output_path=str(output_path),
                org_overrides={"name": "Acme", "dept": "Enterprise Architecture"},
            )

            with zipfile.ZipFile(output_path) as archive:
                media_entries = {
                    entry.filename
                    for entry in archive.infolist()
                    if entry.filename.startswith("word/media/")
                }

            self.assertIn("word/media/image1.png", media_entries)


if __name__ == "__main__":
    unittest.main()
