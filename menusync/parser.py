"""Spatial parsing of OCR boxes into categories, items and prices.

The grouping logic is a cleaned-up version of the original menu_parser.py: boxes are sorted by their
vertical centre, boxes whose centres sit within ~60% of the median text height are one line, each line is
sorted left to right; an all-caps line is a category header, a line with a price-looking token on the
right is an item. Everything here is pure Python on OCR tuples so it is testable without EasyOCR.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image, ImageDraw

PRICE_RE = re.compile(r"^[\$S5]?\s?(\d{1,4})[.,](\d{2})$")
PRICE_LOOSE_RE = re.compile(r"[\$S]\s?\d{1,4}(?:[.,]\d{2})?$|\d{1,4}[.,]\d{2}$")
COLORS = {"title": (79, 209, 197), "category": (240, 113, 138), "item": (232, 236, 246), "price": (242, 184, 75)}


@dataclass
class Box:
    bbox: list
    text: str
    conf: float

    @property
    def x(self) -> float:
        return min(p[0] for p in self.bbox)

    @property
    def yc(self) -> float:
        ys = [p[1] for p in self.bbox]
        return (min(ys) + max(ys)) / 2

    @property
    def height(self) -> float:
        ys = [p[1] for p in self.bbox]
        return max(ys) - min(ys)


@dataclass
class Line:
    boxes: list[Box] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(b.text for b in self.boxes)

    @property
    def yc(self) -> float:
        return statistics.fmean(b.yc for b in self.boxes)


def to_boxes(results, min_conf: float = 0.2) -> list[Box]:
    return [Box([list(map(float, p)) for p in bbox], str(text).strip(), float(conf))
            for bbox, text, conf in results if float(conf) >= min_conf and str(text).strip()]  # fmt: skip


def group_lines(results, min_conf: float = 0.2) -> list[Line]:
    """Group OCR boxes into text lines by vertical centre; tolerance scales with the text height."""
    boxes = sorted(to_boxes(results, min_conf), key=lambda b: b.yc)
    if not boxes:
        return []
    tol = 0.6 * statistics.median(b.height for b in boxes)
    lines: list[Line] = [Line([boxes[0]])]
    for b in boxes[1:]:
        if abs(b.yc - lines[-1].yc) <= tol:
            lines[-1].boxes.append(b)
        else:
            lines.append(Line([b]))
    for ln in lines:
        ln.boxes.sort(key=lambda b: b.x)
    return lines


def split_columns(results, width: int, min_conf: float = 0.2, min_side: int = 6) -> list[list]:
    """Layout detection for multi-column menus. Candidate cuts in the middle third of the page, nearest the centre
    first: a cut crossed by at most one box (the centred title) with item names AND prices on both sides is a column
    gap (the box-free band between names and their dot leaders has no prices on the left, so it never qualifies).
    Returns result groups in reading order: boxes spanning the cut first, then the left column, then the right."""
    boxes = to_boxes(results, min_conf)
    if len(boxes) < 2 * min_side:
        return [results]
    kept = _kept(results, min_conf)
    spans = [(min(p[0] for p in b.bbox), max(p[0] for p in b.bbox)) for b in boxes]
    centre = width / 2
    for x in sorted(range(int(width * 0.35), int(width * 0.65)), key=lambda v: abs(v - centre)):
        crossing = {i for i, (x0, x1) in enumerate(spans) if x0 < x < x1}
        if len(crossing) > 1:
            continue
        left = [r for i, (b, r) in enumerate(zip(boxes, kept, strict=True)) if i not in crossing and b.x < x]
        right = [r for i, (b, r) in enumerate(zip(boxes, kept, strict=True)) if i not in crossing and b.x >= x]
        if len(left) < min_side or len(right) < min_side:
            continue
        if any(_n_prices(side) < 2 or len(side) - _n_prices(side) < 2 for side in (left, right)):
            continue
        return [g for g in ([kept[i] for i in sorted(crossing)], left, right) if g]
    return [results]


def _n_prices(group) -> int:
    return sum(looks_like_price(str(t)) for _, t, _ in group)


def _kept(results, min_conf: float) -> list:
    return [r for r in results if float(r[2]) >= min_conf and str(r[1]).strip()]


def parse_price(text: str) -> float | None:
    """'$12.99', 'S12.99' (OCR for $), '12,99' -> 12.99; None when it is not a price."""
    t = text.replace(" ", "")
    m = PRICE_RE.match(t)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m = re.match(r"^[\$S]?(\d{1,4})$", t)
    if m and t.startswith(("$", "S")):
        return float(m.group(1))
    return None


def looks_like_price(text: str) -> bool:
    return parse_price(text) is not None or bool(PRICE_LOOSE_RE.search(text.replace(" ", "")))


def is_category(line: Line) -> bool:
    t = line.text
    letters = [c for c in t if c.isalpha()]
    return len(letters) >= 3 and t.upper() == t and not any(looks_like_price(b.text) for b in line.boxes)


def structure(lines: list[Line]) -> dict:
    """Lines -> {restaurant, categories: [{name, items: [{name, price, price_text, confidence, bbox}]}]}."""
    menu: dict = {"restaurant": None, "categories": [], "n_lines": len(lines), "unparsed": []}
    current: dict | None = None
    for ln in lines:
        if is_category(ln):
            current = {"name": ln.text.title(), "items": []}
            menu["categories"].append(current)
            continue
        if menu["restaurant"] is None and current is None:
            menu["restaurant"] = ln.text
            continue
        price_box = next((b for b in reversed(ln.boxes) if looks_like_price(b.text)), None)
        name_boxes = [b for b in ln.boxes if b is not price_box and not set(b.text) <= set(".·-_ ")]
        name = " ".join(b.text for b in name_boxes).strip(" .·-_")
        if not name:
            menu["unparsed"].append(ln.text)
            continue
        item = {
            "name": name,
            "price": parse_price(price_box.text) if price_box else None,
            "price_text": price_box.text if price_box else None,
            "confidence": round(min(b.conf for b in ln.boxes), 3),
            "bbox": [int(min(b.x for b in ln.boxes)), int(min(min(p[1] for p in b.bbox) for b in ln.boxes)),
                     int(max(max(p[0] for p in b.bbox) for b in ln.boxes)),
                     int(max(max(p[1] for p in b.bbox) for b in ln.boxes))],
        }  # fmt: skip
        if current is None:
            current = {"name": "Uncategorised", "items": []}
            menu["categories"].append(current)
        current["items"].append(item)
    _fix_currency_glyph(menu)
    menu["n_items"] = sum(len(c["items"]) for c in menu["categories"])
    menu["n_priced"] = sum(1 for c in menu["categories"] for i in c["items"] if i["price"] is not None)
    return menu


def _fix_currency_glyph(menu: dict) -> None:
    """Page-level consistency: if most prices carry a currency glyph ($ or its OCR twin S), a price read as '88.00'
    or '811.00' is '$8.00' / '$11.00' with the $ read as 8. Only applied when the page shows a currency convention."""
    items = [i for c in menu["categories"] for i in c["items"] if i["price_text"]]
    if not items:
        return
    texts = [i["price_text"].replace(" ", "") for i in items]
    with_glyph = sum(t[0] in "$S" for t in texts)
    eight_led = sum(bool(re.match(r"^8\d{1,3}[.,]\d{2}$", t)) for t in texts)
    if eight_led < 2 or with_glyph + eight_led < 0.7 * len(items):
        return
    for i in items:
        t = i["price_text"].replace(" ", "")
        m = re.match(r"^8(\d{1,3})[.,](\d{2})$", t)
        if m and i["price"] is not None and i["price"] >= 80:
            i["price"] = float(f"{m.group(1)}.{m.group(2)}")
            i["price_corrected"] = True


def flatten(menu: dict, source: str = "") -> list[dict]:
    rows = []
    for c in menu["categories"]:
        for i in c["items"]:
            rows.append({"file": source, "restaurant": menu["restaurant"], "category": c["name"],
                         "item": i["name"], "price": i["price"], "confidence": i["confidence"]})  # fmt: skip
    return rows


def load_bgr(image) -> np.ndarray:
    if isinstance(image, str):
        img = cv2.imread(image)
        if img is None:
            raise FileNotFoundError(image)
        return img
    if isinstance(image, Image.Image):
        return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    arr = np.asarray(image)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR) if arr.ndim == 3 else cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)


def preprocess(bgr: np.ndarray) -> np.ndarray:
    """Grayscale + light denoise; EasyOCR does its own scaling and binarisation."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return cv2.bilateralFilter(gray, 5, 40, 40)


class MenuDigitizer:
    """OCR + spatial parsing. `process` returns the structured menu plus the raw boxes for annotation."""

    def __init__(self, min_conf: float = 0.2):
        self.min_conf = min_conf

    def process(self, image) -> dict:
        from menusync.ocr import read

        bgr = load_bgr(image)
        results = read(preprocess(bgr))
        groups = split_columns(results, bgr.shape[1], self.min_conf)
        lines = [ln for g in groups for ln in group_lines(g, self.min_conf)]
        menu = structure(lines)
        menu["columns"] = max(1, len(groups) - (1 if len(groups) == 3 else 0))
        menu["image_size"] = [int(bgr.shape[1]), int(bgr.shape[0])]
        menu["ocr_boxes"] = len(results)
        menu["_lines"] = lines
        return menu

    @staticmethod
    def annotate(image, menu: dict) -> Image.Image:
        pil = Image.fromarray(cv2.cvtColor(load_bgr(image), cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        lines = menu.get("_lines", [])
        for ln in lines:
            kind = "category" if is_category(ln) else "item"
            if menu.get("restaurant") and ln.text == menu["restaurant"]:
                kind = "title"
            for b in ln.boxes:
                k = "price" if kind == "item" and looks_like_price(b.text) else kind
                draw.polygon([tuple(p) for p in b.bbox], outline=COLORS[k], width=3)
        return pil
