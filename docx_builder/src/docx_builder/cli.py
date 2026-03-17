"""
cli.py — Command-line entry point for docx_builder.

Usage:
    python -m docx_builder input.md [--logo path/to/logo.png] [--output path/to/output.docx]

    # Or if installed via pip:
    docx-build input.md --logo assets/logo/logo.png --output exports/output.docx
"""

import argparse
import os
import sys

import yaml

from .builder import build_document


def _load_org_yaml(path: str) -> dict:
    """Load org identity overrides from a YAML file.

    Expected format:
        org:
          name: "Acme Corp"
          dept: "Enterprise Architecture"
          addr1: "123 Main Street"
          addr2: "Anytown, USA"
          url: "www.example.com"

    Returns the nested dict under the 'org' key, or the top-level dict
    if no 'org' key is present (flat format supported).
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('org', data)


def main():
    parser = argparse.ArgumentParser(
        prog="docx-build",
        description="Convert Markdown + YAML front matter to a styled DOCX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  docx-build doc.md
  docx-build doc.md --logo assets/logo/logo.png
  docx-build doc.md --org vars/org.yaml --output exports/doc.docx

YAML front matter keys:
  title           : str   — document title (use \\\\n for line breaks)
  department      : str   — department / org unit
  status          : str   — "Draft" or "Final"
  version         : str   — e.g. "1.0"
  date            : str   — e.g. "2026-03-13"
  author          : str   — primary author
  owner           : str   — document owner
  audience        : list  — intended audience
  related_docs    : list  — optional related document references
  revision_history: list  — [{version, date, author, description}, ...]
        """,
    )
    parser.add_argument(
        'input',
        help="Input .md file path",
    )
    parser.add_argument(
        '--logo',
        default=None,
        metavar='PATH',
        help="Path to logo image (PNG or JPG). Falls back to org name text if not provided.",
    )
    parser.add_argument(
        '--org',
        default=None,
        metavar='PATH',
        help="Path to org.yaml with org identity overrides (name, dept, addr1, addr2, url). "
             "Overrides both constants.py defaults and front matter org: block.",
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        metavar='PATH',
        help="Output .docx path. Defaults to input filename with .docx extension.",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.logo and not os.path.isfile(args.logo):
        print(f"Warning: logo file not found: {args.logo} — using text fallback", file=sys.stderr)

    org_overrides = None
    if args.org:
        if not os.path.isfile(args.org):
            print(f"Error: org file not found: {args.org}", file=sys.stderr)
            sys.exit(1)
        org_overrides = _load_org_yaml(args.org)

    build_document(
        args.input,
        logo_path=args.logo,
        output_path=args.output,
        org_overrides=org_overrides,
    )


if __name__ == '__main__':
    main()
