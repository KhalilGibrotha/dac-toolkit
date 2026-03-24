"""
batch_output.py — Status-based output folder management and file naming.

Rendered DOCX files are organised into subfolders of export_root by document
status. When a document's status changes between renders, the old file is
removed from the previous folder before the new one is written.

Output folder structure
───────────────────────
    exports/
      Draft/
      In-Review/
      Accepted/
      Rejected/
      Proposed/
      Informational/
      Retired/
      .render-index.yml

Folder names are derived from status values by replacing spaces with hyphens
(e.g. "In Review" → "In-Review"). This is consistent and reversible.

Output file naming
──────────────────
    {doc_type}_{domain}_{descriptor}_v{version}.docx

    The filename is derived from the source .md filename, not the front matter,
    so it follows the established file naming convention automatically:

        docs/overview_segmentation_poc-architecture.md
        → exports/Draft/overview_segmentation_poc-architecture_v0.3.docx

    The version suffix is appended before the extension.

Status change handling
──────────────────────
    1. Caller passes the old output path (from the index).
    2. remove_old_output() deletes it if it exists; warns if missing.
    3. Caller renders to resolve_output_path() and updates the index.
"""

import os
from typing import Optional


def status_to_folder(status: str) -> str:
    """
    Convert a status value to the corresponding export subfolder name.

    "In Review" → "In-Review"
    "Draft"     → "Draft"
    """
    return status.replace(' ', '-')


def resolve_output_path(export_root: str, md_path: str, status: str, version: str) -> str:
    """
    Compute the full output path for a rendered DOCX.

    Args:
        export_root: absolute path to the export root directory.
        md_path:     absolute path to the source .md file.
        status:      document status (used for subfolder selection).
        version:     document version (appended to filename).

    Returns:
        Absolute path where the DOCX should be saved, e.g.:
        /repo/exports/Draft/overview_aap_architecture_v0.3.docx
    """
    stem = os.path.splitext(os.path.basename(md_path))[0]
    folder = os.path.join(export_root, status_to_folder(status))
    filename = f"{stem}_v{version}.docx"
    return os.path.join(folder, filename)


def ensure_output_dir(output_path: str) -> None:
    """
    Create the parent directory of output_path if it does not exist.
    Idempotent — safe to call even if the directory already exists.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)


def remove_old_output(old_output: Optional[str], rel_path: str) -> Optional[str]:
    """
    Remove the previously rendered DOCX when a document's status has changed.

    Args:
        old_output: absolute or relative path to the old DOCX file (from index),
                    or None if there is nothing to remove.
        rel_path:   source document rel_path, used only for warning messages.

    Returns:
        A warning string if the file was expected but missing, otherwise None.
    """
    if not old_output:
        return None

    if os.path.isfile(old_output):
        try:
            os.remove(old_output)
        except OSError as e:
            return f"WARN  could not remove old output for {rel_path}: {e}"
        return None
    else:
        return (
            f"WARN  old output not found at expected path for {rel_path}: {old_output} "
            f"(may have been manually deleted — continuing)"
        )
