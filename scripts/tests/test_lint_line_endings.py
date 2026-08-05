"""
tests/test_lint_line_endings.py — Tests for the eol gate's text/binary
classification and its end-to-end behaviour against a real git index.

The classification has been wrong twice, in opposite directions: first it
read only the final suffix, so a renamed `*.yml.disabled` workflow silently
left the policy; then the fix matched ANY suffix, so `data.csv.gz` — a
genuinely binary gzip — was flagged as misclassified text. Both cases live
here so neither regression comes back.

Run with: python -m pytest scripts/tests/ from the repo root.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "lint-line-endings.py"


def _load():
    spec = importlib.util.spec_from_file_location("lint_line_endings", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        # Plain text extensions.
        ("scripts/foo.sh", True),
        ("docs/a.md", True),
        # Compound suffix whose FINAL part names nothing: the rename case.
        # This is the file the check originally exempted by reading only
        # the last suffix.
        (".github/workflows/example-caller.yml.disabled", True),
        ("notes.md.bak", True),
        # Jinja templates: .j2 is itself a text extension.
        ("roles/x/templates/config.yml.j2", True),
        # Extensionless text, known by basename.
        (".gitignore", True),
        (".gitattributes", True),
        ("Containerfile", True),
        ("Makefile", True),
        # Plain binary.
        ("img/logo.png", False),
        # No extension, unknown basename: cannot claim it is text.
        ("bin/tool", False),
        # Compound suffix whose FINAL part is a real binary format. The
        # inner .csv/.md describe wrapped content, not the file's encoding.
        ("data.csv.gz", False),
        ("archive.tar.gz", False),
        ("README.md.png", False),
        # A RENAMED binary: the final suffix names nothing, but the nearest
        # known suffix is binary. Right-to-left scanning is what gets this
        # right - final-suffix-only and any-suffix rules each fail one of
        # this row and the .yml.disabled row above.
        ("data.csv.gz.disabled", False),
        ("backup.tar.gz.old", False),
        # Case-insensitivity.
        ("REPORT.MD", True),
        ("PHOTO.PNG", False),
    ],
)
def test_looks_like_text(path, expected):
    assert MOD.looks_like_text(path) is expected


def _run_gate(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(repo)],
        capture_output=True, text=True,
    )


@pytest.fixture()
def scratch_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(tmp_path), "config", k, v], check=True)
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
    (tmp_path / "good.sh").write_text("#!/bin/bash\necho ok\n", newline="\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-qm", "base"], check=True
    )
    return tmp_path


def test_clean_tree_passes(scratch_repo: Path):
    result = _run_gate(scratch_repo)
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_committed_crlf_fails(scratch_repo: Path):
    # hash-object applies the eol filter unless told otherwise, which would
    # normalize the CRLF away and make this test prove nothing.
    bad = scratch_repo / "bad.sh"
    bad.write_bytes(b"#!/bin/bash\r\necho hi\r\n")
    blob = subprocess.run(
        ["git", "-C", str(scratch_repo), "hash-object", "-w",
         "--no-filters", "bad.sh"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "-C", str(scratch_repo), "update-index", "--add",
         "--cacheinfo", f"100644,{blob},bad.sh"],
        check=True,
    )
    result = _run_gate(scratch_repo)
    assert result.returncode == 1
    assert "CRLF" in result.stdout


def test_text_file_classified_binary_fails(scratch_repo: Path):
    # A lone CR inside the content makes git classify the file binary, at
    # which point every eol attribute is inert. The gate is the only thing
    # that catches this, which is the reason the gate exists.
    cr = scratch_repo / "cr.sh"
    cr.write_bytes(b'#!/bin/bash\necho "x" | tr -d \'\r\'\n')
    subprocess.run(["git", "-C", str(scratch_repo), "add", "cr.sh"], check=True)
    result = _run_gate(scratch_repo)
    assert result.returncode == 1
    assert "BINARY?" in result.stdout


def test_binary_wrapper_not_flagged(scratch_repo: Path):
    # A real gzip is i/-text and must NOT be reported: .gz names the format,
    # whatever the inner suffix claims.
    import gzip

    gz = scratch_repo / "data.csv.gz"
    gz.write_bytes(gzip.compress(b"a,b,c\n1,2,3\n"))
    subprocess.run(
        ["git", "-C", str(scratch_repo), "add", "data.csv.gz"], check=True
    )
    result = _run_gate(scratch_repo)
    assert result.returncode == 0, result.stdout
    assert "BINARY?" not in result.stdout
