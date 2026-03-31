# Rongorongo Decipherment — ALBA Grid v4

A computational approach to deciphering rongorongo, the undeciphered script of Easter Island (Rapa Nui).

## Summary

This repository contains a proposed 48-sign phonetic grid for rongorongo, derived through distributional analysis, brute-force testing, kill-shot validation, cross-tablet confirmation, and limited rebus cues. The grid is validated by four complementary lines of evidence:

- **Leave-one-family-out cross-validation**: combined p<0.001 (equivalent Z=4.65; 10 independent tablet families, 5000 permutations each, Englert-only dictionary — no cognates)
- **Leave-one-tablet-out**: combined p<0.001 (equivalent Z=3.54; 13 classic tablets)
- **Pozdniakov external concordance**: 81% overlap with independently identified 52-glyph inventory (Pozdniakov & Pozdniakov 2007); 4/4 "arm glyphs" confirmed as vowels; frequency rank correlation rho=0.563, p<0.01
- **Robustness without cognates**: Signal strengthens when Polynesian cognates are removed (equivalent Z=5.88 tablet-out, Z=4.65 family-out)
- **Coverage**: 93.6% on classic tablets (A-S), 85.9% full corpus (25 tablets, 18,275 glyphs)
- **Particle proportion**: 31.1% in output vs 32.9% in real Rapa Nui texts

## The 48-Sign Grid

| Type | Count | Examples |
|------|-------|---------|
| Vowels | 20 glyphs → 5 phonemes | /a/ (9 allographs), /e/, /i/, /o/, /u/ |
| Consonants | 11 glyphs → 9 phonemes | /t/, /k/, /h/, /m/, /n/, /r/, /p/, /ng/, /v/ |
| Syllabograms | 17 glyphs → 11 values | /ra/ (6 allographs), /ma/, /ki/, /ko/, /na/, /ri/, /ta/, /te/, /ha/, /hua/ |

Full grid with confidence levels: [`results/grid_48_signs.csv`](results/grid_48_signs.csv)

### Confidence levels

Each sign is classified by converging evidence:

| Level | Criteria | Count |
|-------|----------|-------|
| **A** (near-certain) | Kill-shot confirmed + in Pozdniakov 52 + cross-tablet | 9 signs |
| **B** (strong) | Kill-shot OR (Pozdniakov 52 + high cross-tablet frequency) | 31 signs |
| **C** (speculative) | Brute-force only, not in Pozdniakov 52 | 7 signs |

Confidence matrix: [`results/CONFIDENCE_MATRIX_v1.csv`](results/CONFIDENCE_MATRIX_v1.csv)

## Corpus

- **25 tablets** (A-Y) including the Santiago Staff (I)
- **18,275 glyphs** indexed by tablet, line, and position
- Source: Barthel (1958) codes via [rongopy](https://github.com/joelsimon/rongopy)
- Database: [`data/rongorongo.db`](data/rongorongo.db) (SQLite)

## Scripts

### Translation
```bash
# Viterbi 6-layer bidirectional segmenter (recommended)
python scripts/alba_rongorongo_viterbi.py N        # Connected reading
python scripts/alba_rongorongo_viterbi.py N -i     # Interlinear gloss

# Raw word-by-word translator
python scripts/translate_rongorongo.py N           # Single tablet
python scripts/translate_rongorongo.py --all       # All tablets summary
```

### Validation
```bash
python scripts/robustness_checks.py        # Leave-one-out + random grids
python scripts/alba_rongorongo_family_out.py  # Leave-one-family-out
python scripts/alba_rongorongo_pozdniakov.py  # Pozdniakov CV alternation + frequency
```

## Translated Tablets

| Tablet | Name | Glyphs | Genre | Coverage |
|--------|------|--------|-------|----------|
| A | Tahua | 2,364 | Epic patautau | 93.6% |
| B | Aruku Kurenga | 1,626 | Composite patautau | 93.3% |
| C | Mamari | 1,200 | Composite liturgical | 95.1% |
| D | Echancrée | 332 | Cosmogony | 98.5% |
| E | Keiti | 1,091 | Funerary (ate) | 95.1% |
| G | Petit Santiago | 832 | Biface mana | 90.1% |
| H | Grand Santiago | 2,066 | Grand Texte | 93.6% |
| K | Londres | 264 | Kai-kai | 95.5% |
| N | Petit de Vienne | 310 | Solar hymn | 96.8% |
| P | Grand St-Petersbourg | 1,993 | Grand Texte ceremonial | 91.7% |
| Q | Petit St-Petersbourg | 1,169 | Rain/cradle chant | 93.3% |
| R | Petit de Santiago | 647 | Cosmic path | 96.1% |
| S | Grand de Vienne | 1,012 | Katabasis | 93.1% |

Full translations with philological notes: [`translations/`](translations/)

## Dictionary

9,383 entries from:
- Englert (1978) — primary source (~1,750 entries)
- Kieviet (2017) — modern Rapa Nui grammar
- IDS (Intercontinental Dictionary Series) — Rapa Nui chapter
- Productive morphology: reduplication, haka- (causative), -ga (nominalization)
- Polynesian cognates: Maori, Hawaiian, Tahitian (tested separately in robustness checks)

## Viterbi Segmenter

The 6-layer bidirectional Viterbi applies simultaneously:

1. **Dictionary** — 9,383 words scored by frequency
2. **POS Grammar** — 68 empirical bigrams + 56 forbidden pairs from real Rapa Nui texts
3. **Collocations** — 24 attested pairs from Barthel/Fischer chants
4. **Cross-tablet anchors** — 8 confirmed segmentations
5. **Morphology** — ~200 generated forms (causative, nominalizations, reduplications)
6. **Single-vowel penalty** — Reduces parasitic isolated vowels from 28% to 10%

Bidirectional pass marks confidence: unmarked = both passes agree, `?` = uncertain boundary.

## Validation Summary

*Note on "Englert-only + morphology" (9,653 words)*: This dictionary removes all Polynesian cognates (Maori, Hawaiian, Tahitian) and replaces them with productive morphological forms (causatives, nominalizations, reduplications) derived from attested Rapa Nui bases. The count exceeds the full dictionary (9,383) because morphological expansion generates more forms than the removed cognates.

| Test | Dictionary | Z-equivalent | p-value | Result |
|------|-----------|---------|---------|--------|
| Leave-one-tablet-out | Full (9,383) | 3.54 | < 0.001 | *** |
| Leave-one-tablet-out | Englert-only + morphology (9,653) | 5.88 | < 0.001 | *** |
| Leave-one-family-out | Full (9,383) | 2.59 | < 0.01 | ** |
| Leave-one-family-out | Englert-only + morphology (9,653) | 4.65 | < 0.001 | *** |
| 100 random grids | Full (9,383) | 1.47 | 0.08 | 92nd percentile |
| Pozdniakov frequency | — | rho=0.563 | < 0.01 | ** |

Families: {H,P,Q} (Grand Texte copies), {G,K} (shared passages), + 8 individual tablets.

## Status

This is an **exploratory decipherment** (classification D on the Sproat scale). All phonetic values are hypotheses validated statistically but not yet peer-reviewed. The allograph system is massive (up to 9 variants per phoneme) — some assignments may be incorrect. 6.4% of the classic corpus remains undecoded.

## Citation

If you use this work, please cite:

> Sivan, J. (2026). A Computational Approach to Rongorongo: A 48-Sign Phonetic Grid Validated by Leave-One-Family-Out Cross-Validation and External Concordance with Pozdniakov (2007). ALBA Research. Preprint.

## License

- Code: GPL-3.0
- Data and text: CC-BY 4.0

## Contact

ALBA Research — [alba-project.org](https://alba-project.org) | [github.com/Alba-Research](https://github.com/Alba-Research)
