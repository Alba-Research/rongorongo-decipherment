#!/usr/bin/env python3
"""ALBA Rongorongo — Pozdniakov CV alternation + frequency correlation tests"""
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

DB = 'data/rongorongo.db'

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
TAXO = {"200", "400", "700", "901", "660", "000"}

# Classify ALBA signs into Pozdniakov-style classes
# V = pure vowel (starts with vowel, single phoneme)
# CS = consonant or syllable starting with consonant
def classify(glyph):
    if glyph in TAXO:
        return "SEP"
    val = GRILLE.get(glyph)
    if val is None:
        return "UNK"
    if val == "":  # glottal stop
        return "SEP"
    if val in ('a', 'e', 'i', 'o', 'u'):
        return "V"
    else:
        return "CS"  # consonant or CV syllable


# Load corpus
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT line_id, position, barthel_code FROM glyphs ORDER BY line_id, position")
corpus = defaultdict(list)
for lid, pos, code in c.fetchall():
    corpus[lid].append(code)
conn.close()

CLASSIC = "ABCDEGHKNPQRS"

print("=" * 70)
print("TASK 1c: CV ALTERNATION TEST (Pozdniakov)")
print("=" * 70)

# Count bigram transitions
transitions = Counter()
total_bigrams = 0

for tid in CLASSIC:
    for lid in sorted(corpus.keys()):
        if not lid.startswith(tid):
            continue
        glyphs = corpus[lid]
        classes = [classify(g) for g in glyphs]

        for i in range(len(classes) - 1):
            c1, c2 = classes[i], classes[i + 1]
            if c1 in ("SEP", "UNK") or c2 in ("SEP", "UNK"):
                continue
            transitions[(c1, c2)] += 1
            total_bigrams += 1

print(f"\nTotal classified bigrams: {total_bigrams}")
print(f"\nTransition matrix:")
print(f"  {'':>5s}  {'V':>8s}  {'CS':>8s}")
for c1 in ["V", "CS"]:
    counts = [transitions.get((c1, c2), 0) for c2 in ["V", "CS"]]
    total = sum(counts)
    pcts = [c / total * 100 if total > 0 else 0 for c in counts]
    print(f"  {c1:>5s}  {counts[0]:>5d} ({pcts[0]:4.1f}%)  {counts[1]:>5d} ({pcts[1]:4.1f}%)")

# Alternation rate = V->CS + CS->V as % of all
alt = transitions.get(("V", "CS"), 0) + transitions.get(("CS", "V"), 0)
same = transitions.get(("V", "V"), 0) + transitions.get(("CS", "CS"), 0)
alt_rate = alt / (alt + same) * 100

print(f"\nAlternation rate (V<->CS): {alt_rate:.1f}%")
print(f"  Pozdniakov reports: 75.9%")
print(f"  ALBA achieves: {alt_rate:.1f}%")
if alt_rate > 70:
    print("  >>> CONSISTENT with Pozdniakov <<<")
elif alt_rate > 60:
    print("  >>> PARTIALLY consistent <<<")
else:
    print("  >>> NOT consistent <<<")


print(f"\n{'=' * 70}")
print("TASK 1d: FREQUENCY RANK CORRELATION")
print("=" * 70)

# Count glyph frequencies in corpus
glyph_freq = Counter()
for tid in CLASSIC:
    for lid in corpus:
        if lid.startswith(tid):
            for g in corpus[lid]:
                if g in GRILLE and g not in TAXO:
                    glyph_freq[g] += 1

# Map to phonetic values and aggregate
phoneme_freq = Counter()
for g, count in glyph_freq.items():
    val = GRILLE.get(g, "")
    if val:
        phoneme_freq[val] += count

print("\nALBA phoneme frequencies in corpus:")
for val, cnt in phoneme_freq.most_common(20):
    print(f"  {val:>4s}: {cnt:>5d}")

# Expected Rapa Nui syllable frequencies (approximate, from Kieviet 2017 / general RN)
# Most frequent syllables in Rapa Nui texts:
RN_RANK = ['a', 'i', 'e', 'ra', 'o', 'te', 'u', 'ta', 'ki', 'ka',
           'ma', 'na', 'ko', 'ri', 'ha', 't', 'k', 'h', 'n', 'r',
           'm', 'p', 'ng', 'v', 'hua']

alba_rank = [val for val, _ in phoneme_freq.most_common()]

# Spearman correlation (manual)
# Only compare values present in both rankings
common = set(alba_rank) & set(RN_RANK)
common_list = sorted(common)

alba_ranks = {}
for i, v in enumerate(alba_rank):
    if v not in alba_ranks:
        alba_ranks[v] = i + 1
rn_ranks = {}
for i, v in enumerate(RN_RANK):
    if v not in rn_ranks:
        rn_ranks[v] = i + 1

n = len(common_list)
d_sq_sum = 0
print(f"\nRank comparison ({n} common phonemes):")
print(f"  {'Phoneme':>8s}  {'ALBA rank':>10s}  {'RN rank':>8s}  {'d':>4s}")
for v in common_list:
    ar = alba_ranks[v]
    rr = rn_ranks[v]
    d = ar - rr
    d_sq_sum += d * d
    print(f"  {v:>8s}  {ar:>10d}  {rr:>8d}  {d:>4d}")

# Spearman rho = 1 - 6*sum(d^2) / (n*(n^2-1))
rho = 1 - 6 * d_sq_sum / (n * (n * n - 1))
print(f"\nSpearman rho = {rho:.3f}")

# Approximate t-test for significance
import math
if abs(rho) < 1.0 and n > 2:
    t_stat = rho * math.sqrt((n - 2) / (1 - rho * rho))
    # Approximate p-value from t-distribution (2-tailed)
    # For n-2 degrees of freedom
    df = n - 2
    print(f"t-statistic = {t_stat:.2f} (df={df})")
    if abs(t_stat) > 2.58:
        print(f">>> SIGNIFICANT (p < 0.01) <<<")
    elif abs(t_stat) > 1.96:
        print(f">>> SIGNIFICANT (p < 0.05) <<<")
    else:
        print(f">>> NOT SIGNIFICANT <<<")
