#!/usr/bin/env bash
# vale-bootstrap.sh — Copy pre-baked Vale style packages into a content workspace.
#
# During docker build, vale sync downloads RedHat + write-good packages into
# /opt/vale-styles.  At container start this script copies them into the
# workspace's .vale/styles/ directory so Vale works fully offline.
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

mkdir -p "$CONTENT_DIR/.vale/styles"
if [ -n "$(ls -A "$PREBAKED")" ]; then
    cp -rn "$PREBAKED"/* "$CONTENT_DIR/.vale/styles/"
    echo "vale-bootstrap: pre-baked styles copied to $CONTENT_DIR/.vale/styles/"
else
    echo "vale-bootstrap: no styles found in $PREBAKED — skipping"
fi
