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


class TestDiagramFenceExtraction(unittest.TestCase):
    def test_mermaid_fence_extracted_with_caption(self):
        md = (
            'Intro text.\n\n'
            '```mermaid caption="Figure 1"\n'
            'flowchart LR\n'
            '    A --> B\n'
            '```\n\n'
            'Outro text.\n'
        )
        processed, data = diagrams.extract_diagram_fences(md)
        self.assertIn("__MERMAID_0__", processed)
        self.assertNotIn("```mermaid", processed)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["caption"], "Figure 1")
        self.assertEqual(data[0]["language"], "mermaid")
        self.assertEqual(data[0]["kroki_type"], "mermaid")
        self.assertIn("A --> B", data[0]["source"])

    def test_kroki_language_fences_extracted(self):
        md = (
            "```plantuml\n@startuml\nA -> B\n@enduml\n```\n\n"
            "```graphviz\ndigraph G { a -> b }\n```\n\n"
            "```dot\ndigraph G { c -> d }\n```\n"
        )
        processed, data = diagrams.extract_diagram_fences(md)
        self.assertEqual(len(data), 3)
        self.assertEqual(
            [d["language"] for d in data], ["plantuml", "graphviz", "dot"]
        )
        # ```dot is an alias for the graphviz Kroki type
        self.assertEqual(
            [d["kroki_type"] for d in data], ["plantuml", "graphviz", "graphviz"]
        )
        for idx in range(3):
            self.assertIn(f"__MERMAID_{idx}__", processed)

    def test_non_diagram_fences_untouched(self):
        # ```bash / ```yaml / ```python are ordinary code blocks and must be
        # returned byte-for-byte — the highest-risk regression for this corpus.
        md = (
            "```bash\necho hello\n```\n\n"
            "```yaml\nkey: value\n```\n\n"
            "```python\nprint('hi')\n```\n\n"
            "```text\nplain\n```\n"
        )
        processed, data = diagrams.extract_diagram_fences(md)
        self.assertEqual(processed, md)
        self.assertEqual(data, [])

    def test_mixed_fences_only_extract_diagrams(self):
        md = (
            "```bash\necho one\n```\n\n"
            "```mermaid\nflowchart LR\n    A --> B\n```\n\n"
            "```yaml\nkey: value\n```\n"
        )
        processed, data = diagrams.extract_diagram_fences(md)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["language"], "mermaid")
        self.assertIn("```bash\necho one\n```", processed)
        self.assertIn("```yaml\nkey: value\n```", processed)
        self.assertNotIn("```mermaid", processed)

    def test_plain_fence_untouched(self):
        md = "```\nno info string\n```\n"
        processed, data = diagrams.extract_diagram_fences(md)
        self.assertEqual(processed, md)
        self.assertEqual(data, [])

    def test_extract_mermaid_fences_alias(self):
        # Backwards-compatible alias must keep working for older callers.
        self.assertIs(diagrams.extract_mermaid_fences, diagrams.extract_diagram_fences)


class TestKrokiBackend(unittest.TestCase):
    def test_kroki_posts_source_to_typed_endpoint(self):
        seen = {}

        def fake_urlopen(req, timeout=0):
            seen["url"] = req.full_url
            seen["method"] = req.get_method()
            seen["data"] = req.data
            return _FakeResponse(b"png-bytes")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = str(Path(tmp_dir) / "diagram.png")
            with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                ok = diagrams._render_via_kroki(
                    "digraph G { a -> b }",
                    output_path,
                    diagram_type="graphviz",
                )

        self.assertTrue(ok)
        self.assertTrue(seen["url"].startswith("https://kroki.io/graphviz/png"))
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["data"], b"digraph G { a -> b }")

    def test_kroki_url_env_override(self):
        seen = {}

        def fake_urlopen(req, timeout=0):
            seen["url"] = req.full_url
            return _FakeResponse(b"png-bytes")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = str(Path(tmp_dir) / "diagram.png")
            with mock.patch.dict(
                "os.environ",
                {"DOCX_BUILDER_KROKI_URL": "http://127.0.0.1:8000/"},
                clear=False,
            ):
                with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
                    ok = diagrams._render_via_kroki(
                        "flowchart LR\nA-->B",
                        output_path,
                    )

        self.assertTrue(ok)
        self.assertTrue(seen["url"].startswith("http://127.0.0.1:8000/mermaid/png"))

    def test_render_diagram_falls_back_to_placeholder_on_unreachable_kroki(self):
        # A bogus Kroki host must never crash the build — the diagram degrades
        # to the styled placeholder block containing the raw source.
        import docx

        doc = docx.Document()
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.dict(
                "os.environ",
                {"DOCX_BUILDER_KROKI_URL": "http://nonexistent.invalid"},
                clear=False,
            ):
                diagrams.render_diagram(
                    doc,
                    {
                        "source": "digraph G { a -> b }",
                        "caption": None,
                        "language": "graphviz",
                        "kroki_type": "graphviz",
                    },
                    tmp_dir,
                )

        text = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("digraph G { a -> b }", text)
        self.assertIn("could not be rendered", text)


if __name__ == "__main__":
    unittest.main()
