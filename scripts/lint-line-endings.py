#!/usr/bin/env python3
"""
Fail if any tracked text file carries CRLF in the git index.

Why this exists as a gate rather than a convention: .gitattributes is the
mechanism that keeps line endings consistent, but it is silent when it is
wrong. A pattern that misses a file type produces no error - the file simply
carries CRLF into the index, and the first symptom is a four-line edit
rendering as a whole-file rewrite, weeks later, in someone's pull request.

That is not hypothetical. In one repository using this check, eol=lf was
pinned for *.sh, *.py, *.yml and *.yaml but never for *.md, and 220 of 289
tracked files accumulated CRLF before anyone noticed. This check turns that
silence into a failing job.

It also reports files git has classified as BINARY (`i/-text`) when their
extension suggests otherwise. That classification makes .gitattributes
inert for the file, and the usual cause is a raw control byte embedded in
the source - the kind of thing that is invisible in an editor and fatal in a
container.

Worth stating because it is counter-intuitive: no .gitattributes pattern
rescues that case. `text` and `text=auto` behave identically once git's
detector has called a file binary, because the attribute requests a
conversion the detector never runs. Measured, not assumed - a .sh file
holding a lone CR lands at `i/-text` under `* text=auto eol=lf` and under an
explicit `*.sh text eol=lf` alike, while an ordinary CRLF file normalizes to
`i/lf` under both. So a catch-all is not the weaker choice, and this check
is the only thing that catches what neither pattern can.

Usage:
    lint-line-endings.py [--path .]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import PurePosixPath

# Extensions that must never be classified binary. A binary classification
# here means an embedded control byte, not a legitimately binary format.
TEXT_EXTENSIONS = {
    ".md", ".qmd", ".yml", ".yaml", ".py", ".sh", ".json", ".jsonc",
    ".csv", ".txt", ".cfg", ".ini", ".conf", ".toml", ".scss", ".j2",
}

# Formats that are binary no matter what the inner suffixes claim. The
# FINAL suffix names the actual on-disk format: `data.csv.gz` carries `.csv`
# in its suffixes, but a gzip is binary whatever it wraps.
BINARY_EXTENSIONS = {
    ".gz", ".bz2", ".xz", ".zst", ".zip", ".tar", ".tgz", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svgz",
    ".pdf", ".docx", ".pptx", ".xlsx",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".so", ".dll", ".exe", ".bin", ".pyc", ".whl",
}

# Extensionless files that are text by convention.
TEXT_BASENAMES = {
    ".gitignore", ".gitattributes", ".editorconfig", ".dockerignore",
    ".yamllint", ".ansible-lint", "Containerfile", "Dockerfile",
    "Makefile", "LICENSE", "CODEOWNERS",
}


def looks_like_text(path: str) -> bool:
    """Should this path have been treated as text?

    Scan suffixes right to left and let the first KNOWN one decide. The
    suffix nearest the end that names a real format is the file's format;
    anything after it is renaming (`.disabled`, `.bak`), and anything
    before it is wrapped content.

      example.yml.disabled   .disabled unknown -> .yml text     -> True
      data.csv.gz            .gz binary                          -> False
      data.csv.gz.disabled   .disabled unknown -> .gz binary     -> False
      notes.md.bak           .bak unknown -> .md text            -> True

    The last case above is why the scan cannot stop at the final suffix,
    and the third is why it cannot match any suffix: both simpler rules
    were tried, and each one misclassified a case the other got right.
    """
    p = PurePosixPath(path)
    if p.name in TEXT_BASENAMES:
        return True
    for s in reversed([s.lower() for s in p.suffixes]):
        if s in BINARY_EXTENSIONS:
            return False
        if s in TEXT_EXTENSIONS:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="Repository root (default: cwd).")
    args = ap.parse_args()

    try:
        out = subprocess.run(
            ["git", "-C", args.path, "ls-files", "--eol"],
            capture_output=True, text=True, check=True,
        ).stdout
    except FileNotFoundError:
        print("cannot read git index: git is not on PATH", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        # git's own stderr says which of these it was - not a repository,
        # bad --path, corrupt index. Printing only the exception object
        # gives a CI reader an exit status and nothing to act on.
        print(f"cannot read git index (git exited {exc.returncode}):", file=sys.stderr)
        print((exc.stderr or "").rstrip() or "  (git wrote nothing to stderr)",
              file=sys.stderr)
        return 2

    crlf: list[str] = []
    mixed: list[str] = []
    wrongly_binary: list[str] = []
    checked = 0

    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        index_attr = parts[0]          # e.g. i/lf, i/crlf, i/mixed, i/-text
        path = line.split("\t")[-1].strip()
        checked += 1

        if index_attr == "i/crlf":
            crlf.append(path)
        elif index_attr == "i/mixed":
            mixed.append(path)
        elif index_attr == "i/-text":
            if looks_like_text(path):
                wrongly_binary.append(path)

    for path in crlf:
        print(f"CRLF     {path}")
    for path in mixed:
        print(f"MIXED    {path}")
    for path in wrongly_binary:
        print(f"BINARY?  {path}  (text extension classified binary)")

    print()
    print(f"Checked {checked} tracked file(s). "
          f"{len(crlf)} CRLF, {len(mixed)} mixed, "
          f"{len(wrongly_binary)} misclassified.")

    if not (crlf or mixed or wrongly_binary):
        print("PASS Line endings are consistent.")
        return 0

    print()
    if crlf or mixed:
        print("Fix: confirm .gitattributes covers these paths, then run")
        print("     git add --renormalize . && git commit")
    if wrongly_binary:
        print("A text file classified binary usually holds a raw control byte.")
        print("Remove the byte first - renormalizing will not touch the file")
        print("while git still believes it is binary.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
