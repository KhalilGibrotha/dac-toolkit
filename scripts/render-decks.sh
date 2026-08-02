#!/usr/bin/env bash
# render-decks.sh — build + visual-QA loop for Quarto (.qmd) presentation decks
#
# Renders Markdown-source decks to PowerPoint (.pptx) via Quarto, and can
# export per-slide PNGs for visual review. Works against any content repo:
# the toolkit owns the rendering; the content repo owns its templates and
# .qmd sources.
#
# Usage:
#   bash scripts/render-decks.sh [CONTENT_DIR]                # render all decks
#   bash scripts/render-decks.sh [CONTENT_DIR] deck.qmd       # render one deck
#   bash scripts/render-decks.sh [CONTENT_DIR] --qa [deck]    # render, then export per-slide PNGs
#   bash scripts/render-decks.sh --smoke                      # render the bundled example (self-test)
#
# CONTENT_DIR defaults to $WORKSPACE or the current directory. Decks are read
# from CONTENT_DIR/presentations/*.qmd; outputs land in
# CONTENT_DIR/presentations/exports/. QA images go to $TMPDIR/deck-qa/<deck>/
# — never into a repo.
#
# Requires: quarto, and (for executable Python chunks) python with jupyter +
# matplotlib. QA additionally requires LibreOffice (soffice) and pymupdf; if
# soffice is absent, rendering still works and --qa reports the gap.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
QA_ROOT="${TMPDIR:-/tmp}/deck-qa"

find_bin() { # name, extra candidate paths...
    local name="$1"; shift
    if command -v "$name" >/dev/null 2>&1; then command -v "$name"; return 0; fi
    for c in "$@"; do [ -x "$c" ] && { echo "$c"; return 0; }; done
    return 1
}

QUARTO="$(find_bin quarto \
    "${LOCALAPPDATA:-}/Apps/Quarto/bin/quarto.exe" \
    "${LOCALAPPDATA:-}/Programs/Quarto/bin/quarto.exe" \
    "/c/Program Files/Quarto/bin/quarto.exe" \
    "/usr/local/bin/quarto" "/opt/quarto/bin/quarto")" \
    || { echo "ERROR: quarto not found on PATH" >&2; exit 1; }

find_soffice() {
    find_bin soffice \
        "/c/Program Files/LibreOffice/program/soffice.exe" \
        "/usr/bin/soffice" "/usr/local/bin/soffice" \
        /usr/lib64/libreoffice/program/soffice \
        /opt/libreoffice*/program/soffice
}

qa_export() { # pptx path -> per-slide PNGs + a dark contact-sheet gallery
    local pptx="$1"
    local name; name="$(basename "$pptx" .pptx)"
    local outdir="$QA_ROOT/$name"
    local soffice
    if ! soffice="$(find_soffice)"; then
        echo "NOTE: LibreOffice (soffice) not found — skipping QA PNG export for $name." >&2
        echo "      The .pptx rendered fine; open it directly, or install LibreOffice for the gallery." >&2
        return 0
    fi
    mkdir -p "$outdir"
    rm -f "$outdir"/*.png "$outdir"/*.pdf
    "$soffice" --headless --convert-to pdf --outdir "$outdir" "$pptx" >/dev/null 2>&1 || true
    # LibreOffice's first headless run after a cold start can bootstrap its
    # profile and exit without converting — retry once if the PDF is missing.
    if [ ! -f "$outdir/$name.pdf" ]; then
        sleep 2
        "$soffice" --headless --convert-to pdf --outdir "$outdir" "$pptx" >/dev/null 2>&1
    fi
    [ -f "$outdir/$name.pdf" ] || { echo "ERROR: PDF conversion failed for $pptx" >&2; exit 1; }
    python - "$outdir/$name.pdf" "$outdir" <<'PYEOF'
import sys, pymupdf
pdf, outdir = sys.argv[1], sys.argv[2]
doc = pymupdf.open(pdf)
names = []
for i, page in enumerate(doc, 1):
    n = f"slide-{i:02d}.png"
    page.get_pixmap(dpi=120).save(f"{outdir}/{n}")
    names.append(n)
cards = chr(10).join(
    f'<figure><a href="{n}"><img src="{n}" loading="lazy"></a>'
    f"<figcaption>{i:02d}</figcaption></figure>"
    for i, n in enumerate(names, 1))
html = ("<!doctype html><meta charset='utf-8'><title>Deck QA floor</title>"
 "<style>body{background:#0E1116;color:#F5F7FA;font:14px Consolas,monospace;margin:24px}"
 "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:18px}"
 "img{width:100%;border:1px solid #28313D;border-radius:4px}"
 "figure{margin:0}figcaption{color:#57C88A;padding:4px 2px}</style>"
 f"<h1 style='font-size:16px'>QA floor — inspect every slide for overflow, contrast, clutter</h1><main>{cards}</main>")
with open(f"{outdir}/index.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"{len(doc)} slides -> {outdir}")
print(f"floor: {outdir}/index.html")
PYEOF
}

render_dir() { # render every non-underscore deck in a presentations dir
    local pres="$1"
    [ -d "$pres" ] || { echo "ERROR: no presentations/ dir at $pres" >&2; exit 1; }
    shopt -s nullglob
    local found=0
    for q in "$pres"/*.qmd; do
        case "$(basename "$q")" in _*) continue;; esac
        found=1
        echo "=== rendering $(basename "$q") ==="
        ( cd "$pres" && "$QUARTO" render "$(basename "$q")" --to pptx )
    done
    [ "$found" = 1 ] || echo "No decks found in $pres (underscore-prefixed files are skipped)."
}

smoke() { # render the toolkit's bundled example and confirm a figure embedded
    echo "=== smoke test: rendering bundled example deck ==="

    # Render a writable COPY, never in place. In the published image the bundled
    # deck lives under /opt/dac-toolkit, owned by root, while the container runs
    # as uid 1001 -- so an in-place render dies with PermissionDenied writing the
    # intermediate .quarto_ipynb before Quarto reaches the renderer at all. The
    # shipped self-test was therefore unusable for the shipped user, which the
    # old Release QA step hid by rendering its own throwaway deck in /tmp.
    #
    # The whole presentations tree is copied because the deck resolves
    # _quarto.yml, templates/ (reference-doc), assets/ (matplotlib palette) and
    # themes/ relative to its own directory.
    local work
    work="$(mktemp -d)"
    trap 'rm -rf "$work"' RETURN
    cp -r "$TOOLKIT_ROOT/presentations/." "$work/"

    ( cd "$work" && "$QUARTO" render example_deck.qmd --to pptx )
    local out="$work/exports/example_deck.pptx"
    [ -f "$out" ] || { echo "SMOKE FAIL: pptx not produced" >&2; exit 1; }
    if python - "$out" <<'PYEOF'
import sys, zipfile
media = [f for f in zipfile.ZipFile(sys.argv[1]).namelist() if f.startswith("ppt/media/")]
sys.exit(0 if media else 1)
PYEOF
    then echo "SMOKE: figure rendered into pptx media"; else echo "SMOKE FAIL: no figure image in pptx" >&2; exit 1; fi
    qa_export "$out"
    echo "SMOKE PASS"
}

# ── argument parsing ────────────────────────────────────────────────────────
if [ "${1:-}" = "--smoke" ]; then smoke; exit 0; fi

CONTENT_DIR="${1:-${WORKSPACE:-$(pwd)}}"
# If the first arg looks like a flag or a .qmd, treat CONTENT_DIR as the default.
case "${1:-}" in
    --qa|*.qmd) CONTENT_DIR="${WORKSPACE:-$(pwd)}" ;;
    *) shift 2>/dev/null || true ;;
esac
PRES_DIR="$CONTENT_DIR/presentations"

case "${1:-}" in
    --qa)
        shift 2>/dev/null || true
        target="${1:-}"
        if [ -n "$target" ]; then
            ( cd "$PRES_DIR" && "$QUARTO" render "$(basename "$target")" --to pptx )
            qa_export "$PRES_DIR/exports/$(basename "${target%.qmd}").pptx"
        else
            render_dir "$PRES_DIR"
            shopt -s nullglob
            for p in "$PRES_DIR"/exports/*.pptx; do qa_export "$p"; done
        fi ;;
    "" )
        render_dir "$PRES_DIR" ;;
    *.qmd)
        ( cd "$PRES_DIR" && "$QUARTO" render "$(basename "$1")" --to pptx ) ;;
    *)
        echo "ERROR: unrecognized argument: $1" >&2; exit 1 ;;
esac
