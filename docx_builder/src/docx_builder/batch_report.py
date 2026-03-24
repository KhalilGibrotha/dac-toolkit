"""
batch_report.py — Build result tracking, report formatting, and exit codes.

Each document processed by docx-build-all produces a DocResult. After all
documents are processed, BuildReport aggregates the results and formats the
human-readable summary printed to stdout (and optionally written to a file).

Exit codes
──────────
  0 — all documents rendered or skipped cleanly (no FAILED results)
  1 — one or more documents failed to render
  2 — run-level abort (config error, unwritable export directory, etc.)
      Exit code 2 is raised by the caller (batch_cli.py) before a BuildReport
      is created, so this module only produces codes 0 and 1.

Report format
─────────────
    docx-build-all — 2026-03-20 14:32:00 UTC

      Scanned:    24
      Rendered:    3
      Skipped:    19  (up to date)
      Failed:      1
      Moved:       1  (status change)

    FAILED:
      initiatives/rhel-upgrade/overview_rhel-upgrade-readiness.md
        Error: KeyError: 'title'

    MOVED:
      governance/standard_security_baseline.md
        Draft → In-Review
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .batch_index import RenderIndex


@dataclass
class DocResult:
    """Result record for a single document processed in the batch run."""
    rel_path: str
    outcome: str             # NEW / RENDERED / SKIP / MOVED / FAILED
    old_status: Optional[str] = None   # set when outcome is MOVED
    new_status: Optional[str] = None   # set when outcome is MOVED
    error: Optional[str] = None        # set when outcome is FAILED
    warnings: list[str] = field(default_factory=list)


class BuildReport:
    """
    Aggregates DocResult entries and produces the final run summary.

    Usage:
        report = BuildReport()
        report.add(doc_result)
        ...
        report.print()
        sys.exit(report.exit_code)
    """

    def __init__(self):
        self._results: list[DocResult] = []
        self._scan_warnings: list[str] = []
        self._started_at: str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    def add(self, result: DocResult) -> None:
        self._results.append(result)

    def add_scan_warning(self, warning: str) -> None:
        """Record a warning emitted by the scanner (before per-doc processing)."""
        self._scan_warnings.append(warning)

    # ── Counters ──────────────────────────────────────────────────────────────

    @property
    def n_scanned(self) -> int:
        return len(self._results)

    @property
    def n_rendered(self) -> int:
        return sum(1 for r in self._results
                   if r.outcome in (RenderIndex.OUTCOME_NEW,
                                    RenderIndex.OUTCOME_RENDERED,
                                    RenderIndex.OUTCOME_MOVED))

    @property
    def n_skipped(self) -> int:
        return sum(1 for r in self._results if r.outcome == RenderIndex.OUTCOME_SKIP)

    @property
    def n_failed(self) -> int:
        return sum(1 for r in self._results if r.outcome == RenderIndex.OUTCOME_FAILED)

    @property
    def n_moved(self) -> int:
        return sum(1 for r in self._results if r.outcome == RenderIndex.OUTCOME_MOVED)

    @property
    def exit_code(self) -> int:
        return 1 if self.n_failed > 0 else 0

    # ── Formatting ────────────────────────────────────────────────────────────

    def format(self) -> str:
        """Return the full report as a string."""
        lines: list[str] = []

        lines.append(f"\ndocx-build-all — {self._started_at}\n")

        w = 10   # column width for alignment
        lines.append(f"  {'Scanned:':<{w}} {self.n_scanned:>4}")
        lines.append(f"  {'Rendered:':<{w}} {self.n_rendered:>4}")
        lines.append(f"  {'Skipped:':<{w}} {self.n_skipped:>4}  (up to date)")
        lines.append(f"  {'Failed:':<{w}} {self.n_failed:>4}")
        lines.append(f"  {'Moved:':<{w}} {self.n_moved:>4}  (status change)")

        failed = [r for r in self._results if r.outcome == RenderIndex.OUTCOME_FAILED]
        if failed:
            lines.append("\nFAILED:")
            for r in failed:
                lines.append(f"  {r.rel_path}")
                lines.append(f"    Error: {r.error}")

        moved = [r for r in self._results if r.outcome == RenderIndex.OUTCOME_MOVED]
        if moved:
            lines.append("\nMOVED:")
            for r in moved:
                lines.append(f"  {r.rel_path}")
                lines.append(f"    {r.old_status} → {r.new_status}")

        per_doc_warns = [w for r in self._results for w in r.warnings]
        all_warnings = self._scan_warnings + per_doc_warns
        if all_warnings:
            lines.append("\nWARNINGS:")
            for w in all_warnings:
                lines.append(f"  {w}")

        lines.append("")
        return "\n".join(lines)

    def print(self) -> None:
        """Print the report to stdout."""
        print(self.format(), flush=True)

    def write(self, path: str) -> None:
        """Write the report to a file (in addition to stdout)."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.format())
