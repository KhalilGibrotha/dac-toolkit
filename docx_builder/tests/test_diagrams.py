import tempfile
import unittest
from pathlib import Path
from unittest import mock

from docx_builder import diagrams


class _FakeResponse:
    def __init__(self, data: bytes, content_type: str = "image/png"):
        self._data = data
        self.headers = {"Content-Type": content_type}

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestMermaidRenderScale(unittest.TestCase):
    def test_get_mermaid_render_scale_defaults(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            self.assertEqual(diagrams._get_mermaid_render_scale(), 2.0)

    def test_get_mermaid_render_scale_prefers_generic_setting(self):
        with mock.patch.dict(
            "os.environ",
            {
                "DOCX_BUILDER_DIAGRAM_RENDER_SCALE": "3",
                "DOCX_BUILDER_MERMAID_RENDER_SCALE": "2",
            },
            clear=False,
        ):
            self.assertEqual(diagrams._get_mermaid_render_scale(), 3.0)

    def test_get_mermaid_render_scale_clamps_and_falls_back(self):
        with mock.patch.dict(
            "os.environ",
            {"DOCX_BUILDER_MERMAID_RENDER_SCALE": "not-a-number"},
            clear=False,
        ):
            self.assertEqual(diagrams._get_mermaid_render_scale(), 2.0)

        with mock.patch.dict(
            "os.environ",
            {"DOCX_BUILDER_MERMAID_RENDER_SCALE": "0.5"},
            clear=False,
        ):
            self.assertEqual(diagrams._get_mermaid_render_scale(), 1.0)

        with mock.patch.dict(
            "os.environ",
            {"DOCX_BUILDER_MERMAID_RENDER_SCALE": "5"},
            clear=False,
        ):
            self.assertEqual(diagrams._get_mermaid_render_scale(), 4.0)

    def test_render_via_kroki_passes_scale_query(self):
        seen = {}

        def fake_urlopen(req, timeout=0):
            seen["url"] = req.full_url
            return _FakeResponse(b"png-bytes")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = str(Path(tmp_dir) / "diagram.png")
            with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                ok = diagrams._render_via_kroki(
                    "flowchart LR\nA-->B",
                    output_path,
                    scale=3.0,
                )

        self.assertTrue(ok)
        self.assertIn("scale=3", seen["url"])

    def test_render_via_mermaid_ink_passes_scale_query(self):
        seen = {}

        def fake_urlopen(req, timeout=0):
            seen["url"] = req.full_url
            return _FakeResponse(b"png-bytes")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = str(Path(tmp_dir) / "diagram.png")
            with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                ok = diagrams._render_via_mermaid_ink(
                    "flowchart LR\nA-->B",
                    output_path,
                    scale=2.5,
                )

        self.assertTrue(ok)
        self.assertIn("scale=2.5", seen["url"])

    def test_render_via_mmdc_passes_scale_flag(self):
        def fake_run(cmd, capture_output, text, timeout):
            Path(output_path).write_bytes(b"png-bytes")
            self.assertIn("-s", cmd)
            self.assertIn("3", cmd)
            return mock.Mock(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = str(Path(tmp_dir) / "diagram.png")
            with mock.patch("subprocess.run", side_effect=fake_run):
                ok = diagrams._render_via_mmdc(
                    "flowchart LR\nA-->B",
                    output_path,
                    scale=3.0,
                )

        self.assertTrue(ok)
