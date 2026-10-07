"""Arabic normalization for embedding/search. Original text is kept separately."""

from __future__ import annotations

import re
import unicodedata

_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)
_TATWEEL = "\u0640"
_ALEF_VARIANTS = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
    }
)
_YA_VARIANTS = str.maketrans({"ى": "ي", "ئ": "ي"})
_TA_MARBUTA = str.maketrans({"ة": "ه"})


def normalize_arabic(text: str, *, unify_ta_marbuta: bool = True) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = text.translate(_ALEF_VARIANTS)
    text = text.translate(_YA_VARIANTS)
    if unify_ta_marbuta:
        text = text.translate(_TA_MARBUTA)
    text = re.sub(r"\s+", " ", text).strip()
    return text
