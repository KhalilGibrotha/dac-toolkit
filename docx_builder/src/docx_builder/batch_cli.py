"""
batch_cli.py — CLI entrypoint for docx-build-all.

Registered in pyproject.toml as:
    docx-build-all = "docx_builder.batch_cli:main"

Usage:
    docx-build-all [--config PATH] [--org PATH] [--dry-run] [--force] [--report-file PATH]

Execution flow:
    1. Load and validate config (abort with exit 2 on config error)
    2. Run folder scanner → validated document list + scan warnings
    3. Load render index from export_root
    4. For each document:
         a. Decide outcome (NEW / SKIP / RENDERED / MOVED)
         b. Skip unchanged documents
         c. On MOVED: remove old output file
         d. Render via existing build_document() pipeline
         e. Update index entry
         f. Record result in BuildReport
    5. Save render index (skipped in --dry-run)
    6. Print build report (and optionally write to --report-file)
    7. Exit with appropriate code (0 = clean, 1 = failures, 2 = abort)

Exit codes:
    0 — all documents rendered or skipped cleanly
    1 — one or more documents failed to render
    2 — run-level abort (config error, export dir unwritable)
"""

import argparse
import os
import sys
import traceback

import yaml

from .batch_config import load_config, ConfigError
from .batch_scanner import scan
from .batch_index import RenderIndex
from .batch_output import resolve_output_path, ensure_output_dir, remove_old_output
from .batch_report import BuildReport, DocResult
from .builder import build_document


def _load_org_yaml(path: str) -> dict:
    """Load org identity overrides from a YAML file (same logic as cli.py)."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('org', data)


def main():
    parser = argparse.ArgumentParser(
        prog="docx-build-all",
        description="Batch render Markdown documentation to DOCX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  docx-build-all
  docx-build-all --config path/to/docx-build.yml
  docx-build-all --dry-run
  docx-build-all --force --report-file exports/last-run.txt

Requires a docx-build.yml config file in the current directory or any
parent directory. See the dac-toolkit README for the config schema.
        """,
    )
    parser.add_argument(
        '--config',
        default=None,
        metavar='PATH',
        help="Path to docx-build.yml. Defaults to searching upward from CWD.",
    )
    parser.add_argument(
        '--org',
        default=None,
        metavar='PATH',
        help="Path to org.yaml with org identity overrides. "
             "Takes precedence over the 'org' key in docx-build.yml.",
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Scan and report what would be rendered; do not write any files.",
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Re-render all documents regardless of version or status match.",
    )
    parser.add_argument(
        '--report-file',
        default=None,
        metavar='PATH',
        help="Write the build report to this file in addition to stdout.",
    )

    args = parser.parse_args()

    # ── 1. Load config ────────────────────────────────────────────────────────
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    # ── 2. Validate export_root is writable (skip in dry-run) ─────────────────
    if not args.dry_run:
        try:
            os.makedirs(config.export_root, exist_ok=True)
            test_file = os.path.join(config.export_root, ".write-test")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("")
            os.remove(test_file)
        except OSError as e:
            print(
                f"Error: export directory is not writable: {config.export_root}\n  {e}",
                file=sys.stderr,
            )
            sys.exit(2)

    # ── 3. Load org overrides (CLI --org takes precedence over config) ────────
    org_path = args.org or config.org
    org_overrides = None
    if org_path:
        org_path = os.path.abspath(org_path)
        if not os.path.isfile(org_path):
            print(f"Error: org file not found: {org_path}", file=sys.stderr)
            sys.exit(2)
        try:
            org_overrides = _load_org_yaml(org_path)
        except (OSError, yaml.YAMLError) as e:
            print(f"Error: cannot load org file {org_path}: {e}", file=sys.stderr)
            sys.exit(2)

    # ── 4. Scan ───────────────────────────────────────────────────────────────
    docs, scan_warnings = scan(config)

    # ── 5. Load render index ──────────────────────────────────────────────────
    index = RenderIndex.load(config.export_root)

    # ── 6. Initialise report ──────────────────────────────────────────────────
    report = BuildReport()
    for w in scan_warnings:
        report.add_scan_warning(w)

    # ── 7. Dry-run fast path ──────────────────────────────────────────────────
    if args.dry_run:
        would_render = 0
        would_skip   = 0
        would_move   = 0

        for doc in docs:
            outcome, _ = index.decide(doc.rel_path, doc.version, doc.status, force=args.force)
            if outcome == RenderIndex.OUTCOME_SKIP:
                would_skip += 1
            elif outcome == RenderIndex.OUTCOME_MOVED:
                would_move += 1
                would_render += 1
            else:
                would_render += 1

        print(f"\n[DRY RUN] Would render:  {would_render:>4} documents")
        print(f"[DRY RUN] Would skip:    {would_skip:>4} documents")
        print(f"[DRY RUN] Would move:    {would_move:>4} documents (status change)")
        if scan_warnings:
            print("\n[DRY RUN] Scanner warnings:")
            for w in scan_warnings:
                print(f"  {w}")
        print()
        sys.exit(0)

    # ── 8. Render loop ────────────────────────────────────────────────────────
    for doc in docs:
        result_warnings: list[str] = []
        outcome, existing = index.decide(
            doc.rel_path, doc.version, doc.status, force=args.force
        )

        # SKIP — nothing to do
        if outcome == RenderIndex.OUTCOME_SKIP:
            report.add(DocResult(rel_path=doc.rel_path, outcome=outcome))
            print(f"SKIP     {doc.rel_path}")
            continue

        # MOVED — remove old output before rendering to new location
        old_output_abs = None
        old_status     = None
        if outcome == RenderIndex.OUTCOME_MOVED and existing:
            old_status = existing.status
            # Index stores paths relative to config_dir; resolve to absolute
            old_output_abs = os.path.join(config.config_dir, existing.output) \
                if not os.path.isabs(existing.output) else existing.output
            warn = remove_old_output(old_output_abs, doc.rel_path)
            if warn:
                result_warnings.append(warn)

        # Resolve output path
        output_path = resolve_output_path(
            config.export_root, doc.path, doc.status, doc.version
        )

        # Render
        try:
            ensure_output_dir(output_path)
            build_document(
                doc.path,
                output_path=output_path,
                org_overrides=org_overrides,
            )
            # Store relative path in the index for portability
            rel_output = os.path.relpath(output_path, config.config_dir)
            index.update(doc.rel_path, doc.version, doc.status, rel_output)
            report.add(DocResult(
                rel_path=doc.rel_path,
                outcome=outcome,
                old_status=old_status,
                new_status=doc.status,
                warnings=result_warnings,
            ))
            label = outcome.ljust(8)
            print(f"{label} {doc.rel_path}  →  {output_path}")

        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}"
            rel_output = os.path.relpath(output_path, config.config_dir)
            index.update(doc.rel_path, doc.version, doc.status, rel_output, error=err_msg)
            report.add(DocResult(
                rel_path=doc.rel_path,
                outcome=RenderIndex.OUTCOME_FAILED,
                error=err_msg,
                warnings=result_warnings,
            ))
            print(f"FAILED   {doc.rel_path}")
            print(f"         Error: {err_msg}")
            if os.environ.get('DOCX_BUILD_VERBOSE'):
                traceback.print_exc()

    # ── 9. Save index ─────────────────────────────────────────────────────────
    index.save(config.export_root)

    # ── 10. Report ────────────────────────────────────────────────────────────
    report.print()
    if args.report_file:
        try:
            report.write(args.report_file)
            print(f"Report written to: {args.report_file}")
        except OSError as e:
            print(f"WARN  could not write report file: {e}", file=sys.stderr)

    sys.exit(report.exit_code)


if __name__ == '__main__':
    main()
