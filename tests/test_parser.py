"""Pure parsing logic on hand-made OCR tuples: no EasyOCR needed."""
from menusync.parser import group_lines, is_category, parse_price, structure


def box(x, y, text, conf=0.9, w=None, h=20):
    w = w or 10 * len(text)
    return ([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], text, conf)


FAKE_OCR = [
    box(300, 40, "Bistro 2026", h=40),
    box(80, 130, "APPETIZERS", h=26),
    box(100, 170, "Calamari"),
    box(650, 171, "$12.99"),
    box(100, 205, "Garlic", conf=0.8),
    box(170, 206, "Bread", conf=0.7),
    box(650, 204, "S6.50"),  # EasyOCR often reads $ as S
    box(80, 260, "DRINKS", h=26),
    box(100, 300, "Iced Tea"),
    box(650, 300, "3.00"),
    box(100, 335, "Red Wine"),
    box(400, 336, "....", conf=0.3),
]


def test_group_lines_by_vertical_centre():
    lines = group_lines(FAKE_OCR)
    assert [ln.text for ln in lines][:4] == ["Bistro 2026", "APPETIZERS", "Calamari $12.99", "Garlic Bread S6.50"]


def test_parse_price_variants():
    assert parse_price("$12.99") == 12.99
    assert parse_price("S6.50") == 6.5
    assert parse_price("3,00") == 3.0
    assert parse_price("$8") == 8.0
    assert parse_price("Calamari") is None
    assert parse_price("2026") is None


def test_structure_items_prices_and_categories():
    menu = structure(group_lines(FAKE_OCR))
    assert menu["restaurant"] == "Bistro 2026"
    assert [c["name"] for c in menu["categories"]] == ["Appetizers", "Drinks"]
    app = menu["categories"][0]["items"]
    assert app[0] == {**app[0], "name": "Calamari", "price": 12.99}
    assert app[1]["name"] == "Garlic Bread" and app[1]["price"] == 6.5
    drinks = menu["categories"][1]["items"]
    assert drinks[0]["price"] == 3.0
    assert drinks[1]["name"] == "Red Wine" and drinks[1]["price"] is None
    assert menu["n_items"] == 4 and menu["n_priced"] == 3


def test_category_detection():
    lines = group_lines([box(80, 10, "MAIN COURSE"), box(80, 50, "$12.99"), box(80, 90, "Ok")])
    assert is_category(lines[0]) and not is_category(lines[1]) and not is_category(lines[2])


def test_empty_ocr():
    assert structure(group_lines([])) == {**structure([]), "n_items": 0}


def test_split_columns_two_column_layout():
    from menusync.parser import split_columns

    ocr = [box(400, 20, "Harbor Grill", h=40)]
    for i in range(7):
        ocr += [box(80, 120 + 40 * i, f"Left {i}"), box(380, 120 + 40 * i, "$1.00")]
        ocr += [box(560, 120 + 40 * i, f"Right {i}"), box(860, 120 + 40 * i, "$2.00")]
    groups = split_columns(ocr, width=1000)
    assert len(groups) == 3 and groups[0][0][1] == "Harbor Grill"
    assert all("Left" in t or "$1" in t for _, t, _ in groups[1])
    assert all("Right" in t or "$2" in t for _, t, _ in groups[2])
    assert split_columns(ocr[:5], width=1000) == [ocr[:5]]


def test_currency_glyph_read_as_8_is_corrected():
    ocr = [box(80, 10, "DRINKS")]
    rows = [("Iced Tea", "S3.00"), ("Red Wine", "811.00"), ("Beer", "$8.50"), ("Soda", "88.00")]
    for i, (name, price) in enumerate(rows):
        ocr += [box(100, 50 + 40 * i, name), box(650, 50 + 40 * i, price)]
    items = structure(group_lines(ocr))["categories"][0]["items"]
    assert [i["price"] for i in items] == [3.0, 11.0, 8.5, 8.0]
    assert items[1]["price_corrected"] and "price_corrected" not in items[0]
