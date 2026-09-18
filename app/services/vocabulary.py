"""
Shared item/price vocabulary — used by the voice parser (to match transcribed
speech against known items) and by demo seed data. One source of truth in
data/kongowea_prices.json so both stay in sync.
"""
import json
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "kongowea_prices.json"


def load_vocabulary() -> dict:
    with open(_DATA_PATH, "r") as f:
        return json.load(f)


VOCABULARY = load_vocabulary()
ITEM_NAMES = list(VOCABULARY.keys())
