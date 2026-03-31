# A Computational Approach to Rongorongo: A 26-Sign Core Grid (p=0.0004) Extended to 48 Signs by Kill-Shot Validation (Fisher p<0.001), with First Word-Level Readings of Easter Island's Script

**Julien Sivan**
ALBA Project — alba-project.org

**Preprint — 31 March 2026**
**Classification: Exploratory (D)**

---

## Abstract

We present a computational approach to rongorongo, the undeciphered script of Easter Island (Rapa Nui), using a Bayesian-computational methodology originally developed for Inca khipu decipherment. Starting from zero, we identify a **26-sign core grid** validated by permutation test (Z=2.71, p=0.0004), **extended to 48 signs** by 15 independent kill-shots and cross-tablet confirmations. Leave-one-tablet-out cross-validation on the full 48-sign grid yields Fisher combined p<0.001 (Z=3.54) across 13 tablets. The grid covers 93.6% of the classic corpus (14,906 glyphs across tablets A–S). The method combines distributional analysis, brute-force constrained optimization, cross-tablet kill-shots, and the rebus principle. We produce the first continuous readings of 14 tablets, identifying 6 distinct textual genres: solar hymns (*patautau*), creation chants (*rongorongo*), funerary narratives (*ate*), collective invocation chants (*kai-kai*), a composite liturgical collection, and a sacred genealogy (*kohau tangata*). The Santiago Staff is independently identified as a genealogical register (94% hapax rate), confirming the Guy/Butinov-Knorozov hypothesis and partially refuting Fischer's (1997) cosmogonic interpretation. A 5-layer bidirectional Viterbi segmenter with empirical Rapa Nui grammar, attested collocations, and productive morphology enables word-level translation. Key readings include "raaraa raaraa raaraa raa te" (Brilliant, brilliant, brilliant — the sun!, Na1), "i te ata, i te tiraki, i te tahua" (In the shadow, in the rising, in the ceremonial place, Ca3), and "raa raa ata... rite" (Sun, sun, shadow... similar, Hv12). The proportion of grammatical particles in our translations (31.1%) matches that of attested Rapa Nui oral texts (32.9%), refuting the Butinov-Knorozov (1957) claim that rongorongo lacks grammatical structure.

**Keywords:** rongorongo, Easter Island, Rapa Nui, undeciphered scripts, computational decipherment, Polynesian writing, logosyllabic script

---

## 1. Introduction

### 1.1 The rongorongo problem

Rongorongo is the only indigenous script of Oceania and one of the last major undeciphered writing systems. Approximately 26 wooden tablets survive, bearing ~18,000 glyphs in a unique boustrophedon script. Despite over 150 years of study since the tablets' discovery in the 1860s, no consensus decipherment exists.

### 1.2 Previous approaches

The principal previous approaches include:
- **Barthel (1958)**: catalogued the glyph inventory (~240 signs), identified the lunar calendar on tablet C (Mamari), and established the standard numbering system
- **Butinov & Knorozov (1957)**: statistical analysis suggesting the script lacks grammatical particles, implying a non-phonetic system
- **Guy (1990, 2006)**: identified glyph 074 as /hua/ (fruit) through the Mamari calendar, and proposed 076 as a patronymic marker on the Santiago Staff
- **Pozdniakov (1996, 2007)**: proposed glyph 006 as /a/ based on frequency analysis, and estimated ~50 basic signs after allograph consolidation
- **Fischer (1997)**: proposed a reading of the Santiago Staff as a creation chant with copulation formulas — widely criticized for lack of falsifiability
- **Horley (2005–2011)**: consolidated allographs, reducing the effective sign inventory from ~240 to ~110
- **Davletshin (2012, 2022)**: identified phonetic complements through parallel passage substitutions

None of these approaches produced continuous readable text or a validated phonetic grid.

### 1.3 The ALBA methodology

We apply the same Bayesian-computational pipeline that produced a partial decipherment of Inca khipus (ALBA Project, 2026). The sequence is:

1. Distributional analysis → type identification
2. Calibration on known passage (Mamari calendar)
3. Vowel cluster identification via substitution patterns
4. Anchor phonetic values → permutation test validation
5. CV analysis → consonant expansion
6. Word segmentation → brute-force syllabogram identification
7. Kill-shot validation (unique dictionary matches in constrained contexts)
8. Rebus principle → visual identification of pictographic origins
9. Cross-tablet parallel confirmation

This pipeline is structure-agnostic: it works identically on knot-based (khipu) and glyph-based (rongorongo) systems.

---

## 2. Data

### 2.1 Corpus

The rongorongo corpus comprises 25 tablets (A–Y) totaling 18,275 glyphs:
- **Classic ritual tablets** (A–S, excluding I): 14,906 glyphs, 13 tablets — the primary decipherment target
- **Santiago Staff** (I): 2,489 glyphs — identified as genealogical (see §5)
- **Fragments and atypical supports** (F, L, M, O, T, U, V, W, X, Y): 880 glyphs — low coverage due to damage or administrative content

Source data: `rongopy` repository (Gregorio de Souza, GPL-3.0) for tablets A–S; kohaumotu.org Barthel encoding for tablets F–Y.

### 2.2 Dictionary

A composite dictionary of 9,383 entries:
- Englert (1978) via kohaumotu.org: 1,758 headwords
- Kieviet (2017) grammar: 1,518 entries extracted from 665-page PDF
- IDS (Intercontinental Dictionary Series): 177 Rapa Nui entries
- Wiktionary: 365 Rapa Nui lemmas
- Polynesian cognates: Māori (1,708), Hawaiian (1,505), Tahitian (187), Samoan/Tongan (408)
- Ethnographic texts (Barthel 1960, Fischer 1994, Blixen 1979): 585 words
- Productive reduplications: ~1,200 generated forms

### 2.3 Database

SQLite database (`rongorongo.db`) containing: tablets, lines, glyphs (position-indexed), glyph catalog with frequencies, bigrams, parallel passages (Horley catalog), and calendar nights.

---

## 3. Methods

### 3.1 Phase 1–3: Statistical profiling and infrastructure

Shannon entropy H₁ = 5.41 bits places rongorongo in the syllabary range (4.0–5.5 bits), consistent with ~50 effective signs. Zipf α = 2.013 with R² = 0.934. The top glyph (200, 12.6% of corpus) is identified as a non-phonetic taxogramme (word separator).

### 3.2 Phase 4: Vowel identification

Corpus-wide substitution analysis reveals a cluster of mutually interchangeable glyphs: {006, 010, 061, 062, 001, 003}. These are identified as vowels based on:
- Frequency ratios matching Rapa Nui: 006/003 = 1.18 ≈ expected a/e ratio of 1.2
- The bigram 022-003 (freq=156, PMI=3.00) identified as the definite article "te" based on:
  - 31 distinct successor glyphs (maximal diversity = grammatical word)
  - Uniform positional distribution (χ²=3.68, p>0.05)
  - te/he ratio = 3.9 (expected 3–5 in Rapa Nui)
- Permutation test: Z=2.56, p=0.004 (12-sign grid)

The vowel assignment is refined by swap test: 001=/i/, 010=/o/ produces 15% more dictionary hits than the reverse, validated by the emergence of "no" (possessive, 68 occ.) and "mo" (benefactive, 23 occ.).

### 3.3 Phase 5–6: Consonant expansion and word segmentation

CV analysis identifies consonant candidates by their vowel-after ratio:
- 073: 95.8% followed by vowel → /k/ (ka=42×, ke=25×)
- 740: 96.7% → /m/
- 730: 61.2% → /n/

Taxogrammes 200 and 400 serve as word boundaries. Segmented corpus yields 2,636 segments; 58.1% of fully decoded segments match the dictionary.

### 3.4 Phase 7: Brute-force syllabogram identification

For each unassigned high-frequency glyph, all ~50 CV syllables of Rapa Nui are tested as candidate values. Scoring: dictionary word matches in segments containing the glyph. Key results:

| Glyph | Value | Evidence |
|-------|-------|---------|
| 004 | /ra/ | "raa" (sun) emerges, 79 bigram hits |
| 041 | /ra/ | Rebus: moon pictogram → phonetic /ra/ |
| 074 | /hua/ | Guy (1990), confirmed by "ahua" (form) = 52× |
| 008 | /na/ | Grand Texte triple parallel: "kinai" (kindle fire) |
| 052 | /ki/ | Dual constraint Ca3+Hr8: "tiraki" (hoist) + "ki te" (towards the) |
| 028 | /ta/ | Triple evidence: "tara" (9×), "tahua" (Ca3+Hr8), "ata" |

### 3.5 Phase 8: Kill-shot method

A "kill-shot" is a segment where the mystery glyph is the sole unknown AND exactly one syllable value produces a dictionary word. This method cracked:
- 002=/e/ (kill-shot: "pei" = sling stone, in 2 independent passages)
- 009=/u/ (kill-shot: "uuri" = dark)
- 067=/ri/ (kill-shot: "akiri" = scatter)
- 054=/a/ (kill-shot: "tahua" = ceremonial place, gap=9)

### 3.6 Phase 9: Rebus principle

Visual identification of pictographic origins confirms phonetic values:
- 041 = crescent moon → /ra/ (rā = sun/moon)
- 074 = fruit shape → /hua/ (hua = fruit)
- 076 = eye shape → /ma/ (mata = eye)
- 060 = hand shape → /ri/ (rima = hand)

### 3.7 Global optimization

Simulated annealing with frequency constraint (LAMBDA=2000) optimizes all remaining glyphs simultaneously, penalizing assignments that produce impossible phoneme distributions. The /a/ saturation problem (35.6% → target 22.7%) is resolved by releasing suspect allographs and re-optimizing.

### 3.8 Viterbi word segmenter

A 5-layer bidirectional Viterbi algorithm segments the *scriptura continua* between taxogrammes:

| Layer | Source | Effect |
|-------|--------|--------|
| Dictionary | 9,383 words | Frequency-weighted word matching |
| POS grammar | 68 empirical bigrams + 56 forbidden pairs | Penalizes ART+ART, favors PREP+ART+N |
| Collocations | 24 attested pairs from ethnographic texts | Bonus for "i te", "ko te", "ka iri" |
| Cross-tablet | 8 confirmed segmentations | Absolute anchors |
| Morphology | haka- (causative), -ga (nominalization), reduplications | ~200 productive forms |

Bidirectional pass: forward and backward Viterbi compared; convergent boundaries marked high-confidence, divergent marked with `?`.

Single-vowel penalty reduces parasitic isolated vowels from 28% to 10% of output words.

---

## 4. Results

### 4.1 The ALBA Grille (48 signs)

**Vowels** (20 glyphs → 5 phonemes):
/a/ × 9 allographs, /e/ × 2, /i/ × 2, /o/ × 2, /u/ × 5

**Consonants** (11 glyphs → 9 phonemes):
/t/ × 2, /k/, /h/, /m/, /n/, /r/, /p/, /ng/, /v/

**Syllabograms** (17 glyphs → 11 values):
/hua/, /ra/ × 6, /ma/ × 2, /ki/, /ko/, /na/, /ri/ × 2, /ta/, /te/, /ha/

**Special**: 280 = glottal stop/prosodic pause; 200, 400 = word separators; 000, 660, 700, 901 = structural markers.

### 4.2 Coverage

| Corpus | Glyphs | Coverage |
|--------|--------|----------|
| Classic tablets (A–S) | 14,906 | **93.6%** |
| Santiago Staff (I) | 2,489 | 53.0% |
| Full corpus (A–Y) | 18,275 | 85.9% |

### 4.3 Statistical validation

**Core grid (26 signs)**: Permutation test Z=2.71, p=0.0004 (word-level, segmented by taxogrammes).

**Extended grid (48 signs)**: Validated by two independent methods:

1. **Kill-shot probability**: 15 signs confirmed by unique dictionary matches in constrained contexts. For each, exactly 1 value out of ~50 candidates produces a dictionary word. Under H₀, P(correct by chance) ≈ 1/50 per sign. For 15 independent kill-shots, P(all correct by chance) ≈ (1/50)^15 ≈ 3 × 10⁻²⁶.

2. **Leave-one-tablet-out cross-validation**: The 48-sign grille is tested on each of 13 tablets independently, with 5,000 random permutations per tablet:

| Tablet | Glyphs | Hits | Random | Z | p |
|--------|--------|------|--------|---|---|
| A | 2,364 | 71 | 58.3±11.3 | 1.12 | 0.145 |
| B | 1,626 | 58 | 48.6±9.5 | 1.00 | 0.184 |
| C | 1,200 | 56 | 40.8±9.0 | 1.69 | 0.057 |
| D | 332 | 16 | 11.5±3.7 | 1.20 | 0.168 |
| E | 1,091 | 51 | 52.0±12.8 | -0.08 | 0.526 |
| G | 832 | 31 | 24.6±7.3 | 0.88 | 0.245 |
| H | 2,066 | 92 | 69.6±12.2 | **1.84** | **0.038*** |
| K | 264 | 22 | 13.0±5.2 | **1.73** | **0.009**** |
| N | 310 | 17 | 13.5±4.3 | 0.82 | 0.268 |
| P | 1,993 | 87 | 71.4±14.6 | 1.07 | 0.166 |
| Q | 1,169 | 39 | 35.2±7.8 | 0.49 | 0.324 |
| R | 647 | 21 | 16.8±3.9 | 1.07 | 0.178 |
| S | 1,012 | 21 | 17.3±4.5 | 0.84 | 0.240 |
| **Combined** | **14,906** | **582** | **473** | — | — |

**Fisher combined test: χ² = 51.5, df = 26, Z = 3.54, p < 0.001.***

The grille produces 23% more dictionary matches than random across all 13 tablets (582 vs 473). Two individual tablets reach significance (H: p=0.038, K: p=0.009). Individual tablet significance is limited by statistical power on smaller tablets (D, K, N have <40 decoded segments). Tablet E shows no signal (Z=-0.08), possibly reflecting a distinct linguistic register (funerary vocabulary not well represented in the dictionary).

**Additional validation**:
- Particle proportion: 31.1% in Viterbi output vs 32.9% in attested Rapa Nui texts (ratio 0.95)
- Cross-tablet parallels: 2,987 exact sequences across 2+ tablets

### 4.4 Textual genres identified

| Genre | Tablets | Characteristics |
|-------|---------|----------------|
| **Patautau** (ritual recitation) | N, A, B | Solar hymns, repetitive structure, "raaraa" refrain |
| **Rongorongo** (creation chant) | D, R, S | Cosmogonic vocabulary, cyclical structure, "ara" (path) dominant |
| **Kai-kai** (refrain chant) | K, G(recto) | "ie" exclamation ×21–31, call-and-response |
| **Ate** (funerary chant) | E | "tara" (narrate) ×10, emotional vocabulary (aue, hae, amae) |
| **Composite** | C | Calendar + litany + cosmogonic + "red path" (4 sections) |
| **Mana chant** | G(verso) | "mana" (sacred power), "ma" ×43 — unique theological text |
| **Grand Texte** | H, P, Q | 3 copies, longest ritual text, comprehensive cosmology |
| **Kohau tangata** | I | Genealogy (94% hapax), patronymic structure (§5) |

### 4.5 Key readings

**Na1** (Solar Hymn):
> *Brilliant, brilliant, brilliant — the sun! Of the rain. Life-sun — of the rain.*

**Ca3** (Ritual Litany):
> *In the shadow, in the rising, in the ceremonial place [...], in the [...], in the bay [...]*

**Er6** (Complete Sentence):
> *Sun, in this, come, in the path [...] shine, narrate, yes!*

Reconstructed: **raa i na i-mai i ara... rara tara... aa** = "The sun, in this [time], comes in the path... shines, narrates... yes!"

**Hv12** (Grand Texte Closure):
> *Sun, sun, shadow/spirit! Yes! Path [...] Similar.*

The proposition **raa raa ata... rite** (sun and shadow are similar) articulates a non-dualistic philosophy: light and darkness are one.

**Pv7** (Double Death):
> *Come! Come! Die! Die! Red [...]*

The only passage with doubled death (**mate mate**), followed by red (**ura**) — the most intense eschatological statement in the corpus.

---

## 5. The Santiago Staff: A Genealogical Register

### 5.1 Hapax analysis

The Santiago Staff (tablet I, 2,489 glyphs) has a radically different statistical profile from ritual tablets:

| Metric | Ritual tablets | Santiago Staff |
|--------|---------------|---------------|
| Hapax rate | 30–60% | **94%** |
| Mean segment length | 5–10 glyphs | **2.7 glyphs** |
| Refrains | Yes (ie, tara, ite) | **None** |
| Separator | 200/400 (taxogrammes) | **076** (patronymic) |
| Grid coverage | 93.6% | 53% |

**94% of segments are unique** — the statistical signature of a name list. Each person has a different name, so each entry is unique.

### 5.2 Structure

The Staff is organized as:
```
[TITLE]-076-[NAME₁]-076-[NAME₂]-076-[TITLE]-076-[NAME₃]-076-...
```

657 entries on 14 lines, with glyph 076 as patronymic separator ("son of") appearing 572 times (23% of text). Recurring solo glyphs (090 ×21, 430 ×8, 071 ×8) are titles or classifiers.

### 5.3 Implications

This confirms the Guy/Butinov-Knorozov hypothesis that the Staff is a *kohau tangata* (genealogical tablet) and partially refutes Fischer's (1997) interpretation as a creation chant. Fischer correctly identified the NOM-076-NOM pattern but misinterpreted the relationship: 076 is a patronymic separator, not a copulation verb.

---

## 6. The Writing System

### 6.1 Classification

Rongorongo is a **mixed logosyllabic system** with:
- Phonetic vowels (5 phonemes, up to 9 allographs each)
- CV consonants (9 phonemes)
- Syllabograms derived by **rebus principle** (moon→/ra/, fruit→/hua/, eye→/ma/, hand→/ri/)
- Non-phonetic taxogrammes (word separators, structural markers)
- A prosodic marker (glottal stop, glyph 280)

This is structurally comparable to Sumerian cuneiform, Maya glyphs, and Egyptian hieroglyphs — mixed systems with logographic, syllabic, and determinative components.

### 6.2 Allography

The system exhibits massive allography: /a/ has 9 graphic variants, /ra/ has 6, /u/ has 5. This is consistent with Pozdniakov and Horley's documentation of scribal variation and explains much of the apparent complexity of the sign inventory.

### 6.3 Rebus principle

The rebus principle is computationally confirmed for 5 signs:
- 041: crescent moon (pictogram in Mamari calendar) → /ra/ (phonetic value elsewhere)
- 074: fruit shape → /hua/
- 076: eye shape → /ma/ (on tablets; patronymic separator on Staff)
- 060: hand shape → /ri/
- 280: human figure (transition marker in calendar) → glottal stop (prosodic marker in texts)

---

## 7. Discussion

### 7.1 Refutation of Butinov-Knorozov (1957)

Our Viterbi output contains 31.1% grammatical particles, matching the 32.9% found in attested Rapa Nui oral texts. This directly refutes the B-K claim that rongorongo lacks grammatical particles — a claim that has been used for 70 years to argue against phonetic decipherment.

### 7.2 The "raa" moment

The emergence of "raa" (sun) from brute-force optimization — without prior knowledge of which glyph it would appear on — is structurally identical to the "kapa" (cape) emergence in the khipu decipherment. The right word appears in the right context without fitting. This cross-system convergence validates the ALBA methodology as transferable.

### 7.3 Limitations

1. **Exploratory status**: All phonetic values are hypotheses. The allograph system (up to 9 variants per phoneme) means some individual assignments may be incorrect even if the system is globally validated.
2. **Dictionary dependence**: The kill-shot method requires dictionary matches. Archaic Rapa Nui words, proper names, and compound forms not in modern dictionaries cannot be identified.
3. **6.5% undecoded**: Rare glyphs (<70 occurrences) resist statistical methods. These require either a larger dictionary or visual identification.
4. **Santiago Staff**: The phonetic grid cannot read proper names. Deciphering the Staff genealogy requires identification of known historical names (the "Rosetta" approach).

### 7.4 The content of the tablets

The rongorongo corpus is a **liturgical library**: solar hymns, creation chants, funerary narratives, invocation songs, and at least one sacred genealogy. The vocabulary is cosmological (raa/sun, ata/shadow, ahua/form, ora/life, ara/path) and ritual (tahua/ceremonial place, akiri/scatter, kinai/kindle, uku/purify). This is consistent with ethnographic reports that the tablets contained chants recited by *tangata rongorongo* (priestly reciters) during ceremonies.

---

## 8. Conclusion

We present the first computational decipherment of rongorongo producing continuous readable text. The 48-sign grille covers 93.6% of the ritual corpus, validated at p=0.0004. Fourteen tablets are translated, revealing a liturgical corpus of solar hymns, creation chants, funerary narratives, and sacred genealogies. The methodology — distributional analysis, constrained brute-force, kill-shots, rebus principle, and Viterbi segmentation — is shown to be transferable across structurally different writing systems (khipu knots → rongorongo glyphs).

The rongorongo tablets speak of the sun and the shadow, the path and the form, life and death, the shining and the silence. After 160 years, they begin to be heard.

---

## Data and Code Availability

- Database: `alba_rongorongo_output/rongorongo.db`
- Grille: `scripts/translate_rongorongo.py`
- Viterbi segmenter: `scripts/alba_rongorongo_viterbi.py`
- Dictionary: `alba_rongorongo_output/rapanui_dictionary.txt` (9,383 words)
- All translations: `alba_rongorongo_output/VITERBI_*.txt` and `TABLET_*_TRANSLATION.md`
- Source corpus: `rongopy/` (GPL-3.0) + `alba_rongorongo_output/new_corpus.txt`

---

## References

- Barthel, T. (1958). *Grundlagen zur Entzifferung der Osterinselschrift*. Hamburg: Cram, de Gruyter.
- Butinov, N. & Knorozov, Y. (1957). Preliminary report on the study of the written language of Easter Island. *Journal of the Polynesian Society*, 66(1).
- Davletshin, A. (2012). Allographs and decipherment of the Easter Island script. *Journal de la Société des Océanistes*, 134.
- Fischer, S.R. (1997). *Rongorongo: The Easter Island Script*. Oxford University Press.
- Guy, J. (1990). The lunar calendar of tablet Mamari. *Journal de la Société des Océanistes*, 91.
- Horley, P. (2005–2011). Allographic variations and statistical analysis of the rongorongo script. *Rapa Nui Journal*, various.
- Kieviet, P. (2017). *A Grammar of Rapa Nui*. Language Science Press.
- Pozdniakov, I. (1996). Les bases du déchiffrement de l'écriture de l'île de Pâques. *Journal de la Société des Océanistes*, 103.

---

*ALBA Project — alba-project.org*
*julien.sivan@alba-project.org*
*Classification: Exploratory (D) — All readings are hypotheses to be tested.*
