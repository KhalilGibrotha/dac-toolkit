"""
batch_index.py — Render index reader/writer and skip logic for docx-build-all.

The render index is a YAML file stored at <export_root>/.render-index.yml.
It tracks the last-rendered state of every document so the batch runner can
skip re-rendering files whose version and status have not changed.

Index file format
─────────────────
    docs/overview_aap_architecture.md:
      version: "0.3"
      status: "Draft"
      rendered_at: "2026-03-20T14:32:00Z"
      output: "exports/Draft/overview_aap_architecture_v0.3.docx"

Keys are document rel_paths (relative to the config directory, forward-slash
normalised for cross-platform consistency). Values are RenderRecord dicts.

Skip logic
──────────
  NEW            — no index entry; render and add entry
  SKIP           — version and status match entry; leave file untouched
  RENDERED       — version changed; render and update entry
  MOVED+RENDERED — status changed; render to new folder, remove old file, update entry
  FAILED         — build raised an exception; update entry with error details

The index is loaded once at startup and written back atomically at the end of
the run.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import yaml


INDEX_FILENAME = ".render-index.yml"


@dataclass
class RenderRecord:
    version: str
    status: str
    rendered_at: str     # ISO-8601 UTC timestamp
    output: str          # path to the rendered DOCX (relative to config_dir for portability)
    error: Optional[str] = None  # set on FAILED entries


class RenderIndex:
    """
    In-memory render index with load/save and skip-decision logic.

    Usage:
        index = RenderIndex.load(export_root)
        outcome, record = index.decide(doc)
        # ... render ...
        index.update(doc.rel_path, record)
        index.save(export_root)
    """

    OUTCOME_NEW      = "NEW"
    OUTCOME_SKIP     = "SKIP"
    OUTCOME_RENDERED = "RENDERED"
    OUTCOME_MOVED    = "MOVED"
    OUTCOME_FAILED   = "FAILED"

    def __init__(self, records: dict[str, RenderRecord]):
        self._records: dict[str, RenderRecord] = records

    # ── Persistence ───────────────────────────────────────────────────────────

    @classmethod
    def load(cls, export_root: str) -> "RenderIndex":
        """
        Load the render index from <export_root>/.render-index.yml.

        Returns an empty index if the file does not exist. If the file is
        corrupt or unparseable, logs a warning and returns an empty index
        (the first run will re-render all documents and rebuild it).
        """
        path = os.path.join(export_root, INDEX_FILENAME)
        if not os.path.isfile(path):
            return cls({})

        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            print(f"WARN  render index corrupt or unreadable ({e}); rebuilding.")
            return cls({})

        records: dict[str, RenderRecord] = {}
        for key, val in raw.items():
            if not isinstance(val, dict):
                continue
            try:
                records[_norm_key(key)] = RenderRecord(
                    version=str(val.get('version', '')),
                    status=str(val.get('status', '')),
                    rendered_at=str(val.get('rendered_at', '')),
                    output=str(val.get('output', '')),
                    error=val.get('error'),
                )
            except (TypeError, KeyError):
                continue   # skip malformed entries

        return cls(records)

    def save(self, export_root: str) -> None:
        """
        Write the index to <export_root>/.render-index.yml atomically.

        Creates export_root if it does not exist.
        """
        os.makedirs(export_root, exist_ok=True)
        path    = os.path.join(export_root, INDEX_FILENAME)
        tmp     = path + ".tmp"
        payload = {
            key: {
                'version':     rec.version,
                'status':      rec.status,
                'rendered_at': rec.rendered_at,
                'output':      rec.output,
                **({'error': rec.error} if rec.error else {}),
            }
            for key, rec in sorted(self._records.items())
        }
        with open(tmp, 'w', encoding='utf-8') as f:
            yaml.dump(payload, f, default_flow_style=False, allow_unicode=True)
        os.replace(tmp, path)

    # ── Decision logic ────────────────────────────────────────────────────────

    def decide(self, rel_path: str, version: str, status: str, force: bool = False
               ) -> tuple[str, Optional[RenderRecord]]:
        """
        Determine the outcome for a document before rendering.

        Returns:
            (outcome, existing_record)

            outcome is one of OUTCOME_NEW / OUTCOME_SKIP / OUTCOME_RENDERED /
            OUTCOME_MOVED. OUTCOME_FAILED is set externally after a build error.

            existing_record is the current index entry (or None for NEW).
            Callers use it to locate the old output file when the status changes.
        """
        key = _norm_key(rel_path)
        rec = self._records.get(key)

        if rec is None:
            return self.OUTCOME_NEW, None

        # Status change always takes priority — even in force mode — so the
        # caller knows to clean up the old output file from the previous folder.
        if rec.status != status:
            return self.OUTCOME_MOVED, rec

        if force:
            return self.OUTCOME_RENDERED, rec

        if rec.version != version:
            return self.OUTCOME_RENDERED, rec

        return self.OUTCOME_SKIP, rec

    # ── Mutation ──────────────────────────────────────────────────────────────

    def update(self, rel_path: str, version: str, status: str,
               output: str, error: Optional[str] = None) -> None:
        """Insert or replace the index entry for rel_path."""
        self._records[_norm_key(rel_path)] = RenderRecord(
            version=version,
            status=status,
            rendered_at=_utcnow(),
            output=output,
            error=error,
        )

    def get(self, rel_path: str) -> Optional[RenderRecord]:
        """Return the current index entry for rel_path, or None."""
        return self._records.get(_norm_key(rel_path))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm_key(path: str) -> str:
    """Normalise a rel_path to a consistent forward-slash YAML key."""
    return path.replace(os.sep, '/')


def _utcnow() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
