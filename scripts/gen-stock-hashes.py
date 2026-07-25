#!/usr/bin/env python3
"""Maintainer/CI tool for the starter stock-hash history and build manifest.

The append-only history (stock-hashes.json, kept in the dac-starter repo) is
what lets dac-update recognize any stock revision ever shipped. This tool
appends current hashes, verifies the history has no gaps (the image-build
gate), and emits the build manifest the image bakes in.

    gen-stock-hashes.py --starter <dir> --append          update the history
    gen-stock-hashes.py --starter <dir> --verify          CI gate: exit 1 on gaps
    gen-stock-hashes.py --starter <dir> --emit-manifest manifest.json \\
        --starter-version <ref> --engine-image <ref>      write build manifest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dac_common import atomic_write_json, load_json, managed_files, nhash  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--starter", required=True,
                    help="starter tree root (the repo checkout; files at its top level)")
    ap.add_argument("--history", default=None,
                    help="stock-hashes.json path (default: <starter>/stock-hashes.json)")
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--emit-manifest", default=None, metavar="PATH")
    ap.add_argument("--starter-version", default="unknown")
    ap.add_argument("--engine-image", default="unknown")
    args = ap.parse_args()

    root = Path(args.starter).resolve()
    history_path = Path(args.history) if args.history else root / "stock-hashes.json"
    history = load_json(history_path)
    files = managed_files(root)
    if not files:
        print(f"gen-stock-hashes: no managed files found under {root}", file=sys.stderr)
        return 3
    current = {rel: nhash(root / rel) for rel in files}

    if args.append:
        added = 0
        for rel, h in current.items():
            known = history.setdefault(rel, [])
            if h not in known:
                known.append(h)
                added += 1
        atomic_write_json(history_path, history)
        print(f"appended {added} new hash(es) across {len(files)} managed file(s)")

    if args.verify:
        gaps = [rel for rel, h in current.items() if h not in history.get(rel, [])]
        if gaps:
            print("stock-hash history is missing the CURRENT revision of:",
                  file=sys.stderr)
            for rel in gaps:
                print(f"  {rel}", file=sys.stderr)
            print("run: gen-stock-hashes.py --starter <dir> --append  "
                  "(in the dac-starter repo) and commit stock-hashes.json",
                  file=sys.stderr)
            return 1
        print(f"history OK: all {len(files)} managed files covered")

    if args.emit_manifest:
        atomic_write_json(Path(args.emit_manifest), {
            "starter_version": args.starter_version,
            "engine_image": args.engine_image,
            "files": current,
        })
        print(f"wrote {args.emit_manifest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
