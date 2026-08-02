"""Text normalization for accent-insensitive, Arabic-aware, typo-tolerant search.

The goal: "Coca", "coca", "Coca-Cola", "Cocacola" and "كوكا" should all match
the same product. We build a normalized ``search_blob`` per product at write
time and normalize the query the same way at read time, so lookups stay a
simple indexed ``LIKE`` on pre-folded text — fast even at 50k+ products.
"""
import re
import unicodedata

# Arabic letter normalization: unify alef/hamza forms, ta-marbuta, alef-maqsura,
# and strip harakat (diacritics).
_ARABIC_MAP = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ئ": "ي",
    "ؤ": "و",
    "ة": "ه",
}
_ARABIC_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def strip_accents(text: str) -> str:
    """Fold Latin accents: é->e, ç->c, à->a, etc."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    """Normalize a single token/phrase for search comparison.

    Lower-cases, removes Latin accents, folds Arabic letters, drops diacritics
    and collapses everything that is not a letter/number (spaces, dashes).
    "Coca-Cola" and "cocacola" both become "cocacola".
    """
    if not text:
        return ""
    text = text.strip().lower()
    text = _ARABIC_DIACRITICS.sub("", text)
    text = "".join(_ARABIC_MAP.get(ch, ch) for ch in text)
    text = strip_accents(text)
    # Keep unicode letters/digits, drop separators and punctuation.
    text = re.sub(r"[^0-9a-z؀-ۿ]+", "", text)
    return text


def normalize_tokens(text: str) -> str:
    """Space-separated normalized tokens, preserving word boundaries."""
    if not text:
        return ""
    parts = re.split(r"\s+", text.strip())
    return " ".join(normalize(p) for p in parts if p)


def build_search_blob(*fields: str) -> str:
    """Combine product names/sku/barcode into one normalized search string."""
    chunks = []
    for f in fields:
        if not f:
            continue
        chunks.append(normalize(f))
        chunks.append(normalize_tokens(f))
    # De-duplicate while preserving order.
    seen, out = set(), []
    for c in chunks:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return " ".join(out)


def levenshtein(a: str, b: str) -> int:
    """Classic edit distance — used to rank typo-tolerant matches."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
