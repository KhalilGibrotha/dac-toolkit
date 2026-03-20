# DocOps Vale Style Package

Custom Vale rules for enterprise infrastructure architecture documentation.
Designed for use with the Diátaxis + Red Hat modular docs blended model.

## Rule Index

| File | Rule ID | Severity | Generic? | Description |
|---|---|---|---|---|
| `PurposeStatement.yml` | STRUCT-006 | Suggestion | ✅ Yes | Every document must have a purpose statement after the H1 |
| `HeadingDepth.yml` | STRUCT-002 | Error | ✅ Yes | No headings deeper than H3 |
| `HeadingCapitalization.yml` | STRUCT-003 | Warning | ✅ Yes | Title case for all headings (Chicago style) |
| `FutureTense.yml` | LANG-001 | Warning | ✅ Yes | Avoid future tense in descriptive prose |
| `FillerPhrases.yml` | LANG-003 | Suggestion | ✅ Yes | Remove wordy filler constructions |
| `ConsciousLanguage.yml` | LANG-004 | Error | ✅ Yes | Flag non-inclusive language |
| `MasterSlave.yml` | LANG-004 (supplement) | Error | ✅ Yes | Flag master/slave compound terms — supplements ConsciousLanguage.yml for multi-word patterns |
| `NoShall.yml` | CONTENT-002 | Warning | ✅ Yes | Avoid lowercase "shall" in prose (RFC 2119 uppercase SHALL is exempt) |
| `DeprecatedProductNames.yml` | TERM-002 | Error | ⚠️ Stack-specific | Flag deprecated product names — **customize swap list for your environment** |
| `PlaybookCapitalization.yml` | TERM-003 | Warning | ⚠️ Stack-specific | Ansible-specific capitalization rule — **remove if not using Ansible** |

## Generic vs. Stack-Specific Rules

Rules marked **✅ Generic** apply to any infrastructure documentation team without
modification. Rules marked **⚠️ Stack-specific** reference tooling and product names
specific to the Red Hat / Ansible / ITSM environment used here.

**If you are adopting dac-toolkit for a different environment:**

1. Copy the generic rules (`LANG-*`, `STRUCT-*`, `CONTENT-*`) as-is.
2. Replace `DeprecatedProductNames.yml` with your own canonical product name list.
3. Remove `PlaybookCapitalization.yml` if you are not using Ansible.
4. Add your own `TERM-*` rules for any stack-specific terminology.

## Adding Rules

New rules should follow this header convention:

```yaml
# Rule ID: <CATEGORY>-<NNN>
# Severity: Error | Warning | Suggestion
# Description of what the rule checks.
#
# Reuse note: GENERIC or STACK-SPECIFIC — and why.
extends: <rule-type>
...
```

Categories:
- `STRUCT` — Document structure (headings, purpose statement, section order)
- `LANG` — Language and style (voice, tense, inclusive language)
- `CONTENT` — Content policy (modality, RFC keywords)
- `TERM` — Terminology (product names, capitalization)

## NoShall and RFC 2119

`NoShall.yml` flags lowercase `shall` but intentionally permits uppercase `SHALL`.
Documents with `doc_type: standard` use `SHALL`, `SHOULD`, and `MAY` per RFC 2119
convention. This is correct and should not be suppressed. The case-sensitive
match preserves that distinction automatically.
