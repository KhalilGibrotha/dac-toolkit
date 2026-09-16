"""
docx_builder — Markdown + YAML front matter → styled DOCX

Public surface:
    build_document(md_path, logo_path=None, output_path=None) -> str
"""

# One version source: the installed distribution's metadata, which comes from
# pyproject.toml. A literal here drifted (it read 1.0.0 through two releases).
from importlib.metadata import PackageNotFoundError, version as _dist_version

try:
    __version__ = _dist_version("docx-builder")
except PackageNotFoundError:            # source tree on sys.path, not installed
    __version__ = "0.0.0+uninstalled"

from .builder import build_document

__all__ = ["build_document"]
