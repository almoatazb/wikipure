#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
                              WIKIPURE  v1.0
        A Standalone, Dynamic Multi-Language "Pure" XML Extractor for
                          English Wiktionary Dumps
================================================================================
Author:       Almoataz B. Al-Said
Affiliation:  Kuwait University; Cairo University
Year:         2026
License:      MIT License (see LICENSE file)
================================================================================

ABSTRACT
========
WIKIPURE is a standalone extraction tool that produces a clean, single-
language "<language>_pure.xml.gz" corpus for ANY language named at runtime,
directly from an English Wiktionary dump — without requiring a full
multilingual pipeline, a fixed language list, or any downstream analysis
modules. It is designed as upstream infrastructure for building more
precise, targeted language resources — etymological dictionaries,
phonological/phonemic inventories, dialect corpora, morphological
databases — for whichever language(s) a project needs, without extracting
or processing data for languages outside that scope.

Detection relies on the standard Wiktionary category-naming convention
(see "WHAT 'PURE' MEANS" below). Two curated tiers of hand-built,
dialect-aware category patterns are bundled: a RESOURCE-POOR tier (14
Semitic, Afroasiatic, and other historically under-resourced languages)
and a RESOURCE-RICH tier (10 widely documented languages, usable as a
comparison/control group for borrowing-density or lexical-stratification
research). Any language outside these 24 falls back to an automatically
generated pattern. An optional companion file, language_registry.json,
adds family/region metadata (and a default interwiki code) for a further
~240 languages when present next to the script — this is metadata
enrichment only and never affects detection.

Every run documents exactly which pattern and detection sources were used,
per language, in a companion statistics file — so any number cited from
WIKIPURE output is fully traceable without inspecting the command that
produced it.

WHAT "PURE" MEANS
==================
A page belongs to a language's PURE set if and only if at least one of its
Wiktionary categories matches that language's category pattern — the
standard Wiktionary category-naming convention "<Language> <POS/topic>",
e.g. "Arabic nouns", "Egyptian Arabic verbs", "Biblical Hebrew adjectives".

    pure = pages whose categories match category_pattern            [default]

Two OPTIONAL, OFF-BY-DEFAULT flags widen this definition to two further
detection sources:

    --include-interwiki   add pages reached via an interwiki link in the
                           language's code list (langlinks.sql)
    --include-page-lang   add pages whose SQL page_lang field matches one
                           of the language's codes (page.sql)

Whichever sources are actually enabled for a given run are recorded, per
language, in the accompanying "<language>_pure_statistics.json" file.

VALIDATION STATUS OF BUNDLED PATTERNS
=======================================
The two curated tiers differ in how thoroughly their default patterns have
been checked against real dump data, and this difference is disclosed here
rather than left implicit:

  RESOURCE-POOR tier (14 languages) — the dialect/period variants folded
  into each pattern (e.g. Arabic's pattern also matching "Egyptian Arabic",
  "Levantine Arabic", etc.) were checked against an actual page/category
  extraction run; an earlier, simpler pattern was found to under-count
  pages for exactly this reason and was corrected before this release.

  RESOURCE-RICH tier (10 languages) and any AUTO-GENERATED pattern for a
  language outside both tiers — these are reasonable defaults based on
  Wiktionary's general category-naming convention, but have NOT yet been
  checked against a full real dump in the same way. In particular, the
  Chinese pattern (matching "Chinese" or "Mandarin" category names) is a
  best-effort guess at Wiktionary's actual category-naming practice for
  Sinitic entries and may need adjustment once run against real data.

  RECOMMENDATION: before relying on results for publication, spot-check
  page counts for any language outside the resource-poor tier — e.g. by
  grepping the raw categorylinks/linktarget files for the expected
  category name pattern and comparing the count to the 'pages.pure_total'
  field in that language's statistics JSON. A custom --lang pattern can
  always be supplied if the default under- or over-matches.

CORE ARCHITECTURE
==================
  Phase 1  SQL metadata pass    → build the page/category reverse index
  Phase 2  Single XML pass      → stream pages-articles.xml once, write
                                   every language's pure XML + stats

INPUT FILES REQUIRED (minimum, default mode — category patterns only):
========================================================================
  enwiktionary-YYYYMMDD-page.sql            page metadata, namespace filter
  enwiktionary-YYYYMMDD-categorylinks.sql   page → category assignments
  enwiktionary-YYYYMMDD-linktarget.sql      category ID → category name
  enwiktionary-YYYYMMDD-pages-articles.xml  page content

  ADDITIONAL file required only if the corresponding flag is used:
  enwiktionary-YYYYMMDD-langlinks.sql       required by --include-interwiki

  enwiktionary-YYYYMMDD-category.sql is NEVER required — the detection
  logic here does not consult it; it only feeds category statistics that
  WIKIPURE does not produce.

  DUMP DETECTION IS FORMAT- AND VERSION-AWARE:
    - SQL tables may be plain (.sql) or gzip-compressed (.sql.gz), exactly
      as Wikimedia distributes them — detected automatically by extension.
    - The page-content file may be plain XML, the "multistream" variant, or
      bzip2/gzip-compressed (.xml, .xml.bz2, .xml.gz, or the multistream
      equivalents) — all are searched and the fastest available is used.
    - If more than one dump date is present in source_dir, the most recent
      COMPLETE one (all required files present, in any supported format)
      is selected automatically, and every date found is logged so nothing
      is silently ignored. Pass --dump-date YYYYMMDD to pin an exact one.

  Optional companion file (not a dump file, not required):
  language_registry.json    metadata enrichment only, see VALIDATION
                             STATUS above and ABSTRACT; if absent, WIKIPURE
                             runs normally and simply omits the 'typology'
                             field from the statistics JSON.

OUTPUT STRUCTURE
=================
  <output_dir>/<lang_key>/<lang_key>_pure.xml.gz          MediaWiki-schema XML
  <output_dir>/<lang_key>/<lang_key>_pure_statistics.json documentation/audit
  <output_dir>/wikipure_overlap_report.json               cross-language overlap (2+ langs)
  <output_dir>/wikipure_run.log / wikipure_run.json        run log (text / structured)

USAGE
=====
  # Single language, default (category-pattern-only) detection
  python wikipure.py /path/to/dump --lang arabic:ar,arz,arq

  # Several languages in one run
  python wikipure.py /path/to/dump \\
      --lang arabic:ar,arz,arq \\
      --lang hebrew:he,heb \\
      --lang persian:fa,fas

  # Tier shortcuts instead of listing names one by one
  python wikipure.py /path/to/dump --lang-tier resource-poor
  python wikipure.py /path/to/dump --lang-tier resource-poor --lang-tier resource-rich

  # Custom category pattern override (e.g. to fold in dialect labels)
  python wikipure.py /path/to/dump \\
      --lang "arabic:ar,arz,arq:^(?:Arabic|Egyptian Arabic|Levantine Arabic|Gulf Arabic)\\s+"

  # Widen detection beyond category patterns (explicit, off by default)
  python wikipure.py /path/to/dump --lang arabic:ar,arz --include-interwiki --include-page-lang

  # No arguments at all (e.g. F5 inside IDLE) launches a minimal interactive
  # prompt instead — see interactive_main().

REQUIREMENTS
============
  Python 3.8+   Standard library only   No mandatory external dependencies
  (optional accelerators, auto-detected if installed: ujson, lxml)

================================================================================
"""

import re
try:
    import ujson as json
    _UJSON_AVAILABLE = True
except ImportError:
    import json
    _UJSON_AVAILABLE = False
import gzip
import bz2
try:
    from lxml import etree as ET
    _LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    _LXML_AVAILABLE = False
import argparse
import glob
import gc
import sys
import time
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Set, Tuple


# ============================================================================
# LANGUAGE SPECIFICATION (dynamic — no hard-coded language table)
# ============================================================================

class LanguageSpec:
    """
    Runtime-defined language configuration.

    A LanguageSpec is built entirely from what the user passes on the
    command line via --lang, except that for a curated set of languages
    (see CURATED_LANGUAGE_PATTERNS) a hand-built, dialect-aware pattern is
    used automatically instead of the generic auto-generated one.

    key               lowercase identifier, also the output folder/file stem
    name              display name (title-cased key, used inside stats JSON)
    interwiki_codes   list of interwiki language codes, e.g. ['ar','arz']
    category_pattern  compiled regex matched against category names
    pattern_origin    'curated_preset' | 'custom' | 'auto_generated'
    pattern_source    human-readable regex string, for the audit JSON
    tier              'resource-poor' | 'resource-rich' | None
    typology          optional dict from language_registry.json (family,
                       top_family, geo_region) — metadata only, never used
                       in detection logic
    """

    def __init__(self, key: str, interwiki_codes: List[str],
                 category_pattern: 're.Pattern', pattern_origin: str,
                 pattern_source: str, tier: Optional[str] = None,
                 typology: Optional[Dict] = None):
        self.key = key
        self.name = key.replace('_', ' ').title()
        self.interwiki_codes = interwiki_codes
        self.category_pattern = category_pattern
        self.pattern_origin = pattern_origin
        self.pattern_source = pattern_source
        self.tier = tier
        self.typology = typology

    @property
    def pattern_is_custom(self) -> bool:
        return self.pattern_origin == 'custom'


def _default_category_pattern(name: str) -> str:
    """
    Auto-generate the standard Wiktionary category-pattern for a language:
    a category belongs to language X if its name starts with "X " (POS/topic
    categories are named "<Language> <thing>", e.g. "Arabic nouns").
    """
    return rf'^{re.escape(name)}\s+'


# CURATED LANGUAGE PATTERNS — hand-built, dialect-aware category patterns
# for a set of Semitic, Afroasiatic, and other historically under-resourced
# languages. Each pattern folds in the relevant dialect/period labels used
# in Wiktionary's own category taxonomy (e.g. Arabic also matches "Egyptian
# Arabic", "Levantine Arabic", etc.), so detection does not silently miss
# dialect-specific entries. When a --lang name matches one of these keys and
# no custom regex is supplied, this pattern is used automatically; any
# other language name falls back to the generic auto-generated pattern above.
CURATED_LANGUAGE_PATTERNS: Dict[str, Dict] = {
    'arabic': {
        'pattern': r'^(?:Arabic|Standard Arabic|Modern Standard Arabic|Classical Arabic|'
                   r'Old Arabic|Quranic Arabic|Egyptian Arabic|Levantine Arabic|'
                   r'Gulf Arabic|Iraqi Arabic|Moroccan Arabic|Algerian Arabic|'
                   r'Tunisian Arabic|Libyan Arabic|Saudi Arabic|Yemeni Arabic)\s+',
        'codes': ['ar', 'arb', 'ara', 'arq', 'arz', 'acm', 'afb', 'apc', 'ary'],
    },
    'hebrew': {
        'pattern': r'^(?:Hebrew|Biblical Hebrew|Modern Hebrew|Ancient Hebrew)\s+',
        'codes': ['he', 'heb', 'hbo'],
    },
    'aramaic': {
        'pattern': r'^(?:Aramaic|Syriac|Classical Syriac|Assyrian Neo-Aramaic)\s+',
        'codes': ['arc', 'syc', 'aii', 'cld'],
    },
    'persian': {
        'pattern': r'^(?:Persian|Old Persian|Middle Persian|Dari|Tajik)\s+',
        'codes': ['fa', 'fas', 'prs', 'tg', 'tgk', 'pes', 'peo', 'pal'],
    },
    'kurdish': {
        'pattern': r'^(?:Kurdish|Kurmanji|Sorani|Central Kurdish)\s+',
        'codes': ['ku', 'kur', 'ckb', 'kmr', 'sdh'],
    },
    'urdu': {
        'pattern': r'^(?:Urdu|Classical Urdu)\s+',
        'codes': ['ur', 'urd'],
    },
    'coptic': {
        'pattern': r'^(?:Coptic|Bohairic|Sahidic)\s+',
        'codes': ['cop'],
    },
    'amharic': {
        'pattern': r'^(?:Amharic|Classical Amharic)\s+',
        'codes': ['am', 'amh'],
    },
    'tigrinya': {
        'pattern': r'^(?:Tigrinya|Tigrigna)\s+',
        'codes': ['ti', 'tir'],
    },
    'hausa': {
        'pattern': r'^(?:Hausa|Old Hausa)\s+',
        'codes': ['ha', 'hau'],
    },
    'swahili': {
        'pattern': r'^(?:Swahili|Old Swahili)\s+',
        'codes': ['sw', 'swa', 'swh'],
    },
    'amazigh': {
        'pattern': r'^(?:Amazigh|Berber|Tamazight|Kabyle|Riffian)\s+',
        'codes': ['ber', 'tzm', 'kab', 'rif', 'shi'],
    },
    'turkic': {
        'pattern': r'^(?:Turkish|Azerbaijani|Uzbek|Kazakh|Ottoman Turkish|Chagatai)\s+',
        'codes': ['tr', 'tur', 'ota', 'otk', 'az', 'uz', 'kk', 'ky', 'ug', 'tk', 'tt'],
    },
    'maltese': {
        'pattern': r'^(?:Maltese|Old Maltese)\s+',
        'codes': ['mt', 'mlt'],
    },
}

# Convenience alias: the dict above is the RESOURCE-POOR tier (14 languages).
RESOURCE_POOR_LANGUAGE_PATTERNS = CURATED_LANGUAGE_PATTERNS

# RESOURCE-RICH TIER — a comparison/control group for research questions
# about lexical-stratification or borrowing-density differences between
# under-documented and well-documented languages (e.g. "does Arabic show a
# different loanword layering pattern than English?"). Unlike the
# resource-poor tier, these languages' Wiktionary category taxonomy is not
# meaningfully dialect-fragmented, so plain default patterns are used
# rather than folding in historical stages (e.g. "Old English", "Middle
# High German" are treated as distinct languages here, not variants of
# their modern descendant — consistent with standard historical-linguistic
# practice and with how Wiktionary itself categorizes them).
# See "VALIDATION STATUS OF BUNDLED PATTERNS" in the module docstring:
# these patterns are reasonable defaults, not yet checked against a real
# dump the way the resource-poor tier's patterns were.
RESOURCE_RICH_LANGUAGE_PATTERNS: Dict[str, Dict] = {
    'english':    {'pattern': r'^English\s+',    'codes': ['en']},
    'spanish':    {'pattern': r'^Spanish\s+',    'codes': ['es']},
    'french':     {'pattern': r'^French\s+',     'codes': ['fr']},
    'german':     {'pattern': r'^German\s+',     'codes': ['de']},
    'russian':    {'pattern': r'^Russian\s+',    'codes': ['ru']},
    'italian':    {'pattern': r'^Italian\s+',    'codes': ['it']},
    'chinese':    {'pattern': r'^(?:Chinese|Mandarin)\s+', 'codes': ['zh']},
    'hindi':      {'pattern': r'^Hindi\s+',      'codes': ['hi']},
    'greek':      {'pattern': r'^Greek\s+',      'codes': ['el']},
    'latin':      {'pattern': r'^Latin\s+',      'codes': ['la']},
}

# Merge both tiers for pattern lookup in parse_lang_arg()
CURATED_LANGUAGE_PATTERNS = {**RESOURCE_POOR_LANGUAGE_PATTERNS, **RESOURCE_RICH_LANGUAGE_PATTERNS}

# Tier keyword shortcuts recognized in --lang-tier / interactive mode
LANGUAGE_TIERS: Dict[str, List[str]] = {
    'resource-poor': list(RESOURCE_POOR_LANGUAGE_PATTERNS.keys()),
    'resource-rich': list(RESOURCE_RICH_LANGUAGE_PATTERNS.keys()),
}
LANGUAGE_TIERS['all'] = LANGUAGE_TIERS['resource-poor'] + LANGUAGE_TIERS['resource-rich']


# ============================================================================
# LANGUAGE TYPOLOGY REGISTRY (optional metadata enrichment)
# ============================================================================

def _load_language_registry() -> Dict[str, Dict]:
    """
    Load the optional companion file 'language_registry.json' (family,
    macro-family, geographic region, and a default interwiki code for a
    broad set of languages) if it is present next to this script. This is
    purely for METADATA ENRICHMENT of the output statistics — detection
    logic never depends on it, so its absence never breaks a run.
    """
    registry_path = Path(__file__).resolve().parent / 'language_registry.json'
    if not registry_path.exists():
        return {}
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        return {name.lower(): meta for name, meta in raw.items()}
    except Exception:
        return {}


LANGUAGE_REGISTRY = _load_language_registry()


def parse_lang_arg(raw: str) -> LanguageSpec:
    """
    Parse one --lang argument.

    Accepted forms (interwiki codes are OPTIONAL — they are only consulted
    at all when --include-interwiki is passed; the default 'pure' detection
    uses category patterns alone and never touches them):
        name
        name:iw1,iw2,iw3
        name::custom_regex                (empty codes, explicit pattern)
        name:iw1,iw2,iw3:custom_regex

    'name' becomes the output key (lower-cased, spaces → underscores).

    Pattern resolution priority:
      1. Explicit custom_regex, if supplied                    -> pattern_origin='custom'
      2. CURATED_LANGUAGE_PATTERNS[key], if name matches one    -> pattern_origin='curated_preset'
         of the hand-curated languages                             (dialect-aware regex)
      3. Auto-generated ^Name\\s+ fallback                       -> pattern_origin='auto_generated'

    Interwiki codes: explicit codes given by the user always win; otherwise
    a preset's codes are used as the default when applicable.
    """
    parts = raw.split(':', 2)

    name_raw = parts[0].strip()
    codes_raw = parts[1].strip() if len(parts) >= 2 else ''
    custom_regex = parts[2] if len(parts) == 3 else None

    if not name_raw:
        raise argparse.ArgumentTypeError(f"--lang '{raw}': empty language name")

    key = name_raw.lower().replace(' ', '_')
    display_name = name_raw.title()
    interwiki_codes = [c.strip() for c in codes_raw.split(',') if c.strip()]

    preset = CURATED_LANGUAGE_PATTERNS.get(key)

    if custom_regex:
        pattern_source = custom_regex
        pattern_origin = 'custom'
    elif preset:
        pattern_source = preset['pattern']
        pattern_origin = 'curated_preset'
        if not interwiki_codes:
            interwiki_codes = list(preset['codes'])
    else:
        pattern_source = _default_category_pattern(display_name)
        pattern_origin = 'auto_generated'

    # Fallback interwiki code from the typology registry, if nothing else
    # supplied one (lowest priority: explicit > curated preset > registry)
    typology = LANGUAGE_REGISTRY.get(key.replace('_', ' ')) or LANGUAGE_REGISTRY.get(display_name.lower())
    if not interwiki_codes and typology and typology.get('code'):
        interwiki_codes = [typology['code']]

    if key in RESOURCE_POOR_LANGUAGE_PATTERNS:
        tier = 'resource-poor'
    elif key in RESOURCE_RICH_LANGUAGE_PATTERNS:
        tier = 'resource-rich'
    else:
        tier = None

    try:
        compiled = re.compile(pattern_source, re.IGNORECASE)
    except re.error as e:
        raise argparse.ArgumentTypeError(f"--lang '{raw}': invalid regex ({e})")

    return LanguageSpec(
        key=key,
        interwiki_codes=interwiki_codes,
        category_pattern=compiled,
        pattern_origin=pattern_origin,
        pattern_source=pattern_source,
        tier=tier,
        typology=typology,
    )


def expand_tier_keyword(name: str) -> Optional[List[str]]:
    """
    If 'name' is a recognized tier keyword ('resource-poor', 'resource-rich',
    or 'all'), return the list of language names in that tier; otherwise
    return None so the caller treats it as a literal language name.
    """
    key = name.strip().lower().replace('_', '-')
    if key in LANGUAGE_TIERS:
        return [k.replace('_', ' ').title() for k in LANGUAGE_TIERS[key]]
    return None


# ============================================================================
# ADVANCED STATISTICS (per-language word-frequency tracking)
# ============================================================================

class WordFrequencyTracker:
    """
    Memory-safe per-language word-frequency counter, used to compute
    type-token ratio, hapax legomena ratio, and an approximate Zipf slope —
    without holding an unbounded vocabulary in RAM for high-resource
    languages selected by name (e.g. 'Turkish').

    Trimming strategy: once the
    vocabulary exceeds max_items * 3, keep only the top max_items by count.
    This slightly under-counts true hapax legomena for very large corpora
    (a trimmed-away word could have reappeared later), which is disclosed
    in the stats JSON via 'approximate: true' rather than silently assumed
    exact.
    """

    def __init__(self, max_items: int = 200_000):
        self.max_items = max_items
        self.counts: Counter = Counter()
        self.total_tokens = 0
        self.pages_seen = 0
        self.trimmed = False

    def add_text(self, text: str):
        if not text:
            return
        words = re.findall(r'\w+', text.lower())
        self.total_tokens += len(words)
        self.counts.update(words)
        self.pages_seen += 1
        if len(self.counts) > self.max_items * 3:
            self.counts = Counter(dict(self.counts.most_common(self.max_items)))
            self.trimmed = True

    @staticmethod
    def _zipf_slope(ranked_counts: List[int]) -> Optional[float]:
        """
        Least-squares slope of log(frequency) vs log(rank) over the top
        entries — the standard quick-and-dirty Zipf-law diagnostic (an
        ideal Zipf distribution gives a slope near -1). Returns None if
        there are fewer than 10 distinct words (insufficient for a
        meaningful fit).
        """
        import math
        if len(ranked_counts) < 10:
            return None
        xs = [math.log(r) for r in range(1, len(ranked_counts) + 1)]
        ys = [math.log(c) for c in ranked_counts]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        den = sum((x - mean_x) ** 2 for x in xs)
        return round(num / den, 4) if den else None

    def summary(self, top_n: int = 30) -> Dict:
        unique = len(self.counts)
        hapax = sum(1 for c in self.counts.values() if c == 1)
        top = self.counts.most_common(max(top_n, 1000))
        return {
            'total_tokens': self.total_tokens,
            'unique_tokens_observed': unique,
            'type_token_ratio': round(unique / self.total_tokens, 4) if self.total_tokens else 0,
            'hapax_legomena': hapax,
            'hapax_legomena_ratio': round(hapax / unique, 4) if unique else 0,
            'zipf_slope': self._zipf_slope([c for _, c in top]),
            'approximate': self.trimmed,
            'top_words': [{'word': w, 'count': c} for w, c in top[:top_n]],
        }


# ============================================================================
# MAIN BUILDER
# ============================================================================

class Wikipure:
    """
    Two-phase pipeline:

      Phase 1  SQL metadata   → category names, page metadata, category
                                 assignments, (optional) interwiki links,
                                 then the reverse-index language detection
                                 pass described in "WHAT 'PURE' MEANS" above.

      Phase 2  Single XML pass → stream pages-articles.xml once, and for
                                 every page that landed in a language's pure
                                 set, write an identical-schema <page> XML
                                 snippet to that language's *_pure.xml.gz.
    """

    def __init__(self, source_dir: str, output_dir: Optional[str],
                 languages: List[LanguageSpec],
                 include_interwiki: bool, include_page_lang: bool,
                 dump_date_override: Optional[str] = None):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir) if output_dir else self.source_dir / 'wikipure_output'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.languages: Dict[str, LanguageSpec] = {lang.key: lang for lang in languages}
        self.include_interwiki = include_interwiki
        self.include_page_lang = include_page_lang
        self.dump_date_override = dump_date_override

        self.start_time = time.time()
        self.log_lines: List[str] = []

        self._compile_sql_patterns()
        self._setup_file_paths()

        # In-RAM data structures, kept to only what 'pure' detection and
        # XML serialization need
        self.category_names: Dict[int, str] = {}          # category_id -> name
        self.page_metadata: Dict[int, Dict] = {}           # page_id -> {title, page_length, content_model}
        self.page_lang_codes: Dict[int, str] = {}          # page_id -> page_lang value
        self.page_categories: Dict[int, List[str]] = {}    # page_id -> [category names]
        self.page_interwiki_links: Dict[int, Dict[str, str]] = {}  # page_id -> {code: title}
        self.category_counts: Counter = Counter()          # category name -> assignment count
        self.valid_pages: Set[int] = set()                 # namespace-0, non-redirect page IDs

        # language_key -> {'category': set, 'interwiki': set, 'page_lang': set, 'pure': set}
        self.language_page_sets: Dict[str, Dict[str, Set[int]]] = {
            lang_key: {'category': set(), 'interwiki': set(), 'page_lang': set(), 'pure': set()}
            for lang_key in self.languages
        }

        self.language_stats: Dict[str, Dict] = {
            lang_key: {'pages': 0, 'words': 0, 'chars': 0}
            for lang_key in self.languages
        }

        # Advanced statistics: per-language word-frequency tracker (TTR,
        # hapax legomena, approximate Zipf slope) — see WordFrequencyTracker.
        self.word_trackers: Dict[str, WordFrequencyTracker] = {
            lang_key: WordFrequencyTracker() for lang_key in self.languages
        }

        # Structured run log (see write_run_log): phase name -> seconds
        self.phase_durations: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # SETUP
    # ------------------------------------------------------------------

    def _compile_sql_patterns(self):
        """
        Regexes for the SQL tables WIKIPURE needs (page, categorylinks,
        linktarget), plus langlinks for the optional --include-interwiki mode.
        """
        self.patterns = {
            'linktarget': re.compile(r"\((\d+),14,'([^']+)'\)"),
            'categorylinks': re.compile(
                r"\((\d+),'[^']*','[^']*','[^']*','[^']*',\d+,(\d+)\)"),
            'langlinks': re.compile(r"\((\d+),'([^']+)','([^']+)'\)"),
            'page': re.compile(
                r"\((\d+)"                      # [00] page_id
                r",(\d+)"                       # [01] page_namespace
                r",'((?:[^'\\]|\\.)*)'"         # [02] page_title
                r",(\d)"                        # [03] page_is_redirect
                r",\d"                          # [04] page_is_new        (skip)
                r",[\d.]+"                      # [05] page_random        (skip)
                r",'[^']*'"                     # [06] page_touched       (skip)
                r",(?:'[^']*'|NULL)"            # [07] page_links_updated (skip)
                r",\d+"                         # [08] page_latest        (skip)
                r",(\d+)"                       # [09] page_len
                r",'([^']*)'"                   # [10] page_content_model
                r",(NULL|'[^']*')"              # [11] page_lang
                r"\)"
            ),
        }

    # ------------------------------------------------------------------
    # SMART DUMP-FILE DETECTION
    #
    # Real Wiktionary dump directories can vary in three ways this method
    # accounts for:
    #   1. Multiple dump dates present at once (e.g. an old dump not yet
    #      cleaned up) — the most recent COMPLETE one is selected by
    #      default; every date found is logged so nothing is silently
    #      ignored, and dump_date_override lets the caller pin one exactly.
    #   2. SQL tables shipped gzip-compressed (page.sql.gz, etc.) as
    #      Wikimedia distributes them — detected by file suffix and
    #      streamed transparently, no manual decompression needed.
    #   3. The page dump shipped as plain XML, as a "multistream" variant,
    #      or bzip2/gzip-compressed — all four combinations are searched,
    #      in order of parse speed (plain XML first).
    # ------------------------------------------------------------------

    _SQL_BASENAMES = ('page', 'linktarget', 'categorylinks', 'langlinks')
    _XML_VARIANTS = (
        'pages-articles.xml',
        'pages-articles-multistream.xml',
        'pages-articles.xml.bz2',
        'pages-articles-multistream.xml.bz2',
        'pages-articles.xml.gz',
    )

    @staticmethod
    def _open_text(path: Path):
        """Open a .sql file for text reading, transparently handling .gz."""
        if path.suffix == '.gz':
            return gzip.open(path, 'rt', encoding='utf-8', errors='ignore')
        return open(path, 'r', encoding='utf-8', errors='ignore')

    def _resolve_sql_file(self, base_name: str, date: str) -> Optional[Path]:
        """Find one SQL table for a given dump date, plain or .gz."""
        for suffix in ('.sql', '.sql.gz'):
            candidate = self.source_dir / f'enwiktionary-{date}-{base_name}{suffix}'
            if candidate.exists():
                return candidate
        return None

    def _resolve_xml_file(self, date: str) -> Optional[Path]:
        """Find the page-content dump for a given date, trying known variants
        in order of parse speed (plain XML fastest, compressed slowest)."""
        for variant in self._XML_VARIANTS:
            candidate = self.source_dir / f'enwiktionary-{date}-{variant}'
            if candidate.exists():
                return candidate
        return None

    def _dump_is_complete(self, date: str) -> bool:
        required = ['page', 'linktarget', 'categorylinks']
        if self.include_interwiki:
            required.append('langlinks')
        if not all(self._resolve_sql_file(b, date) for b in required):
            return False
        return self._resolve_xml_file(date) is not None

    def _discover_dump_dates(self) -> List[str]:
        """All distinct dump dates present in source_dir, newest first."""
        dates = set()
        for match in glob.glob(str(self.source_dir / 'enwiktionary-*-page.sql*')):
            m = re.search(r'enwiktionary-(\d{8})-page\.sql', match)
            if m:
                dates.add(m.group(1))
        return sorted(dates, reverse=True)

    def _setup_file_paths(self):
        """
        Auto-detect the dump date and every required file, preferring the
        most recent COMPLETE dump when several dates are present. Set
        self.dump_date_override (before calling this) to pin an exact date
        instead of auto-selecting.
        """
        all_dates = self._discover_dump_dates()
        if not all_dates:
            raise FileNotFoundError(
                f"Could not find any 'enwiktionary-*-page.sql[.gz]' in {self.source_dir}. "
                "WIKIPURE cannot auto-detect the dump date."
            )

        if len(all_dates) > 1:
            self.log(f"Multiple dump dates found in source directory: {', '.join(all_dates)}")

        if self.dump_date_override:
            if self.dump_date_override not in all_dates:
                raise FileNotFoundError(
                    f"Requested dump date {self.dump_date_override} not found. "
                    f"Available: {', '.join(all_dates)}"
                )
            chosen = self.dump_date_override
            self.log(f"Using explicitly requested dump date: {chosen}")
        else:
            complete_dates = [d for d in all_dates if self._dump_is_complete(d)]
            if not complete_dates:
                raise FileNotFoundError(
                    f"Found dump date(s) {', '.join(all_dates)} but none has all required "
                    f"files (page, linktarget, categorylinks"
                    f"{', langlinks' if self.include_interwiki else ''}, and a pages-articles "
                    f"XML variant). Check the source directory."
                )
            chosen = complete_dates[0]  # newest complete
            if len(all_dates) > 1:
                self.log(f"Selected most recent complete dump: {chosen}")

        self.dump_date = chosen

        self.input_files = {
            'page':          self._resolve_sql_file('page', chosen),
            'linktarget':    self._resolve_sql_file('linktarget', chosen),
            'categorylinks': self._resolve_sql_file('categorylinks', chosen),
            'xml':           self._resolve_xml_file(chosen),
        }
        if self.include_interwiki:
            self.input_files['langlinks'] = self._resolve_sql_file('langlinks', chosen)

        missing = [k for k, p in self.input_files.items() if p is None]
        if missing:
            raise FileNotFoundError(f"Required dump file(s) not found for {missing}")

        self.log(f"Dump date: {self.dump_date}")
        for key, path in self.input_files.items():
            self.log(f"  {key:15s} {path.name}")
        self.log(f"Detection sources: category patterns (always)"
                  f"{', interwiki links' if self.include_interwiki else ''}"
                  f"{', page_lang field' if self.include_page_lang else ''}")

    def log(self, message: str):
        elapsed = time.time() - self.start_time
        line = f"[{elapsed:7.1f}s] {message}"
        print(line)
        self.log_lines.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}")

    # ------------------------------------------------------------------
    # PHASE 1 — SQL METADATA
    # ------------------------------------------------------------------

    def pass1_load_category_names(self):
        start = time.time()
        self.log("PASS 1: Loading category names (linktarget.sql)")
        with self._open_text(self.input_files['linktarget']) as f:
            for line in f:
                if not line.startswith('INSERT INTO'):
                    continue
                for category_id, category_title in self.patterns['linktarget'].findall(line):
                    self.category_names[int(category_id)] = category_title.replace('_', ' ')
        self.log(f"  -> {len(self.category_names):,} categories in {time.time()-start:.1f}s")

    def pass2_load_page_metadata(self):
        start = time.time()
        self.log("PASS 2: Loading page metadata (page.sql)")
        valid_count = 0
        with self._open_text(self.input_files['page']) as f:
            for line in f:
                if not line.startswith('INSERT INTO'):
                    continue
                for page_id, namespace, title, is_redirect, page_len, content_model, page_lang_raw \
                        in self.patterns['page'].findall(line):
                    ns = int(namespace)
                    is_redir = int(is_redirect) == 1
                    if ns != 0 or is_redir:
                        continue

                    pid = int(page_id)
                    self.valid_pages.add(pid)
                    valid_count += 1
                    self.page_metadata[pid] = {
                        'title': title.replace('_', ' '),
                        'page_length': int(page_len),
                        'content_model': content_model if content_model else 'wikitext',
                    }

                    if self.include_page_lang and page_lang_raw and page_lang_raw != 'NULL':
                        lang_val = page_lang_raw.strip("'").strip()
                        if lang_val:
                            self.page_lang_codes[pid] = lang_val

                    if valid_count % 500_000 == 0:
                        self.log(f"  ... {valid_count:,} pages processed")
        gc.collect()
        self.log(f"  -> {valid_count:,} valid (ns0, non-redirect) pages in {time.time()-start:.1f}s")

    def pass3_build_category_assignments(self):
        start = time.time()
        self.log("PASS 3: Building category assignments (categorylinks.sql)")
        assignments = 0
        with self._open_text(self.input_files['categorylinks']) as f:
            for line in f:
                if not line.startswith('INSERT INTO'):
                    continue
                for page_id, category_target_id in self.patterns['categorylinks'].findall(line):
                    pid = int(page_id)
                    if pid not in self.valid_pages:
                        continue
                    cat_name = self.category_names.get(int(category_target_id))
                    if cat_name is None:
                        continue
                    self.page_categories.setdefault(pid, []).append(cat_name)
                    self.category_counts[cat_name] += 1
                    assignments += 1
        self.log(f"  -> {assignments:,} category assignments "
                  f"({len(self.page_categories):,} pages) in {time.time()-start:.1f}s")

    def pass4_load_interwiki_links(self):
        if not self.include_interwiki:
            return
        start = time.time()
        self.log("PASS 4: Loading interwiki links (langlinks.sql)  [--include-interwiki]")
        links = 0
        with self._open_text(self.input_files['langlinks']) as f:
            for line in f:
                if not line.startswith('INSERT INTO'):
                    continue
                for page_id, lang_code, lang_title in self.patterns['langlinks'].findall(line):
                    pid = int(page_id)
                    if pid not in self.valid_pages:
                        continue
                    self.page_interwiki_links.setdefault(pid, {})[lang_code] = lang_title.replace('_', ' ')
                    links += 1
        self.log(f"  -> {links:,} interwiki links in {time.time()-start:.1f}s")

    def pass5_detect_languages(self):
        """
        Reverse-index detection: build category -> {language_keys} once
        (O(unique_categories)) rather than testing every page against every
        pattern (O(pages x languages)).
        """
        start = time.time()
        self.log("PASS 5: Language detection (reverse index)")

        cat_to_lang: Dict[str, Set[str]] = {}
        for cat in self.category_counts.keys():
            for lang_key, lang_spec in self.languages.items():
                if lang_spec.category_pattern.match(cat):
                    cat_to_lang.setdefault(cat, set()).add(lang_key)

        iw_to_lang: Dict[str, Set[str]] = {}
        if self.include_interwiki:
            for lang_key, lang_spec in self.languages.items():
                for code in lang_spec.interwiki_codes:
                    iw_to_lang.setdefault(code, set()).add(lang_key)

        for page_id, cats in self.page_categories.items():
            for cat in cats:
                for lang_key in cat_to_lang.get(cat, ()):
                    self.language_page_sets[lang_key]['category'].add(page_id)

        if self.include_interwiki:
            for page_id, links in self.page_interwiki_links.items():
                for code in links.keys():
                    for lang_key in iw_to_lang.get(code, ()):
                        self.language_page_sets[lang_key]['interwiki'].add(page_id)

        if self.include_page_lang:
            for lang_key, lang_spec in self.languages.items():
                code_set = set(lang_spec.interwiki_codes)
                for page_id, lang_code in self.page_lang_codes.items():
                    if lang_code in code_set:
                        self.language_page_sets[lang_key]['page_lang'].add(page_id)

        for lang_key in self.languages:
            sets = self.language_page_sets[lang_key]
            sets['pure'] = set(sets['category'])
            if self.include_interwiki:
                sets['pure'] |= sets['interwiki']
            if self.include_page_lang:
                sets['pure'] |= sets['page_lang']

        del cat_to_lang, iw_to_lang
        gc.collect()

        for lang_key, lang_spec in self.languages.items():
            n = len(self.language_page_sets[lang_key]['pure'])
            self.log(f"  {lang_spec.name:20s} {n:>8,} pure pages")
        self.log(f"  -> detection complete in {time.time()-start:.1f}s")

    def phase1(self):
        _t0 = time.time()
        self.log("=" * 70)
        self.log("PHASE 1: SQL METADATA")
        self.log("=" * 70)
        self.pass1_load_category_names()
        self.pass2_load_page_metadata()
        self.pass3_build_category_assignments()
        self.pass4_load_interwiki_links()
        self.pass5_detect_languages()
        self.phase_durations['phase1_sql_metadata'] = round(time.time() - _t0, 2)

    # ------------------------------------------------------------------
    # PHASE 2 — XML EXTRACTION
    # ------------------------------------------------------------------

    def _extract_page_data(self, elem) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """Extract (page_id, title, revision text) for a <page> XML element."""
        id_elem = elem.find('.//{http://www.mediawiki.org/xml/export-0.11/}id')
        if id_elem is None or id_elem.text is None:
            return None, None, None
        try:
            page_id = int(id_elem.text)
        except ValueError:
            return None, None, None
        if page_id not in self.page_metadata:
            return None, None, None

        title = self.page_metadata[page_id]['title']
        text_content = ""
        rev_elem = elem.find('.//{http://www.mediawiki.org/xml/export-0.11/}revision')
        if rev_elem is not None:
            text_elem = rev_elem.find('.//{http://www.mediawiki.org/xml/export-0.11/}text')
            if text_elem is not None and text_elem.text:
                text_content = text_elem.text
        return page_id, title, text_content

    @staticmethod
    def _xml_escape(text: str) -> str:
        """Escape XML special characters (&, <, >) in output text."""
        if not text:
            return ""
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _generate_xml_snippet(self, page_id: int, title: str, text: str) -> str:
        """Serialize one page to the output <page> XML schema."""
        snippet = '  <page>\n'
        snippet += f'    <title>{self._xml_escape(title)}</title>\n'
        snippet += f'    <id>{page_id}</id>\n'

        if page_id in self.page_categories:
            snippet += '    <categories>\n'
            for cat in sorted(self.page_categories[page_id],
                               key=lambda c: self.category_counts.get(c, 0), reverse=True):
                snippet += f'      <category>{self._xml_escape(cat)}</category>\n'
            snippet += '    </categories>\n'

        if text:
            snippet += '    <revision>\n'
            snippet += '      <text xml:space="preserve">'
            snippet += self._xml_escape(text)
            snippet += '</text>\n'
            snippet += '    </revision>\n'

        snippet += '  </page>\n'
        return snippet

    @staticmethod
    def _open_xml_source(path: Path):
        """
        Return whatever ET.iterparse should consume for this dump's page
        file, decompressing on the fly if needed.

        Plain .xml: return the path itself (str) — both lxml and the
        standard library parse a path fastest by handling their own
        buffering, rather than going through a Python file object.

        .xml.bz2 / multistream .xml.bz2: bz2.open() transparently
        decompresses concatenated bz2 streams (which is exactly what a
        "multistream" dump is), so no special-casing is needed beyond
        opening it in binary mode.

        .xml.gz: gzip.open() in binary mode.

        Returns (source, file_handle_to_close_or_None).
        """
        if path.suffix == '.bz2':
            fh = bz2.open(path, 'rb')
            return fh, fh
        if path.suffix == '.gz':
            fh = gzip.open(path, 'rb')
            return fh, fh
        return str(path), None

    def phase2_extract_xml(self):
        start = time.time()
        self.log("=" * 70)
        self.log("PHASE 2: XML EXTRACTION (single pass)")
        self.log("=" * 70)

        lang_dirs = {}
        output_files = {}
        for lang_key in self.languages:
            lang_dir = self.output_dir / lang_key
            lang_dir.mkdir(parents=True, exist_ok=True)
            lang_dirs[lang_key] = lang_dir
            output_files[lang_key] = gzip.open(
                lang_dir / f"{lang_key}_pure.xml.gz", 'wt', encoding='utf-8', compresslevel=1
            )
            output_files[lang_key].write('<?xml version="1.0" encoding="UTF-8"?>\n')
            output_files[lang_key].write(
                '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/" version="0.11">\n'
            )

        self.log(f"Opened {len(output_files)} output file(s)")

        processed = included = 0
        last_log = time.time()
        _xml_source, _xml_fh = self._open_xml_source(self.input_files['xml'])
        self.log(f"Reading page content from: {self.input_files['xml'].name}")

        try:
            for event, elem in ET.iterparse(_xml_source, events=('end',)):
                if not elem.tag.endswith('page'):
                    continue
                processed += 1

                if time.time() - last_log > 30:
                    self.log(f"  ... {processed:,} pages scanned, {included:,} written")
                    last_log = time.time()

                page_id, title, text = self._extract_page_data(elem)
                if page_id is None:
                    elem.clear()
                    continue

                wrote_any = False
                for lang_key in self.languages:
                    if page_id in self.language_page_sets[lang_key]['pure']:
                        snippet = self._generate_xml_snippet(page_id, title, text)
                        output_files[lang_key].write(snippet)
                        self.language_stats[lang_key]['pages'] += 1
                        if text:
                            word_count = len(re.findall(r'\w+', text.lower()))
                            self.language_stats[lang_key]['words'] += word_count
                            self.language_stats[lang_key]['chars'] += len(text)
                            self.word_trackers[lang_key].add_text(text)
                        wrote_any = True

                if wrote_any:
                    included += 1
                elem.clear()

                if included % 5000 == 0 and included:
                    for f in output_files.values():
                        f.flush()
                    if included % 50000 == 0:
                        gc.collect()
        finally:
            if _xml_fh is not None:
                _xml_fh.close()

        for f in output_files.values():
            f.write('</mediawiki>\n')
            f.close()

        self.log(f"  -> {processed:,} pages scanned, {included:,} pages written "
                  f"in {time.time()-start:.1f}s")
        self.phase_durations['phase2_xml_extraction'] = round(time.time() - start, 2)

    # ------------------------------------------------------------------
    # STATISTICS / AUDIT JSON
    # ------------------------------------------------------------------

    def write_statistics(self):
        self.log("Writing per-language statistics JSON")
        generated_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        sources_enabled = ['category_patterns']
        if self.include_interwiki:
            sources_enabled.append('interwiki_links')
        if self.include_page_lang:
            sources_enabled.append('page_lang_field')

        for lang_key, lang_spec in self.languages.items():
            sets = self.language_page_sets[lang_key]
            stat = self.language_stats[lang_key]
            pure_n = len(sets['pure'])

            top_categories = Counter()
            for pid in sets['pure']:
                for cat in self.page_categories.get(pid, []):
                    top_categories[cat] += 1

            advanced = self.word_trackers[lang_key].summary()

            stats = {
                'tool': 'WIKIPURE v1.0',
                'language': lang_spec.name,
                'language_key': lang_key,
                'tier': lang_spec.tier,
                'typology': lang_spec.typology,
                'generated_at': generated_at,
                'dump_date': self.dump_date,
                'detection': {
                    'sources_enabled': sources_enabled,
                    'category_pattern': lang_spec.pattern_source,
                    'category_pattern_origin': lang_spec.pattern_origin,
                    'category_pattern_validated_against_real_dump': (lang_spec.tier == 'resource-poor'),
                    'interwiki_codes': lang_spec.interwiki_codes,
                },
                'pages': {
                    'pure_total': pure_n,
                    'from_category_patterns': len(sets['category']),
                    'from_interwiki_links': len(sets['interwiki']) if self.include_interwiki else None,
                    'from_page_lang_field': len(sets['page_lang']) if self.include_page_lang else None,
                },
                'corpus': {
                    'total_words': stat['words'],
                    'total_characters': stat['chars'],
                    'avg_words_per_page': round(stat['words'] / pure_n, 2) if pure_n else 0,
                    'type_token_ratio': advanced['type_token_ratio'],
                    'unique_tokens_observed': advanced['unique_tokens_observed'],
                    'hapax_legomena': advanced['hapax_legomena'],
                    'hapax_legomena_ratio': advanced['hapax_legomena_ratio'],
                    'zipf_slope': advanced['zipf_slope'],
                    'word_frequency_approximate': advanced['approximate'],
                },
                'top_words': advanced['top_words'],
                'top_categories': [
                    {'category': cat, 'count': count}
                    for cat, count in top_categories.most_common(20)
                ],
                'output_file': f"{lang_key}_pure.xml.gz",
            }

            lang_dir = self.output_dir / lang_key
            with open(lang_dir / f"{lang_key}_pure_statistics.json", 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

        if len(self.languages) > 1:
            self._write_overlap_report(generated_at)

    def _write_overlap_report(self, generated_at: str):
        """
        Cross-language overlap: pages whose categories matched more than one
        of the selected languages' patterns in the same run — relevant for
        lexical-contact / borrowing studies (e.g. shared entries across
        Arabic and Aramaic pure sets).
        """
        self.log("Writing cross-language overlap report")
        keys = list(self.languages.keys())
        pairs = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                shared = self.language_page_sets[k1]['pure'] & self.language_page_sets[k2]['pure']
                if shared:
                    pairs.append({
                        'language_a': self.languages[k1].name,
                        'language_b': self.languages[k2].name,
                        'shared_pages': len(shared),
                        'sample_page_ids': sorted(list(shared))[:20],
                    })

        report = {
            'tool': 'WIKIPURE v1.0',
            'generated_at': generated_at,
            'dump_date': self.dump_date,
            'languages_in_run': [self.languages[k].name for k in keys],
            'note': 'A page appears in more than one language\'s pure set when its '
                    'Wiktionary categories matched both languages\' category patterns '
                    '(e.g. a page with both an "Arabic ..." and an "Aramaic ..." '
                    'category). This is a raw overlap count, not a claim about '
                    'etymological borrowing.',
            'overlaps': pairs,
        }
        with open(self.output_dir / 'wikipure_overlap_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # ORCHESTRATION
    # ------------------------------------------------------------------

    def write_run_log(self, status: str, error: Optional[str] = None):
        """
        Two files for reproducibility / efficiency auditing:
          wikipure_run.log   plain timestamped text, mirrors console output
          wikipure_run.json  structured machine-readable summary: phase
                              durations, environment, per-language final
                              counts, dump date, and run status
        """
        total_time = time.time() - self.start_time

        with open(self.output_dir / 'wikipure_run.log', 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.log_lines) + '\n')

        summary = {
            'tool': 'WIKIPURE v1.0',
            'status': status,
            'error': error,
            'started_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.start_time)),
            'finished_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'total_seconds': round(total_time, 2),
            'dump_date': getattr(self, 'dump_date', None),
            'source_dir': str(self.source_dir),
            'output_dir': str(self.output_dir),
            'environment': {
                'ujson_available': _UJSON_AVAILABLE,
                'lxml_available': _LXML_AVAILABLE,
                'python_version': sys.version.split()[0],
            },
            'detection_flags': {
                'include_interwiki': self.include_interwiki,
                'include_page_lang': self.include_page_lang,
            },
            'phase_durations_seconds': self.phase_durations,
            'languages': {
                lang_key: {
                    'pages': self.language_stats[lang_key]['pages'],
                    'words': self.language_stats[lang_key]['words'],
                    'category_pattern_origin': self.languages[lang_key].pattern_origin,
                }
                for lang_key in self.languages
            },
        }
        with open(self.output_dir / 'wikipure_run.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def build(self):
        try:
            self.phase1()
            self.phase2_extract_xml()
            self.write_statistics()

            total_time = time.time() - self.start_time
            self.log("=" * 70)
            self.log(f"DONE in {int(total_time//60)}m {int(total_time%60)}s")
            self.log("=" * 70)
            for lang_key, lang_spec in self.languages.items():
                n = self.language_stats[lang_key]['pages']
                self.log(f"  {lang_spec.name:20s} {n:>8,} pages "
                         f"-> {self.output_dir / lang_key / (lang_key + '_pure.xml.gz')}")
            self.write_run_log(status='success')
        except Exception as e:
            self.log(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.write_run_log(status='failed', error=str(e))
            raise


# ============================================================================
# INTERACTIVE MODE (for running directly inside IDLE / double-click, i.e.
# whenever the script is launched with no command-line arguments at all)
# ============================================================================

def _ask(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else (default or "")


def _ask_yes_no(prompt: str, default_no: bool = True) -> bool:
    suffix = " [y/N]" if default_no else " [Y/n]"
    val = input(f"{prompt}{suffix}: ").strip().lower()
    if not val:
        return not default_no
    return val in ('y', 'yes')


def interactive_main():
    print("=" * 70)
    print("WIKIPURE v1.0 — Interactive Mode")
    print("=" * 70)
    print("Default: category-pattern detection only. Just two questions.")
    print(f"Tier shortcuts: type 'resource-poor' ({len(LANGUAGE_TIERS['resource-poor'])} langs), "
          f"'resource-rich' ({len(LANGUAGE_TIERS['resource-rich'])} langs), or 'all' "
          f"instead of listing names.")
    print("=" * 70)

    source_dir = _ask("Dump directory (folder containing the enwiktionary-* files)")
    while not source_dir or not Path(source_dir).exists():
        print(f"  Directory not found: '{source_dir}'")
        source_dir = _ask("Dump directory (folder containing the enwiktionary-* files)")

    names_raw = _ask("Language(s) to extract, comma-separated, or a tier keyword (e.g. Arabic, Hebrew)")
    while not names_raw.strip():
        names_raw = _ask("Please enter at least one language name or tier keyword")

    languages: Dict[str, LanguageSpec] = {}
    for token in [n.strip() for n in names_raw.split(',') if n.strip()]:
        expanded = expand_tier_keyword(token)
        for name in (expanded if expanded else [token]):
            lang_spec = parse_lang_arg(name)   # name only -> curated/auto pattern, no explicit codes
            languages[lang_spec.key] = lang_spec

    output_dir = str(Path(source_dir) / 'wikipure_output')

    print("\n" + "=" * 70)
    print(f"Source:     {source_dir}")
    print(f"Output:     {output_dir}")
    print(f"Languages:  " + ", ".join(l.name for l in languages.values()))
    print(f"Detection:  category patterns only")
    for l in languages.values():
        origin_note = {
            'curated_preset': '[hand-curated dialect-aware pattern]',
            'auto_generated': '[auto-generated — not in the curated language list]',
            'custom': '[custom]',
        }[l.pattern_origin]
        print(f"            {l.name}: {l.pattern_source}  {origin_note}")
    print("=" * 70)
    print("(For dialect codes, custom patterns, or widened detection, run from")
    print(" the command line instead — see --help.)")
    print("=" * 70)

    builder = Wikipure(
        source_dir=source_dir,
        output_dir=output_dir,
        languages=list(languages.values()),
        include_interwiki=False,
        include_page_lang=False,
    )
    builder.build()

    # IDLE's shell window stays open on its own after the script finishes,
    # so the pause is only needed when double-clicked from Windows Explorer
    # (where the console closes instantly and would hide the results).
    if 'idlelib' not in sys.modules:
        input("\nDone. Press Enter to close...")


# ============================================================================
# CLI
# ============================================================================

def main():
    # No arguments at all (e.g. launched via IDLE's Run/F5, or double-clicked)
    # → fall back to the interactive prompt instead of failing on argparse.
    if len(sys.argv) == 1:
        interactive_main()
        return

    parser = argparse.ArgumentParser(
        prog='wikipure.py',
        description='WIKIPURE v1.0 — Dynamic multi-language "pure" XML extractor for Wiktionary dumps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
Examples:
  python wikipure.py /path/to/dump --lang arabic:ar,arz,arq
  python wikipure.py /path/to/dump --lang arabic --lang hebrew
  python wikipure.py /path/to/dump --lang "arabic:ar,arz:^(?:Arabic|Egyptian Arabic)\s+"
  python wikipure.py /path/to/dump --lang arabic:ar,arz --include-interwiki --include-page-lang
  python wikipure.py /path/to/dump --lang-tier resource-poor
  python wikipure.py /path/to/dump --lang-tier resource-poor --lang-tier resource-rich
  python wikipure.py /path/to/dump --lang-tier resource-rich --lang aramaic

  Running with NO arguments (e.g. F5 inside IDLE) launches interactive mode
  instead, which prompts for everything step by step.
        """,
    )
    parser.add_argument('source_dir', help='Directory containing the Wiktionary dump files')
    parser.add_argument(
        '--lang', action='append', required=False, default=[], dest='languages',
        type=parse_lang_arg, metavar='name[:code1,code2][:custom_regex]',
        help='Language to extract. Repeatable. Format: name[:iw_code1,iw_code2][:custom_category_regex]. '
             'Interwiki codes are optional and only used with --include-interwiki.'
    )
    parser.add_argument(
        '--lang-tier', action='append', default=[], dest='lang_tiers',
        choices=['resource-poor', 'resource-rich', 'all'],
        help="Add every language in a tier shortcut instead of listing names one by one. "
             f"resource-poor = {len(LANGUAGE_TIERS['resource-poor'])} curated low-resource languages, "
             f"resource-rich = {len(LANGUAGE_TIERS['resource-rich'])} comparison languages, "
             "all = both. Repeatable; combine freely with --lang."
    )
    parser.add_argument('--output-dir', default=None,
                         help='Output directory (default: <source_dir>/wikipure_output)')
    parser.add_argument('--dump-date', default=None, metavar='YYYYMMDD',
                         help='Pin an exact dump date instead of auto-selecting the most '
                              'recent complete one found in source_dir (useful when several '
                              'dump dates are present at once).')
    parser.add_argument('--include-interwiki', action='store_true',
                         help='Widen "pure" to also include pages reached via interwiki links (requires langlinks.sql)')
    parser.add_argument('--include-page-lang', action='store_true',
                         help='Widen "pure" to also include pages whose page_lang field matches')

    args = parser.parse_args()

    # De-duplicate languages by key, keeping the last definition if repeated
    languages: Dict[str, LanguageSpec] = {}
    for tier in args.lang_tiers:
        for name in expand_tier_keyword(tier):
            lang_spec = parse_lang_arg(name)
            languages[lang_spec.key] = lang_spec
    for lang in args.languages:
        languages[lang.key] = lang

    if not languages:
        parser.error("no languages specified — use --lang and/or --lang-tier")

    print("=" * 70)
    print("WIKIPURE v1.0 — Dynamic Multi-Language Pure XML Extractor")
    print("=" * 70)
    print(f"Source:  {args.source_dir}")
    print(f"Output:  {args.output_dir or (Path(args.source_dir) / 'wikipure_output')}")
    print(f"Languages ({len(languages)}): " + ", ".join(l.name for l in languages.values()))
    print("=" * 70)

    builder = Wikipure(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        languages=list(languages.values()),
        include_interwiki=args.include_interwiki,
        include_page_lang=args.include_page_lang,
        dump_date_override=args.dump_date,
    )
    builder.build()


if __name__ == '__main__':
    main()
