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

Adopted repositories get this for free — `dac-init` installs `DocOps/` at
`dac/vale/styles/DocOps/` along with a working `.vale.ini`. The rest of this
section is for anyone wiring it up by hand or extending it.

The canonical layout puts the styles path under `dac/`:

```ini
StylesPath = dac/vale/styles
MinAlertLevel = suggestion
Vocab = <YourVocabName>

[*.md]
BasedOnStyles = DocOps, RedHat, write-good
```

### Where the pieces live

```text
dac/vale/styles/
|-- DocOps/                        committed - the house style, this package
|-- config/
|   `-- vocabularies/
|       `-- <YourVocabName>/       committed - your terms
|           |-- accept.txt
|           `-- reject.txt
|-- RedHat/                        gitignored - vale sync regenerates
|-- write-good/                    gitignored - vale sync regenerates
`-- ai-tells/                      gitignored - vale sync regenerates
```

**Vocabularies belong at `<StylesPath>/config/vocabularies/<Name>/`**, where
`<Name>` is the folder name that `Vocab =` refers to in `.vale.ini`. Vale 2
read them from `<StylesPath>/Vocab/<Name>/`. That path is dead in Vale 3:
entries placed there are ignored with no error, and a repo carrying both
locations drifts apart silently. Migrating an older repo means moving the
folder and deleting the old one.

Packages named in `Packages =` are downloaded by `vale sync` into the styles
path. Gitignore those and commit only what you author: the house style and
your vocabularies.

## Customizing for Your Environment

`DeprecatedProductNames.yml` ships with examples for Red Hat platform tooling
(Tower, AWX) and common SaaS products (JIRA, Nessus). Extend or replace the
`swap` map with your own canonical product names.

`PlaybookCapitalization.yml` is Ansible-specific. Remove it if your stack
does not use Ansible.
