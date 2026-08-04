#!/usr/bin/env python3
"""
Fail if any tracked text file carries CRLF in the git index.

Why this exists as a gate rather than a convention: .gitattributes is the
mechanism that keeps line endings consistent, but it is silent when it is
wrong. A pattern that misses a file type produces no error - the file simply
carries CRLF into the index, and the first symptom is a four-line edit
rendering as a whole-file rewrite, weeks later, in someone's pull request.

That happened here: eol=lf was pinned for *.sh, *.py, *.yml and *.yaml but
never for *.md, and 220 of 289 tracked files accumulated CRLF before anyone
noticed. This check turns that silence into a failing job.

It also reports files git has classified as BINARY (`i/-text`) when their
extension suggests otherwise. That classification makes .gitattributes
inert for the file, and the usual cause is a raw control byte embedded in
the source - the kind of thing that is invisible in an editor and fatal in a
container.

Usage:
    lint-line-endings.py [--path .]
"""

from __future__ import annotations

import argparse
import subprocess
import sys

# Extensions that must never be classified binary. A binary classification
# here means an embedded control byte, not a legitimately binary format.
TEXT_EXTENSIONS = {
    ".md", ".qmd", ".yml", ".yaml", ".py", ".sh", ".json", ".jsonc",
    ".csv", ".txt", ".cfg", ".ini", ".conf", ".toml", ".scss", ".j2",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="Repository root (default: cwd).")
    args = ap.parse_args()

    try:
        out = subprocess.run(
            ["git", "-C", args.path, "ls-files", "--eol"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"cannot read git index: {exc}", file=sys.stderr)
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
            dot = path.rfind(".")
            if dot != -1 and path[dot:].lower() in TEXT_EXTENSIONS:
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
