"""
batch_output.py — Output folder management and file naming.

Two layouts are supported, selected by the 'layout' key in docx-build.yml.

    status  (default)  exports/<Status>/<name>_v<version>.docx
                       Groups by review state; the path encodes status and
                       version, so both change as a document progresses.

    mirror             exports/<source path>/<name>.docx
                       Reproduces the source tree. No status folder, no version
                       suffix - the path is stable across promotions and version
                       bumps, so syncing the export folder to a document library
                       updates files in place instead of leaving duplicates.

The rest of this docstring describes the 'status' layout.

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


def resolve_output_path(
    export_root: str,
    md_path: str,
    status: str,
    version: str,
    layout: str = 'status',
    content_root: Optional[str] = None,
) -> str:
    """
    Compute the full output path for a rendered DOCX.

    Args:
        export_root:  absolute path to the export root directory.
        md_path:      absolute path to the source .md file.
        status:       document status (subfolder selection in 'status' layout).
        version:      document version (filename suffix in 'status' layout).
        layout:       'status' (default) or 'mirror'. See module docstring.
        content_root: repo root the source tree is relative to. Required for
                      'mirror'; unused by 'status'.

    Returns:
        Absolute path where the DOCX should be saved, e.g.
        status: /repo/exports/Draft/overview_aap_architecture_v0.3.docx
        mirror: /repo/exports/initiatives/aap/overview_aap_architecture.docx

    Raises:
        ValueError: unknown layout, or 'mirror' without content_root.
    """
    stem = os.path.splitext(os.path.basename(md_path))[0]

    if layout == 'status':
        folder = os.path.join(export_root, status_to_folder(status))
        return os.path.join(folder, f"{stem}_v{version}.docx")

    if layout != 'mirror':
        raise ValueError(f"unknown layout: {layout!r}")
    if not content_root:
        raise ValueError("layout 'mirror' requires content_root")

    # Mirror deliberately omits both the status folder and the version suffix.
    # The point of this layout is a path that does NOT change when a document is
    # promoted or revised, so that syncing the export folder updates files in
    # place rather than accumulating relocated or renamed duplicates.
    rel_dir = os.path.relpath(os.path.dirname(md_path), content_root)
    if rel_dir == os.curdir or rel_dir.startswith(os.pardir):
        # Source sits at, or outside, the content root. Fall back to flat rather
        # than writing outside export_root.
        rel_dir = ''
    return os.path.join(export_root, rel_dir, f"{stem}.docx")


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
