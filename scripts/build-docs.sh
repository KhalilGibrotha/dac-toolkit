#!/usr/bin/env bash
# build-docs.sh — Full documentation pipeline (fully offline)
#
# 1. Render all Mermaid diagrams via render-diagrams.sh
# 2. Build DOCX for every Markdown file with YAML front matter
#
# Usage:
#   bash scripts/build-docs.sh [CONTENT_DIR]                  # build all
#   bash scripts/build-docs.sh [CONTENT_DIR] path/to/doc.md   # build one file
#
# CONTENT_DIR defaults to $WORKSPACE or the current directory.
# Looks for an org.yaml in CONTENT_DIR/vars/ for org identity overrides.
set -euo pipefail

CONTENT_DIR="${1:-${WORKSPACE:-$(pwd)}}"
shift 2>/dev/null || true

EXPORTS="$CONTENT_DIR/exports"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Look for logo and org config in the content repo
LOGO="$CONTENT_DIR/assets/logo/logo.png"
ORG_YAML="$CONTENT_DIR/vars/org.yaml"

mkdir -p "$EXPORTS"

# ── Phase 1: Render diagrams ────────────────────────────────────────────────
echo "=== Phase 1: Rendering diagrams ==="
bash "$SCRIPT_DIR/render-diagrams.sh" "$CONTENT_DIR"

# ── Phase 2: Build DOCX documents ───────────────────────────────────────────
echo ""
echo "=== Phase 2: Building DOCX documents ==="

built=0
skipped=0

logo_args=()
if [[ -f "$LOGO" ]]; then
  logo_args=(--logo "$LOGO")
fi

org_args=()
if [[ -f "$ORG_YAML" ]]; then
  org_args=(--org "$ORG_YAML")
fi

build_one() {
  local md_file="$1"
  # Only process files with YAML front matter (starts with ---)
  if ! head -1 "$md_file" | grep -q '^---$'; then
    skipped=$((skipped + 1))
    return
  fi

  # Mirror the source tree under exports/ rather than flattening it into the
  # filename. This keeps the published set copyable as a folder: the structure
  # matches the repo, and re-copying updates files in place instead of leaving
  # renamed duplicates behind.
  local rel_path="${md_file#"$CONTENT_DIR"/}"
  local out_rel="${rel_path%.md}.docx"
  local out_path="$EXPORTS/$out_rel"

  mkdir -p "$(dirname "$out_path")"
  echo "  Building: $rel_path -> exports/$out_rel"
  docx-build "$md_file" "${logo_args[@]}" "${org_args[@]}" --output "$out_path"
  built=$((built + 1))
}

if [[ $# -gt 0 ]]; then
  # Build a specific file
  build_one "$1"
else
  # Which top-level directories carry publishable content is a property of the
  # content repo, not of this engine. Override with DAC_DOC_DIRS (space
  # separated) to publish a different set without editing the toolkit.
  # Directories that do not exist are skipped silently.
  DOC_DIRS="${DAC_DOC_DIRS:-docs initiatives patterns governance decisions references}"

  search_dirs=()
  for d in $DOC_DIRS; do
    [[ -d "$CONTENT_DIR/$d" ]] && search_dirs+=("$CONTENT_DIR/$d")
  done

  if [[ ${#search_dirs[@]} -eq 0 ]]; then
    echo "  No content directories found under $CONTENT_DIR (looked for: $DOC_DIRS)"
  else
    # Build all content Markdown files (skip READMEs and archived material)
    while IFS= read -r -d '' md_file; do
      build_one "$md_file"
    done < <(find "${search_dirs[@]}" \
      -name '*.md' -not -name 'README.md' \
      -not -path '*/.git/*' -not -path '*/archive/*' \
      -print0 2>/dev/null)
  fi
fi

echo ""
echo "Build complete: $built documents built, $skipped files skipped"
