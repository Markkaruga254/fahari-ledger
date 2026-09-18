"""
Keyword/segment matcher against a fixed vocabulary — deliberately NOT a
trained NLU model. Given a transcript like "kilo mbili za sukuma bei mia
moja", find the known item, resolve quantity from the words before it, and
resolve price from a supported price marker such as "bei", "for", or "at".
Falls back to None so the caller can ask a clarifying question rather than
guessing wrong.
"""
import re

from app.services.vocabulary import ITEM_NAMES

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

_MULTI_WORD_NUMBERS = {
    "mia moja": 100, "mia mbili": 200, "mia tatu": 300, "mia nne": 400, "mia tano": 500,
}
_SINGLE_WORD_NUMBERS = {
    "moja": 1, "mbili": 2, "tatu": 3, "nne": 4, "tano": 5,
    "sita": 6, "saba": 7, "nane": 8, "tisa": 9, "kumi": 10,
    "mia": 100,
}

_PRICE_MARKERS = ("bei", "for", "at")


def _resolve_number(segment: str) -> float | None:
    digit_match = _NUMBER_RE.search(segment)
    if digit_match:
        return float(digit_match.group())
    for phrase, value in _MULTI_WORD_NUMBERS.items():
        if phrase in segment:
            return float(value)
    for word in segment.split():
        if word in _SINGLE_WORD_NUMBERS:
            return float(_SINGLE_WORD_NUMBERS[word])
    return None


def parse_transcript(transcript: str) -> dict | None:
    text = transcript.lower().strip()
    item = next((name for name in ITEM_NAMES if name in text), None)
    if item is None:
        return None

    item_idx = text.index(item)
    before = text[:item_idx]
    after = text[item_idx + len(item):]

    quantity = _resolve_number(before)
    price = None

    for marker in _PRICE_MARKERS:
        if marker in after:
            price_segment = after.split(marker, 1)[1]
            price = _resolve_number(price_segment)
            break

    if quantity is None:
        return None

    return {"item": item, "quantity": quantity, "price": price}
