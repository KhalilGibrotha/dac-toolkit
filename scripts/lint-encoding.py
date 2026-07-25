#!/usr/bin/env python3
"""
Check Markdown files for encoding artifacts: mojibake, smart quotes, and
non-breaking spaces.

Mojibake is text corruption from a UTF-8/Windows-1252 round-trip (for example
an em dash "—" becoming "â€"", or an arrow "→" becoming "â†'"). Smart quotes
and non-breaking spaces are disallowed by the repo style guide.

This is a self-contained companion to the fuller `lint-markdown.sh` in
claude-repo-tools, so CI can run an encoding gate without the sibling repo.

Fenced code blocks are skipped (front matter is scanned — a corrupted title or
related_docs value is a real artifact). Exit codes: 0 = clean (or --no-exit),
1 = issues found.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

# Characters a CP1252 byte 0x80-0xFF decodes to. When any of the mojibake lead
# bytes (Ã Â â Å Æ, themselves 0xC3/0xC2/0xE2/0xC5/0xC6 -> these glyphs) is
# followed by one of these continuation glyphs, it is mojibake — this covers
# single- and multiply-encoded forms, including arrows (â†') and math (â‰¥).
_CONT = bytes(range(0x80, 0x100)).decode("cp1252", errors="ignore")
_LEADS = "ÃÂâÅÆ"
MOJIBAKE = re.compile("[" + re.escape(_LEADS) + "][" + re.escape(_CONT) + "]")

SMART_QUOTES = re.compile("[“”‘’]")
NBSP = re.compile(" ")

# U+FFFD appears when errors="replace" decodes invalid UTF-8. Flagging it
# means invalid bytes are reported as an issue, not silently masked.
INVALID_UTF8 = re.compile("�")

CHECKS = {
    "mojibake": MOJIBAKE,
    "smart-quotes": SMART_QUOTES,
    "non-breaking-space": NBSP,
    "invalid-utf8": INVALID_UTF8,
}

SKIP_NAMES = {"README.md", "CONTRIBUTING.md", "CHANGELOG.md", "CLAUDE.md"}
SKIP_DIRS = {".git", ".vale", ".github", "node_modules", "exports", "diagrams"}


def iter_md(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith((".md", ".qmd")) and fn not in SKIP_NAMES:
                yield os.path.join(dirpath, fn)


def check_file(path: str) -> list[tuple[int, str, str]]:
    issues: list[tuple[int, str, str]] = []
    # utf-8-sig transparently strips a leading BOM (common from Windows editors).
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        lines = fh.readlines()
    in_code = False
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\n").rstrip("\r")
        # Fenced code blocks may be indented up to 3 spaces.
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for name, pat in CHECKS.items():
            if pat.search(line):
                issues.append((i, name, line))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="Root directory to scan")
    ap.add_argument("--no-exit", action="store_true", help="Always exit 0 (advisory mode)")
    args = ap.parse_args()

    total = 0
    checked = 0
    for path in iter_md(args.path):
        checked += 1
        for line_no, name, line in check_file(path):
            rel = os.path.relpath(path, args.path)
            print(f"  {rel}:{line_no}  [{name}]")
            print(f"    {line.strip()[:120]}")
            total += 1

    print()
    if total == 0:
        print(f"PASS Checked {checked} file(s). No encoding artifacts found.")
        return 0
    print(f"FAIL Checked {checked} file(s). {total} encoding artifact(s) found.")
    return 0 if args.no_exit else 1


if __name__ == "__main__":
    sys.exit(main())
