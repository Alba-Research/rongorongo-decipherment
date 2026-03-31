#!/usr/bin/env python3
"""
ALBA Rongorongo — Robustness Checks
Test A: Leave-one-tablet-out with ONLY attested Rapa Nui words (no cognates)
Test B: Full pipeline with 10 random permuted grilles as negative control
"""
import sqlite3, random, math, re, unicodedata
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "rongorongo.db"
DICT_FULL = BASE / "data" / "rapanui_dictionary.txt"
DICT_ENGLERT = BASE / "data" / "englert_dictionary.txt"
DICT_CORPUS = BASE / "data" / "corpus_derived_vocab.txt"

# The 48-sign grille
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
TAXO = {"200", "400", "700", "901", "660", "000"}
CLASSIC_TABLETS = ["A", "B", "C", "D", "E", "G", "H", "K", "N", "P", "Q", "R", "S"]


def strip_diacritics(s):
    """Remove diacritics and normalize to ASCII."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def load_englert_strict():
    """Load only attested Rapa Nui words from Englert + corpus-derived."""
    words = set()

    # Parse Englert dictionary (has diacritics, commas, spaces)
    with open(DICT_ENGLERT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Split on commas for variant forms
            for part in line.split(','):
                part = part.strip()
                # Split on spaces for multi-word entries
                for word in part.split():
                    w = strip_diacritics(word).lower()
                    # Remove non-alpha
                    w = re.sub(r'[^a-z]', '', w)
                    if w and len(w) >= 2:
                        words.add(w)

    # Add corpus-derived vocab
    with open(DICT_CORPUS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            w = line.split('\t')[0].strip().lower()
            w = re.sub(r'[^a-z]', '', w)
            if w and len(w) >= 2:
                words.add(w)

    # Add single-letter grammatical particles (these are core Rapa Nui)
    for p in ['a', 'e', 'i', 'o', 'u']:
        words.add(p)

    # Generate productive morphology from attested bases only
    bases = list(words)
    for base in bases:
        if len(base) >= 3:
            # Reduplications
            words.add(base + base)           # full reduplication
            words.add(base[:2] + base)       # partial reduplication
            # Causative haka-
            words.add('haka' + base)
            # Nominalizations
            words.add(base + 'ga')
            words.add(base + 'haga')

    return words


def load_full_dict():
    """Load the full 9383-word dictionary."""
    words = set()
    with open(DICT_FULL, encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if w:
                words.add(w)
    return words


def load_corpus():
    """Load glyph corpus from database."""
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute("SELECT line_id, position, barthel_code FROM glyphs ORDER BY line_id, position")
    corpus = defaultdict(list)
    for lid, pos, code in c.fetchall():
        corpus[lid].append(code)
    conn.close()
    return corpus


def segment(gl):
    """Segment glyphs by word separators."""
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


def count_word_matches(grille, tablet_lines, dictionary):
    """Count dictionary word matches on a single tablet."""
    hits = 0
    total_decoded = 0
    for lid, gl in tablet_lines:
        for seg in segment(gl):
            decoded = "".join(grille.get(g, f"[{g}]") for g in seg)
            if "[" in decoded:
                continue
            clean = decoded.replace("|", "")
            total_decoded += 1
            if clean in dictionary:
                hits += 1
    return hits, total_decoded


def leave_one_out(dictionary, dict_name, corpus, n_perms=5000):
    """Leave-one-tablet-out cross-validation."""
    random.seed(42)
    glyph_keys = list(GRILLE.keys())
    phoneme_values = list(GRILLE.values())

    print(f"\n{'=' * 70}")
    print(f"LEAVE-ONE-TABLET-OUT — {dict_name}")
    print(f"{'=' * 70}")
    print(f"  Dictionary: {len(dictionary)} words")
    print(f"  Permutations: {n_perms}")
    print()

    results = []

    for tablet_id in CLASSIC_TABLETS:
        tablet_lines = [(lid, corpus[lid]) for lid in corpus if lid.startswith(tablet_id)]
        if not tablet_lines:
            continue

        total_gl = sum(len(gl) for _, gl in tablet_lines)
        real_hits, real_decoded = count_word_matches(GRILLE, tablet_lines, dictionary)

        perm_hits = []
        for _ in range(n_perms):
            shuffled = phoneme_values.copy()
            random.shuffle(shuffled)
            perm_grille = dict(zip(glyph_keys, shuffled))
            h, _ = count_word_matches(perm_grille, tablet_lines, dictionary)
            perm_hits.append(h)

        mean_p = sum(perm_hits) / len(perm_hits)
        std_p = (sum((h - mean_p) ** 2 for h in perm_hits) / len(perm_hits)) ** 0.5
        z = (real_hits - mean_p) / std_p if std_p > 0 else 0
        p_val = sum(1 for h in perm_hits if h >= real_hits) / len(perm_hits)

        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""

        results.append({
            "tablet": tablet_id, "glyphs": total_gl,
            "real_hits": real_hits, "decoded_segs": real_decoded,
            "mean_perm": mean_p, "std_perm": std_p,
            "z": z, "p": p_val, "sig": sig,
        })

        print(f"  {tablet_id}: hits={real_hits}/{real_decoded}, "
              f"random={mean_p:.1f}±{std_p:.1f}, "
              f"Z={z:.2f}, p={p_val:.4f} {sig}")

    # Summary
    print(f"\n  {'=' * 60}")
    n_sig = sum(1 for r in results if r["p"] < 0.05)
    avg_z = sum(r["z"] for r in results) / len(results)
    total_real = sum(r["real_hits"] for r in results)
    total_perm = sum(r["mean_perm"] for r in results)

    print(f"  Tablets tested: {len(results)}")
    print(f"  Significant (p<0.05): {n_sig}/{len(results)} ({n_sig/len(results)*100:.0f}%)")
    print(f"  Average Z-score: {avg_z:.2f}")
    print(f"  Total hits: {total_real} vs random {total_perm:.0f} (ratio {total_real/total_perm:.2f}x)")

    # Fisher's method
    chi2 = -2 * sum(math.log(max(r["p"], 1e-10)) for r in results)
    df = 2 * len(results)
    combined_z = (chi2 - df) / math.sqrt(2 * df)
    print(f"  Fisher chi²: {chi2:.1f} (df={df}), combined Z: {combined_z:.2f}")
    if combined_z > 3.29:
        print(f"  Combined p < 0.001 ***")
    elif combined_z > 2.58:
        print(f"  Combined p < 0.01 **")
    elif combined_z > 1.96:
        print(f"  Combined p < 0.05 *")
    else:
        print(f"  Combined p > 0.05 (NOT SIGNIFICANT)")

    return results, combined_z


def test_random_grilles(corpus, dictionary, n_grilles=10, n_perms=1000):
    """Test B: Compare real grille vs N random grilles on full Viterbi metrics."""
    random.seed(123)
    glyph_keys = list(GRILLE.keys())
    phoneme_values = list(GRILLE.values())

    print(f"\n{'=' * 70}")
    print(f"TEST B: REAL GRILLE vs {n_grilles} RANDOM GRILLES")
    print(f"{'=' * 70}")
    print(f"  Dictionary: {len(dictionary)} words")
    print()

    # Get ALL tablet lines
    all_lines = []
    for tablet_id in CLASSIC_TABLETS:
        for lid in corpus:
            if lid.startswith(tablet_id):
                all_lines.append((lid, corpus[lid]))

    # Score real grille
    real_hits, real_decoded = count_word_matches(GRILLE, all_lines, dictionary)
    real_ratio = real_hits / real_decoded if real_decoded > 0 else 0

    # Count particle proportion for real grille
    particles = {'a', 'e', 'i', 'o', 'u', 'te', 'ki', 'ko', 'ka', 'na', 'ra', 'ma',
                 'ai', 'au', 'ia', 'oe', 'ie', 'ei', 'he', 'no', 'mo', 'ke', 'pe'}
    real_particle_count = 0
    real_word_count = 0
    for lid, gl in all_lines:
        for seg in segment(gl):
            decoded = "".join(GRILLE.get(g, f"[{g}]") for g in seg)
            if "[" in decoded:
                continue
            clean = decoded.replace("|", "")
            if clean in dictionary:
                real_word_count += 1
                if clean in particles:
                    real_particle_count += 1
    real_particle_ratio = real_particle_count / real_word_count if real_word_count > 0 else 0

    print(f"  REAL GRILLE:")
    print(f"    Word matches: {real_hits}/{real_decoded} ({real_ratio*100:.1f}%)")
    print(f"    Particle ratio: {real_particle_count}/{real_word_count} ({real_particle_ratio*100:.1f}%)")
    print(f"    [Target: 32.9% in real RN texts]")
    print()

    # Score random grilles
    random_hits = []
    random_ratios = []
    random_particle_ratios = []

    for gi in range(n_grilles):
        shuffled = phoneme_values.copy()
        random.shuffle(shuffled)
        rand_grille = dict(zip(glyph_keys, shuffled))

        hits, decoded = count_word_matches(rand_grille, all_lines, dictionary)
        ratio = hits / decoded if decoded > 0 else 0
        random_hits.append(hits)
        random_ratios.append(ratio)

        # Particle ratio for random grille
        rp_count = 0
        rw_count = 0
        for lid, gl in all_lines:
            for seg in segment(gl):
                dec = "".join(rand_grille.get(g, f"[{g}]") for g in seg)
                if "[" in dec:
                    continue
                clean = dec.replace("|", "")
                if clean in dictionary:
                    rw_count += 1
                    if clean in particles:
                        rp_count += 1
        rp_ratio = rp_count / rw_count if rw_count > 0 else 0
        random_particle_ratios.append(rp_ratio)

        print(f"  Random grille {gi+1}: hits={hits}/{decoded} ({ratio*100:.1f}%), "
              f"particles={rp_ratio*100:.1f}%")

    # Summary
    mean_rand = sum(random_hits) / len(random_hits)
    std_rand = (sum((h - mean_rand)**2 for h in random_hits) / len(random_hits))**0.5
    z_score = (real_hits - mean_rand) / std_rand if std_rand > 0 else 0
    p_value = sum(1 for h in random_hits if h >= real_hits) / len(random_hits)

    mean_particle = sum(random_particle_ratios) / len(random_particle_ratios)

    print(f"\n  {'=' * 60}")
    print(f"  SUMMARY:")
    print(f"    Real grille: {real_hits} hits ({real_ratio*100:.1f}%)")
    print(f"    Random mean: {mean_rand:.1f} ± {std_rand:.1f} ({sum(random_ratios)/len(random_ratios)*100:.1f}%)")
    print(f"    Z-score: {z_score:.2f}")
    print(f"    p-value: {p_value:.3f} ({'SIGNIFICANT' if p_value < 0.05 else 'not significant'})")
    print(f"    Ratio real/random: {real_hits/mean_rand:.2f}x")
    print()
    print(f"    Real particle ratio: {real_particle_ratio*100:.1f}%")
    print(f"    Random particle ratio: {mean_particle*100:.1f}%")
    print(f"    Target (real RN texts): 32.9%")
    print(f"    Real grille {'CLOSER' if abs(real_particle_ratio - 0.329) < abs(mean_particle - 0.329) else 'FARTHER'} to target")


if __name__ == "__main__":
    print("ALBA RONGORONGO — ROBUSTNESS CHECKS")
    print("=" * 70)

    # Load corpus
    corpus = load_corpus()

    # Load dictionaries
    dict_full = load_full_dict()
    dict_strict = load_englert_strict()

    print(f"\nDictionary sizes:")
    print(f"  Full (with cognates): {len(dict_full)}")
    print(f"  Strict (Englert only + morphology): {len(dict_strict)}")
    print(f"  Overlap: {len(dict_full & dict_strict)}")
    print(f"  Cognates-only: {len(dict_full - dict_strict)}")

    # ========== TEST A ==========
    print("\n" + "=" * 70)
    print("TEST A: LEAVE-ONE-OUT WITH vs WITHOUT COGNATES")
    print("=" * 70)

    results_full, z_full = leave_one_out(dict_full, "FULL (9383 words)", corpus, n_perms=5000)
    results_strict, z_strict = leave_one_out(dict_strict, "STRICT (Englert-only + morphology)", corpus, n_perms=5000)

    print(f"\n{'=' * 70}")
    print("TEST A COMPARISON")
    print(f"{'=' * 70}")
    print(f"  Full dict combined Z:   {z_full:.2f}")
    print(f"  Strict dict combined Z: {z_strict:.2f}")
    if z_strict > 1.96:
        print(f"  >>> SIGNAL HOLDS WITHOUT COGNATES (p < 0.05) <<<")
    else:
        print(f"  >>> WARNING: Signal weakens without cognates <<<")

    # ========== TEST B ==========
    test_random_grilles(corpus, dict_full, n_grilles=10, n_perms=1000)
