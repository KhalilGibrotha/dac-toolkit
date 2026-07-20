#!/usr/bin/env python3
"""Deck quality gate: every committed deck source has a committed, intact render.

Checks a content repo's presentations/ directory:
1. Every top-level .qmd (not underscore-prefixed) has exports/<name>.pptx
   committed — the outputs-beside-sources rule.
2. Every committed .pptx passes a ZIP package-integrity test and is a real
   pptx package.
3. No orphan .pptx without a matching source.

Usage:
    python scripts/lint-decks.py [CONTENT_DIR]

CONTENT_DIR defaults to $WORKSPACE or the current directory. Exit 1 on any
failure. Rendering itself is not done in CI; freshness is enforced by review
convention (re-render in the same PR that edits a source).
"""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

content_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    os.environ.get("WORKSPACE", "."))
pres = (content_dir / "presentations").resolve()
exports = pres / "exports"

if not pres.is_dir():
    print(f"PASS no presentations/ directory at {pres} — nothing to check.")
    sys.exit(0)

failures: list[str] = []

sources = [p for p in pres.glob("*.qmd") if not p.name.startswith("_")]
for src in sources:
    pptx = exports / (src.stem + ".pptx")
    if not pptx.is_file():
        failures.append(
            f"missing render: presentations/exports/{pptx.name} "
            f"(source {src.name} has no committed pptx)")

stems = {s.stem for s in sources}
renders = sorted(exports.glob("*.pptx")) if exports.is_dir() else []
for pptx in renders:
    if pptx.stem not in stems:
        failures.append(
            f"orphan render: {pptx.name} has no matching source .qmd "
            f"— delete it or restore the source")
    try:
        with zipfile.ZipFile(pptx) as z:
            bad = z.testzip()
            if bad is not None:
                failures.append(f"corrupt member in {pptx.name}: {bad}")
            if "ppt/presentation.xml" not in z.namelist():
                failures.append(f"not a pptx package: {pptx.name}")
    except (zipfile.BadZipFile, OSError) as exc:
        failures.append(f"unreadable package {pptx.name}: {exc.__class__.__name__}")

if failures:
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)

print(f"PASS {len(sources)} deck source(s), {len(renders)} render(s) intact.")
