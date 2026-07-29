#!/usr/bin/env bash
# vale-bootstrap.sh — Copy pre-baked Vale style packages into a content workspace.
#
# During docker build, vale sync downloads RedHat + write-good packages into
# /opt/vale-styles.  At container start this script copies them into the
# workspace's styles directory so Vale works fully offline. The destination
# is read from the repo's own .vale.ini StylesPath, so this works for the
# canonical dac/vale/styles layout and for legacy .vale/styles alike.
#
# Usage:
#   bash vale-bootstrap.sh [CONTENT_DIR]
#
# CONTENT_DIR defaults to $WORKSPACE or the current directory.

set -euo pipefail

CONTENT_DIR="${1:-${WORKSPACE:-$(pwd)}}"
PREBAKED="/opt/vale-styles"

if [[ ! -f "$CONTENT_DIR/.vale.ini" ]]; then
    echo "vale-bootstrap: no .vale.ini found in $CONTENT_DIR — skipping"
    exit 0
fi

if [[ ! -d "$PREBAKED" ]]; then
    echo "vale-bootstrap: no pre-baked styles at $PREBAKED — skipping"
    exit 0
fi

# Resolve StylesPath from .vale.ini rather than assuming a layout. Copying to
# the wrong path leaves BasedOnStyles unresolvable in an offline workspace,
# which surfaces as a confusing "style not found" rather than a missing file.
STYLES_REL="$(sed -n 's/^[[:space:]]*StylesPath[[:space:]]*=[[:space:]]*//p'     "$CONTENT_DIR/.vale.ini" | head -n 1 | tr -d '')"
STYLES_REL="${STYLES_REL:-.vale/styles}"
STYLES_DIR="$CONTENT_DIR/$STYLES_REL"

mkdir -p "$STYLES_DIR"
if [ -n "$(ls -A "$PREBAKED")" ]; then
    cp -rn "$PREBAKED"/* "$STYLES_DIR/"
    echo "vale-bootstrap: pre-baked styles copied to $STYLES_DIR/"
else
    echo "vale-bootstrap: no styles found in $PREBAKED — skipping"
fi
