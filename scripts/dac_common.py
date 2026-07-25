"""Shared plumbing for dac-init / dac-update.

Design: docs/ design memo "dac-init / dac-update" (conffile hash-set model).
A file is STOCK if its normalized hash matches any revision ever shipped;
anything else is customized and is never overwritten. Normalization (BOM
strip, CRLF->LF, single trailing newline) keeps Windows checkouts from
classifying as customized. Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

# The managed set: root tool files by name, plus everything under dac/ except
# the files a team creates from examples (org identity, logo) and the record
# this tooling itself writes. Content folders are never managed.
MANAGED_ROOT_FILES = [
    "devfile.yaml",
    ".vale.ini",
    ".markdownlint.json",
    ".pre-commit-config.yaml",
    ".github/workflows/lint.yml",
    ".vscode/settings.json",
    ".vscode/extensions.json",
]
MANAGED_PREFIX = "dac/"
UNMANAGED = {
    "dac/org.yaml",
    "dac/logo.png",
    "dac/.dac-manifest.json",
}

REPO_MANIFEST = "dac/.dac-manifest.json"
STARTER_DEFAULT = os.environ.get("DAC_STARTER_DIR", "/opt/dac-toolkit/starter")


def normalize(data: bytes) -> bytes:
    """Normalize file content before hashing: strip UTF-8 BOM, CRLF->LF,
    exactly one trailing newline."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    data = data.replace(b"\r\n", b"\n")
    return data.rstrip(b"\n") + b"\n" if data else data


def nhash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(normalize(path.read_bytes())).hexdigest()


def managed_files(starter_files_dir: Path) -> list[str]:
    """Relative paths of every managed file present in a starter tree."""
    out = []
    for name in MANAGED_ROOT_FILES:
        if (starter_files_dir / name).is_file():
            out.append(name)
    dac_dir = starter_files_dir / "dac"
    if dac_dir.is_dir():
        for p in sorted(dac_dir.rglob("*")):
            if p.is_file():
                rel = p.relative_to(starter_files_dir).as_posix()
                if rel not in UNMANAGED:
                    out.append(rel)
    return out


def load_json(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".dac-tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, obj: dict) -> None:
    atomic_write_bytes(path, (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def looks_like_repo_root(path: Path) -> bool:
    return (path / ".git").exists()
