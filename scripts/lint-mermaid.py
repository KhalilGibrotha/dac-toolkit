#!/usr/bin/env python3
"""
Preflight Mermaid fences in formal markdown documents.

This is a lightweight content check that catches fence-shape issues and a few
house-style violations before a full DOCX render is attempted.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
SKIP_DIRS = {".git", ".github", ".vale", "archive", "exports", "diagrams", "node_modules"}
SKIP_NAMES = {"README.md", "CLAUDE.md", "CONTRIBUTING.md", "CHANGELOG.md"}
VALID_STARTERS = (
    "flowchart ",
    "sequenceDiagram",
    "requirementDiagram",
    "stateDiagram-v2",
    "classDiagram",
)


def eligible_markdown_files(root: Path, include_templates: bool) -> list[Path]:
    results: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if path.name in SKIP_NAMES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not include_templates and "templates" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if FRONT_MATTER_RE.match(text):
            results.append(path)
    return results


def lint_file(path: Path, root: Path) -> list[tuple[str, int, str]]:
    issues: list[tuple[str, int, str]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence = False
    fence_start = 0
    fence_body: list[str] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not in_fence and stripped.startswith("``` mermaid"):
            issues.append(("ERROR", idx, "Use '```mermaid' with no space after the opening backticks."))
            continue

        if not in_fence and stripped.startswith("```mermaid"):
            in_fence = True
            fence_start = idx
            fence_body = []
            continue

        if in_fence and stripped == "```":
            content_lines = [item.strip() for item in fence_body if item.strip()]
            if not content_lines:
                issues.append(("ERROR", fence_start, "Mermaid fence is empty."))
            else:
                # The diagram type is the first non-directive line; skip any
                # leading '%%{init}%%' directives or '%%' comments.
                first = next((c for c in content_lines if not c.startswith("%%")), content_lines[0])
                if first.startswith("graph "):
                    issues.append(("ERROR", fence_start, "Use 'flowchart TD/LR' instead of deprecated 'graph TD/LR'."))
                elif not first.startswith(VALID_STARTERS):
                    issues.append((
                        "WARNING",
                        fence_start,
                        "First Mermaid line does not match the repo's preferred diagram starters "
                        "(flowchart, sequenceDiagram, requirementDiagram, stateDiagram-v2, classDiagram).",
                    ))

                # Semicolons break sequence/state diagram labels: ';' is a
                # Mermaid statement separator, so it truncates the unquoted
                # label and the renderer rejects the diagram (HTTP 400).
                # Flowchart labels are bracket-quoted, so they are exempt.
                # Skip '%%' comment lines, which may legitimately contain ';'.
                if first.startswith(("sequenceDiagram", "stateDiagram")):
                    for offset, body_line in enumerate(fence_body):
                        if body_line.strip().startswith("%%"):
                            continue
                        if ";" in body_line:
                            issues.append((
                                "ERROR",
                                fence_start + 1 + offset,
                                "Semicolon in a sequence/state diagram label breaks rendering "
                                "(';' is a Mermaid statement separator). Use a comma or dash.",
                            ))
            in_fence = False
            fence_start = 0
            fence_body = []
            continue

        if in_fence:
            fence_body.append(line)

    if in_fence:
        issues.append(("ERROR", fence_start, "Unclosed Mermaid fence."))

    if issues:
        rel = path.relative_to(root).as_posix()
        return [(severity, line_no, f"{rel}:{line_no}: {message}") for severity, line_no, message in issues]
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".", help="Repo root to scan.")
    parser.add_argument("--include-templates", action="store_true")
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    files = eligible_markdown_files(root, include_templates=args.include_templates)

    all_issues: list[tuple[str, int, str]] = []
    for path in files:
        all_issues.extend(lint_file(path, root))

    errors = 0
    warnings = 0
    for severity, _, message in all_issues:
        print(f"[{severity}] {message}")
        if severity == "ERROR":
            errors += 1
        else:
            warnings += 1

    print(f"\nChecked {len(files)} file(s). Errors: {errors}, Warnings: {warnings}.")
    if errors or (args.strict_warnings and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
