#!/usr/bin/env bash
# render-diagrams.sh — Render Mermaid diagrams to PNG (fully offline via mmdc)
#
# Usage:
#   bash scripts/render-diagrams.sh [CONTENT_DIR]
#
# CONTENT_DIR defaults to $WORKSPACE or the current directory.
# Searches CONTENT_DIR/diagrams/source/ for .mmd files and all .md files
# for ```mermaid fences.
#
# All rendering uses the bundled Chromium in the container — no network calls.
set -euo pipefail

CONTENT_DIR="${1:-${WORKSPACE:-$(pwd)}}"
DIAGRAMS_SRC="$CONTENT_DIR/diagrams/source"
DIAGRAMS_OUT="$CONTENT_DIR/diagrams/exported"
PUPPETEER_CFG="${PUPPETEER_CONFIG:-/opt/puppeteer-config.json}"

mkdir -p "$DIAGRAMS_OUT"

rendered=0
errors=0

# ── Phase 1: Standalone .mmd files ──────────────────────────────────────────
echo "=== Phase 1: Standalone .mmd files ==="

if compgen -G "$DIAGRAMS_SRC"/*.mmd > /dev/null 2>&1; then
  for mmd_file in "$DIAGRAMS_SRC"/*.mmd; do
    base=$(basename "$mmd_file" .mmd)
    out="$DIAGRAMS_OUT/${base}.png"
    echo "  Rendering $mmd_file -> $out"
    if mmdc -i "$mmd_file" -o "$out" -p "$PUPPETEER_CFG" --scale 2; then
      rendered=$((rendered + 1))
    else
      echo "  ERROR: Failed to render $mmd_file" >&2
      errors=$((errors + 1))
    fi
  done
else
  echo "  No .mmd files found in $DIAGRAMS_SRC"
fi

# ── Phase 2: Mermaid fences in Markdown ─────────────────────────────────────
echo ""
echo "=== Phase 2: Mermaid fences in Markdown files ==="

while IFS= read -r -d '' md_file; do
  # Check if file contains any mermaid fences before processing
  if ! grep -q '```mermaid' "$md_file" 2>/dev/null; then
    continue
  fi

  rel_path="${md_file#"$CONTENT_DIR"/}"
  safe_name=$(echo "$rel_path" | tr '/' '_' | sed 's/\.md$//')
  fence_idx=0

  # Extract each mermaid fence to a temp file and render it
  in_fence=false
  tmp_fence=$(mktemp)

  while IFS= read -r line; do
    if [[ "$in_fence" == false ]] && [[ "$line" == '```mermaid' ]]; then
      in_fence=true
      > "$tmp_fence"
    elif [[ "$in_fence" == true ]] && [[ "$line" == '```' ]]; then
      in_fence=false
      fence_idx=$((fence_idx + 1))
      out="$DIAGRAMS_OUT/${safe_name}_mermaid_${fence_idx}.png"
      echo "  Rendering fence #$fence_idx from $rel_path -> $out"
      if mmdc -i "$tmp_fence" -o "$out" -p "$PUPPETEER_CFG" --scale 2; then
        rendered=$((rendered + 1))
      else
        echo "  ERROR: Failed to render fence #$fence_idx from $rel_path" >&2
        errors=$((errors + 1))
      fi
    elif [[ "$in_fence" == true ]]; then
      echo "$line" >> "$tmp_fence"
    fi
  done < "$md_file"

  rm -f "$tmp_fence"
done < <(find "$CONTENT_DIR" -name '*.md' -not -path '*/.git/*' -not -path '*/node_modules/*' -print0)

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "Diagram rendering complete: $rendered rendered, $errors errors"
[[ $errors -eq 0 ]] || exit 1
