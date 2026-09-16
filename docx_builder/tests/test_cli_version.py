"""The CLI reports the package version, and the package has one version source.

The literal in __init__.py read 1.0.0 through two releases whose headline
changes were inside this package. __version__ now comes from the installed
distribution metadata, which pyproject.toml feeds, and `docx-build --version`
prints it. Tests compare the CLI output to __version__ rather than to a
literal, so they hold in a source-tree run against an older installed
distribution as well as in CI, where the tree under test is what is installed.
"""
import re
import sys

import pytest

import docx_builder
from docx_builder.cli import main


def test_dunder_version_looks_like_a_release():
    # Either the installed distribution's version or the explicit
    # "not installed" marker; never a stale hand-maintained literal.
    assert re.fullmatch(r"\d+\.\d+\.\d+(\+uninstalled)?", docx_builder.__version__)


def test_cli_version_flag_prints_the_package_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["docx-build", "--version"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"docx-build {docx_builder.__version__}"
