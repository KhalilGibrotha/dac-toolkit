# Vale Styles — DocOps

Custom Vale rules for technical documentation. The `DocOps` style package
enforces consistent structure, language, and terminology standards in
Markdown-based documentation repositories.

## Rules

| File | Rule ID | Level | What It Catches |
|---|---|---|---|
| `ConsciousLanguage.yml` | LANG-004 | error | Non-inclusive terms (blacklist, whitelist, etc.) |
| `MasterSlave.yml` | LANG-004 | error | master/slave compound references |
| `DeprecatedProductNames.yml` | TERM-002 | error | Deprecated product names (Tower, AWX, JIRA, Nessus) |
| `HeadingDepth.yml` | STRUCT-002 | error | H4 or deeper headings |
| `HeadingCapitalization.yml` | STRUCT-003 | warning | Headings not in title case |
| `FutureTense.yml` | LANG-001 | warning | "will + verb" in non-roadmap prose |
| `PlaybookCapitalization.yml` | TERM-003 | warning | Capitalized "Playbook" in running text |
| `NoShall.yml` | CONTENT-002 | warning | "shall" in governance language |
| `FillerPhrases.yml` | LANG-003 | suggestion | "in order to", "basically", etc. |

## Usage

Copy the `DocOps/` folder into your content repo's `.vale/styles/` directory,
then reference it in `.vale.ini`:

```ini
StylesPath = .vale/styles
MinAlertLevel = suggestion

[*.md]
BasedOnStyles = DocOps, RedHat, write-good
```

## Customizing for Your Environment

`DeprecatedProductNames.yml` ships with examples for Red Hat platform tooling
(Tower, AWX) and common SaaS products (JIRA, Nessus). Extend or replace the
`swap` map with your own canonical product names.

`PlaybookCapitalization.yml` is Ansible-specific. Remove it if your stack
does not use Ansible.
