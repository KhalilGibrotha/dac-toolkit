#!/usr/bin/env python3
"""
Run Vale against formal documentation in a content repository, with a
GitHub Actions job summary.

By default this targets only Markdown files with YAML front matter, which
keeps the signal focused on real documents rather than folder READMEs,
templates, and support files — the same opt-in-per-file behavior the front
matter gate uses. Use --include-support-docs to lint the broader corpus.

One Vale run in JSON mode feeds three renderings: the per-finding log, a
per-document summary table written to GITHUB_STEP_SUMMARY when CI provides
it, and a headline score — percent of documents error-free. Errors drive the
score because errors are what reviewers are told to prioritise; a
warnings-inclusive score buries error progress under style noise.

This script ships in the toolkit image and runs against whatever repository
it is pointed at:

    lint-prose.py --no-exit            # CI: advisory on findings
    lint-prose.py --path /some/repo    # explicit root (default: cwd)

Exit codes: 0 clean or advisory; 1 error-severity findings (without
--no-exit); Vale's own code on runtime failure — a Vale that cannot run has
checked nothing, and that must fail even in advisory mode.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
TARGET_DIRS = {
    "docs",
    "initiatives",
    "patterns",
    "governance",
    "decisions",
    "references",
    "notes",
}
SKIP_NAMES = {"README.md", "CONTRIBUTING.md", "CHANGELOG.md", "CLAUDE.md"}
SKIP_DIRS = {".git", ".github", "vale", "node_modules", "exports", "archive", "diagrams"}


def formal_markdown_files(root: Path, include_templates: bool) -> list[str]:
    paths: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]

        current = Path(dirpath)
        rel_dir = current.relative_to(root)
        top_level = rel_dir.parts[0] if rel_dir.parts else ""
        template_dir = rel_dir.as_posix() == "dac/templates" or rel_dir.as_posix().startswith("dac/templates/")
        allowed = (
            top_level in TARGET_DIRS
            or (include_templates and (template_dir or rel_dir.as_posix() == "dac"))
        )
        if top_level and not allowed:
            dirnames[:] = []
            continue
        if top_level == "dac" and not template_dir and rel_dir.as_posix() != "dac":
            # inside dac/ but outside dac/templates (vale styles, org data)
            dirnames[:] = []
            continue
        if rel_dir.as_posix() == "dac":
            # descend only into templates; never lint dac/ root files
            dirnames[:] = [name for name in dirnames if name == "templates"]
            filenames = []

        for filename in sorted(filenames):
            if not filename.endswith(".md"):
                continue
            if filename in SKIP_NAMES:
                continue

            path = current / filename
            text = path.read_text(encoding="utf-8", errors="replace")
            if FRONT_MATTER_RE.match(text):
                paths.append(str(path.relative_to(root)))

    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-exit", action="store_true", help="Advisory: exit 0 on findings.")
    parser.add_argument(
        "--path",
        default=".",
        help="Repository root to lint (default: current directory).",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Include dac/templates/ in the lint target set.",
    )
    parser.add_argument(
        "--include-support-docs",
        action="store_true",
        help="Lint the broader repo paths instead of only formal front-matter documents.",
    )
    args = parser.parse_args()

    repo_root = Path(args.path).resolve()
    if not repo_root.is_dir():
        print(f"not a directory: {repo_root}", file=sys.stderr)
        return 2

    cmd = ["vale", "--output=JSON"]

    if args.include_support_docs:
        targets = sorted(d for d in TARGET_DIRS if (repo_root / d).is_dir())
        if args.include_templates and (repo_root / "dac" / "templates").is_dir():
            targets.append("dac/templates")
        if not targets:
            print("No target directories exist under the repository root.", file=sys.stderr)
            return 0
        cmd.extend(targets)
        total_targets = None  # directory mode: file count unknown up front
    else:
        targets = formal_markdown_files(repo_root, include_templates=args.include_templates)
        if not targets:
            print("No formal Markdown documents with front matter were found.")
            return 0
        cmd.extend(targets)
        total_targets = len(targets)

    try:
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    except FileNotFoundError:
        print("vale is not installed or not on PATH.", file=sys.stderr)
        return 1

    # Vale exits 1 when it finds error-severity issues and 2 on runtime
    # failure (missing style, bad config). Runtime failure must fail the job
    # even in advisory mode - a Vale that cannot run has checked nothing.
    if result.returncode not in (0, 1):
        sys.stderr.write(result.stderr)
        print("Vale runtime failure (missing styles? run 'vale sync').", file=sys.stderr)
        return result.returncode

    try:
        findings: dict[str, list[dict]] = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        sys.stderr.write(result.stdout)
        print("Could not parse Vale JSON output.", file=sys.stderr)
        return 2

    sev_names = ("error", "warning", "suggestion")
    per_file: dict[str, Counter] = {}
    totals: Counter = Counter()
    for path, items in sorted(findings.items()):
        counts = Counter(i.get("Severity", "suggestion") for i in items)
        per_file[path] = counts
        totals.update(counts)
        # Log detail: compact, one line per finding, greppable in the CI log.
        print(path)
        for i in items:
            print(
                f"  {i.get('Line', 0)}:{(i.get('Span') or [0])[0]}"
                f"  {i.get('Severity', '?'):<10}"
                f"  {i.get('Check', '?')}  {i.get('Message', '')}"
            )
        print()

    flagged = len(per_file)
    if total_targets is None:
        total_targets = flagged  # directory mode: report flagged files only
    clean = max(total_targets - flagged, 0)
    with_errors = sum(1 for c in per_file.values() if c.get("error", 0))
    error_free = max(total_targets - with_errors, 0)
    score = round(100 * error_free / total_targets) if total_targets else 100

    tally = " - ".join(f"{totals.get(s, 0)} {s}s" for s in sev_names)
    print(f"{tally} across {flagged} of {total_targets} documents; {score}% error-free")

    # GitHub Actions job summary - the piece that keeps an advisory gate
    # honest. Same heading pattern every gate uses: '## <name> - <state>'.
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        state = "ADVISORY - findings below" if per_file else "CLEAN"
        lines = [
            f"## Vale prose lint - {state}",
            "",
            f"**{score}% of documents error-free** ({error_free} of {total_targets}; "
            f"{clean} fully clean) - {tally}",
            "",
        ]
        if per_file:
            lines += [
                "| Document | Errors | Warnings | Suggestions |",
                "|---|---:|---:|---:|",
            ]
            ranked = sorted(
                per_file.items(),
                key=lambda kv: (-kv[1].get("error", 0), -kv[1].get("warning", 0), kv[0]),
            )
            shown = ranked[:30]
            for path, c in shown:
                lines.append(
                    f"| {path} | {c.get('error', 0)} | {c.get('warning', 0)} | {c.get('suggestion', 0)} |"
                )
            if len(ranked) > len(shown):
                rest = ranked[len(shown):]
                lines.append(
                    f"| _...and {len(rest)} more documents_ | "
                    f"{sum(c.get('error', 0) for _, c in rest)} | "
                    f"{sum(c.get('warning', 0) for _, c in rest)} | "
                    f"{sum(c.get('suggestion', 0) for _, c in rest)} |"
                )
            lines += [
                "",
                "_Advisory: findings do not block this merge. Errors are the "
                "priority; warnings are style guidance. Full detail is in the "
                "job log._",
            ]
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    if not args.no_exit and totals.get("error", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
