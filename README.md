# WIKIPURE

**A standalone, dynamic multi-language "pure" XML extractor for English Wiktionary dumps.**

WIKIPURE extracts a clean, single-language `<language>_pure.xml.gz` corpus for **any language named at runtime**, directly from an English Wiktionary dump — without requiring a full multilingual pipeline, a fixed language list, or any downstream analysis modules. It is designed as upstream infrastructure for building more precise, targeted language resources: etymological dictionaries, phonological/phonemic inventories, dialect corpora, morphological databases — for whichever language(s) a project needs, without extracting or processing data for languages outside that scope.

- **Author:** Almoataz B. Al-Said
- **Affiliation:** Kuwait University; Cairo University
- **Year:** 2026
- **License:** MIT License (see [LICENSE](LICENSE))

---

## What "pure" means

A page belongs to a language's **pure** set if and only if at least one of its Wiktionary categories matches that language's category pattern — the standard Wiktionary category-naming convention `<Language> <POS/topic>`, e.g. *"Arabic nouns"*, *"Egyptian Arabic verbs"*, *"Biblical Hebrew adjectives"*.

```
pure = pages whose categories match category_pattern            [default]
```

Two optional, off-by-default flags widen this definition:

| Flag | Adds pages... |
|---|---|
| `--include-interwiki` | ...reached via an interwiki link in the language's code list (`langlinks.sql`) |
| `--include-page-lang` | ...whose SQL `page_lang` field matches one of the language's codes (`page.sql`) |

Whichever sources are actually enabled for a given run are recorded, per language, in the accompanying `<language>_pure_statistics.json` file — so any number cited from WIKIPURE output is fully traceable without inspecting the command that produced it.

## Curated language tiers

| Tier | Languages | Purpose |
|---|---|---|
| **resource-poor** (14) | Arabic, Hebrew, Aramaic, Persian, Kurdish, Urdu, Coptic, Amharic, Tigrinya, Hausa, Swahili, Amazigh, Turkic family, Maltese | Historically under-resourced languages; patterns fold in dialect/period variants (e.g. Arabic also matches "Egyptian Arabic", "Levantine Arabic", ...) |
| **resource-rich** (10) | English, Spanish, French, German, Russian, Italian, Chinese, Hindi, Greek, Latin | Comparison/control group for borrowing-density or lexical-stratification research |

Any language outside these 24 falls back to an automatically generated pattern (`^Name\s+`). An optional companion file, `language_registry.json`, adds family/region metadata (and a default interwiki code) for a further ~240 languages when present next to the script — this is metadata enrichment only and never affects detection.

### Validation status — please read before publishing results

The two tiers differ in how thoroughly their default patterns have been checked against real dump data:

- **resource-poor tier** — the dialect/period variants folded into each pattern were checked against an actual page/category extraction run; an earlier, simpler pattern was found to under-count pages for exactly this reason and was corrected before this release.
- **resource-rich tier** and any **auto-generated** pattern — reasonable defaults based on Wiktionary's general category-naming convention, but **not yet checked against a full real dump** the same way. The Chinese pattern in particular (`Chinese`/`Mandarin`) is a best-effort guess that may need adjustment.

**Recommendation:** before relying on results for publication, spot-check page counts for any language outside the resource-poor tier (e.g. by grepping the raw `categorylinks`/`linktarget` files for the expected category name and comparing to `pages.pure_total` in that language's statistics JSON). Supply a custom `--lang` pattern if the default under- or over-matches. Every statistics JSON also carries this signal directly in `detection.category_pattern_validated_against_real_dump` (`true`/`false`), so it travels with the data itself.

## Installation

No installation needed — a single Python 3.8+ script, standard library only.

```bash
git clone https://github.com/almoatazb/wikipure.git
cd wikipure
python wikipure.py --help
```

Optional accelerators (auto-detected if installed, not required): `ujson`, `lxml`.

## Input files

Minimum required (default mode — category patterns only):

```
enwiktionary-YYYYMMDD-page.sql            page metadata, namespace filter
enwiktionary-YYYYMMDD-categorylinks.sql   page → category assignments
enwiktionary-YYYYMMDD-linktarget.sql      category ID → category name
enwiktionary-YYYYMMDD-pages-articles.xml  page content
```

Additional file required only for `--include-interwiki`:

```
enwiktionary-YYYYMMDD-langlinks.sql
```

`enwiktionary-YYYYMMDD-category.sql` is **never** required.

### Format- and version-aware dump detection

- SQL tables may be plain (`.sql`) or gzip-compressed (`.sql.gz`), exactly as Wikimedia distributes them.
- The page-content file may be plain XML, the "multistream" variant, or bzip2/gzip-compressed (`.xml`, `.xml.bz2`, `.xml.gz`, or the multistream equivalents) — all are searched and the fastest available is used automatically.
- If more than one dump date is present in the source directory, the most recent **complete** one is selected automatically, and every date found is logged. Pass `--dump-date YYYYMMDD` to pin an exact one.

## Usage

```bash
# Single language, default (category-pattern-only) detection
python wikipure.py /path/to/dump --lang arabic:ar,arz,arq

# Several languages in one run
python wikipure.py /path/to/dump \
    --lang arabic:ar,arz,arq \
    --lang hebrew:he,heb \
    --lang persian:fa,fas

# Tier shortcuts instead of listing names one by one
python wikipure.py /path/to/dump --lang-tier resource-poor
python wikipure.py /path/to/dump --lang-tier resource-poor --lang-tier resource-rich

# Custom category pattern override (e.g. to fold in dialect labels)
python wikipure.py /path/to/dump \
    --lang "arabic:ar,arz,arq:^(?:Arabic|Egyptian Arabic|Levantine Arabic|Gulf Arabic)\s+"

# Widen detection beyond category patterns (explicit, off by default)
python wikipure.py /path/to/dump --lang arabic:ar,arz --include-interwiki --include-page-lang

# Pin an exact dump date
python wikipure.py /path/to/dump --lang arabic --dump-date 20260301
```

Running with **no arguments** (e.g. pressing F5 inside IDLE, or double-clicking the file) launches a minimal interactive prompt instead — it asks only for the dump directory and the language(s) to extract, using default detection throughout.

### `--lang` syntax

```
name[:code1,code2][:custom_regex]
```

- `name` — the language name; becomes the output folder/file stem.
- `code1,code2` — optional interwiki codes; only consulted with `--include-interwiki`.
- `custom_regex` — optional category-pattern override; if omitted, a curated preset is used automatically for the 24 tiered languages, otherwise a pattern is auto-generated from the name.

## Output structure

```
<output_dir>/<lang_key>/<lang_key>_pure.xml.gz           MediaWiki-schema XML
<output_dir>/<lang_key>/<lang_key>_pure_statistics.json  documentation/audit
<output_dir>/wikipure_overlap_report.json                cross-language overlap (2+ languages)
<output_dir>/wikipure_run.log                            plain timestamped run log
<output_dir>/wikipure_run.json                           structured run summary
```

Each `<lang_key>_pure_statistics.json` documents: which detection sources were enabled, the exact category pattern used and its origin (curated preset / custom / auto-generated) and validation status, page counts by source, corpus statistics (type-token ratio, hapax legomena, approximate Zipf slope, top words), top categories, and — when a `language_registry.json` is present — typological metadata (family, macro-family, geographic region).

## Advanced statistics

Per language, in addition to page/word counts:

- **Type-token ratio**, **hapax legomena** count and ratio
- **Approximate Zipf slope** (log-log least-squares fit over top word frequencies)
- **Top 30 words** by frequency
- **Cross-language overlap report** (when 2+ languages are extracted in one run) — pages whose categories matched more than one selected language, relevant for lexical-contact/borrowing studies

Word-frequency tracking is memory-safe: vocabularies are trimmed once they exceed a threshold, and the statistics JSON discloses `word_frequency_approximate: true` whenever this trimming occurred.

## Reproducibility

Every run writes `wikipure_run.log` (plain text, timestamped, mirrors console output) and `wikipure_run.json` (structured: phase durations in seconds, Python version, optional-library availability, dump date, detection flags, per-language final counts, and success/failure status — written even if the run fails).

## Project files

```
wikipure.py             the tool (single file, no mandatory dependencies)
language_registry.json  optional typology metadata for ~240 languages
LICENSE                 MIT License
CITATION.cff            machine-readable citation metadata (GitHub/Zenodo)
README.md               this file
```

## Citation

If you use WIKIPURE in academic work, please cite it as software. A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff); once deposited, Zenodo will also generate this automatically from that file. Suggested citation:


> Al-Said, A. B. (2026). *WIKIPURE: A Standalone, Dynamic Multi-Language "Pure" XML Extractor for English Wiktionary Dumps* (Version v1.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.21429856

## License

MIT License — see [LICENSE](LICENSE) for the full text.
