#!/usr/bin/env python3
"""Manifest-driven DOCX render wrapper for content repositories."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import yaml

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_NAME = Path("manifests") / "render-manifest.yaml"
DEFAULT_KROKI_URL = "http://127.0.0.1:8000"
SUPPORTED_DIAGRAM_TYPES = {
    "mermaid": "mermaid",
    "plantuml": "plantuml",
    "c4plantuml": "c4plantuml",
    "graphviz": "graphviz",
    "dot": "graphviz",
    "d2": "d2",
    "pikchr": "pikchr",
    "erd": "erd",
    "svgbob": "svgbob",
    "nomnoml": "nomnoml",
    "structurizr": "structurizr",
    "ditaa": "ditaa",
    "seqdiag": "seqdiag",
    "blockdiag": "blockdiag",
    "nwdiag": "nwdiag",
    "packetdiag": "packetdiag",
    "rackdiag": "rackdiag",
    "umlet": "umlet",
    "vega": "vega",
    "vegalite": "vegalite",
    "wavedrom": "wavedrom",
    "wireviz": "wireviz",
    "dbml": "dbml",
    "bpmn": "bpmn",
    "excalidraw": "excalidraw",
    "bytefield": "bytefield",
    "goat": "goat",
}
FENCE_RE = re.compile(r"```([A-Za-z0-9_-]+)[^\n]*\n(.*?)\n```", re.DOTALL)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RENDER_SCALE_DEFAULT = 2.0
RENDER_SCALE_MIN = 1.0
RENDER_SCALE_MAX = 4.0


@dataclass(frozen=True)
class DocumentSpec:
    id: str
    input: Path
    output: Path
    rewritten_markdown: Path
    assets_dir: Path
    org: Path | None
    logo: Path | None


class ManifestError(RuntimeError):
    """Raised when the manifest is invalid."""


class DiagramRenderError(RuntimeError):
    """Raised when Kroki rejects a diagram block."""


def resolve_path(base_dir: Path, raw_value: str | None) -> Path | None:
    if raw_value in (None, ""):
        return None
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return base_dir / path


def get_render_scale() -> float:
    raw = ""
    for name in ("DOCX_BUILDER_DIAGRAM_RENDER_SCALE", "KROKI_RENDER_SCALE"):
        value = os.environ.get(name)
        if value is not None and value.strip():
            raw = value.strip()
            break
    if not raw:
        return RENDER_SCALE_DEFAULT
    try:
        scale = float(raw)
    except ValueError:
        return RENDER_SCALE_DEFAULT
    return min(max(scale, RENDER_SCALE_MIN), RENDER_SCALE_MAX)


def format_scale(scale: float) -> str:
    if float(scale).is_integer():
        return str(int(scale))
    return str(scale)


def build_render_endpoint(kroki_url: str, diagram_type: str, *, scale: float) -> str:
    params = urllib.parse.urlencode({"scale": format_scale(scale)})
    return f"{kroki_url.rstrip('/')}/{diagram_type}/png?{params}"


def ensure_png_bytes(payload: bytes, *, diagram_type: str, endpoint: str) -> bytes:
    if payload.startswith(PNG_SIGNATURE):
        return payload
    preview = payload[:80].decode("utf-8", errors="replace").replace("\n", "\\n")
    raise DiagramRenderError(
        f"Kroki returned a non-PNG payload for {diagram_type} at {endpoint}. "
        f"Leading bytes: {preview}"
    )


def render_diagram_png(diagram_type: str, diagram_source: str, kroki_url: str) -> bytes:
    endpoint = build_render_endpoint(kroki_url, diagram_type, scale=get_render_scale())
    request = urllib.request.Request(
        endpoint,
        data=diagram_source.encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return ensure_png_bytes(
                response.read(),
                diagram_type=diagram_type,
                endpoint=endpoint,
            )
    except urllib.error.HTTPError as exc:
        preview = diagram_source.strip().splitlines()
        preview_text = preview[0] if preview else "<empty>"
        raise DiagramRenderError(
            f"Kroki rejected {diagram_type} diagram at {endpoint}: "
            f"HTTP {exc.code} {exc.reason}. First line: {preview_text}"
        ) from exc


def rewrite_markdown(
    markdown_text: str,
    *,
    output_markdown_path: Path,
    assets_dir: Path,
    kroki_url: str,
) -> tuple[str, int]:
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    rendered = 0
    rewritten_parts: list[str] = []
    last_index = 0

    for match in FENCE_RE.finditer(markdown_text):
        language = match.group(1).strip().lower()
        kroki_type = SUPPORTED_DIAGRAM_TYPES.get(language)
        if not kroki_type:
            continue

        rendered += 1
        rewritten_parts.append(markdown_text[last_index:match.start()])

        asset_name = f"{kroki_type}-{rendered:03d}.png"
        asset_path = assets_dir / asset_name
        asset_path.write_bytes(render_diagram_png(kroki_type, match.group(2).strip(), kroki_url))

        relative_asset_path = os.path.relpath(asset_path, output_markdown_path.parent).replace(os.sep, "/")
        human_label = language.upper() if language in {"d2", "dbml", "bpmn"} else language.capitalize()
        rewritten_parts.append(f"![Generated {human_label} diagram {rendered}]({relative_asset_path})")
        last_index = match.end()

    rewritten_parts.append(markdown_text[last_index:])
    return "".join(rewritten_parts), rendered


def derive_output_path(content_root: Path, input_path: Path) -> Path:
    relative = input_path.relative_to(content_root).with_suffix(".docx")
    return content_root / "exports" / relative


def derive_rewritten_path(content_root: Path, input_path: Path) -> Path:
    relative = input_path.relative_to(content_root)
    return content_root / "build" / "rewritten" / relative


def derive_assets_dir(content_root: Path, doc_id: str) -> Path:
    return content_root / "build" / "diagrams" / doc_id


def load_manifest(manifest_path: Path, *, content_root: Path) -> list[DocumentSpec]:
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    documents = data.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ManifestError(f"Manifest {manifest_path} does not define a non-empty 'documents' list.")

    default_org = content_root / "vars" / "org.yaml"
    default_logo = content_root / "assets" / "logo" / "logo.png"

    specs: list[DocumentSpec] = []
    for index, entry in enumerate(documents, start=1):
        if not isinstance(entry, dict):
            raise ManifestError(f"Manifest entry {index} in {manifest_path} is not a mapping.")
        if not entry.get("id") or not entry.get("input"):
            raise ManifestError(f"Manifest entry {index} in {manifest_path} must define 'id' and 'input'.")

        doc_id = str(entry["id"])
        input_path = resolve_path(content_root, str(entry["input"]))
        assert input_path is not None

        output_path = resolve_path(content_root, entry.get("output")) or derive_output_path(content_root, input_path)
        rewritten_markdown = resolve_path(content_root, entry.get("rewritten_markdown")) or derive_rewritten_path(content_root, input_path)
        assets_dir = resolve_path(content_root, entry.get("assets_dir")) or derive_assets_dir(content_root, doc_id)

        org_path = resolve_path(content_root, entry.get("org"))
        if org_path is None and default_org.is_file():
            org_path = default_org

        logo_path = resolve_path(content_root, entry.get("logo"))
        if logo_path is None and default_logo.is_file():
            logo_path = default_logo

        specs.append(
            DocumentSpec(
                id=doc_id,
                input=input_path,
                output=output_path,
                rewritten_markdown=rewritten_markdown,
                assets_dir=assets_dir,
                org=org_path,
                logo=logo_path,
            )
        )
    return specs


def select_documents(specs: list[DocumentSpec], document_id: str | None) -> list[DocumentSpec]:
    if document_id is None:
        return specs
    selected = [spec for spec in specs if spec.id == document_id]
    if not selected:
        available = ", ".join(spec.id for spec in specs)
        raise ManifestError(f"Document id '{document_id}' not found. Available ids: {available}")
    return selected


def validate_document(spec: DocumentSpec) -> list[str]:
    problems: list[str] = []
    if not spec.input.is_file():
        problems.append(f"missing input: {spec.input}")
    if spec.org is not None and not spec.org.is_file():
        problems.append(f"missing org: {spec.org}")
    if spec.logo is not None and not spec.logo.is_file():
        problems.append(f"missing logo: {spec.logo}")
    return problems


def ensure_docx_builder(venv_dir: Path, *, python_bin: str) -> Path:
    if os.name == "nt":
        venv_python = venv_dir / "Scripts" / "python.exe"
        docx_build = venv_dir / "Scripts" / "docx-build.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        docx_build = venv_dir / "bin" / "docx-build"

    if not venv_python.exists():
        subprocess.run([python_bin, "-m", "venv", str(venv_dir)], check=True)

    if not docx_build.exists():
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--no-cache-dir", "-e", str(TOOLKIT_ROOT / "docx_builder")],
            check=True,
        )

    return docx_build


def render_document(spec: DocumentSpec, *, kroki_url: str, docx_build: Path) -> None:
    spec.output.parent.mkdir(parents=True, exist_ok=True)
    spec.rewritten_markdown.parent.mkdir(parents=True, exist_ok=True)
    spec.assets_dir.mkdir(parents=True, exist_ok=True)

    source_text = spec.input.read_text(encoding="utf-8")
    rewritten_text, rendered = rewrite_markdown(
        source_text,
        output_markdown_path=spec.rewritten_markdown,
        assets_dir=spec.assets_dir,
        kroki_url=kroki_url,
    )
    spec.rewritten_markdown.write_text(rewritten_text, encoding="utf-8")

    cmd = [str(docx_build), str(spec.rewritten_markdown), "--output", str(spec.output)]
    if spec.org is not None:
        cmd.extend(["--org", str(spec.org)])
    if spec.logo is not None:
        cmd.extend(["--logo", str(spec.logo)])
    subprocess.run(cmd, check=True)
    print(f"Saved: {spec.output}")
    print(f"OK render: {spec.id} ({rendered} Kroki diagram(s))")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manifest-driven DOCX render wrapper for content repositories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--content-root", type=Path, default=Path.cwd())
        subparser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_NAME)
        subparser.add_argument("--document-id", default=None)

    list_parser = subparsers.add_parser("list", help="List manifest-managed documents.")
    add_common_arguments(list_parser)

    validate_parser = subparsers.add_parser("validate", help="Validate manifest-managed document paths.")
    add_common_arguments(validate_parser)

    render_parser = subparsers.add_parser("render", help="Render manifest-managed documents.")
    add_common_arguments(render_parser)
    render_parser.add_argument("--kroki-url", default=DEFAULT_KROKI_URL)
    render_parser.add_argument("--python-bin", default=sys.executable)
    render_parser.add_argument("--venv-dir", type=Path, default=None)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content_root = args.content_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest.is_absolute() else (content_root / args.manifest).resolve()
    specs = select_documents(load_manifest(manifest_path, content_root=content_root), args.document_id)

    if args.command == "list":
        for spec in specs:
            print(f"{spec.id}: {spec.input} -> {spec.output}")
        return 0

    if args.command == "validate":
        failures = 0
        for spec in specs:
            problems = validate_document(spec)
            if problems:
                failures += 1
                print(f"FAIL {spec.id}")
                for problem in problems:
                    print(f"  - {problem}")
            else:
                print(f"OK   {spec.id}")
        print(f"\nValidated {len(specs)} document(s). Failures: {failures}.")
        return 1 if failures else 0

    if args.command == "render":
        failures = 0
        venv_dir = args.venv_dir.resolve() if args.venv_dir else content_root / ".venv-docx-render"
        docx_build = ensure_docx_builder(venv_dir, python_bin=args.python_bin)
        for spec in specs:
            print(f"\n=== {spec.id} ===")
            print(f"input:  {spec.input}")
            print(f"output: {spec.output}")
            problems = validate_document(spec)
            if problems:
                failures += 1
                print(f"FAIL validate: {spec.id}")
                for problem in problems:
                    print(f"  - {problem}")
                continue
            try:
                render_document(spec, kroki_url=args.kroki_url, docx_build=docx_build)
            except (subprocess.CalledProcessError, DiagramRenderError) as exc:
                failures += 1
                print(f"FAIL render: {spec.id}")
                print(exc)
        print(f"\nCompleted {len(specs)} document(s). Failures: {failures}.")
        return 1 if failures else 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
