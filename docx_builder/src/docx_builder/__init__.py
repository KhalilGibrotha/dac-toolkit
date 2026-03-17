"""
docx_builder — Markdown + YAML front matter → styled DOCX

Public surface:
    build_document(md_path, logo_path=None, output_path=None) -> str
"""

__version__ = "1.0.0"

from .builder import build_document

__all__ = ["build_document"]
