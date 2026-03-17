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

  local rel_path="${md_file#"$CONTENT_DIR"/}"
  local base
  base=$(basename "$md_file" .md)
  local dir_name
  dir_name=$(dirname "$rel_path" | tr '/' '_')
  local out_name="${dir_name}_${base}.docx"
  local out_path="$EXPORTS/$out_name"

  echo "  Building: $rel_path -> exports/$out_name"
  docx-build "$md_file" "${logo_args[@]}" "${org_args[@]}" --output "$out_path"
  built=$((built + 1))
}

if [[ $# -gt 0 ]]; then
  # Build a specific file
  build_one "$1"
else
  # Build all content Markdown files (skip READMEs)
  while IFS= read -r -d '' md_file; do
    build_one "$md_file"
  done < <(find \
    "$CONTENT_DIR/docs" \
    "$CONTENT_DIR/initiatives" \
    "$CONTENT_DIR/patterns" \
    "$CONTENT_DIR/governance" \
    "$CONTENT_DIR/decisions" \
    -name '*.md' -not -name 'README.md' -not -path '*/.git/*' \
    -print0 2>/dev/null)
fi

echo ""
echo "Build complete: $built documents built, $skipped files skipped"
