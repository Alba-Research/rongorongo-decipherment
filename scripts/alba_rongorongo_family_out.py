#!/usr/bin/env python3
"""ALBA Rongorongo — Leave-one-FAMILY-out cross-validation"""
import sqlite3, random, math, re, unicodedata
from collections import defaultdict

DB = 'data/rongorongo.db'
DICT_FULL_PATH = 'data/rapanui_dictionary.txt'
DICT_ENGLERT_PATH = 'data/englert_dictionary.txt'
DICT_CORPUS_PATH = 'data/corpus_derived_vocab.txt'

GRILLE = {
    "006": "a", "003": "e", "001": "i", "010": "o",
    "061": "u", "062": "u", "066": "u", "045": "i",
    "002": "e", "009": "u", "044": "a", "005": "ra",
    "070": "a", "099": "o", "008": "na", "067": "ri",
    "069": "a", "280": "", "054": "a", "047": "a",
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

FAMILIES = {
    "HPQ": ["H", "P", "Q"],
    "GK": ["G", "K"],
    "A": ["A"], "B": ["B"], "C": ["C"], "D": ["D"],
    "E": ["E"], "N": ["N"], "R": ["R"], "S": ["S"],
}


def strip_diacritics(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def load_full():
    d = set()
    with open(DICT_FULL_PATH, encoding='utf-8') as f:
        for l in f:
            w = l.strip().lower()
            if w:
                d.add(w)
    return d


def load_strict():
    words = set()
    with open(DICT_ENGLERT_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            for part in line.split(','):
                for word in part.strip().split():
                    w = strip_diacritics(word).lower()
                    w = re.sub(r'[^a-z]', '', w)
                    if w:
                        words.add(w)
    with open(DICT_CORPUS_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            w = line.split('\t')[0].strip().lower()
            w = re.sub(r'[^a-z]', '', w)
            if w:
                words.add(w)
    for p in ['a', 'e', 'i', 'o', 'u']:
        words.add(p)
    bases = list(words)
    for base in bases:
        if len(base) >= 3:
            words.add(base + base)
            words.add(base[:2] + base)
            words.add('haka' + base)
            words.add(base + 'ga')
            words.add(base + 'haga')
    return words


def segment(gl):
    segs, cur = [], []
    for g in gl:
        if g in SEP:
            if cur:
                segs.append(list(cur))
            cur = []
        else:
            cur.append(g)
    if cur:
        segs.append(cur)
    return segs


def count_matches(grille, lines, dictionary):
    hits, total = 0, 0
    for lid, gl in lines:
        for seg in segment(gl):
            decoded = "".join(grille.get(g, f"[{g}]") for g in seg)
            if "[" in decoded:
                continue
            total += 1
            if decoded.replace("|", "") in dictionary:
                hits += 1
    return hits, total


def run_family_out(dictionary, name, corpus, n_perms=5000):
    random.seed(42)
    glyph_keys = list(GRILLE.keys())
    phoneme_values = list(GRILLE.values())

    print(f"\n{'=' * 70}")
    print(f"LEAVE-ONE-FAMILY-OUT -- {name}")
    print(f"{'=' * 70}")
    print(f"  Dict: {len(dictionary)} | Families: {len(FAMILIES)} | Perms: {n_perms}")
    print()

    results = []
    for fam_name, tablets in sorted(FAMILIES.items()):
        fam_lines = []
        for tid in tablets:
            for lid in corpus:
                if lid.startswith(tid):
                    fam_lines.append((lid, corpus[lid]))
        if not fam_lines:
            continue

        total_gl = sum(len(gl) for _, gl in fam_lines)
        real_hits, real_dec = count_matches(GRILLE, fam_lines, dictionary)

        perm_hits = []
        for _ in range(n_perms):
            shuffled = phoneme_values.copy()
            random.shuffle(shuffled)
            perm = dict(zip(glyph_keys, shuffled))
            h, _ = count_matches(perm, fam_lines, dictionary)
            perm_hits.append(h)

        mean_p = sum(perm_hits) / len(perm_hits)
        std_p = (sum((h - mean_p) ** 2 for h in perm_hits) / len(perm_hits)) ** 0.5
        z = (real_hits - mean_p) / std_p if std_p > 0 else 0
        p = sum(1 for h in perm_hits if h >= real_hits) / len(perm_hits)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""

        results.append({"family": fam_name, "tablets": ",".join(tablets),
                        "glyphs": total_gl, "hits": real_hits, "segs": real_dec,
                        "mean": mean_p, "std": std_p, "z": z, "p": p, "sig": sig})

        print(f"  {fam_name:4s} ({'+'.join(tablets):5s}): hits={real_hits}/{real_dec}, "
              f"random={mean_p:.1f}+/-{std_p:.1f}, Z={z:.2f}, p={p:.4f} {sig}")

    n_sig = sum(1 for r in results if r["p"] < 0.05)
    avg_z = sum(r["z"] for r in results) / len(results)
    total_real = sum(r["hits"] for r in results)
    total_rand = sum(r["mean"] for r in results)

    chi2 = -2 * sum(math.log(max(r["p"], 1e-10)) for r in results)
    df = 2 * len(results)
    cz = (chi2 - df) / math.sqrt(2 * df)

    print(f"\n  Sig: {n_sig}/{len(results)} | Avg Z: {avg_z:.2f} | "
          f"Hits: {total_real} vs {total_rand:.0f} ({total_real / total_rand:.2f}x)")
    print(f"  Fisher chi2={chi2:.1f} (df={df}), Z={cz:.2f}", end="")
    if cz > 3.29:
        print(" p < 0.001 ***")
    elif cz > 2.58:
        print(" p < 0.01 **")
    elif cz > 1.96:
        print(" p < 0.05 *")
    else:
        print(" NOT SIGNIFICANT")

    return results, cz


if __name__ == "__main__":
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT line_id, position, barthel_code FROM glyphs ORDER BY line_id, position")
    corpus = defaultdict(list)
    for lid, pos, code in c.fetchall():
        corpus[lid].append(code)
    conn.close()

    dict_full = load_full()
    dict_strict = load_strict()

    r1, z1 = run_family_out(dict_full, f"FULL ({len(dict_full)} words)", corpus)
    r2, z2 = run_family_out(dict_strict, f"STRICT Englert+morpho ({len(dict_strict)} words)", corpus)

    print(f"\n{'=' * 70}")
    print("COMPARISON: FAMILY-OUT vs TABLET-OUT")
    print(f"{'=' * 70}")
    print(f"  Tablet-out (full):   Z=3.54")
    print(f"  Family-out (full):   Z={z1:.2f}")
    print(f"  Tablet-out (strict): Z=5.88")
    print(f"  Family-out (strict): Z={z2:.2f}")
