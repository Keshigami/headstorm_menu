"""Batch engine: every image under samples/ -> output/menus.json, output/menus.csv, output/errors.log.
If samples/ground_truth.json exists it also scores extraction accuracy into output/eval.json."""
from __future__ import annotations

import csv
import difflib
import json
import time
import traceback
from pathlib import Path

from menusync.parser import MenuDigitizer, flatten

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()


def evaluate(menus: dict[str, dict], truth: dict[str, dict]) -> dict:
    """Item recall (fuzzy name match >= 0.8), price accuracy on matched items, category recall, per file."""
    per_file = {}
    tot_items = tot_found = tot_price_ok = tot_cats = tot_cats_ok = 0
    for fname, gt in truth.items():
        menu = menus.get(fname)
        if not menu:
            continue
        found_names = [_norm(i["name"]) for c in menu["categories"] for i in c["items"]]
        found_prices = {_norm(i["name"]): i["price"] for c in menu["categories"] for i in c["items"]}
        found_cats = [_norm(c["name"]) for c in menu["categories"]]
        n_items = n_found = n_price_ok = 0
        for c in gt["categories"]:
            tot_cats += 1
            if difflib.get_close_matches(_norm(c["name"]), found_cats, n=1, cutoff=0.8):
                tot_cats_ok += 1
            for it in c["items"]:
                n_items += 1
                m = difflib.get_close_matches(_norm(it["name"]), found_names, n=1, cutoff=0.8)
                if m:
                    n_found += 1
                    if found_prices.get(m[0]) is not None and abs(found_prices[m[0]] - it["price"]) < 0.005:
                        n_price_ok += 1
        per_file[fname] = {"items": n_items, "found": n_found, "price_ok": n_price_ok,
                           "item_recall": round(n_found / max(n_items, 1), 3),
                           "price_accuracy": round(n_price_ok / max(n_found, 1), 3)}  # fmt: skip
        tot_items += n_items
        tot_found += n_found
        tot_price_ok += n_price_ok
    return {
        "files": len(per_file),
        "items": tot_items,
        "item_recall": round(tot_found / max(tot_items, 1), 3),
        "price_accuracy_on_found": round(tot_price_ok / max(tot_found, 1), 3),
        "item_and_price_accuracy": round(tot_price_ok / max(tot_items, 1), 3),
        "category_recall": round(tot_cats_ok / max(tot_cats, 1), 3),
        "per_file": per_file,
    }


def run_batch(samples_dir: Path, out_dir: Path, limit: int | None = None, log=print) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in samples_dir.iterdir() if p.suffix.lower() in IMAGE_EXT)[:limit]
    digitizer = MenuDigitizer()
    menus: dict[str, dict] = {}
    rows: list[dict] = []
    errors: list[str] = []
    t0 = time.perf_counter()
    for i, p in enumerate(files, 1):
        s = time.perf_counter()
        try:
            menu = digitizer.process(str(p))
            menu.pop("_lines", None)
            menus[p.name] = menu
            rows.extend(flatten(menu, p.name))
            log(f"[{i}/{len(files)}] {p.name}: {menu['n_items']} items, {menu['n_priced']} priced, "
                f"{time.perf_counter() - s:.1f}s")  # fmt: skip
        except Exception as e:  # noqa: BLE001 - per-file failure is logged, batch continues
            errors.append(f"{p.name}: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            log(f"[{i}/{len(files)}] {p.name}: FAILED {type(e).__name__}: {e}")
    elapsed = time.perf_counter() - t0
    (out_dir / "menus.json").write_text(json.dumps(menus, indent=2))
    with (out_dir / "menus.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["file", "restaurant", "category", "item", "price", "confidence"])
        wr.writeheader()
        wr.writerows(rows)
    (out_dir / "errors.log").write_text("\n".join(errors))
    summary = {
        "files": len(files),
        "succeeded": len(menus),
        "failed": len(errors),
        "items": len(rows),
        "priced": sum(1 for r in rows if r["price"] is not None),
        "seconds": round(elapsed, 2),
        "seconds_per_file": round(elapsed / max(len(files), 1), 2),
        "outputs": [str(out_dir / n) for n in ("menus.json", "menus.csv", "errors.log")],
    }
    gt = samples_dir / "ground_truth.json"
    if gt.exists():
        summary["eval"] = evaluate(menus, json.loads(gt.read_text()))
        (out_dir / "eval.json").write_text(json.dumps(summary["eval"], indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary
