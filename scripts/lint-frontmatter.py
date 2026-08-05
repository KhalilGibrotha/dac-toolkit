#!/usr/bin/env python3
"""
lint-frontmatter.py — Validate YAML front matter in all Markdown documents.

Checks:
  - Required fields present (title, doc_type, status, version, date, author, owner)
  - doc_type is from the approved list
  - status is valid for the doc_type (per track)

Exits 0 if all files pass, 1 if any violations are found.

Usage:
    python scripts/lint-frontmatter.py [--path docs/] [--strict]

    --path    Root path to scan (default: repo root)
    --strict  Exit non-zero on warnings as well as errors (default: errors only)
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

# ── Approved values ────────────────────────────────────────────────────────────

APPROVED_DOC_TYPES = {
    "overview",
    "gap-analysis",
    "pattern",
    "checklist",
    "reference",
    "guide",
    "adr",
    "proposal",
    "standard",
    "policy",
    "runbook",
    "request",
    "release-notes",
    "rca",
    "spec",
    "sad",
    "meeting-notes",
}

# Status tracks
STANDARD_STATUSES   = {"Draft", "In Review", "Accepted", "Retired"}
DECISION_STATUSES   = {"Proposed", "Accepted", "Rejected", "Retired"}
INFORMATIONAL_STATUSES = {"Informational"}

# Map doc_type to its status track
DECISION_TYPES      = {"adr", "proposal"}
INFORMATIONAL_TYPES = {"meeting-notes"}

# Informational documents (meeting notes, informal captures) have a reduced
# required field set — no doc_type, domain, version, or owner.
REQUIRED_FIELDS_STANDARD     = ["title", "doc_type", "domain", "department", "status", "version", "date", "author", "owner"]

# Fields a repository-level org file may supply, so a document that omits
# them still renders. Passing --org tells this linter which of these have a
# default and drops them from the required set; without it, nothing changes.
# Rendering and linting must agree on what a document is allowed to omit, or
# CI rejects documents the builder handles perfectly well.
ORG_DEFAULTABLE_FIELDS = ["owner"]
REQUIRED_FIELDS_INFORMATIONAL = ["title", "status", "date", "author"]

# Files to skip entirely (no front matter expected)
SKIP_NAMES = {"README.md", "CONTRIBUTING.md", "CHANGELOG.md", "CLAUDE.md"}

# Directories to skip
SKIP_DIRS = {
    ".git", ".vale", "node_modules", ".github",
    "exports", "archive", "diagrams",
}


# ── Front matter parser ────────────────────────────────────────────────────────

_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class FrontMatterParseError(Exception):
    """Raised when a front matter block exists but cannot be parsed."""


def extract_front_matter(text: str) -> dict | None:
    """Return parsed YAML front matter dict, or None if no front matter block.

    Raises FrontMatterParseError if a front matter block is present but the
    YAML inside it is malformed or is not a YAML mapping (e.g., a bare list
    or scalar), which would cause validate() to crash on .get() calls.
    """
    m = _FM_PATTERN.match(text)
    if not m:
        return None
    try:
        result = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        raise FrontMatterParseError(str(exc)) from exc
    if result is None:
        return {}
    if not isinstance(result, dict):
        raise FrontMatterParseError(
            f"Front matter parsed as {type(result).__name__}, expected a YAML mapping"
        )
    return result


# ── Validation ─────────────────────────────────────────────────────────────────

def valid_statuses_for(doc_type: str) -> set[str]:
    if doc_type in DECISION_TYPES:
        return DECISION_STATUSES
    if doc_type in INFORMATIONAL_TYPES:
        return INFORMATIONAL_STATUSES
    return STANDARD_STATUSES


# Where an org file conventionally lives, relative to the scanned root.
# Auto-detection exists so every entry point behaves the same without each
# one remembering a flag: CI, pre-commit, the Dev Spaces task, and whatever
# a developer types by hand. A flag that only some callers pass reproduces
# the exact inconsistency this feature was added to remove.
ORG_FILE_CANDIDATES = ["dac/org.yaml", "org.yaml", "vars/org.yaml"]


def _find_org_file(root: Path, explicit: str | None) -> Path | None:
    """Resolve the org file: an explicit path, else the conventional one.

    A relative --org is tried against the working directory first, because
    that is what every CLI does with a path argument, and then against the
    scanned root, because --org describes the tree being linted and a caller
    standing elsewhere reasonably writes the path relative to it. Honouring
    only one of the two reports "not found" for a file that is plainly there.
    """
    if explicit:
        for candidate in (Path(explicit), root / explicit):
            if candidate.is_file():
                return candidate
        return None
    for rel in ORG_FILE_CANDIDATES:
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return None


def _org_defaults(org_path: Path | str | None) -> set[str]:
    """Fields the org file supplies a default for.

    Read leniently: unreadable, malformed, or simply not a mapping means "no
    defaults", not a crash. A YAML file that parses to a list or a scalar is
    valid YAML and useless here, and this linter validates documents - the
    org file's own shape is not its business to enforce.
    """
    if not org_path:
        return set()
    try:
        with open(org_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError, UnicodeDecodeError):
        # UnicodeDecodeError is a ValueError, not an OSError, so it escapes
        # the obvious catch: a latin-1 or binary file reaches this line and
        # takes the linter down on the read rather than the parse.
        return set()
    if not isinstance(data, dict):
        return set()
    org = data.get("org", data)
    if not isinstance(org, dict):
        return set()
    return {
        field for field in ORG_DEFAULTABLE_FIELDS
        if str(org.get(field, "")).strip()
    }


def validate(fm: dict, org_defaults: set[str] | None = None) -> list[tuple[str, str]]:
    """
    Return a list of (severity, message) tuples.
    Severity is "ERROR" or "WARNING".
    """
    issues: list[tuple[str, str]] = []

    # Informational documents use a reduced required-field set
    status = str(fm.get("status", "")).strip()
    required = (
        REQUIRED_FIELDS_INFORMATIONAL
        if status == "Informational"
        else REQUIRED_FIELDS_STANDARD
    )
    # A field the org file defaults is not missing when a document omits it.
    if org_defaults:
        required = [f for f in required if f not in org_defaults]

    # Required fields
    for field in required:
        if field not in fm or fm[field] is None or str(fm[field]).strip() == "":
            issues.append(("ERROR", f"Missing required field: '{field}'"))

    # doc_type (skip check for Informational docs — field is legitimately absent)
    doc_type = str(fm.get("doc_type", "")).strip()
    if doc_type and doc_type not in APPROVED_DOC_TYPES:
        issues.append((
            "ERROR",
            f"Invalid doc_type: '{doc_type}'. Approved values: {sorted(APPROVED_DOC_TYPES)}",
        ))

    # status
    if status and doc_type in APPROVED_DOC_TYPES:
        allowed = valid_statuses_for(doc_type)
        if status not in allowed:
            issues.append((
                "ERROR",
                f"Invalid status: '{status}' for doc_type '{doc_type}'. "
                f"Allowed: {sorted(allowed)}",
            ))

    # version sanity (warn if not semver-ish; "rolling" is a documented exception)
    version = str(fm.get("version", "")).strip()
    if version and version != "rolling" and not re.match(r"^\d+\.\d+", version):
        issues.append(("WARNING", f"Version '{version}' does not look like a semver string (e.g., '0.1', '1.0')."))

    return issues


# ── Scanner ────────────────────────────────────────────────────────────────────

def scan(root: Path, strict: bool, org_defaults: set[str] | None = None) -> int:
    """Walk root, validate each eligible .md file. Returns exit code."""
    errors   = 0
    warnings = 0
    skipped  = 0
    checked  = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped directories in-place so os.walk doesn't descend
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in sorted(filenames):
            if not filename.endswith(".md"):
                continue
            if filename in SKIP_NAMES:
                skipped += 1
                continue

            filepath = Path(dirpath) / filename
            rel      = filepath.relative_to(root)

            text = filepath.read_text(encoding="utf-8")
            try:
                fm = extract_front_matter(text)
            except FrontMatterParseError as exc:
                print(f"[ERROR] {rel}: Front matter YAML is malformed — {exc}")
                errors  += 1
                checked += 1
                continue

            if fm is None:
                # No front matter block at all — skip (not a formal document)
                skipped += 1
                continue

            issues = validate(fm, org_defaults)
            checked += 1

            for severity, msg in issues:
                print(f"[{severity}] {rel}: {msg}")
                if severity == "ERROR":
                    errors += 1
                else:
                    warnings += 1

    # ── Summary ────────────────────────────────────────────────────────────────
    total_issues = errors + (warnings if strict else 0)
    status_icon  = "PASS" if total_issues == 0 else "FAIL"
    print(
        f"\n{status_icon} Checked {checked} file(s), skipped {skipped}. "
        f"Errors: {errors}, Warnings: {warnings}."
    )

    return 1 if total_issues > 0 else 0


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="lint-frontmatter",
        description="Validate YAML front matter in Markdown documents.",
    )
    parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on warnings as well as errors",
    )
    parser.add_argument(
        "--org",
        metavar="FILE",
        help="Path to org.yaml. Fields it supplies a default for (currently "
             "owner) stop being required in front matter, matching what "
             "docx-build --org already accepts. Auto-detected from "
             + ", ".join(ORG_FILE_CANDIDATES) + " when omitted.",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Error: path is not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    org_file = _find_org_file(root, args.org)
    if args.org and org_file is None:
        print(f"Error: org file not found: {args.org}", file=sys.stderr)
        sys.exit(1)

    sys.exit(scan(root, strict=args.strict, org_defaults=_org_defaults(org_file)))


if __name__ == "__main__":
    main()
