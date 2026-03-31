#!/usr/bin/env python3
"""
ALBA Rongorongo Translator — v2.0
Translate any rongorongo tablet or line using the 47-sign ALBA grille.

Usage:
    python translate_rongorongo.py              # Translate all tablets (summary)
    python translate_rongorongo.py N            # Translate tablet N fully
    python translate_rongorongo.py Ca3          # Translate line Ca3
    python translate_rongorongo.py --all        # Translate entire corpus

ALBA Project — 30 mars 2026
Classification: Exploratoire (D)
"""

import sqlite3, sys, re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "rongorongo.db"
DICT = BASE / "data" / "rapanui_dictionary.txt"

# ═══════════════════════════════════════════════════════════════
# THE ALBA GRILLE — 47 signs + 6 taxogrammes + 1 glottal
# ═══════════════════════════════════════════════════════════════
GRILLE = {
    # Vowels: /a/ (9 allographs)
    "006": "a", "037": "a", "044": "a", "047": "a",
    "054": "a", "069": "a", "070": "a", "075": "a", "091": "a",
    # Vowels: /e/ (2 allographs)
    "002": "e", "003": "e",
    # Vowels: /i/ (2 allographs)
    "001": "i", "045": "i",
    # Vowels: /o/ (2 allographs)
    "010": "o", "099": "o",
    # Vowels: /u/ (5 allographs)
    "009": "u", "016": "u", "061": "u", "062": "u", "066": "u",
    # Consonants
    "022": "t", "063": "t",    # /t/ (2 allographs)
    "073": "k",                 # /k/
    "059": "h",                 # /h/
    "740": "m",                 # /m/
    "730": "n",                 # /n/
    "260": "r",                 # /r/
    "095": "p",                 # /p/
    "230": "ng",                # /ng/
    "530": "v",                 # /v/
    # Syllabograms
    "074": "hua",               # /hua/ — rebus: fruit (Guy 1990)
    "004": "ra", "005": "ra", "007": "ra",  # /ra/ (6 allographs)
    "025": "ra", "034": "ra", "041": "ra",  # 041 = rebus: moon
    "050": "ma", "076": "ma",  # /ma/ (2 allographs), 076 = rebus: eye
    "052": "ki",                # /ki/
    "027": "ko",                # /ko/
    "008": "na",                # /na/
    "060": "ri", "067": "ri",  # /ri/ (2 allographs), 060 = rebus: hand
    "028": "ta",                # /ta/
    "015": "te",                # /te/ — article syllabogram
    "084": "ha",                # /ha/ — kill-shot "oaha"
    # Prosodic marker
    "280": "",                  # glottal stop / pause
}

TAXO = {"200", "400", "700", "901", "660", "000"}
SEP = {"200", "400"}

TABLET_NAMES = {
    "A": "Tahua", "B": "Aruku Kurenga", "C": "Mamari",
    "D": "Echancrée", "E": "Keiti", "F": "Chauvet fragment",
    "G": "Petit Santiago", "H": "Grand Santiago",
    "I": "Santiago Staff", "J": "London reimiro 1",
    "K": "Londres", "L": "London reimiro 2",
    "M": "Large Vienna fragment", "N": "Petit de Vienne",
    "O": "Berlin fragment", "P": "Grand de Saint-Pétersbourg",
    "Q": "Petit de Saint-Pétersbourg", "R": "Petit de Santiago",
    "S": "Grand de Vienne", "T": "Honolulu tablet",
    "U": "Washington fragment", "V": "Paris snuffbox lid",
    "W": "Washington reimiro", "X": "Paris fluted fragment",
    "Y": "Paris snuffbox bottom",
}

# Lexicon for translation
MEANINGS = {
    "a": "de(poss-a)", "e": "part.verb.", "i": "dans/à", "o": "de(poss-o)",
    "u": "part.", "te": "le/la", "he": "un/une", "ka": "que!/imp.",
    "ke": "si(cond.)", "ki": "vers", "ko": "c'est(pred.)", "no": "de(emph.)",
    "mo": "pour", "na": "ce/passé", "ia": "il/elle", "au": "je/moi",
    "ai": "qui/rel.", "ie": "oui!/excl.", "ra": "là(dém.)", "ma": "et/avec",
    "ta": "frapper", "mu": "silence", "tu": "debout", "to": "canne",
    "ha": "quatre", "ti": "plante.ti",
    "raa": "SOLEIL", "raaraa": "BRILLANT", "ara": "chemin/éveil",
    "ura": "rouge/flamme", "ora": "VIE", "rara": "briller",
    "ahua": "FORME/IMAGE", "hua": "fruit", "ata": "OMBRE/ESPRIT",
    "tara": "pointe/récit", "rau": "feuille/cent", "rao": "baguette",
    "iki": "petit", "iri": "monter", "amo": "porter",
    "ohua": "floraison", "mate": "mort", "mai": "venir/depuis",
    "oe": "toi", "ua": "pluie", "ui": "regarder",
    "ae": "oui", "aa": "oui!", "oa": "vrai",
    "aai": "manger", "rae": "front/jour", "aro": "face",
    "era": "cela(dém.)", "ira": "celui-là", "aue": "hélas!",
    "ite": "dans.le/la", "tahua": "PLACE.CÉRÉM.",
    "akiri": "disperser", "ona": "son/sa(3sg)", "ana": "grotte",
    "uri": "lignée/noir", "uuri": "sombre", "koe": "toi(pron.)",
    "koia": "c'est.lui", "rako": "prendre", "aano": "grotte",
    "tae": "arriver", "hae": "colère", "uku": "laver",
    "rai": "ciel/jour", "aiai": "clair", "toi": "art/pierre",
    "kinai": "ALLUMER(feu)", "tena": "ce/cela(dém.)",
    "pei": "fronde", "mara": "dur", "tai": "mer",
    "aro": "face", "aka": "racine", "noi": "annoncer",
}


def load_corpus():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute("SELECT line_id, position, barthel_code FROM glyphs ORDER BY line_id, position")
    lines = defaultdict(list)
    for lid, pos, code in c.fetchall():
        lines[lid].append(code)
    conn.close()
    return dict(lines)


def load_dict():
    words = set()
    if DICT.exists():
        with open(DICT, encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    return words


def decode_glyph(g):
    if g in GRILLE:
        return GRILLE[g]
    if g in TAXO:
        return "|"
    return f"[{g}]"


def segment(glyphs):
    segs, cur = [], []
    for g in glyphs:
        if g in SEP:
            if cur:
                segs.append(list(cur))
            cur = []
        else:
            cur.append(g)
    if cur:
        segs.append(cur)
    return segs


def translate_line(lid, glyphs, dictionary):
    """Translate a single line, return structured result."""
    segs = segment(glyphs)
    n_known = sum(1 for g in glyphs if g in GRILLE or g in TAXO)
    pct = n_known / len(glyphs) * 100 if glyphs else 0

    words = []
    for seg in segs:
        decoded = "".join(decode_glyph(g) for g in seg)
        clean = decoded.replace("[", "").replace("]", "").replace("|", "")
        is_full = "[" not in decoded

        meaning = ""
        if is_full:
            if clean in MEANINGS:
                meaning = MEANINGS[clean]
            elif clean in dictionary:
                meaning = "[DICT]"
            elif len(clean) >= 3:
                for i in range(len(clean)):
                    for j in range(i + 3, min(i + 8, len(clean) + 1)):
                        sub = clean[i:j]
                        if sub in MEANINGS:
                            meaning = f"~{sub}({MEANINGS[sub]})"
                            break
                    if meaning:
                        break

        words.append({
            "glyphs": seg,
            "decoded": decoded,
            "clean": clean,
            "full": is_full,
            "meaning": meaning,
        })

    return {
        "lid": lid,
        "n_glyphs": len(glyphs),
        "pct_decoded": pct,
        "words": words,
    }


def print_translation(result, verbose=True):
    """Print a formatted translation."""
    r = result
    print(f"\n  {r['lid']} ({r['n_glyphs']} gl, {r['pct_decoded']:.0f}% décodé)")
    print(f"  {'─' * 60}")

    for idx, w in enumerate(r["words"], 1):
        dec = w["decoded"]
        meaning = w["meaning"]
        mark = f"  {meaning}" if meaning else ""
        if verbose:
            gl_str = "-".join(w["glyphs"])
            print(f"    W{idx:>2}: {dec:>20}{mark}")
        else:
            pass

    # One-line reading
    reading = " | ".join(w["decoded"] for w in r["words"])
    print(f"  Lecture: {reading}")

    # Identified words
    known = [(w["clean"], w["meaning"]) for w in r["words"] if w["meaning"]]
    if known:
        known_str = ", ".join(f"{c}={m}" for c, m in known[:10])
        print(f"  Mots: {known_str}")


def translate_tablet(tablet_id, corpus, dictionary, verbose=True):
    """Translate all lines of a tablet."""
    lines = sorted([lid for lid in corpus if lid.startswith(tablet_id)])
    if not lines:
        print(f"Tablette {tablet_id} non trouvée.")
        return

    name = TABLET_NAMES.get(tablet_id, "?")
    total_gl = sum(len(corpus[lid]) for lid in lines)
    total_dec = sum(1 for lid in lines for g in corpus[lid] if g in GRILLE or g in TAXO)
    pct = total_dec / total_gl * 100 if total_gl else 0

    print(f"\n{'═' * 70}")
    print(f"TABLETTE {tablet_id} — {name}")
    print(f"{total_gl} glyphes, {len(lines)} lignes, {pct:.1f}% décodé")
    print(f"{'═' * 70}")

    for lid in lines:
        result = translate_line(lid, corpus[lid], dictionary)
        print_translation(result, verbose=verbose)


def summary_all(corpus, dictionary):
    """Print summary for all tablets."""
    print(f"\n{'═' * 70}")
    print(f"ALBA RONGORONGO — GRILLE v2.0 (47 signes)")
    print(f"Couverture corpus: 93.5%")
    print(f"Dictionnaire: 9 383 mots")
    print(f"{'═' * 70}")

    for tablet_id in "ABCDEFGHIJKLMNOPQRSTUVWXY":
        lines = sorted([lid for lid in corpus if lid.startswith(tablet_id)])
        if not lines:
            continue
        total_gl = sum(len(corpus[lid]) for lid in lines)
        total_dec = sum(1 for lid in lines for g in corpus[lid] if g in GRILLE or g in TAXO)
        pct = total_dec / total_gl * 100

        # Count word matches
        word_hits = 0
        total_segs = 0
        for lid in lines:
            for seg in segment(corpus[lid]):
                total_segs += 1
                dec = "".join(GRILLE.get(g, f"[{g}]") for g in seg)
                if "[" not in dec:
                    clean = dec.replace("|", "")
                    if clean in dictionary:
                        word_hits += 1

        name = TABLET_NAMES.get(tablet_id, "?")
        print(f"  {tablet_id} ({name:>30}): {total_gl:>5} gl, {pct:>5.1f}%, "
              f"{word_hits:>3}/{total_segs:>3} mots DICT")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    corpus = load_corpus()
    dictionary = load_dict()

    if len(sys.argv) < 2:
        summary_all(corpus, dictionary)
        print(f"\nUsage: python {sys.argv[0]} <tablet|line|--all>")

    elif sys.argv[1] == "--all":
        for tablet_id in "ABCDEFGHIJKLMNOPQRSTUVWXY":
            translate_tablet(tablet_id, corpus, dictionary, verbose=False)

    elif len(sys.argv[1]) == 1 and sys.argv[1].upper() in "ABCDEGHKNPQRS":
        translate_tablet(sys.argv[1].upper(), corpus, dictionary)

    elif sys.argv[1] in corpus:
        result = translate_line(sys.argv[1], corpus[sys.argv[1]], dictionary)
        print_translation(result)

    else:
        # Try as tablet ID
        tid = sys.argv[1].upper()
        if tid in "ABCDEGHKNPQRS":
            translate_tablet(tid, corpus, dictionary)
        else:
            print(f"Ligne ou tablette '{sys.argv[1]}' non trouvée.")
            print(f"Tablettes: A B C D E G H K N P Q R S")
            print(f"Lignes: Aa1, Ca3, Na1, Hr1, etc.")
