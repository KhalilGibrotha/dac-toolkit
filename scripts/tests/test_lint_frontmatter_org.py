"""
tests/test_lint_frontmatter_org.py — org-supplied front-matter defaults.

`owner:` may be omitted from a document when org.yaml supplies it, because
the builder resolves that default and CI rejecting the same document would
put rendering and linting in disagreement.

Two failure modes are pinned here:

  * The org file is auto-detected, so every entry point behaves the same
    without each one remembering a flag. A flag only some callers pass
    reproduces the inconsistency this feature exists to remove.
  * A malformed org file degrades to "no defaults" rather than crashing.
    Valid YAML that parses to a list or a scalar is useless here but must
    not take the linter down - it validates documents, not org files.

Runs the script as a subprocess, so what is tested is what CI invokes.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "lint-frontmatter.py"

DOC_WITHOUT_OWNER = """---
title: "Test Document"
doc_type: "reference"
domain: "automation"
department: "Infrastructure & Operations"
status: "Draft"
version: "0.1"
date: "2026-08-05"
author: "Alex Gambino"
---

# Test Document

This reference exists to exercise owner defaulting.
"""


def _run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(root), *extra],
        capture_output=True, text=True,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "doc.md").write_text(DOC_WITHOUT_OWNER, encoding="utf-8")
    (tmp_path / "dac").mkdir()
    return tmp_path


def _write_org(repo: Path, text: str) -> None:
    (repo / "dac" / "org.yaml").write_text(text, encoding="utf-8")


def test_owner_required_when_no_org_file(repo):
    result = _run(repo)
    assert result.returncode == 1
    assert "owner" in result.stdout


def test_org_file_is_auto_detected(repo):
    # No --org flag. The Dev Spaces task, the README command, and a developer
    # typing it by hand all invoke the script this way.
    _write_org(repo, 'org:\n  owner: "Some Team"\n')
    assert _run(repo).returncode == 0


def test_flat_org_file_without_org_key(repo):
    _write_org(repo, 'owner: "Some Team"\n')
    assert _run(repo).returncode == 0


def test_blank_owner_is_not_a_default(repo):
    # Present but empty supplies nothing, so the document is still missing it.
    _write_org(repo, 'org:\n  owner: ""\n')
    assert _run(repo).returncode == 1


@pytest.mark.parametrize(
    ("label", "content"),
    [
        ("list", "- one\n- two\n"),
        ("scalar", "just-a-string\n"),
        ("empty", ""),
        ("malformed", "org:\n  owner: [unclosed\n"),
    ],
)
def test_unusable_org_file_degrades_rather_than_crashing(repo, label, content):
    _write_org(repo, content)
    result = _run(repo)
    # Exit 1 is the document failing validation, which is correct - no default
    # was available. Exit 2 or a traceback would be the linter itself dying.
    assert result.returncode == 1, f"{label}: {result.stderr}"
    assert "Traceback" not in result.stderr, f"{label}: linter crashed"


def test_explicit_org_path_overrides_detection(repo):
    _write_org(repo, 'org:\n  owner: ""\n')          # would not satisfy it
    other = repo / "elsewhere.yaml"
    other.write_text('org:\n  owner: "Other Team"\n', encoding="utf-8")
    assert _run(repo, "--org", str(other)).returncode == 0


def test_missing_explicit_org_path_is_an_error_not_a_shrug(repo):
    # Silently ignoring a path the caller asked for would hide a typo in CI
    # config as a lint pass. Exit 1 matches this script's existing convention
    # for usage errors (see the not-a-directory check); stderr is what
    # distinguishes a config mistake from a document failure.
    result = _run(repo, "--org", str(repo / "nope.yaml"))
    assert result.returncode != 0
    assert "not found" in result.stderr
    assert "Checked" not in result.stdout, "should fail before scanning"
