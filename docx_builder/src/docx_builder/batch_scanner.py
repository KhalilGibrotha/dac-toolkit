"""
batch_scanner.py — Folder scanner for docx-build-all.

Walks the directories declared in BatchConfig.scan, skips any path matching
BatchConfig.exclude, reads YAML front matter from each .md file found, and
returns a validated document list plus a list of human-readable warnings.

Front matter requirements
─────────────────────────
  Required for all documents:   title, status, version
  Required unless Informational: doc_type

  status must be one of the valid values in VALID_STATUSES.

  Files with no front matter block are skipped silently (READMEs, etc.).
  Files with invalid/missing required fields emit a SKIP warning and are
  excluded from the returned list. The run continues.

Options applied here
────────────────────
  config.options.skip_retired      — drop status: Retired docs before returning
  config.options.skip_informational — drop status: Informational docs before returning
"""

import os
from dataclasses import dataclass
from typing import Optional

from .batch_config import BatchConfig
from .metadata import parse_front_matter


REQUIRED_FIELDS = ('title', 'doc_type', 'status', 'version')
INFORMATIONAL_REQUIRED = ('title', 'status', 'version')   # doc_type exempt

VALID_STATUSES = frozenset({
    'Draft', 'In Review', 'Accepted', 'Rejected',
    'Retired', 'Proposed', 'Informational',
})


@dataclass
class ScannedDoc:
    """A single validated, renderable document discovered by the scanner."""
    path: str        # absolute path to .md source file
    rel_path: str    # path relative to config_dir (for display and index keys)
    title: str
    doc_type: str    # empty string for Informational docs
    status: str
    version: str
    meta: dict       # full parsed front matter dict


# ── Internal helpers ──────────────────────────────────────────────────────────

def _rel(path: str, base: str) -> str:
    """Return path relative to base; fall back to absolute if on a different drive."""
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return path


def _is_excluded(abs_path: str, exclude_abs: list[str]) -> bool:
    """Return True if abs_path is at or under any of the exclude_abs roots."""
    norm = os.path.normpath(abs_path)
    for excl in exclude_abs:
        excl_norm = os.path.normpath(excl)
        if norm == excl_norm or norm.startswith(excl_norm + os.sep):
            return True
    return False


# ── Public API ────────────────────────────────────────────────────────────────

def scan(config: BatchConfig) -> tuple[list[ScannedDoc], list[str]]:
    """
    Walk config.scan paths and return (valid_docs, warnings).

    valid_docs — list[ScannedDoc] ready for the render pipeline, in
                 filesystem traversal order (deterministic across platforms
                 because os.walk is used without topdown sorting, but filenames
                 within each directory are sorted for reproducibility).
    warnings   — list[str] of WARN/SKIP messages describing files that were
                 skipped; empty if everything was clean.
    """
    valid_docs: list[ScannedDoc] = []
    warnings: list[str] = []

    for scan_root in config.scan:
        if not os.path.isdir(scan_root):
            rel = _rel(scan_root, config.config_dir)
            warnings.append(f"WARN  scan path not found, skipping: {rel}")
            continue

        for dirpath, dirnames, filenames in os.walk(scan_root, topdown=True):
            # Prune excluded directories in-place so os.walk never descends into them
            dirnames[:] = sorted(
                d for d in dirnames
                if not _is_excluded(os.path.join(dirpath, d), config.exclude)
            )

            for fname in sorted(f for f in filenames if f.endswith('.md')):
                fpath = os.path.normpath(os.path.join(dirpath, fname))

                if _is_excluded(fpath, config.exclude):
                    continue

                rel = _rel(fpath, config.config_dir)

                # ── Read ──────────────────────────────────────────────────────
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        raw = f.read()
                except OSError as e:
                    warnings.append(f"WARN  cannot read {rel}: {e}")
                    continue

                # ── Parse front matter ─────────────────────────────────────
                meta, _ = parse_front_matter(raw)
                if not meta:
                    # No front matter — README or freeform note; skip silently
                    continue

                # ── Validate required fields ───────────────────────────────
                informational = str(meta.get('status', '')).strip() == 'Informational'
                required = INFORMATIONAL_REQUIRED if informational else REQUIRED_FIELDS
                missing = [f for f in required if not str(meta.get(f, '')).strip()]
                if missing:
                    warnings.append(
                        f"SKIP  {rel}: missing front matter: {', '.join(missing)}"
                    )
                    continue

                # ── Validate status value ──────────────────────────────────
                status = str(meta['status']).strip()
                if status not in VALID_STATUSES:
                    warnings.append(
                        f"SKIP  {rel}: unknown status '{status}' "
                        f"(expected one of: {', '.join(sorted(VALID_STATUSES))})"
                    )
                    continue

                # ── Apply options filters ──────────────────────────────────
                if config.options.skip_retired and status == 'Retired':
                    continue
                if config.options.skip_informational and status == 'Informational':
                    continue

                valid_docs.append(ScannedDoc(
                    path=fpath,
                    rel_path=rel,
                    title=str(meta['title']).strip(),
                    doc_type=str(meta.get('doc_type', '')).strip(),
                    status=status,
                    version=str(meta['version']).strip(),
                    meta=meta,
                ))

    return valid_docs, warnings
