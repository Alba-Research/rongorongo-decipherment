#!/usr/bin/env python3
"""
ALBA Rongorongo — Viterbi word segmenter
3-layer segmentation: dictionary + grammar + cross-tablet parallels.
"""
import math, re, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "rongorongo.db"
DICT = BASE / "data" / "rapanui_dictionary.txt"
TEXTS = BASE / "rongopy" / "rapa_nui_texts"

# ═══════════════════════════════════════════════════════
# POS TAGS & TAGGED LEXICON
# ═══════════════════════════════════════════════════════
# Tags: ART=article, PREP=preposition, PART=particle,
#       V=verb, N=noun, ADJ=adjective, PRON=pronoun,
#       DEM=demonstrative, EXCL=exclamation, CONJ=conjunction,
#       NUM=number, DIR=directional

POS_LEXICON = {
    # Articles
    "te": "ART", "he": "ART",
    # Prepositions
    "i": "PREP", "ki": "PREP", "o": "PREP", "a": "PREP",
    "no": "PREP", "mo": "PREP",
    # Particles
    "e": "PART", "ka": "PART", "ke": "PART", "ko": "PART",
    "na": "DEM", "u": "PART",
    # Pronouns
    "au": "PRON", "ia": "PRON", "oe": "PRON", "koe": "PRON",
    "raua": "PRON", "koia": "PRON",
    # Demonstratives
    "ra": "DEM", "era": "DEM", "ira": "DEM", "tera": "DEM",
    "tena": "DEM", "ona": "DEM",
    # Exclamations
    "ie": "EXCL", "aa": "EXCL", "ae": "EXCL", "aue": "EXCL",
    "ei": "EXCL", "ee": "EXCL",
    # Directionals
    "mai": "DIR", "atu": "DIR", "iho": "DIR",
    # Conjunctions
    "ma": "CONJ", "ai": "CONJ",
    # Numbers
    "ha": "NUM",
    # Verbs
    "rara": "V", "iri": "V", "tu": "V", "ta": "V", "tae": "V",
    "hano": "V", "rako": "V", "amo": "V", "mate": "V", "aai": "V",
    "moe": "V", "ui": "V", "akiri": "V", "kinai": "V", "uku": "V",
    "ea": "V", "ou": "V", "ue": "V", "ori": "V", "rarau": "V",
    "emae": "V", "nana": "V", "oo": "V", "ute": "V",
    "tiraki": "V",
    # Nouns
    "raa": "N", "ara": "N", "ura": "N", "ora": "N", "ahua": "N",
    "hua": "N", "ata": "N", "ohua": "N", "rae": "N", "rai": "N",
    "ua": "N", "tai": "N", "ana": "N", "tahua": "N", "mana": "N",
    "rao": "N", "aka": "N", "uri": "N", "mara": "N", "tara": "N",
    "maa": "N", "pei": "N", "hae": "N", "epe": "N", "ama": "N",
    "ao": "N", "io": "N", "pu": "N", "mu": "N",
    "iki": "N", "rau": "N", "oa": "N",
    "ariki": "N", "hare": "N", "vaka": "N", "ahu": "N",
    "motu": "N", "henua": "N", "roto": "N",
    # Adjectives
    "nui": "ADJ", "iti": "ADJ", "rite": "ADJ", "mara": "ADJ",
    "uuri": "ADJ", "pe": "ADJ", "koa": "ADJ",
    # Compound/reduplication
    "raaraa": "ADJ", "rarara": "V", "riterite": "ADJ",
    "ahuahua": "N", "uraura": "ADJ", "araa": "N",
    "aara": "N", "ite": "PREP",  # i+te fused
    # Productive reduplications found in corpus
    "araara": "N", "rararara": "V", "raerae": "N",
    "huahua": "N", "oraora": "N", "matemate": "V",
    "ataata": "N", "akiaki": "V",
}

# ═══════════════════════════════════════════════════════
# GRAMMAR: POS bigram probabilities (Rapa Nui VSO)
# ═══════════════════════════════════════════════════════
# Score: higher = more grammatical
# Empirical POS bigrams from Barthel/Fischer/Blixen texts (1905 tokens)
# Values = log-probability * weight, calibrated for Viterbi scoring
POS_BIGRAMS = {
    # ART → (93% N, 5% V)
    ("ART", "N"): 4.0, ("ART", "V"): 1.5, ("ART", "DEM"): 0.5,
    # PREP → (70% N, 21% ART, 7% V)
    ("PREP", "ART"): 3.5, ("PREP", "N"): 3.0, ("PREP", "V"): 1.5,
    ("PREP", "PRON"): 1.0, ("PREP", "NUM"): 1.0,
    # PART → (63% N, 19% V, 12% ART)
    ("PART", "V"): 3.5, ("PART", "N"): 2.5, ("PART", "ART"): 2.0,
    ("PART", "PART"): 0.5, ("PART", "ADJ"): 1.0,
    # V → (46% N, 14% ART, 12% DIR, 8% PART)
    ("V", "N"): 3.0, ("V", "ART"): 2.5, ("V", "DIR"): 2.5,
    ("V", "PART"): 1.5, ("V", "PREP"): 1.5, ("V", "PRON"): 2.0,
    ("V", "DEM"): 1.5, ("V", "V"): 0.5, ("V", "ADJ"): 1.0,
    # N → (52% N, 16% PREP, 12% PART, 5% ART, 5% ADJ)
    ("N", "N"): 2.5, ("N", "PREP"): 2.5, ("N", "PART"): 2.0,
    ("N", "ART"): 1.5, ("N", "ADJ"): 2.0, ("N", "V"): 1.0,
    ("N", "CONJ"): 1.5, ("N", "DEM"): 1.5, ("N", "EXCL"): 1.0,
    ("N", "DIR"): 1.0, ("N", "PRON"): 0.5,
    # ADJ → (39% N, 28% PREP, 17% DEM, 17% ART)
    ("ADJ", "N"): 2.5, ("ADJ", "PREP"): 2.0, ("ADJ", "DEM"): 1.5,
    ("ADJ", "ART"): 1.5,
    # PRON → (45% N, 18% PART, 14% PRON, 14% PREP)
    ("PRON", "N"): 2.5, ("PRON", "PART"): 1.5, ("PRON", "PRON"): 1.0,
    ("PRON", "PREP"): 1.5, ("PRON", "ART"): 1.0,
    # DEM → (25% V, 25% N, 17% ART, 17% PART)
    ("DEM", "V"): 2.0, ("DEM", "N"): 2.0, ("DEM", "ART"): 1.5,
    ("DEM", "PART"): 1.5, ("DEM", "DEM"): 0.5, ("DEM", "PREP"): 1.0,
    # EXCL → (100% PREP in data, but allow more)
    ("EXCL", "PREP"): 2.0, ("EXCL", "N"): 1.0, ("EXCL", "V"): 1.0,
    ("EXCL", "ART"): 1.0, ("EXCL", "EXCL"): 0.5,
    # CONJ → (78% N, 11% CONJ, 11% ART)
    ("CONJ", "N"): 3.0, ("CONJ", "ART"): 2.0, ("CONJ", "CONJ"): 0.5,
    # DIR → (57% N, 20% DEM, 11% PRON)
    ("DIR", "N"): 2.5, ("DIR", "DEM"): 2.0, ("DIR", "PRON"): 1.5,
    ("DIR", "PREP"): 1.0, ("DIR", "V"): 0.5,
    # NUM → (100% N)
    ("NUM", "N"): 3.0,
    # START → anything (beginning of segment)
    ("START", "N"): 2.0, ("START", "V"): 2.0, ("START", "PART"): 2.5,
    ("START", "PREP"): 2.5, ("START", "ART"): 2.5, ("START", "PRON"): 1.5,
    ("START", "DEM"): 1.5, ("START", "EXCL"): 2.0, ("START", "ADJ"): 1.0,
    ("START", "CONJ"): 1.0,
}

# FORBIDDEN bigrams — strong negative penalty
FORBIDDEN_BIGRAMS = {
    ("ART", "ART"), ("ART", "PREP"), ("ART", "PART"), ("ART", "PRON"),
    ("ART", "EXCL"), ("ART", "CONJ"), ("ART", "DIR"),
    ("PREP", "EXCL"), ("PREP", "CONJ"),
    ("PART", "EXCL"), ("PART", "CONJ"), ("PART", "DIR"),
    ("ADJ", "PART"), ("ADJ", "V"), ("ADJ", "ADJ"), ("ADJ", "PRON"),
    ("ADJ", "EXCL"), ("ADJ", "CONJ"), ("ADJ", "DIR"),
    ("PRON", "ADJ"), ("PRON", "EXCL"), ("PRON", "CONJ"), ("PRON", "DIR"),
    ("DEM", "ADJ"), ("DEM", "EXCL"), ("DEM", "CONJ"), ("DEM", "DIR"),
    ("EXCL", "PART"), ("EXCL", "ADJ"), ("EXCL", "PRON"),
    ("EXCL", "DEM"), ("EXCL", "CONJ"), ("EXCL", "DIR"),
    ("CONJ", "PREP"), ("CONJ", "PART"), ("CONJ", "ADJ"),
    ("CONJ", "PRON"), ("CONJ", "EXCL"), ("CONJ", "DIR"),
    ("DIR", "ART"), ("DIR", "ADJ"), ("DIR", "EXCL"),
    ("DIR", "CONJ"), ("DIR", "DIR"),
}

DEFAULT_BIGRAM = 0.3  # unseen but not forbidden
FORBIDDEN_PENALTY = -3.0  # moderate penalty — rongorongo may have archaic constructions

# ═══════════════════════════════════════════════════════
# WORD FREQUENCIES (from Rapa Nui texts)
# ═══════════════════════════════════════════════════════
def build_word_freqs():
    freqs = Counter()
    for txt_file in TEXTS.glob("*.txt"):
        with open(txt_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("[") or not line:
                    continue
                for w in line.lower().split():
                    w = re.sub(r"[.,;:!?()'\"-]", "", w)
                    if w and len(w) >= 1:
                        freqs[w] += 1
    # Boost grammar words (always common)
    for w in POS_LEXICON:
        freqs[w] = max(freqs.get(w, 0), 10)
    return freqs

WORD_FREQS = build_word_freqs()
TOTAL_FREQ = sum(WORD_FREQS.values())

# ═══════════════════════════════════════════════════════
# CONFIRMED SEGMENTATIONS (cross-tablet anchors)
# ═══════════════════════════════════════════════════════
CONFIRMED = {
    "ite": ["i", "te"],
    "iteata": ["i", "te", "ata"],
    "itetiraki": ["i", "te", "tiraki"],
    "raaraaraarauraaraaraate": ["raaraa", "raaraa", "raaraa", "raa", "te"],
    "irariterite": ["ira", "rite", "rite"],
    "atahuau": ["a", "tahua", "u"],
    "teurauraera": ["te", "uraura", "era"],
    "oraramoma": ["ora", "ra", "mo", "ma"],
}

# Collocations from Barthel/Fischer/Blixen texts (freq >= 4)
# These are word PAIRS that should be segmented together
COLLOCATIONS = {
    ("ko", "te"): 21, ("i", "te"): 20, ("o", "te"): 14,
    ("ki", "te"): 12, ("e", "te"): 11, ("te", "vaka"): 9,
    ("e", "ure"): 8, ("a", "ure"): 7, ("ka", "iri"): 7,
    ("te", "manu"): 6, ("i", "tua"): 6, ("e", "pua"): 6,
    ("ka", "hau"): 6, ("te", "hare"): 6, ("a", "te"): 5,
    ("ka", "tere"): 4, ("te", "raa"): 4, ("te", "ahi"): 4,
    ("he", "oho"): 3, ("ka", "oho"): 3, ("te", "atua"): 3,
    ("te", "henua"): 3, ("i", "roto"): 3, ("ki", "hiva"): 3,
}

# Productive reduplications (add to dictionary + MEANINGS)
REDUPLICATIONS = {
    "araara": ("ara", "path(intensive)"),
    "rararara": ("rara", "shine(absolute)"),
    "raerae": ("rae", "day/brow(intensive)"),
    "raaraa": ("raa", "brilliant"),
    "huahua": ("hua", "fruit(abundant)"),
    "uraura": ("ura", "red(intensive)"),
    "oraora": ("ora", "life(intense)"),
    "ahuaahua": ("ahua", "form(redoubled)"),
    "matemate": ("mate", "die(repeated)"),
    "ataata": ("ata", "shadow(multiple)"),
    "riterite": ("rite", "perfectly.similar"),
    "akiaki": ("aki", "beat(repeated)"),
    "rarara": ("rara", "shine×3"),
}


# ═══════════════════════════════════════════════════════
# VITERBI SEGMENTER
# ═══════════════════════════════════════════════════════
def viterbi_segment(text, dictionary):
    """
    Find optimal word segmentation using Viterbi with:
    - Layer 1: dictionary match + word frequency
    - Layer 2: POS bigram grammar score
    - Layer 3: confirmed segmentation anchors
    """
    text = text.replace("'", "")
    n = len(text)
    if n == 0:
        return []

    # Check confirmed segmentations first (Layer 3)
    if text in CONFIRMED:
        return [(w, True) for w in CONFIRMED[text]]

    # Layer 5: Morphological decomposition
    # Expand dictionary dynamically with productive morphology
    morph_expanded = set()
    morph_meanings = {}

    # Rapa Nui productive prefixes
    PREFIXES = {
        "haka": ("V", "make"),         # causative
        "taka": ("V", "around"),       # circumlocutive
        "haa": ("V", "make(var)"),     # causative variant
    }
    # Rapa Nui productive suffixes
    SUFFIXES = {
        "ga": ("N", "the.act.of"),          # nominalization
        "haga": ("N", "action.of"),         # action nominalization
        "aga": ("N", "action.of(var)"),     # variant
        "a": ("N", "result.of"),            # passive/resultative
    }

    # Known roots for morphological generation
    MORPH_ROOTS = {
        "rara": ("V", "shine"), "tuu": ("V", "stand"), "noho": ("V", "dwell"),
        "rere": ("V", "fly"), "oho": ("V", "go"), "tere": ("V", "sail"),
        "mate": ("V", "die"), "ora": ("V", "live"), "kai": ("V", "eat"),
        "moe": ("V", "sleep"), "huri": ("V", "turn"), "topa": ("V", "fall"),
        "iri": ("V", "rise"), "amo": ("V", "carry"), "hano": ("V", "go"),
        "rako": ("V", "seize"), "tae": ("V", "arrive"), "ui": ("V", "look"),
        "uku": ("V", "wash"), "aki": ("V", "beat"), "ori": ("V", "dance"),
        "ea": ("V", "rise"), "tu": ("V", "stand"), "ta": ("V", "strike"),
        "ue": ("V", "shake"), "ou": ("V", "go"), "nana": ("V", "observe"),
        "raka": ("N", "branch"), "hau": ("N", "wind"), "para": ("N", "wall"),
        "ata": ("N", "shadow"), "ahua": ("N", "form"), "ara": ("N", "path"),
        "ura": ("N", "red"), "raa": ("N", "sun"), "hua": ("N", "fruit"),
        "rae": ("N", "brow"), "mana": ("N", "power"), "tara": ("N", "point"),
        "nui": ("ADJ", "great"), "iti": ("ADJ", "small"), "roa": ("ADJ", "long"),
        "kave": ("V", "take.away"),
    }

    # Generate prefix+root forms (always generate meaning, add to dict if missing)
    for prefix, (pref_pos, pref_meaning) in PREFIXES.items():
        for root, (root_pos, root_meaning) in MORPH_ROOTS.items():
            compound = prefix + root
            if len(compound) >= 5:
                morph_expanded.add(compound)
                morph_meanings[compound] = f"{pref_meaning}.{root_meaning}"

    # Generate root+suffix forms
    for root, (root_pos, root_meaning) in MORPH_ROOTS.items():
        for suffix, (suf_pos, suf_meaning) in SUFFIXES.items():
            if suffix == "a" and len(root) < 3:
                continue
            compound = root + suffix
            if len(compound) >= 4:
                morph_expanded.add(compound)
                morph_meanings[compound] = f"{suf_meaning}.{root_meaning}"

    # Generate reduplications (full: XY→XYXY)
    for root, (root_pos, root_meaning) in MORPH_ROOTS.items():
        if len(root) >= 2:
            redup = root + root
            morph_expanded.add(redup)
            morph_meanings[redup] = f"{root_meaning}(intensif)"

    # Add morphological expansions to working dictionary
    expanded_dict = dictionary | morph_expanded
    # Inject ALL morphological meanings into global MEANINGS
    for mw, mm in morph_meanings.items():
        if mw not in MEANINGS:
            MEANINGS[mw] = mm

    # Viterbi: dp[i] = (best_score, best_path)
    # path = list of (word, pos_tag)
    INF = float("-inf")
    dp = [(INF, [])] * (n + 1)
    dp[0] = (0.0, [])

    for i in range(1, n + 1):
        for word_len in range(1, min(i, 10) + 1):
            start = i - word_len
            candidate = text[start:i]

            # Must be in expanded dictionary or POS lexicon
            is_known = candidate in expanded_dict or candidate in POS_LEXICON
            if not is_known and word_len > 1:
                continue
            if not is_known and word_len == 1:
                # Single unmatched char — small penalty
                score = dp[start][0] - 2.0
                if score > dp[i][0]:
                    dp[i] = (score, dp[start][1] + [(candidate, "?")])
                continue

            # Layer 1: word frequency score
            freq = WORD_FREQS.get(candidate, 1)
            freq_score = math.log(freq / TOTAL_FREQ + 1e-8)

            # Length bonus: STRONGLY prefer longer words
            # Single vowels (a,e,i,o,u) get a penalty unless in valid context
            if word_len == 1 and candidate in "aeiou":
                # Single vowels are almost always wrong segmentation
                # Only valid in very specific contexts
                prev_pos_tag = dp[start][1][-1][1] if dp[start][1] else "START"
                # Look ahead: what follows?
                next_char = text[i] if i < n else ""
                # Valid: "a" or "o" between two N (possessive construction)
                # or "i" before ART (preposition "i te")
                if candidate in ("i", "e") and next_char in "tkh":
                    len_bonus = -0.3  # "i te", "e [verb]" — valid
                elif prev_pos_tag == "N" and candidate in ("a", "o"):
                    len_bonus = -1.0  # N + a/o — sometimes valid but prefer longer
                else:
                    len_bonus = -3.0  # strong penalty: almost certainly wrong
            elif word_len == 1:
                len_bonus = -2.0  # single consonant: strong penalty
            elif word_len == 2:
                len_bonus = 0.5  # 2-char words: moderate bonus
            else:
                # Longer words get strong progressive bonus
                len_bonus = word_len * 0.7

            # Layer 2: POS bigram score with forbidden penalty
            pos = POS_LEXICON.get(candidate, "N")  # default noun
            prev_pos = dp[start][1][-1][1] if dp[start][1] else "START"
            if (prev_pos, pos) in FORBIDDEN_BIGRAMS:
                bigram_score = FORBIDDEN_PENALTY
            else:
                bigram_score = POS_BIGRAMS.get((prev_pos, pos), DEFAULT_BIGRAM)

            # Layer 4: Collocation bonus
            colloc_bonus = 0.0
            if dp[start][1]:
                prev_word = dp[start][1][-1][0]
                if (prev_word, candidate) in COLLOCATIONS:
                    colloc_bonus = 2.0  # strong bonus for attested collocations

            # Combined score
            total = dp[start][0] + freq_score + len_bonus + bigram_score + colloc_bonus

            if total > dp[i][0]:
                dp[i] = (total, dp[start][1] + [(candidate, pos)])

    if dp[n][0] == INF:
        return [(text, False)]

    forward_result = dp[n][1]  # list of (word, pos)

    # ── BACKWARD PASS (right-to-left) ──────────────────
    rev_text = text[::-1]
    dp_b = [(INF, [])] * (n + 1)
    dp_b[0] = (0.0, [])

    for i in range(1, n + 1):
        for word_len in range(1, min(i, 10) + 1):
            start = i - word_len
            candidate_rev = rev_text[start:i]
            candidate = candidate_rev[::-1]  # un-reverse the word

            is_known = candidate in expanded_dict or candidate in POS_LEXICON
            if not is_known and word_len > 1:
                continue
            if not is_known and word_len == 1:
                score = dp_b[start][0] - 2.0
                if score > dp_b[i][0]:
                    dp_b[i] = (score, dp_b[start][1] + [(candidate, "?")])
                continue

            freq = WORD_FREQS.get(candidate, 1)
            freq_score = math.log(freq / TOTAL_FREQ + 1e-8)
            len_bonus = word_len * 0.3

            pos = POS_LEXICON.get(candidate, "N")
            # For backward, use the NEXT word's POS (which is prev in reversed order)
            next_pos = dp_b[start][1][-1][1] if dp_b[start][1] else "START"
            if (pos, next_pos) in FORBIDDEN_BIGRAMS:
                bigram_score = FORBIDDEN_PENALTY
            else:
                bigram_score = POS_BIGRAMS.get((pos, next_pos), DEFAULT_BIGRAM)

            total = dp_b[start][0] + freq_score + len_bonus + bigram_score

            if total > dp_b[i][0]:
                dp_b[i] = (total, dp_b[start][1] + [(candidate, pos)])

    backward_result = list(reversed(dp_b[n][1])) if dp_b[n][0] > INF else []

    # ── MERGE: forward + backward ──────────────────────
    # Extract word boundaries from both passes
    def get_boundaries(path):
        boundaries = set()
        pos = 0
        for word, _ in path:
            pos += len(word)
            boundaries.add(pos)
        return boundaries

    fwd_bounds = get_boundaries(forward_result)
    bwd_bounds = get_boundaries(backward_result)
    agreed = fwd_bounds & bwd_bounds  # positions where both agree

    # Use forward result as base, mark confidence
    result = []
    pos = 0
    for word, tag in forward_result:
        word_end = pos + len(word)
        is_known = word in POS_LEXICON or word in expanded_dict
        # Inject morphological meanings
        if word in morph_meanings and word not in MEANINGS:
            MEANINGS[word] = morph_meanings[word]
        # High confidence if both forward and backward agree on this boundary
        high_conf = word_end in agreed
        result.append((word, is_known, high_conf))
        pos = word_end

    # Return with confidence (third element: True = both passes agree)
    return [(w, k, c) for w, k, c in result]


# ═══════════════════════════════════════════════════════
# MEANINGS (same as fluent translator)
# ═══════════════════════════════════════════════════════
MEANINGS = {
    # Grammar
    "te": "the", "he": "a/some", "e": "[v]", "ka": "let!",
    "ke": "if", "ki": "towards", "ko": "it.is", "i": "in",
    "o": "of", "a": "of", "no": "of(emph.)", "mo": "for",
    "na": "this/past", "ai": "who/by", "au": "I/me", "ia": "him/her",
    "oe": "you", "ie": "yes!", "ra": "there", "ma": "and/with",
    "mai": "come/from", "u": "~",
    # Cosmological
    "raa": "sun", "raaraa": "brilliant", "ara": "path",
    "ura": "red/flame", "ora": "life", "rara": "shine",
    "ahua": "form/image", "hua": "fruit", "ata": "shadow/spirit",
    "ohua": "bloom", "rae": "brow/day", "rai": "sky",
    "ua": "rain", "tai": "sea", "ana": "cave",
    # Ritual
    "tahua": "ceremonial.place", "akiri": "scatter",
    "kinai": "kindle.fire", "uku": "purify",
    "iki": "small", "tara": "narrate/point",
    "mana": "sacred.power", "rao": "counting.stick",
    # Verbs
    "tu": "stand", "ta": "strike", "tae": "arrive",
    "hano": "go", "rako": "seize", "amo": "carry",
    "iri": "rise", "mate": "die", "aai": "eat",
    "moe": "sleep", "ui": "look", "mu": "silence",
    # Nouns/Adj
    "mara": "hard", "aka": "root", "uri": "lineage/dark",
    "oa": "true", "aa": "yes!", "ae": "yes",
    "aue": "alas!", "era": "that", "ira": "that.one",
    "ona": "his/her", "koe": "you", "maa": "food",
    "pei": "grooves/toboggan", "hae": "anger", "rau": "leaf/hundred",
    "epe": "mat", "rite": "similar", "pe": "like/as",
    "ha": "four", "ti": "~", "to": "sugarcane",
    "nui": "great", "iti": "small",
    # Reduplications
    "riterite": "perfectly.similar", "rarara": "shine×3",
    "uraura": "red-red", "ahuahua": "form-form",
    "araa": "path-sun", "aara": "awakening",
    # Syllabograms
    "tiraki": "hoist/raise", "ite": "in.the",
    # Enriched (Kieviet/cognates)
    "ao": "world/cloud", "ea": "rise", "ou": "go",
    "ei": "hey!", "oi": "here", "ori": "dance",
    "ari": "appearance", "koa": "joy", "uma": "embrace",
    "ina": "if", "nana": "observe", "pu": "conch/base",
    "ngu": "moan", "tera": "that.one", "raua": "they.two",
    "rarau": "seize", "emae": "die(archaic)", "uea": "lift!",
    "ama": "bay/outrigger", "eo": "smell", "oo": "pierce",
    "ee": "yes", "eu": "move", "io": "hawk",
    "nu": "rumble", "ue": "shake", "ute": "cradle",
    "ate": "funeral.chant", "nga": "breathe",
    "ii": "intense", "uu": "breast/cry",
    # Batch 2: CONFIRMED meanings only (Englert/Kieviet attested)
    "ahu": "altar/platform", "mau": "true/fixed",
    "hara": "sin/offense", "arii": "chief/noble",
    "naa": "those(pl.)", "ena": "there(near)",
    "aei": "when?", "hee": "flee", "raki": "north.wind",
    "una": "shell/scale", "rari": "rare/scarce",
    "aea": "where?", "rate": "miss/fail",
    "urau": "red.leaf", "tena": "that/those",
    "aahua": "form(long)",
    # Reasonable compositional (e+X patterns)
    "eena": "those(emph.)", "eera": "that(emph.)",
    # Batch 3: Englert dictionary definitions (verified)
    "noma": "flash.of.lightning", "emu": "sink/founder",
    "rama": "torch(dry.leaves)", "rahu": "coal",
    "uta": "upland/inland", "oti": "finish/end",
    "hei": "headband/hey!", "uru": "feast.for.dead",
    "mama": "chew/mouth-feed", "pua": "flower",
    "kua": "past.tense(names)", "ako": "sing/recite",
    "rano": "volcano/crater.lake", "oho": "go/depart",
    "miro": "wood/tree", "pei": "grooves.on.slopes",
    # Batch 4: Full Englert sweep (51 entries matched)
    "aha": "what?/which?", "raau": "medicine/remedy",
    "mou": "keep.quiet", "tui": "sew/string",
    "oira": "before(time)", "paa": "barren/sterile",
    "tea": "light/fair/white", "nape": "give.a.name",
    "aau": "throw(both.hands)", "umu": "cooking.pit",
    "hu": "article(rare)", "keri": "dig",
    "riri": "angry", "rana": "obsidian.point",
    "ohu": "cry/bawl", "mao": "healed/cured",
    "keke": "descend(after.peak)", "nei": "this/here",
    "uira": "lightning.flash", "ohe": "bamboo",
    "hau": "thread/string", "taau": "this.precisely",
    "maoa": "open.earth.oven", "ihi": "singing.women",
    "po": "night", "tari": "carry/take",
    "pera": "cemetery/taboo.place", "raka": "smooth/polished",
    "rapa": "shine", "nua": "mother",
    "keu": "communal.work", "ioio": "bit/piece",
    "kona": "place/terrain", "heu": "mixed.offspring",
    "oaha": "interjection!", "kia": "let's.go!",
    "papa": "underground.rock", "pa": "surround",
    "nanai": "spider", "oou": "possessive(3sg)",
    "aano": "width/breadth", "mahu": "begin.to.heal",
    "ihu": "nose", "ooka": "stab/perforate",
    "tuki": "fecundate", "nako": "marrow",
    "teko": "giant",
    # NOT included (still unattested/uncertain):
    # uo, uai, ri, oeu, narara, ipe, eri → stay as «unknown»
}


# Inject reduplications into MEANINGS
for _redup, (_root, _meaning) in REDUPLICATIONS.items():
    MEANINGS[_redup] = _meaning

# ═══════════════════════════════════════════════════════
# MAIN TRANSLATOR
# ═══════════════════════════════════════════════════════
def load_all():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute("SELECT line_id, position, barthel_code FROM glyphs ORDER BY line_id, position")
    corpus = defaultdict(list)
    for lid, pos, code in c.fetchall():
        corpus[lid].append(code)
    conn.close()

    dictionary = set()
    with open(DICT, encoding="utf-8") as f:
        for l in f:
            w = l.strip().lower()
            if w:
                dictionary.add(w)
    # Add all MEANINGS keys
    dictionary.update(MEANINGS.keys())
    dictionary.update(POS_LEXICON.keys())
    return dict(corpus), dictionary


GRILLE = {
    "006": "a", "003": "e", "001": "i", "010": "o",
    "061": "u", "062": "u", "066": "u", "045": "i",
    "002": "e", "009": "u", "044": "a", "005": "ra",
    "070": "a", "099": "o", "008": "na", "067": "ri",
    "069": "a", "280": "'", "054": "a", "047": "a",
    "076": "ma", "060": "ri", "084": "ha",
    "025": "ra", "015": "te", "037": "a", "016": "u",
    "022": "t", "063": "t", "073": "k", "059": "h",
    "740": "m", "730": "n", "260": "r",
    "095": "p", "230": "ng", "530": "v",
    "074": "hua", "004": "ra", "041": "ra", "007": "ra",
    "034": "ra", "050": "ma", "075": "a", "091": "a",
    "052": "ki", "028": "ta", "027": "ko",
}
SEP = {"200", "400"}
TAXO = {"200", "400", "700", "901", "660", "000"}


def translate_line_viterbi(lid, glyphs, dictionary):
    parts = []
    for g in glyphs:
        if g in SEP:
            parts.append("|")
        elif g in TAXO:
            parts.append("|")
        elif g in GRILLE:
            parts.append(GRILLE[g])
        else:
            parts.append(f"[{g}]")
    decoded = "".join(parts)

    segments = [s for s in decoded.split("|") if s.strip()]
    output = []

    for seg in segments:
        if "[" in seg:
            output.append("[...]")
            continue

        seg_clean = seg.replace("'", "")
        words = viterbi_segment(seg_clean, dictionary)

        for item in words:
            # Handle both 2-tuple (old) and 3-tuple (new with confidence)
            if len(item) == 3:
                word, is_known, high_conf = item
            else:
                word, is_known = item
                high_conf = True

            if word in MEANINGS:
                meaning = MEANINGS[word]
                if high_conf:
                    output.append(meaning)
                else:
                    output.append(f"{meaning}?")
            elif is_known:
                output.append(f"\u00ab{word}\u00bb")
            elif len(word) <= 2 and all(c in "thpnrkvm" for c in word):
                output.append("~")
            else:
                output.append(f"({word})")

    # Clean consecutive ~
    cleaned = []
    for w in output:
        if w == "~" and cleaned and cleaned[-1] == "~":
            continue
        cleaned.append(w)

    # English post-processing: contract particles for fluent reading
    text = " ".join(cleaned)
    # Contract: "of the" stays (natural in English)
    # "in the" stays (natural)
    # Remove stutter: "of of" → "of"
    while "of of" in text:
        text = text.replace("of of", "of")
    # Noise: "[v] of" or "of [v]" → "[v]"
    text = text.replace("[v] of", "[v]")
    text = text.replace("of [v]", "[v]")
    # Noise: "~ of" or "of ~" → "~"
    text = text.replace("~ of", "~")
    text = text.replace("of ~", "~")
    # Multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")

    return text.strip()


def interlinear_line(lid, glyphs, dictionary):
    """Produce interlinear gloss: Rapa Nui segmented + French gloss below."""
    parts = []
    for g in glyphs:
        if g in SEP:
            parts.append("|")
        elif g in TAXO:
            parts.append("|")
        elif g in GRILLE:
            parts.append(GRILLE[g])
        else:
            parts.append(f"[{g}]")
    decoded = "".join(parts)

    segments = [s for s in decoded.split("|") if s.strip()]
    rn_line = []  # Rapa Nui words
    gl_line = []  # French glosses

    for seg in segments:
        if "[" in seg:
            rn_line.append("[...]")
            gl_line.append("[...]")
            continue

        seg_clean = seg.replace("'", "")
        words = viterbi_segment(seg_clean, dictionary)

        for item in words:
            if len(item) == 3:
                word, is_known, high_conf = item
            else:
                word, is_known = item
                high_conf = True

            rn_line.append(word)
            if word in MEANINGS:
                m = MEANINGS[word]
                if m in ("~", "[v]", "[?]"):
                    gl_line.append(m)
                else:
                    gl_line.append(m)
            elif is_known:
                gl_line.append("?")
            else:
                gl_line.append("·")

    # Format: align columns
    max_widths = [max(len(r), len(g)) for r, g in zip(rn_line, gl_line)]
    rn_str = "  ".join(r.ljust(w) for r, w in zip(rn_line, max_widths))
    gl_str = "  ".join(g.ljust(w) for g, w in zip(gl_line, max_widths))

    return rn_str, gl_str


if __name__ == "__main__":
    corpus, dictionary = load_all()

    # Parse args
    interlinear_mode = "--interlinear" in sys.argv or "-i" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if not args:
        print("Usage: python alba_rongorongo_viterbi.py <tablet|line> [-i/--interlinear]")
        sys.exit(0)

    arg = args[0]

    if len(arg) == 1 and arg.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXY":
        tablet = arg.upper()
        lines = sorted([lid for lid in corpus if lid.startswith(tablet)])
        mode = "INTERLINÉAIRE" if interlinear_mode else "VITERBI"
        print(f"\n{'=' * 70}")
        print(f"TABLETTE {tablet} — TRADUCTION {mode}")
        print(f"{'=' * 70}\n")
        for lid in lines:
            if interlinear_mode:
                rn, gl = interlinear_line(lid, corpus[lid], dictionary)
                print(f"  {lid}:")
                print(f"    RN:  {rn}")
                print(f"    FR:  {gl}")
                print()
            else:
                result = translate_line_viterbi(lid, corpus[lid], dictionary)
                print(f"  {lid}: {result}\n")
    elif arg in corpus:
        if interlinear_mode:
            rn, gl = interlinear_line(arg, corpus[arg], dictionary)
            print(f"\n  {arg}:")
            print(f"    RN:  {rn}")
            print(f"    FR:  {gl}")
        else:
            result = translate_line_viterbi(arg, corpus[arg], dictionary)
            print(f"\n  {arg}: {result}")
    else:
        print(f"'{arg}' non trouve.")
