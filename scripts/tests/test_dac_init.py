"""
tests/test_dac_init.py — Tests for dac-init, focused on the manifest
bootstrap behavior: a repo whose managed files are already present (e.g.
created from the starter template) must still get a provenance record, or
dac-update has nothing to sync from and refuses to run.

Runs the script as a real subprocess against a fake starter tree and a fake
adopter repo, so nothing here depends on the baked toolkit image.

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
SCRIPT = SCRIPTS_DIR / "dac-init"

sys.path.insert(0, str(SCRIPTS_DIR))
from dac_common import atomic_write_json, nhash  # noqa: E402

VALE_STOCK = "StylesPath = vale\nMinAlertLevel = suggestion\n"
DOCX_BUILD_STOCK = "org: dac/org.yaml.example\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))


def _sha_of(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def starter(tmp_path):
    """A fake starter tree: files/, manifest.json, stock-hashes.json."""
    root = tmp_path / "starter"
    files = root / "files"

    _write(files / ".vale.ini", VALE_STOCK)
    _write(files / "dac" / "docx-build.yml", DOCX_BUILD_STOCK)

    history = {
        ".vale.ini": [nhash(files / ".vale.ini")],
        "dac/docx-build.yml": [nhash(files / "dac" / "docx-build.yml")],
    }
    atomic_write_json(root / "stock-hashes.json", history)
    atomic_write_json(root / "manifest.json", {
        "starter_version": "v2.0.0",
        "engine_image": "ghcr.io/example/dac-toolkit@sha256:test",
        "files": {
            ".vale.ini": nhash(files / ".vale.ini"),
            "dac/docx-build.yml": nhash(files / "dac" / "docx-build.yml"),
        },
    })
    return root


@pytest.fixture
def repo(tmp_path):
    """A bare adopter repo -- just a .git dir, nothing adopted yet."""
    r = tmp_path / "repo"
    (r / ".git").mkdir(parents=True)
    return r


def _run(repo_path: Path, starter_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(repo_path),
         "--starter-dir", str(starter_path), *extra],
        capture_output=True, text=True, check=False,
    )


# ── ordinary install path ───────────────────────────────────────────────────

def test_fresh_repo_installs_everything(repo, starter):
    result = _run(repo, starter)

    assert result.returncode == 0
    assert (repo / ".vale.ini").is_file()
    assert (repo / "dac" / "docx-build.yml").is_file()

    record = json.loads((repo / "dac" / ".dac-manifest.json").read_text(encoding="utf-8"))
    assert record["files"][".vale.ini"] == nhash(starter / "files" / ".vale.ini")
    assert record["files"]["dac/docx-build.yml"] == nhash(
        starter / "files" / "dac" / "docx-build.yml")


# ── the template-repo bootstrap gap this fixes ─────────────────────────────

def test_bootstrap_manifest_on_no_op(repo, starter):
    """A repo built from the dac-starter template already has every managed
    file, so dac-init installs 0 of them. It must still write a manifest --
    otherwise dac-update finds no dac/.dac-manifest.json and refuses to run,
    a dead end for exactly the repos that need it most.

    Mixes a file that matches stock untouched with one a team already
    customized: only the stock-matching one belongs in the provenance map."""
    _write(repo / ".vale.ini", VALE_STOCK)                        # unmodified stock
    _write(repo / "dac" / "docx-build.yml", "org: mine.yaml\n")   # customized

    result = _run(repo, starter)

    assert result.returncode == 0
    assert "0 installed" in result.stdout

    manifest_path = repo / "dac" / ".dac-manifest.json"
    assert manifest_path.is_file()
    record = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert record["files"][".vale.ini"] == nhash(starter / "files" / ".vale.ini")
    assert "dac/docx-build.yml" not in record["files"]
    assert "installed" in record and record["installed"]


def test_bootstrap_recognizes_older_stock_revision(repo, starter):
    """A present file matching an OLD stock revision, not the one just
    shipped, still counts as known stock rather than a customization."""
    old_vale = "StylesPath = vale\nMinAlertLevel = warning\n"
    history_path = starter / "stock-hashes.json"
    history = json.loads(history_path.read_text(encoding="utf-8"))
    history[".vale.ini"].insert(0, _sha_of(old_vale))
    atomic_write_json(history_path, history)

    _write(repo / ".vale.ini", old_vale)
    _write(repo / "dac" / "docx-build.yml", DOCX_BUILD_STOCK)

    result = _run(repo, starter)

    assert result.returncode == 0
    record = json.loads((repo / "dac" / ".dac-manifest.json").read_text(encoding="utf-8"))
    assert record["files"][".vale.ini"] == _sha_of(old_vale)


# ── dry-run ─────────────────────────────────────────────────────────────────

def test_dry_run_writes_no_manifest(repo, starter):
    _write(repo / ".vale.ini", VALE_STOCK)
    _write(repo / "dac" / "docx-build.yml", DOCX_BUILD_STOCK)

    result = _run(repo, starter, "--dry-run")

    assert result.returncode == 0
    assert not (repo / "dac" / ".dac-manifest.json").exists()


# ── idempotence / manifest bookkeeping ─────────────────────────────────────

def test_second_run_preserves_installed_date(repo, starter):
    first = _run(repo, starter)
    assert first.returncode == 0
    record_path = repo / "dac" / ".dac-manifest.json"
    installed_date = json.loads(record_path.read_text(encoding="utf-8"))["installed"]

    second = _run(repo, starter)

    assert second.returncode == 0
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["installed"] == installed_date


# ── --help stands on its own ────────────────────────────────────────────────

def test_help_is_self_contained():
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                             capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert "--dry-run" in result.stdout
    assert "--force" in result.stdout
    assert "manifest" in result.stdout.lower()
