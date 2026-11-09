"""Draw synthetic menus with PIL and save the ground truth next to them, so OCR extraction accuracy is measurable."""
from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RESTAURANTS = ["Bistro 2026", "Harbor Grill", "Casa Verde", "Noodle Lab", "The Food Spot"]
MENU = {
    "APPETIZERS": [("Calamari", 12.99), ("Garlic Bread", 6.50), ("Bruschetta", 9.00), ("Soup of the Day", 7.25)],
    "MAIN COURSE": [("Ribeye Steak", 34.99), ("Grilled Salmon", 28.00), ("Pasta Carbonara", 19.50),
                    ("Veggie Burger", 16.00), ("Chicken Tikka", 18.75), ("Mushroom Risotto", 21.00)],
    "SIDES": [("French Fries", 5.00), ("Cole Slaw", 4.00), ("Mashed Potatoes", 6.00), ("Grilled Corn", 4.50)],
    "DRINKS": [("Iced Tea", 3.00), ("Red Wine", 11.00), ("Craft Beer", 8.50), ("Espresso", 3.50)],
    "DESSERTS": [("Tiramisu", 9.00), ("Cheesecake", 8.00), ("Lemon Tart", 7.50)],
}  # fmt: skip
FONT_FILES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Trebuchet MS.ttf",
    "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def font(size: int, path: str | None):
    if path and Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def draw_menu(path: Path, name: str, rng: random.Random, two_column: bool = False) -> dict:
    """One menu image. Returns the ground truth: categories, items and prices as drawn."""
    w, h = (1000, 1300) if two_column else (800, 1200)
    paper = rng.choice([(255, 255, 252), (250, 246, 236), (246, 246, 246)])
    ink = rng.choice([(0, 0, 0), (40, 40, 40), (60, 30, 20)])
    accent = rng.choice([(150, 0, 0), (0, 70, 120), (90, 60, 10)])
    fpath = rng.choice(FONT_FILES)
    body, head, title = rng.choice([(22, 26, 40), (24, 28, 44), (20, 24, 36)])
    img = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(img)
    tf = font(title, fpath)
    tw = d.textlength(name, font=tf)
    d.text(((w - tw) / 2, 40), name, fill=ink, font=tf)
    d.line([(80, 40 + title + 18), (w - 80, 40 + title + 18)], fill=accent, width=2)

    cats = list(MENU)
    rng.shuffle(cats)
    truth = {"restaurant": name, "categories": []}
    cols = [(80, w // 2 - 40), (w // 2 + 40, w - 80)] if two_column else [(80, w - 80)]
    y_by_col = [130] * len(cols)
    col = 0
    for cat in cats:
        items = rng.sample(MENU[cat], k=min(len(MENU[cat]), rng.randint(2, 4)))
        truth["categories"].append({"name": cat.title(), "items": [{"name": n, "price": p} for n, p in items]})
        if two_column:
            col = y_by_col.index(min(y_by_col))
        x0, x1 = cols[col]
        y = y_by_col[col]
        d.text((x0, y), cat, fill=accent, font=font(head, fpath))
        y += head + 16
        bf = font(body, fpath)
        for n, p in items:
            price = f"${p:.2f}"
            pw = d.textlength(price, font=bf)
            d.text((x0 + 20, y), n, fill=ink, font=bf)
            nw = d.textlength(n, font=bf)
            dots_x0, dots_x1 = x0 + 30 + nw, x1 - pw - 12
            if dots_x1 > dots_x0 + 20:
                for dx in range(int(dots_x0), int(dots_x1), 9):
                    d.ellipse([dx, y + body * 0.7, dx + 2, y + body * 0.7 + 2], fill=(170, 170, 170))
            d.text((x1 - pw, y), price, fill=ink, font=bf)
            y += body + 14
        y_by_col[col] = y + 26
    if rng.random() < 0.5:  # mild noise and a slight tilt, like a phone photo
        img = img.rotate(rng.uniform(-1.2, 1.2), resample=Image.BICUBIC, fillcolor=paper)
    img.save(path)
    return truth


def generate(out_dir: Path, n: int = 5, seed: int = 42) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    truth = {}
    paths = []
    for i in range(n):
        p = out_dir / f"menu_{i + 1:02d}.png"
        truth[p.name] = draw_menu(p, RESTAURANTS[i % len(RESTAURANTS)], rng, two_column=(i == n - 1))
        paths.append(p)
    (out_dir / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    return paths
