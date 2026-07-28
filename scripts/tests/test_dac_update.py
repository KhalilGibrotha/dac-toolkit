"""
tests/test_dac_update.py — Tests for the dac-update conffile-model tool.

Runs the script as a real subprocess against a fake starter tree and a fake
adopter repo, so nothing here depends on the baked toolkit image. Covers the
four conffile transitions (skip / replace / keep+new / install) plus the
Windows line-ending case that normalize()/nhash() exist to handle.

Run with: python -m pytest scripts/tests/ from the repo root.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS_DIR / "dac-update"

sys.path.insert(0, str(SCRIPTS_DIR))
from dac_common import atomic_write_json, nhash  # noqa: E402

VALE_V1 = "StylesPath = vale\nMinAlertLevel = warning\n"   # oldest shipped revision
VALE_V2 = "StylesPath = vale\nMinAlertLevel = suggestion\n"  # current stock revision
DOCX_BUILD_STOCK = "org: dac/org.yaml.example\n"
NEWFILE_STOCK = "added: true\n"
RETIRED_STOCK = "this file was managed once, not anymore\n"  # dropped from current stock


def _write(path: Path, content: str, newline: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.replace("\n", newline).encode("utf-8"))


def _sha_of(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def starter(tmp_path):
    """A fake starter tree: files/, manifest.json, stock-hashes.json."""
    root = tmp_path / "starter"
    files = root / "files"

    _write(files / ".vale.ini", VALE_V2)
    _write(files / "dac" / "docx-build.yml", DOCX_BUILD_STOCK)
    _write(files / "dac" / "newfile.yml", NEWFILE_STOCK)

    history = {
        ".vale.ini": [_sha_of(VALE_V1), nhash(files / ".vale.ini")],
        "dac/docx-build.yml": [nhash(files / "dac" / "docx-build.yml")],
        # dac/newfile.yml intentionally absent from history: it is new to the
        # managed set as of this stock revision, never shipped before.
        # dac/retired.yml: shipped once, then dropped from the managed set.
        # It stays in files/ history but has no file under files/ -- exactly
        # what a starter revision that removes a managed file looks like.
        "dac/retired.yml": [_sha_of(RETIRED_STOCK)],
    }
    atomic_write_json(root / "stock-hashes.json", history)
    atomic_write_json(root / "manifest.json", {
        "starter_version": "v2.0.0",
        "engine_image": "ghcr.io/example/dac-toolkit@sha256:test",
        "files": {
            ".vale.ini": nhash(files / ".vale.ini"),
            "dac/docx-build.yml": nhash(files / "dac" / "docx-build.yml"),
            "dac/newfile.yml": nhash(files / "dac" / "newfile.yml"),
        },
    })
    return root


@pytest.fixture
def repo(tmp_path):
    """A fake adopter repo that has already run dac-init once."""
    r = tmp_path / "repo"
    (r / ".git").mkdir(parents=True)
    atomic_write_json(r / "dac" / ".dac-manifest.json", {
        "dac_manifest_version": 1,
        "starter_version": "v1.0.0",
        "engine_image": "ghcr.io/example/dac-toolkit@sha256:old",
        "installed": "2026-01-01",
        "files": {},
    })
    return r


def _run(repo_path: Path, starter_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(repo_path),
         "--starter-dir", str(starter_path), *extra],
        capture_output=True, text=True, check=False,
    )


# ── setup / precondition checks ────────────────────────────────────────────

def test_fails_clearly_without_manifest(tmp_path, starter):
    repo_no_manifest = tmp_path / "bare-repo"
    (repo_no_manifest / ".git").mkdir(parents=True)

    result = _run(repo_no_manifest, starter)

    assert result.returncode != 0
    assert "dac-init first" in result.stderr


def test_fails_clearly_without_starter_tree(tmp_path, repo):
    result = _run(repo, tmp_path / "no-such-starter")

    assert result.returncode != 0
    assert "starter tree not found" in result.stderr


# ── the four conffile transitions ──────────────────────────────────────────

def test_skip_when_already_current(repo, starter):
    _write(repo / ".vale.ini", VALE_V2)
    before = (repo / ".vale.ini").read_bytes()

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "skip      .vale.ini  (already current)" in result.stdout
    assert (repo / ".vale.ini").read_bytes() == before
    assert not (repo / ".vale.ini.new").exists()


def test_replace_unmodified_older_revision(repo, starter):
    _write(repo / ".vale.ini", VALE_V1)

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "replace   .vale.ini" in result.stdout
    assert (repo / ".vale.ini").read_bytes() == VALE_V2.encode("utf-8")
    assert not (repo / ".vale.ini.new").exists()


def test_replace_recognizes_crlf_as_unmodified_not_customized(repo, starter):
    """The whole point of normalize()/nhash(): a Windows checkout with CRLF
    line endings on an otherwise-untouched stock file must NOT be treated as
    locally customized."""
    _write(repo / ".vale.ini", VALE_V1, newline="\r\n")

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "replace   .vale.ini" in result.stdout
    assert "keep+new" not in result.stdout
    assert (repo / ".vale.ini").read_bytes() == VALE_V2.encode("utf-8")
    assert not (repo / ".vale.ini.new").exists()


def test_keep_new_for_locally_customized_file(repo, starter):
    _write(repo / "dac" / "docx-build.yml", "org: something-i-changed.yaml\n")

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "keep+new  dac/docx-build.yml" in result.stdout
    assert (repo / "dac" / "docx-build.yml").read_bytes() == b"org: something-i-changed.yaml\n"
    new_file = repo / "dac" / "docx-build.yml.new"
    assert new_file.is_file()
    assert new_file.read_bytes() == DOCX_BUILD_STOCK.encode("utf-8")


def test_install_missing_file(repo, starter):
    assert not (repo / "dac" / "newfile.yml").exists()

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "install   dac/newfile.yml" in result.stdout
    installed = repo / "dac" / "newfile.yml"
    assert installed.is_file()
    assert installed.read_bytes() == NEWFILE_STOCK.encode("utf-8")


# ── dry-run ─────────────────────────────────────────────────────────────────

def test_dry_run_reports_but_writes_nothing(repo, starter):
    _write(repo / ".vale.ini", VALE_V1)                          # -> replace
    _write(repo / "dac" / "docx-build.yml", "org: mine.yaml\n")  # -> keep+new
    # dac/newfile.yml stays missing                               -> install
    manifest_before = (repo / "dac" / ".dac-manifest.json").read_bytes()

    result = _run(repo, starter, "--dry-run")

    assert result.returncode == 0
    assert "would replace   .vale.ini" in result.stdout
    assert "would install   dac/newfile.yml" in result.stdout
    assert "keep+new  dac/docx-build.yml" in result.stdout
    assert "Run without --dry-run to apply." in result.stdout

    # Nothing on disk changed.
    assert (repo / ".vale.ini").read_bytes() == VALE_V1.encode("utf-8")
    assert not (repo / "dac" / "docx-build.yml.new").exists()
    assert not (repo / "dac" / "newfile.yml").exists()
    assert (repo / "dac" / ".dac-manifest.json").read_bytes() == manifest_before


# ── manifest bookkeeping ────────────────────────────────────────────────────

def test_manifest_updated_after_real_run_preserves_installed_date(repo, starter):
    _write(repo / ".vale.ini", VALE_V1)

    result = _run(repo, starter)
    assert result.returncode == 0

    record = json.loads((repo / "dac" / ".dac-manifest.json").read_text(encoding="utf-8"))
    assert record["starter_version"] == "v2.0.0"
    assert record["engine_image"] == "ghcr.io/example/dac-toolkit@sha256:test"
    assert record["installed"] == "2026-01-01"          # original date preserved
    assert "updated" in record and record["updated"]
    assert record["files"][".vale.ini"] == nhash(starter / "files" / ".vale.ini")
    assert "dac/newfile.yml" in record["files"]          # touched during this run


def test_exit_code_is_zero_even_with_files_needing_review(repo, starter):
    """Locally customized files are a routine outcome, not an error."""
    _write(repo / "dac" / "docx-build.yml", "org: totally-different.yaml\n")

    result = _run(repo, starter)

    assert result.returncode == 0


def test_keep_new_not_recorded_in_manifest(repo, starter):
    """A keep+new file is customized by definition -- recording it as stock
    would tell the next dac-update run the opposite of what just happened."""
    _write(repo / "dac" / "docx-build.yml", "org: something-i-changed.yaml\n")

    result = _run(repo, starter)

    assert result.returncode == 0
    record = json.loads((repo / "dac" / ".dac-manifest.json").read_text(encoding="utf-8"))
    assert "dac/docx-build.yml" not in record["files"]


def test_keep_new_drops_stale_manifest_entry(repo, starter):
    """A prior run may have wrongly recorded the file as stock (the bug this
    fixes). Once the file is customized, that stale entry must go."""
    record_path = repo / "dac" / ".dac-manifest.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["files"]["dac/docx-build.yml"] = nhash(starter / "files" / "dac" / "docx-build.yml")
    atomic_write_json(record_path, record)
    _write(repo / "dac" / "docx-build.yml", "org: something-i-changed.yaml\n")

    result = _run(repo, starter)

    assert result.returncode == 0
    updated = json.loads(record_path.read_text(encoding="utf-8"))
    assert "dac/docx-build.yml" not in updated["files"]


# ── files that left the managed set ────────────────────────────────────────

def test_obsolete_file_removed_when_unmodified(repo, starter):
    _write(repo / "dac" / "retired.yml", RETIRED_STOCK)

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "remove    dac/retired.yml" in result.stdout
    assert not (repo / "dac" / "retired.yml").exists()

    record = json.loads((repo / "dac" / ".dac-manifest.json").read_text(encoding="utf-8"))
    assert "dac/retired.yml" not in record["files"]


def test_obsolete_file_kept_when_customized(repo, starter):
    _write(repo / "dac" / "retired.yml", "someone edited this before it was dropped\n")

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "obsolete  dac/retired.yml" in result.stdout
    assert (repo / "dac" / "retired.yml").read_bytes() == \
        b"someone edited this before it was dropped\n"

    record = json.loads((repo / "dac" / ".dac-manifest.json").read_text(encoding="utf-8"))
    assert "dac/retired.yml" not in record["files"]


def test_obsolete_reconciliation_is_dry_run_pure(repo, starter):
    _write(repo / "dac" / "retired.yml", RETIRED_STOCK)          # would be removed
    manifest_before = (repo / "dac" / ".dac-manifest.json").read_bytes()

    result = _run(repo, starter, "--dry-run")

    assert result.returncode == 0
    assert "would remove    dac/retired.yml" in result.stdout
    assert (repo / "dac" / "retired.yml").read_bytes() == RETIRED_STOCK.encode("utf-8")
    assert (repo / "dac" / ".dac-manifest.json").read_bytes() == manifest_before


def test_absent_obsolete_file_is_silently_skipped(repo, starter):
    """dac/retired.yml is in stock-hashes.json but was never installed in
    this repo -- nothing to reconcile, nothing to report."""
    result = _run(repo, starter)

    assert result.returncode == 0
    assert "retired.yml" not in result.stdout


# ── --help stands on its own ────────────────────────────────────────────────

def test_help_is_self_contained():
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                             capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert "--dry-run" in result.stdout
    assert "--path" in result.stdout
    assert "dac-init" in result.stdout          # states the precondition
    assert "skip" in result.stdout and "replace" in result.stdout
