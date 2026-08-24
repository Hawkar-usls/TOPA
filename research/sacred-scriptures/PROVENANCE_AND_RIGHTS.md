# Provenance, Rights and Community-Control Gates

TOPA does not treat “available on the web” as “free to mirror, transform, tokenize or redistribute”.

Every scripture witness must carry two independent fields:

```text
SOURCE_PROVENANCE = where this exact witness/edition came from
REUSE_STATUS      = what TOPA is permitted to copy/store/transform
```

## Admission states

| State | Meaning |
|---|---|
| `MIRROR_OK` | Full text may be stored under the verified terms. |
| `VERBATIM_ONLY` | Full text may be stored only unchanged with required attribution/notice. |
| `METADATA_ONLY` | Store title, identifiers, source URL, edition/manuscript and analysis receipts; do not mirror full text. |
| `COMMUNITY_PERMISSION_REQUIRED` | Sacred/oral/restricted material requires community/context-specific permission or a clearly authorized public edition. |
| `RIGHTS_UNKNOWN` | Do not mirror until rights are resolved. |

## Verified source examples

### Hebrew Bible / Jewish texts — Sefaria

Source root: <https://www.sefaria.org/texts>

Sefaria exposes multiple versions and translations with version-specific licensing. A visible translation is **not automatically public domain**. Example pages expose license metadata for individual versions.

TOPA rule:

```text
SEFARIA_PAGE_VISIBLE != MIRROR_PERMISSION
VERSION_LICENSE_REQUIRED = true
```

Prefer original-language/public-domain witnesses where rights are clear; otherwise store source metadata and passage identifiers.

### Christian Bible — KJV example

Source root: <https://www.biblegateway.com/versions/King-James-Version-KJV-Bible/>

BibleGateway currently labels its KJV edition as public domain in the United States.

TOPA rule:

```text
KJV_PD_US = SOURCE_REPORTED
OTHER_BIBLE_TRANSLATION != KJV_RIGHTS
```

Catholic, Orthodox, Ethiopian and modern translations require their own edition-level rights checks.

### Qur'an — Tanzil Arabic text

Source root: <https://tanzil.net/download/>

License page: <https://tanzil.net/docs/Text_License>

Tanzil permits copying and distributing **verbatim** copies of its Qur'an text with source attribution/link and copyright notice, while explicitly forbidding modification of the text.

TOPA rule:

```text
TANZIL_ARABIC = VERBATIM_ONLY
NORMALIZED_DERIVATIVE_TEXT = FORBIDDEN_FROM_TANZIL_COPY
ANALYSIS_OUTPUT_MUST_NOT_REPLACE_OR_MUTATE_SOURCE_TEXT
```

Translations listed by Tanzil have different reuse restrictions and must not inherit the Arabic-text license.

### Early Buddhist texts — SuttaCentral

Source root: <https://suttacentral.net/>

Licensing page: <https://suttacentral.net/licensing>

SuttaCentral distinguishes original-language texts, SuttaCentral-created material and third-party translations. It states that original Buddhist texts in Pali, Chinese, Sanskrit, Tibetan and other ancient languages are public domain, while many translations have separate licenses. It also asks that its content not be scraped or used to create generative-AI datasets.

TOPA rule:

```text
NO_BULK_SCRAPE_FROM_SUTTACENTRAL_FOR_AI_CORPUS
USE_FOR_CANON_MAPPING_AND_LICENSE_DISCOVERY
TRANSLATION_LICENSE = PER_TEXT
PREFER_PUBLIC_DOMAIN_ORIGIN_WITNESS_FROM_AUTHORIZED_DOWNLOAD_SOURCE
```

This project is an analysis corpus, not a model-training dataset, but the stricter no-bulk-scrape rule is retained to respect the source's stated preference.

### Sanskrit / Indian-language texts — GRETIL

Source root: <https://gretil.sub.uni-goettingen.de/>

GRETIL provides electronic editions across Vedic, epic and other Indian textual corpora. Each electronic edition must retain editor/inputter provenance and any reuse notes.

TOPA rule:

```text
ANCIENT_TEXT_PD != ELECTRONIC_EDITION_HAS_NO_PROVENANCE
PRESERVE_EDITOR_INPUTTER_EDITION = true
```

### Tibetan Buddhist translations — 84000

Source root: <https://84000.co/>

Individual 84000 translations can carry licenses such as CC BY-NC-ND. Because no-derivatives conditions and tradition-specific reading warnings may apply, TOPA defaults to `METADATA_ONLY` for translations until the exact work's terms are checked.

TOPA rule:

```text
84000_TRANSLATION_DEFAULT = METADATA_ONLY
EXACT_TEXT_LICENSE_REQUIRED = true
RITUAL_OR_LINEAGE_WARNING_PRESERVED = true
```

## Oral and community-controlled traditions

For Ifá, Māori, Indigenous North American, Aboriginal Australian and other community-specific sacred knowledge, “not copyrighted in the Western textual sense” does not imply ethical permission to aggregate, decontextualize or publish restricted material.

TOPA must first split umbrella labels into named communities and identify whether the material is:

- already intentionally public;
- restricted by role/initiation/season/location;
- preserved through a community-authorized archive;
- a colonial transcription whose context or consent is uncertain.

Default state:

```text
ORAL_SACRED_MATERIAL = COMMUNITY_PERMISSION_REQUIRED
COLONIAL_TRANSCRIPTION != COMMUNITY_AUTHORIZATION
PUBLIC_SCAN != ETHICAL_CLEARANCE
```

## Translation drift gate

No cross-tradition match may be promoted from translated wording alone.

For every high-value parallel TOPA should attempt:

```text
TRANSLATION_A
  -> ORIGINAL_TERM_A
TRANSLATION_B
  -> ORIGINAL_TERM_B
  -> semantic range comparison
  -> historical translation route
  -> false-friend / harmonization check
```

If original-language checking is impossible, the result remains `TRANSLATION_DEPENDENT`.

## Sacred-text integrity rule

A source text is immutable evidence. TOPA may tokenize or normalize **derived working copies only when the license permits it**, and must retain the untouched source hash/receipt.

```text
SOURCE_TEXT -> IMMUTABLE
DERIVED_ANALYSIS_COPY -> EXPLICITLY_LABELLED
MODEL_SUMMARY -> NOT_SOURCE_TEXT
```

For `VERBATIM_ONLY` sources, normalization should happen as an external index/mapping rather than by rewriting the stored source text.
