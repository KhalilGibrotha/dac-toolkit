"""
batch_config.py — Config file loader and schema validator for docx-build-all.

Loads docx-build.yml from the current directory (or walks up to the repo root),
validates the schema, and returns a structured BatchConfig object.

Config schema (docx-build.yml):

    export_root: exports/          # required — root folder for DOCX output
    org: vars/org.yaml             # optional — org identity YAML (same as --org flag)

    scan:                          # required — at least one entry
      - docs/
      - governance/
      - references/
      - patterns/
      - initiatives/

    exclude:                       # optional — paths to skip even if under scan
      - templates/
      - archive/

    options:                       # optional — all keys have defaults
      skip_retired: true           # default: true  — skip status: Retired docs
      skip_informational: false    # default: false — render status: Informational docs

Paths in scan and exclude are resolved relative to the config file's directory.
"""

import os
from dataclasses import dataclass
from typing import Optional

import yaml


def _parse_bool(value) -> bool:
    """Parse a YAML value as boolean, handling quoted strings like 'false'."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes')
    return bool(value)


class ConfigError(Exception):
    """Raised when the config file is missing, unreadable, or fails schema validation."""


@dataclass
class BatchOptions:
    skip_retired: bool = True
    skip_informational: bool = False


@dataclass
class BatchConfig:
    export_root: str          # resolved absolute path
    scan: list[str]           # resolved absolute paths
    exclude: list[str]        # resolved absolute paths
    org: Optional[str]        # resolved absolute path, or None
    options: BatchOptions
    config_path: str          # absolute path to the config file itself
    config_dir: str           # directory containing the config file


def find_config(start_dir: str, filename: str = "docx-build.yml") -> Optional[str]:
    """
    Walk up the directory tree from start_dir looking for filename.

    Returns the absolute path to the config file, or None if not found before
    reaching the filesystem root.
    """
    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, filename)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:       # filesystem root reached
            return None
        current = parent


def load_config(path: Optional[str] = None) -> BatchConfig:
    """
    Load and validate docx-build.yml.

    Args:
        path: explicit path to the config file, or None to search upward from CWD.

    Returns:
        BatchConfig — validated configuration object with all paths resolved to absolute.

    Raises:
        ConfigError: config file not found, unreadable, or fails schema validation.
    """
    if path is None:
        path = find_config(os.getcwd())
        if path is None:
            raise ConfigError(
                "No docx-build.yml found. "
                "Run from the repo root or pass --config <path>."
            )
    else:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f) or {}
    except OSError as e:
        raise ConfigError(f"Cannot read config file {path}: {e}") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML parse error in {path}: {e}") from e

    config_dir = os.path.dirname(path)
    errors: list[str] = []

    # ── Required fields ───────────────────────────────────────────────────────

    export_root_raw = raw.get('export_root')
    if not export_root_raw:
        errors.append("  - 'export_root' is required (e.g. export_root: exports/)")
    else:
        export_root = os.path.normpath(os.path.join(config_dir, str(export_root_raw)))

    scan_raw = raw.get('scan')
    if not scan_raw or not isinstance(scan_raw, list):
        errors.append("  - 'scan' is required and must be a non-empty list of folder paths")
    else:
        scan = [os.path.normpath(os.path.join(config_dir, str(s))) for s in scan_raw]

    if errors:
        raise ConfigError(
            f"Invalid config file: {path}\n" + "\n".join(errors)
        )

    # ── Optional fields ───────────────────────────────────────────────────────

    exclude_raw = raw.get('exclude') or []
    if isinstance(exclude_raw, str):
        exclude_raw = [exclude_raw]    # single string → one-element list
    exclude = [os.path.normpath(os.path.join(config_dir, str(e))) for e in exclude_raw]

    org_raw = raw.get('org')
    if org_raw:
        org_resolved = os.path.normpath(os.path.join(config_dir, str(org_raw)))
        if not os.path.isfile(org_resolved):
            raise ConfigError(
                f"org file specified in config not found: {org_resolved}"
            )
        org: Optional[str] = org_resolved
    else:
        org = None

    raw_opts = raw.get('options') or {}
    options = BatchOptions(
        skip_retired=_parse_bool(raw_opts.get('skip_retired', True)),
        skip_informational=_parse_bool(raw_opts.get('skip_informational', False)),
    )

    return BatchConfig(
        export_root=export_root,
        scan=scan,
        exclude=exclude,
        org=org,
        options=options,
        config_path=path,
        config_dir=config_dir,
    )
