# Vale Styles — InfraOps

Custom Vale rules for Infrastructure & Operations documentation, implementing the
[I&O Documentation Style Guide](https://github.com/KhalilGibrotha/architecture-docs).

## Rules

| File | Rule ID | Level | What It Catches |
|---|---|---|---|
| `ConsciousLanguage.yml` | LANG-004 | error | Non-inclusive terms (blacklist, whitelist, etc.) |
| `MasterSlave.yml` | LANG-004 | error | master/slave compound references |
| `DeprecatedProductNames.yml` | TERM-002 | error | Tower, AWX, JIRA, Nessus → canonical names |
| `HeadingDepth.yml` | STRUCT-002 | error | H4 or deeper headings |
| `HeadingCapitalization.yml` | STRUCT-003 | warning | Headings not in title case |
| `FutureTense.yml` | LANG-001 | warning | "will + verb" in non-roadmap prose |
| `PlaybookCapitalization.yml` | TERM-003 | warning | Capitalized "Playbook" in running text |
| `NoShall.yml` | CONTENT-002 | warning | "shall" in governance language |
| `FillerPhrases.yml` | LANG-003 | suggestion | "in order to", "basically", etc. |

## Usage

Content repositories (e.g., `architecture-docs`) reference these styles in their `.vale.ini`:

```ini
StylesPath = .vale/styles
MinAlertLevel = suggestion

[*.md]
BasedOnStyles = InfraOps, RedHat, write-good
```

Copy the `InfraOps/` folder into your content repo's `.vale/styles/` directory, or
symlink it during Dev Spaces workspace setup.
