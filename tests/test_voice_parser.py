from app.voice.item_parser import parse_transcript


def test_parses_known_item_and_quantity():
    # "sukuma" matches directly against the vocabulary (data/kongowea_prices.json).
    result = parse_transcript("kilo mbili za sukuma bei mia moja")
    assert result is not None
    assert result["item"] == "sukuma"
    assert result["quantity"] == 2.0  # "mbili" resolves via the Swahili number fallback


def test_parses_numeric_quantity_when_present():
    result = parse_transcript("2 kilo za tomato bei 100")
    assert result is not None
    assert result["item"] == "tomato"
    assert result["quantity"] == 2.0
    assert result["price"] == 100.0


def test_returns_none_for_unknown_item():
    result = parse_transcript("nataka kununua ndege")
    assert result is None
