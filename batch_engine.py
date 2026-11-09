"""Run the batch engine over samples/ and print the summary.  uv run python batch_engine.py [--limit N]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from menusync.batch import run_batch

HERE = Path(__file__).parent

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=Path, default=HERE / "samples")
    ap.add_argument("--out", type=Path, default=HERE / "output")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if not any(a.samples.glob("*.png")):
        from menusync.samples import generate

        generate(a.samples)
    s = run_batch(a.samples, a.out, a.limit)
    print(json.dumps({k: v for k, v in s.items() if k != "eval"}, indent=2))
    if "eval" in s:
        e = s["eval"]
        print(f"eval vs ground truth: item recall {e['item_recall']:.1%}, price accuracy on found items "
              f"{e['price_accuracy_on_found']:.1%}, item+price {e['item_and_price_accuracy']:.1%}, "
              f"category recall {e['category_recall']:.1%}")  # fmt: skip
