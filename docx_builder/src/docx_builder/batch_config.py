"""
batch_config.py — Config file loader and schema validator for docx-build-all.

Loads docx-build.yml from the current directory (or walks up to the repo root),
validates the schema, and returns a structured BatchConfig object.

Config schema (docx-build.yml):

    export_root: exports/          # required — root folder for DOCX output
    org: vars/org.yaml             # optional — org identity YAML (same as --org flag)
    logo: assets/logo/logo.png     # optional — cover logo image (same as --logo flag)
    layout: status                 # optional — 'status' (default) or 'mirror'

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

Logo
────
    When the 'logo' key is absent, assets/logo/logo.png relative to the config
    file's directory is used if it exists — the same convention build-docs.sh
    and docx_manifest.py already auto-detect, so a repo that follows the
    recommended shape gets its logo on every cover without any config. When no
    logo is found the cover falls back to the org name as styled text.

Layout
──────
    status  (default)  exports/<Status>/<name>_v<version>.docx
                       Groups by review state. Good when the export set is read
                       as "what is accepted vs still in draft".

    mirror             exports/<source path>/<name>.docx
                       Reproduces the source tree, with no status folder and no
                       version in the filename. Use this when the export set is
                       synced to a document library as a folder: paths stay
                       stable across status changes and version bumps, so a
                       re-upload updates files in place instead of leaving
                       renamed or relocated duplicates behind.
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


LAYOUTS = ('status', 'mirror')
DEFAULT_LAYOUT = 'status'


@dataclass
class BatchConfig:
    export_root: str          # resolved absolute path
    scan: list[str]           # resolved absolute paths
    exclude: list[str]        # resolved absolute paths
    exclude_names: list[str]  # bare names, matched at any depth
    org: Optional[str]        # resolved absolute path, or None
    logo: Optional[str]       # resolved absolute path, or None
    options: BatchOptions
    config_path: str          # absolute path to the config file itself
    config_dir: str           # directory containing the config file
    layout: str = DEFAULT_LAYOUT   # 'status' or 'mirror'


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

    # An exclude entry is read one of two ways:
    #
    #   'initiatives/old/'  contains a separator -> a PATH, rooted at config_dir
    #   'archive'           a bare name          -> matched at ANY depth
    #
    # The bare-name form exists because the natural thing to write is 'archive/',
    # meaning "archived material wherever it lives". Resolving that as a path
    # produced <repo>/archive, which usually does not exist, so nested archive
    # folders were scanned anyway - and build-docs.sh, which prunes */archive/*
    # at any depth, disagreed with this tool about what gets published.
    exclude: list[str] = []
    exclude_names: list[str] = []
    for e in exclude_raw:
        entry = str(e).strip().rstrip('/' + os.sep)
        if not entry:
            continue
        if '/' in entry or os.sep in entry:
            exclude.append(os.path.normpath(os.path.join(config_dir, entry)))
        else:
            exclude_names.append(entry)

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

    logo_raw = raw.get('logo')
    if logo_raw:
        # An explicit key pointing at a missing file is a config error, same as
        # 'org': failing fast beats silently rendering a whole batch of covers
        # with the text fallback.
        logo_resolved = os.path.normpath(os.path.join(config_dir, str(logo_raw)))
        if not os.path.isfile(logo_resolved):
            raise ConfigError(
                f"logo file specified in config not found: {logo_resolved}"
            )
        logo: Optional[str] = logo_resolved
    else:
        # Auto-detect the conventional location (see "Logo" in the module
        # docstring). Absence is not an error — the cover has a text fallback.
        candidate = os.path.normpath(
            os.path.join(config_dir, 'assets', 'logo', 'logo.png')
        )
        logo = candidate if os.path.isfile(candidate) else None

    layout = str(raw.get('layout') or DEFAULT_LAYOUT).strip().lower()
    if layout not in LAYOUTS:
        raise ConfigError(
            f"Invalid config file: {path}\n"
            f"  - 'layout' must be one of {', '.join(LAYOUTS)} (got: {layout!r})"
        )

    raw_opts = raw.get('options') or {}
    options = BatchOptions(
        skip_retired=_parse_bool(raw_opts.get('skip_retired', True)),
        skip_informational=_parse_bool(raw_opts.get('skip_informational', False)),
    )

    return BatchConfig(
        export_root=export_root,
        scan=scan,
        exclude=exclude,
        exclude_names=exclude_names,
        org=org,
        logo=logo,
        options=options,
        config_path=path,
        config_dir=config_dir,
        layout=layout,
    )
